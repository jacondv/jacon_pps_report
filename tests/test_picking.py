import numpy as np
import pytest

from pps.render import picking
from pps.render.picking import drape_on_surface, resample_closed_polyline


@pytest.fixture
def fake_camera(monkeypatch):
    """screen (x, y) = world (x, y); larger z = nearer the camera."""
    monkeypatch.setattr(
        picking,
        "project_to_screen_with_depth",
        lambda points, plotter: (points[:, :2].copy(), 100.0 - points[:, 2]),
    )


def test_resample_keeps_vertices_and_spacing():
    square = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    samples = resample_closed_polyline(square, step=2.5)
    assert len(samples) == 16
    for vertex in square:
        assert vertex in samples
    gaps = np.linalg.norm(np.diff(np.vstack([samples, samples[:1]]), axis=0), axis=1)
    assert np.allclose(gaps, 2.5)


def test_resample_caps_sample_count():
    square = [(0.0, 0.0), (1000.0, 0.0), (1000.0, 1000.0), (0.0, 1000.0)]
    assert len(resample_closed_polyline(square, step=1.0, max_samples=100)) <= 100


def test_drape_picks_the_nearest_surface_and_drops_misses(fake_camera):
    points = np.array([
        [10.0, 10.0, -5.0],  # behind
        [10.0, 10.0, 0.0],   # in front — visible
        [50.0, 50.0, 0.0],
    ])
    draped = drape_on_surface([(10.0, 10.0), (500.0, 500.0), (50.0, 50.0)], points, plotter=None)
    assert draped == [(10.0, 10.0, 0.0), (50.0, 50.0, 0.0)]


def test_drape_ignores_points_behind_the_camera(fake_camera):
    points = np.array([[10.0, 10.0, 150.0], [10.0, 10.0, 0.0]])  # first has depth < 0
    assert drape_on_surface([(10.0, 10.0)], points, plotter=None) == [(10.0, 10.0, 0.0)]


def test_drape_collapses_repeated_points(fake_camera):
    points = np.array([[0.0, 0.0, 0.0], [10.0, 0.0, 0.0]])
    samples = [(0.0, 0.0), (1.0, 0.0), (10.0, 0.0), (9.0, 0.0), (0.5, 0.0)]
    assert drape_on_surface(samples, points, plotter=None) == [(0.0, 0.0, 0.0), (10.0, 0.0, 0.0)]
