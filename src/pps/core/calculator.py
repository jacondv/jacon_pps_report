"""
Calculate surface area and volume from point cloud data.
Uses surface reconstruction and thickness information.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional

from pps.core.surface_area import surface_area as bpa_surface_area

from pps.utils.timing import timeit

# |d| below this is treated as "no damage" and set to 0.
NO_DAMAGE_THRESHOLD_MM = 12.0
# Default upper limit of the PPS hardware's measurable range. Points above
# it are treated as noise: excluded from every thickness figure and from the
# distribution, but still used for the surface area. User-configurable in
# Settings (AppSettings.max_measurable_mm).
DEFAULT_MAX_MEASURABLE_MM = 300.0


def clean_distances(distances: np.ndarray) -> np.ndarray:
    """Return |distances| with values below NO_DAMAGE_THRESHOLD_MM set to 0.

    Returns a new array; the input is never modified.
    """
    cleaned = np.abs(np.asarray(distances, dtype=np.float64))
    cleaned[cleaned < NO_DAMAGE_THRESHOLD_MM] = 0.0
    return cleaned


def in_range_mask(distances: np.ndarray, max_measurable_mm: float) -> np.ndarray:
    """True for points inside the measurable range (|d| <= max_measurable_mm).
    A point exactly at the limit is kept."""
    return np.abs(np.asarray(distances)) <= max_measurable_mm


@dataclass
class CalculationResult:
    """Results from area and volume calculations."""
    surface_area_m2: float  # Surface area in square meters
    volume_m3: float  # Volume in cubic meters
    mean_thickness_mm: float  # Mean thickness in mm
    min_thickness_mm: float
    max_thickness_mm: float
    std_thickness_mm: float
    num_points: int
    area_reached_target_m2: float = 0
    out_of_range_count: int = 0  # points with |d| > max_measurable_mm (noise)
    max_measurable_mm: float = DEFAULT_MAX_MEASURABLE_MM

    @property
    def out_of_range_percent(self) -> float:
        if self.num_points > 0:
            return 100 * self.out_of_range_count / self.num_points
        return 0.0

    @property
    def surface_area_cm2(self) -> float:
        return self.surface_area_m2 * 10000

    @property
    def area_reached_target(self) -> float:
        return self.area_reached_target_m2 

    @property
    def volume_liters(self) -> float:
        return self.volume_m3 * 1000
    @property
    def area_reached_target_percent(self) -> Optional[float]:
        if self.surface_area_m2 > 0:
            return 100 * self.area_reached_target_m2 / self.surface_area_m2
        return None


@dataclass
class ThicknessDistribution:
    """Thickness distribution for histogram."""
    below_target: int  # Points below target thickness
    within_target: int  # Points within target range
    above_target: int  # Points above target thickness
    
    below_target_percent: float
    within_target_percent: float
    above_target_percent: float
    
    histogram_bins: np.ndarray
    histogram_counts: np.ndarray
    
    target_min: float
    target_max: float



@timeit
def _extract_points_and_distances(cloud):
    """Extract point and thickness arrays from a cloud-like object."""
    if cloud is None:
        return np.empty((0, 3), dtype=np.float64), np.empty((0,), dtype=np.float64)

    if isinstance(cloud, tuple) and len(cloud) == 2:
        pts, dists = cloud
        return np.asarray(pts, dtype=np.float64), np.asarray(dists, dtype=np.float64)

    if hasattr(cloud, 'points') and hasattr(cloud, 'distances'):
        return np.asarray(cloud.points, dtype=np.float64), np.asarray(cloud.distances, dtype=np.float64)

    raise TypeError(
        "cloud must be a tuple (points, distances) or an object with .points and .distances"
    )



@timeit
def _to_open3d_pointcloud(cloud, points=None):
    """Convert a cloud-like object into an Open3D PointCloud."""
    try:
        import open3d as o3d
    except ImportError as exc:
        raise ImportError("Open3D is required for BPA surface estimation") from exc

    if isinstance(cloud, o3d.geometry.PointCloud):
        return cloud

    if points is None and hasattr(cloud, 'points'):
        points = cloud.points

    if points is None:
        raise TypeError("Cannot convert cloud to Open3D PointCloud; no point data available")

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(np.asarray(points, dtype=np.float64))
    return pcd


@timeit
def calculate_area_and_volume(
    *args,
    method: str = "bpa",
    target_min=None,
    max_measurable_mm: float = DEFAULT_MAX_MEASURABLE_MM,
) -> CalculationResult:
    """
    Calculate surface area and volume from a cloud-like object.

    Thickness rules:
      * |d| < 12 mm is set to 0 (no damage); every other value is |d|.
      * |d| > max_measurable_mm is noise: masked out of the "reached" points
        (so out of mean/min/max/std, reached area and volume) but still part
        of the total surface area.
      * A point reaches the target when d > target_min (default 20 mm).

    Volume = reached area x mean thickness of the reached points.

    Args:
        *args: Either (cloud,) where cloud has .points and .distances or is a
               tuple/list (points, distances), or (points, distances).
        method: Ignored. BPA is always used for surface area estimation.
        target_min: Lower bound of the target range (mm).
        max_measurable_mm: Upper limit of the measurable range (mm).

    Returns:
        CalculationResult with area and volume. `distances` is not modified.
    """
    if len(args) == 1:
        cloud = args[0]
    elif len(args) == 2:
        cloud = (args[0], args[1])
    else:
        raise TypeError(
            "calculate_area_and_volume() takes either a single cloud object or two arguments (points, distances)."
        )

    points, distances = _extract_points_and_distances(cloud)

    if len(points) == 0:
        return CalculationResult(
            surface_area_m2=0,
            volume_m3=0,
            mean_thickness_mm=0,
            min_thickness_mm=0,
            max_thickness_mm=0,
            std_thickness_mm=0,
            num_points=0,
            area_reached_target_m2=0,
            max_measurable_mm=max_measurable_mm,
        )

    cleaned = clean_distances(distances)
    in_range = in_range_mask(cleaned, max_measurable_mm)
    out_of_range_count = int(np.count_nonzero(cleaned > max_measurable_mm))

    min_reached_thickness_mm = target_min if target_min is not None else 20
    mask_reached_target = in_range & (cleaned > min_reached_thickness_mm)

    reached_points = points[mask_reached_target]
    reached_distances = cleaned[mask_reached_target]
    if len(reached_points) < 100:
        reached_area = 0.0
    else:
        reached_pcd = _to_open3d_pointcloud(None, reached_points)
        reached_area = bpa_surface_area(reached_pcd, radii=(0.05, 0.1))  # m²

    has_reached = len(reached_distances) > 0
    avg_thickness_mm = float(reached_distances.mean()) if has_reached else 0.0

    # Total area uses every point, out-of-range ones included: dropping
    # them would punch holes in the surface.
    pcd = _to_open3d_pointcloud(cloud, points)
    total_area_m2 = bpa_surface_area(pcd, radii=(0.05, 0.1))
    volume_m3 = reached_area * avg_thickness_mm / 1000

    return CalculationResult(
        surface_area_m2=total_area_m2,
        volume_m3=volume_m3,
        mean_thickness_mm=avg_thickness_mm,
        min_thickness_mm=float(np.min(reached_distances)) if has_reached else 0.0,
        max_thickness_mm=float(np.max(reached_distances)) if has_reached else 0.0,
        std_thickness_mm=float(np.std(reached_distances)) if has_reached else 0.0,
        num_points=len(points),
        area_reached_target_m2=reached_area,
        out_of_range_count=out_of_range_count,
        max_measurable_mm=max_measurable_mm,
    )


@timeit
def calculate_thickness_distribution(distances: np.ndarray,
                                    target_min: float,
                                    target_max: float,
                                    num_bins: int = 50,
                                    max_measurable_mm: float = DEFAULT_MAX_MEASURABLE_MM,
                                    ) -> ThicknessDistribution:
    """
    Calculate thickness distribution for histogram.

    Distances are cleaned the same way as in calculate_area_and_volume()
    (|d|, < 12 mm -> 0), and out-of-range points (> max_measurable_mm) are
    left out entirely, so counts and percentages cover in-range points only.

    Args:
        distances: Array of thickness values in mm (not modified)
        target_min: Minimum target thickness (mm)
        target_max: Maximum target thickness (mm)
        num_bins: Number of histogram bins
        max_measurable_mm: Upper limit of the measurable range (mm)

    Returns:
        ThicknessDistribution with histogram data
    """
    finite = np.asarray(distances, dtype=np.float64)
    finite = finite[np.isfinite(finite)]
    cleaned = clean_distances(finite)
    valid = cleaned[in_range_mask(cleaned, max_measurable_mm)]

    if len(valid) == 0:
        return ThicknessDistribution(
            below_target=0,
            within_target=0,
            above_target=0,
            below_target_percent=0,
            within_target_percent=0,
            above_target_percent=0,
            histogram_bins=np.array([]),
            histogram_counts=np.array([]),
            target_min=target_min,
            target_max=target_max
        )
    
    # Count points in each category
    below = np.sum(valid < target_min)
    within = np.sum((valid >= target_min) & (valid <= target_max))
    above = np.sum(valid > target_max)
    
    total = len(valid)
    
    # Create histogram
    hist_min = max(0, valid.min() - 10)
    hist_max = valid.max() + 10
    bins = np.linspace(hist_min, hist_max, num_bins + 1)
    counts, _ = np.histogram(valid, bins=bins)
    
    return ThicknessDistribution(
        below_target=int(below),
        within_target=int(within),
        above_target=int(above),
        below_target_percent=100 * below / total,
        within_target_percent=100 * within / total,
        above_target_percent=100 * above / total,
        histogram_bins=bins,
        histogram_counts=counts,
        target_min=target_min,
        target_max=target_max
    )
