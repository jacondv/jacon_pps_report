"""
Reference implementation of the open3d-free surface-area method chosen in
PLAN.md Phase 3.2 (block-wise VTK Delaunay). Prototype only — the agent ports
this into src/pps/core/surface_area.py with tests; do not import it from src/.

Depends only on numpy + pyvista (VTK), which the app already ships.

Run (repo root):
    .venv\\Scripts\\python docs\\dep-slimming\\reference_area.py
"""
import os
import sys
import time

import numpy as np
import pyvista as pv

VOXEL_M = 0.025          # = min(radii) / 2, same as the old open3d pipeline
OUTLIER_RADIUS_M = 0.1   # = 2 * min(radii)
OUTLIER_MIN_POINTS = 8   # neighbours incl. the point itself, as open3d counts
BLOCK_SIZE_M = 1.0
BLOCK_MARGIN_M = 0.25
R_MAX_M = 0.07           # max 3D circumradius of a kept triangle


def voxel_down(points, voxel):
    """Centroid of the points in each occupied voxel."""
    keys = np.floor(points / voxel).astype(np.int64)
    _, inverse, counts = np.unique(keys, axis=0, return_inverse=True, return_counts=True)
    inverse = inverse.ravel()
    out = np.empty((len(counts), 3))
    for d in range(3):
        out[:, d] = np.bincount(inverse, points[:, d], minlength=len(counts))
    return out / counts[:, None]


def neighbour_counts(points, radius, chunk=8000):
    """Number of points within `radius` of each point (incl. itself), using a
    uniform grid with cell = radius and the 27 surrounding cells."""
    n = len(points)
    key = np.floor(points / radius).astype(np.int64)
    key -= key.min(0)
    dims = key.max(0) + 3
    cell = (key[:, 0] * dims[1] + key[:, 1]) * dims[2] + key[:, 2]
    order = np.argsort(cell, kind="stable")
    uniq, start = np.unique(cell[order], return_index=True)
    end = np.append(start[1:], n)
    offsets = np.array([(a * dims[1] + b) * dims[2] + c
                        for a in (-1, 0, 1) for b in (-1, 0, 1) for c in (-1, 0, 1)])
    r2 = radius * radius
    counts = np.zeros(n, np.int64)
    for s in range(0, n, chunk):
        idx = np.arange(s, min(s + chunk, n))
        q = cell[idx][:, None] + offsets[None, :]
        pos = np.minimum(np.searchsorted(uniq, q), len(uniq) - 1)
        hit = uniq[pos] == q
        st = np.where(hit, start[pos], 0).ravel()
        ln = np.where(hit, end[pos] - start[pos], 0).ravel()
        owner = np.repeat(np.repeat(idx, 27), ln)
        cand = order[np.repeat(st - np.cumsum(ln) + ln, ln) + np.arange(ln.sum())]
        inside = ((points[owner] - points[cand]) ** 2).sum(1) <= r2
        counts[idx] = np.bincount(owner[inside] - s, minlength=len(idx))
    return counts


def preprocess(points):
    p = voxel_down(np.asarray(points, dtype=np.float64), VOXEL_M)
    if len(p) == 0:
        return p
    return p[neighbour_counts(p, OUTLIER_RADIUS_M) >= OUTLIER_MIN_POINTS]


def _cross(a, b):
    return np.stack([a[:, 1] * b[:, 2] - a[:, 2] * b[:, 1],
                     a[:, 2] * b[:, 0] - a[:, 0] * b[:, 2],
                     a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]], -1)


def surface_area(points):
    """Surface area (m²) of a point cloud: voxel + outlier filter, then per
    1 m block a 2D Delaunay on the block's PCA plane, keeping triangles whose
    3D circumradius <= R_MAX_M and whose centroid lies in the block core."""
    p = preprocess(points)
    if len(p) < 3:
        return 0.0
    origin = p.min(0)
    total = 0.0
    for k in np.unique(np.floor((p - origin) / BLOCK_SIZE_M).astype(np.int64), axis=0):
        lo = origin + k * BLOCK_SIZE_M
        hi = lo + BLOCK_SIZE_M
        q = p[np.all((p >= lo - BLOCK_MARGIN_M) & (p < hi + BLOCK_MARGIN_M), axis=1)]
        if len(q) < 3:
            continue
        mu = q.mean(0)
        _, _, vt = np.linalg.svd(q - mu, full_matrices=False)
        uv = (q - mu) @ vt[:2].T
        faces = pv.PolyData(np.column_stack([uv, np.zeros(len(uv))])).delaunay_2d().faces
        if len(faces) == 0:
            continue
        f = faces.reshape(-1, 4)[:, 1:]
        a, b, c = q[f[:, 0]], q[f[:, 1]], q[f[:, 2]]
        ab, ac = b - a, c - a
        n = _cross(ab, ac)
        nn = (n * n).sum(1)
        ok = nn > 1e-24
        nn_safe = np.where(ok, nn, 1.0)
        off = ((ac * ac).sum(1)[:, None] * _cross(n, ab)
               + (ab * ab).sum(1)[:, None] * _cross(ac, n)) / (2 * nn_safe[:, None])
        ok &= (off * off).sum(1) <= R_MAX_M ** 2
        g = (a + b + c) / 3
        ok &= np.all((g >= lo) & (g < hi), axis=1)
        total += 0.5 * np.sqrt(nn[ok]).sum()
    return float(total)


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, os.path.join(root, "src"))
    from pps.core.ply_loader import load_ply

    cloud = load_ply(os.path.join(root, "sample", "2_thickness_01#20260203_093652#cloud_compared_07.ply"),
                     "distances")
    pts, d = cloud.points, cloud.distances.copy()
    d[np.abs(d) < 12] = 0
    d[np.abs(d) > 500] = 0
    open3d_ref = {"full": 99.748, 20: 16.588, 40: 14.154, 50: 13.775, 100: 11.727}
    for key, ref in open3d_ref.items():
        x = pts if key == "full" else pts[d > key]
        t = time.perf_counter()
        a = surface_area(x)
        print(f"{str(key):>5}: {a:8.3f} m²  vs open3d {ref:8.3f}  ({100 * (a / ref - 1):+5.1f}%)  "
              f"{time.perf_counter() - t:.2f}s")

    rng = np.random.default_rng(0)
    th, z = np.meshgrid(np.arange(0, np.pi, 0.01 / 3), np.arange(0, 2, 0.01))
    cyl = np.column_stack([3 * np.cos(th.ravel()), 3 * np.sin(th.ravel()), z.ravel()])
    cyl += rng.normal(0, 0.003, cyl.shape)
    g = np.stack(np.meshgrid(np.arange(0, 2, 0.01), np.arange(0, 3, 0.01)), -1).reshape(-1, 2)
    g = g[np.hypot(g[:, 0] - 1, g[:, 1] - 1.5) > 0.5]
    plane = np.column_stack([g, rng.normal(0, 0.003, len(g))])
    for name, x, true in (("half-cylinder R3 L2", cyl, np.pi * 6), ("plane 2x3 hole R0.5", plane, 6 - np.pi * 0.25)):
        a = surface_area(x)
        print(f"{name}: {a:.3f} m²  true {true:.3f}  ({100 * (a / true - 1):+.1f}%)")
        a2 = surface_area(x + 0.3)
        print(f"  shifted +0.3 m: {a2:.3f} ({100 * (a2 / a - 1):+.2f}%)")
