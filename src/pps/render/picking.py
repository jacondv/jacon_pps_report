"""
Screen-space projection and hit-testing.

`project_to_screen` mirrors PointCloudViewer._project_to_screen() from the
old code exactly (same matrix math), so polygon/rectangle/lasso selection
behaves identically to before.
"""

from typing import List, Optional, Tuple

import numpy as np
from vtkmodules.vtkRenderingCore import vtkPointPicker
from matplotlib.path import Path


def project_to_screen(points: np.ndarray, plotter) -> Optional[np.ndarray]:
    """Project 3D world points to 2D screen pixels (VTK convention: origin
    bottom-left), using the plotter's current camera. Returns None on any
    VTK/camera error (e.g. degenerate view) instead of raising, matching
    the old code's tolerance for a bad frame.
    """
    projected = project_to_screen_with_depth(points, plotter)
    return None if projected is None else projected[0]


def project_to_screen_with_depth(
    points: np.ndarray, plotter
) -> Optional[Tuple[np.ndarray, np.ndarray]]:
    """Like project_to_screen, plus each point's distance in front of the
    camera along the view direction (smaller = nearer; <= 0 = behind the
    camera). Works for both perspective and parallel projection."""
    try:
        renderer = plotter.renderer
        camera = renderer.GetActiveCamera()
        aspect = renderer.GetTiledAspectRatio()

        def to_np(matrix):
            return np.array(
                [[matrix.GetElement(i, j) for j in range(4)] for i in range(4)],
                dtype=np.float64,
            )

        view = to_np(camera.GetViewTransformMatrix())
        proj = to_np(camera.GetProjectionTransformMatrix(aspect, -1, 1))

        n = len(points)
        homogeneous = np.ones((n, 4), dtype=np.float64)
        homogeneous[:, :3] = points

        eye = homogeneous @ view.T  # camera looks down -z in eye space
        clip = eye @ proj.T
        w = clip[:, 3:4]
        w = np.where(np.abs(w) < 1e-10, 1e-10, w)
        ndc = clip[:, :2] / w

        width, height = plotter.ren_win.GetSize()
        sx = (ndc[:, 0] + 1.0) * 0.5 * width
        sy = (ndc[:, 1] + 1.0) * 0.5 * height

        return np.column_stack([sx, sy]), -eye[:, 2]
    except Exception:
        return None


def drape_on_surface(
    screen_points: List[Tuple[float, float]], points: np.ndarray, plotter, radius_px: float = 6.0
) -> List[Tuple[float, float, float]]:
    """Map screen positions onto the visible cloud surface.

    For each screen position, returns the cloud point nearest the camera
    among those projecting within `radius_px` of it — i.e. the point the
    user sees there, never one hidden behind it. Positions with no cloud
    point nearby (drawn off the cloud) are dropped, so the result can be
    shorter than the input. Vectorized over the whole cloud instead of one
    vtkPointPicker ray cast per position, which is too slow for an outline
    of a few hundred samples.
    """
    if len(points) == 0 or not screen_points:
        return []
    projected = project_to_screen_with_depth(points, plotter)
    if projected is None:
        return []
    xy, depth = projected
    in_front = depth > 0
    xy, depth, candidates = xy[in_front], depth[in_front], points[in_front]

    draped = []
    r2 = radius_px * radius_px
    for sx, sy in screen_points:
        d2 = (xy[:, 0] - sx) ** 2 + (xy[:, 1] - sy) ** 2
        idx = np.flatnonzero(d2 <= r2)
        if len(idx) == 0:
            continue
        # Nearest to the camera; among equally deep, nearest on screen.
        best = idx[np.lexsort((d2[idx], depth[idx]))[0]]
        point = tuple(float(v) for v in candidates[best])
        if not draped or point != draped[-1]:  # neighboring samples often snap to the same point
            draped.append(point)
    if len(draped) > 1 and draped[0] == draped[-1]:
        draped.pop()
    return draped


def resample_closed_polyline(
    polygon: List[Tuple[float, float]], step: float, max_samples: int = 256
) -> List[Tuple[float, float]]:
    """Evenly spaced points along a closed screen polygon, about `step`
    pixels apart (spacing grows if that would exceed `max_samples`). The
    original vertices are kept so corners stay sharp."""
    pts = np.asarray(polygon, dtype=np.float64)
    closed = np.vstack([pts, pts[:1]])
    edge_lengths = np.linalg.norm(np.diff(closed, axis=0), axis=1)
    step = max(step, float(edge_lengths.sum()) / max_samples)

    samples = []
    for start, end, length in zip(closed[:-1], closed[1:], edge_lengths):
        count = max(1, int(np.ceil(length / step)))
        for t in np.arange(count) / count:
            p = start + (end - start) * t
            samples.append((float(p[0]), float(p[1])))
    return samples


def points_in_polygon(points_2d: np.ndarray, polygon_2d: List[Tuple[float, float]]) -> np.ndarray:
    """Boolean mask of which `points_2d` fall inside the (screen-space)
    polygon. Works for any simple polygon, including a rectangle or a
    freehand lasso path — they're all just a list of vertices here."""
    if len(polygon_2d) < 3 or len(points_2d) == 0:
        return np.zeros(len(points_2d), dtype=bool)
    return Path(polygon_2d).contains_points(points_2d)


def rectangle_to_polygon(p0: Tuple[float, float], p1: Tuple[float, float]) -> List[Tuple[float, float]]:
    """Turn two opposite corners into a 4-vertex polygon for points_in_polygon."""
    x0, y0 = p0
    x1, y1 = p1
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def pick_nearest_point_3d(
    x: float, y: float, plotter, tolerance: float = 0.02
) -> Optional[Tuple[float, float, float]]:
    """Snap to the nearest visible cloud point under the cursor.

    Uses vtkPointPicker, which ray-casts from the given screen pixel and
    returns the closest dataset point within `tolerance` (fraction of the
    renderer's diagonal) — this naturally respects depth (a point behind
    the visible surface from the current angle is never picked) and avoids
    reimplementing nearest-neighbor search ourselves.

    Returns None if no point was within tolerance.
    """
    picker = vtkPointPicker()
    picker.SetTolerance(tolerance)
    picker.Pick(x, y, 0, plotter.renderer)
    if picker.GetPointId() < 0:
        return None
    return tuple(picker.GetPickPosition())
