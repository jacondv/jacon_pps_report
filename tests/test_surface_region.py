import numpy as np

from pps.core.surface_region import nearest_point, points_inside_outline


def _square_outline(z=0.0):
    return [(0.0, 0.0, z), (10.0, 0.0, z), (10.0, 10.0, z), (0.0, 10.0, z)]


def test_points_inside_flat_outline_including_outline_points():
    points = np.array([
        [5.0, 5.0, 0.0],    # inside
        [0.0, 0.0, 0.0],    # an outline vertex
        [5.0, 0.0, 0.0],    # on an outline edge
        [15.0, 5.0, 0.0],   # outside
    ])
    mask = points_inside_outline(points, _square_outline())
    assert mask.tolist() == [True, True, True, False]


def test_winding_direction_does_not_matter():
    points = np.array([[5.0, 5.0, 0.0], [0.0, 0.0, 0.0], [15.0, 5.0, 0.0]])
    clockwise = points_inside_outline(points, _square_outline())
    counter_clockwise = points_inside_outline(points, _square_outline()[::-1])
    assert clockwise.tolist() == counter_clockwise.tolist() == [True, True, False]


def test_surface_behind_the_region_is_excluded():
    points = np.array([[5.0, 5.0, 0.0], [5.0, 5.0, -3.0], [5.0, 5.0, 3.0]])
    mask = points_inside_outline(points, _square_outline())
    assert mask.tolist() == [True, False, False]


def test_curved_patch_keeps_its_bulge():
    # Outline on the rim of a shallow dome; the dome's top bulges above the
    # outline's plane by more than the margin, but the outline itself bends
    # just as much, so the whole patch is kept.
    angles = np.linspace(0, 2 * np.pi, 24, endpoint=False)
    rim_z = 0.5 * np.cos(angles) ** 2
    outline = list(zip(5 + 5 * np.cos(angles), 5 + 5 * np.sin(angles), rim_z))
    points = np.array([[5.0, 5.0, 0.6], [5.0, 5.0, 5.0]])
    mask = points_inside_outline(points, outline)
    assert mask.tolist() == [True, False]


def test_tilted_outline():
    # Same square, rotated 45 degrees about the x axis.
    c = np.cos(np.pi / 4)
    outline = [(x, y * c, y * c) for x, y, _ in _square_outline()]
    inside = (5.0, 5.0 * c, 5.0 * c)
    outside = (5.0, 15.0 * c, 15.0 * c)
    mask = points_inside_outline(np.array([inside, outside]), outline)
    assert mask.tolist() == [True, False]


def test_degenerate_input():
    assert points_inside_outline(np.zeros((3, 3)), _square_outline()[:2]).tolist() == [False] * 3
    assert len(points_inside_outline(np.empty((0, 3)), _square_outline())) == 0


def test_nearest_point():
    points = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [5.0, 5.0, 5.0]])
    assert nearest_point(points, (0.9, 1.2, 1.0)) == (1.0, 1.0, 1.0)
