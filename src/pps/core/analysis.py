"""
Run the area/volume/distribution calculation pipeline.

Both steps clean the distances the same way (|d|, < 12 mm -> 0) and leave
out points above `max_measurable_mm`; neither modifies `distances`.
"""

from typing import Tuple

import numpy as np

from pps.core.calculator import (
    DEFAULT_MAX_MEASURABLE_MM,
    CalculationResult,
    ThicknessDistribution,
    calculate_area_and_volume,
    calculate_thickness_distribution,
)
from pps.core.surface_area import surface_area

# Same radii as calculate_area_and_volume() uses for the report's surface
# area — the Measure Area tool must stay consistent with the report number.
AREA_MEASUREMENT_RADII = (0.05, 0.1)


def run_analysis(
    points: np.ndarray,
    distances: np.ndarray,
    target_min: float,
    target_max: float,
    max_measurable_mm: float = DEFAULT_MAX_MEASURABLE_MM,
) -> Tuple[CalculationResult, ThicknessDistribution]:
    calc = calculate_area_and_volume(
        points, distances, target_min=target_min, max_measurable_mm=max_measurable_mm
    )
    dist = calculate_thickness_distribution(
        distances, target_min, target_max, max_measurable_mm=max_measurable_mm
    )
    return calc, dist


def compute_area_m2(points: np.ndarray, radii: Tuple[float, float] = AREA_MEASUREMENT_RADII) -> float:
    """Surface area (m²) of a raw point set via the same BPA method/radii
    used for the report's surface area — used by the Measure Area tool."""
    import open3d as o3d

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(np.asarray(points, dtype=np.float64))
    return surface_area(pcd, radii=radii)
