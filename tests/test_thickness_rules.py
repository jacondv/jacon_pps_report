"""
Thickness rules: |d| < 12 mm -> 0, every other value is |d|; points above
the max measurable thickness are noise — masked out of the thickness
figures and the distribution, but still used for the total surface area,
colored separately in 3D, and reported as a warning under the report chart.

BPA is replaced by a stub that returns the number of points it was given,
so the area figures show exactly which points went into each mesh.
"""

import numpy as np
import pytest

from pps.core import calculator
from pps.core.calculator import (
    CalculationResult,
    calculate_area_and_volume,
    calculate_thickness_distribution,
    clean_distances,
    in_range_mask,
)
from pps.render.layer_renderer import threshold_colors
from pps.report.core.html_pdf_generator import HTMLPDFGenerator


@pytest.fixture
def count_points_area(monkeypatch):
    monkeypatch.setattr(calculator, "bpa_surface_area", lambda pcd, radii: float(len(pcd.points)))


def test_clean_distances_zeroes_below_12_and_takes_abs():
    d = np.array([-11.9, 11.9, -12.0, 12.0, -40.0, 0.0])
    np.testing.assert_array_equal(clean_distances(d), [0, 0, 12, 12, 40, 0])
    assert d[0] == -11.9  # input untouched


def test_in_range_mask_keeps_the_limit_itself():
    d = np.array([0.0, 299.9, 300.0, 300.1, -350.0])
    np.testing.assert_array_equal(in_range_mask(d, 300.0), [True, True, True, False, False])


def test_out_of_range_points_are_excluded_from_thickness_but_not_from_area(count_points_area):
    # 200 points within target (50 mm), 100 noise points (450 mm), 50 no-damage points.
    distances = np.concatenate([np.full(200, 50.0), np.full(100, -450.0), np.full(50, 5.0)])
    points = np.random.default_rng(0).random((len(distances), 3))

    calc = calculate_area_and_volume(points, distances.copy(), target_min=40, max_measurable_mm=300)

    assert calc.num_points == 350
    assert calc.out_of_range_count == 100
    assert calc.out_of_range_percent == pytest.approx(100 * 100 / 350)
    assert calc.surface_area_m2 == 350          # total area: every point
    assert calc.area_reached_target_m2 == 200   # reached area: no noise points
    assert calc.mean_thickness_mm == pytest.approx(50.0)
    assert calc.max_thickness_mm == pytest.approx(50.0)
    assert calc.volume_m3 == pytest.approx(200 * 50.0 / 1000)


def test_max_measurable_is_configurable(count_points_area):
    distances = np.concatenate([np.full(200, 50.0), np.full(100, 450.0)])
    points = np.zeros((len(distances), 3))

    calc = calculate_area_and_volume(points, distances, target_min=40, max_measurable_mm=500)

    assert calc.out_of_range_count == 0
    assert calc.area_reached_target_m2 == 300
    assert calc.max_measurable_mm == 500


def test_calculation_does_not_modify_distances(count_points_area):
    distances = np.array([5.0, -50.0, 450.0] * 50)
    before = distances.copy()
    calculate_area_and_volume(np.zeros((len(distances), 3)), distances, target_min=40)
    np.testing.assert_array_equal(distances, before)


def test_distribution_leaves_out_noise_points():
    distances = np.array([5.0, 30.0, 50.0, 55.0, 80.0, 300.0, 300.1, -450.0])
    dist = calculate_thickness_distribution(distances, 40, 60, max_measurable_mm=300)

    assert (dist.below_target, dist.within_target, dist.above_target) == (2, 2, 2)
    assert dist.below_target_percent + dist.within_target_percent + dist.above_target_percent == pytest.approx(100)
    assert dist.histogram_counts.sum() == 6


def test_noise_points_get_their_own_color():
    noise = (0.5, 0.8, 1.0)
    colors = threshold_colors(
        np.array([10.0, 50.0, 100.0, 300.0, 301.0]), 40, 60,
        color_below=(1, 0, 0), color_within=(0, 1, 0), color_above=(0, 0, 1),
        max_measurable_mm=300, color_out_of_range=noise,
    )
    np.testing.assert_allclose(colors[3], (0, 0, 1))
    np.testing.assert_allclose(colors[4], noise)


def _result(out_of_range_count, num_points=1000, max_mm=300.0):
    return CalculationResult(
        surface_area_m2=1, volume_m3=1, mean_thickness_mm=1, min_thickness_mm=1,
        max_thickness_mm=1, std_thickness_mm=1, num_points=num_points,
        out_of_range_count=out_of_range_count, max_measurable_mm=max_mm,
    )


def test_report_warning_text():
    note = HTMLPDFGenerator._out_of_range_note(_result(1234, num_points=20000))
    assert note == (
        "1,234 points (6.2%) exceed the measurable range (300 mm) and were "
        "excluded from the thickness figures - possibly noise."
    )


def test_report_warning_hidden_without_noise():
    assert HTMLPDFGenerator._out_of_range_note(_result(0)) is None
    assert HTMLPDFGenerator._out_of_range_note(None) is None
