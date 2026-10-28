"""
Points of a cloud enclosed by a closed outline lying on its surface.

The outline is a ring of 3D points draped on the cloud (see
pps.render.picking.drape_on_surface). Selection works in 3D, independent of
the camera: fit a plane to the outline, project both outline and cloud onto
it, keep the points inside the projected polygon — but only those within a
depth band around the outline, so a surface behind or in front of the
region (e.g. the opposite tunnel wall) is never included.

Valid for regions that are roughly a height field over their best-fit plane,
which covers a measured patch of shotcrete; a region wrapping around more
than ~half a tunnel would fold over itself when projected.
"""

from typing import Sequence, Tuple

import numpy as np
from matplotlib.path import Path

Point3D = Tuple[float, float, float]

# Extra depth (m) beyond how far the outline itself bends away from its
# plane — covers bulges inside the region; far smaller than the distance to
# any other surface of a tunnel.
DEPTH_MARGIN_M = 0.2

# Tolerance for a point lying on the outline itself.
_ON_OUTLINE_M = 1e-6


def fit_plane(points: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Least-squares plane through `points`: (centroid, 3x3 basis) where the
    basis rows are two in-plane axes followed by the plane normal."""
    centroid = points.mean(axis=0)
    _, _, vt = np.linalg.svd(points - centroid, full_matrices=False)
    return centroid, vt


def points_inside_outline(
    points: np.ndarray, outline: Sequence[Point3D], depth_margin: float = DEPTH_MARGIN_M
) -> np.ndarray:
    """Boolean mask of the `points` enclosed by the surface `outline`."""
    outline = np.asarray(outline, dtype=np.float64)
    if len(outline) < 3 or len(points) == 0:
        return np.zeros(len(points), dtype=bool)

    centroid, basis = fit_plane(outline)
    outline_local = (outline - centroid) @ basis.T
    points_local = (np.asarray(points, dtype=np.float64) - centroid) @ basis.T

    depth_limit = np.abs(outline_local[:, 2]).max() + depth_margin
    near_surface = np.abs(points_local[:, 2]) <= depth_limit

    mask = np.zeros(len(points), dtype=bool)
    candidates = np.flatnonzero(near_surface)
    if len(candidates):
        polygon = Path(outline_local[:, :2])
        xy = points_local[candidates, :2]
        # The outline is made of cloud points, which belong to the region;
        # grow the polygon by a hair so points on it count as inside.
        # (matplotlib's radius sign depends on the polygon's winding, so
        # take both.)
        mask[candidates] = polygon.contains_points(xy, radius=_ON_OUTLINE_M) | polygon.contains_points(
            xy, radius=-_ON_OUTLINE_M
        )
    return mask


def nearest_point(points: np.ndarray, target: Sequence[float]) -> Point3D:
    """The point of `points` closest to `target` — e.g. to anchor a label on
    the surface rather than at a centroid floating off a curved patch."""
    nearest = points[np.argmin(((points - np.asarray(target)) ** 2).sum(axis=1))]
    return (float(nearest[0]), float(nearest[1]), float(nearest[2]))
