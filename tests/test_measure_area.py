import numpy as np
import pytest

from pps.render import picking
from pps.scene.document import Document
from pps.scene.measurements import AreaMeasurement
from pps.tools.base import MouseButton, PointerEvent, PointerEventType, ToolContext
from pps.tools.measure_area import MeasureAreaTool
from pps.tools.region_select import RegionMode

GRID_STEP = 5.0
FRONT_Z = 0.0
BACK_Z = -40.0  # a second surface right behind the first, like the opposite tunnel wall


class FakeOverlayRenderer:
    def AddActor(self, actor):
        pass

    def RemoveActor(self, actor):
        pass


class FakeViewport:
    plotter = None


def make_ctx(document, status_calls=None):
    from pps.render.overlay import Overlay

    return ToolContext(
        document=document,
        viewport=FakeViewport(),
        overlay=Overlay(FakeOverlayRenderer()),
        undo_stack=document.undo_stack,
        set_status=(status_calls.append if status_calls is not None else (lambda s: None)),
        request_render=lambda: None,
    )


def _grid(z):
    coords = np.arange(0.0, 100.0 + GRID_STEP, GRID_STEP)
    xx, yy = np.meshgrid(coords, coords)
    return np.column_stack([xx.ravel(), yy.ravel(), np.full(xx.size, z)])


@pytest.fixture
def document_with_two_surfaces(qtbot):
    """A 21x21 grid at z=0 and an identical one 40 units behind it."""
    points = np.vstack([_grid(FRONT_Z), _grid(BACK_Z)])
    doc = Document()
    doc.load_point_cloud(
        source_path="C:/data/sample.ply",
        project_info=None,
        points=points,
        distances=np.full(len(points), 30.0),
        distance_field="distances",
        target_min=0.0,
        target_max=100.0,
    )
    return doc


@pytest.fixture(autouse=True)
def fake_camera(monkeypatch):
    """Camera looking down -z: screen (x, y) = world (x, y), and points with
    larger z are nearer (the front grid hides the back one)."""
    monkeypatch.setattr(
        picking,
        "project_to_screen_with_depth",
        lambda points, plotter: (points[:, :2].copy(), 100.0 - points[:, 2]),
    )


def press(x, y, **kw):
    return PointerEvent(kind=PointerEventType.PRESS, x=x, y=y, button=MouseButton.LEFT, **kw)


def double_click(x, y, **kw):
    return PointerEvent(kind=PointerEventType.DOUBLE_CLICK, x=x, y=y, button=MouseButton.LEFT, **kw)


def draw_square(tool, x0, y0, x1, y1):
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        tool.handle_pointer(press(x, y))
    tool.handle_pointer(double_click(x0, y1))


def test_polygon_area_measurement_uses_enclosed_front_surface_points(document_with_two_surfaces):
    doc = document_with_two_surfaces
    original_id = doc.layer_manager.original.id
    recorded = {}

    def fake_requester(points, on_done):
        recorded["points"] = points
        on_done(42.5)

    tool = MeasureAreaTool(area_requester=fake_requester)
    tool.activate(make_ctx(doc))
    draw_square(tool, 20, 20, 80, 80)

    assert len(doc.measurements) == 1
    measurement = doc.measurements[0]
    assert isinstance(measurement, AreaMeasurement)
    assert measurement.area_m2 == 42.5
    assert measurement.sources[0].layer_id == original_id

    # Grid points from 20 to 80 inclusive on the front surface only: the
    # outline's own points belong to the region, the back surface doesn't.
    enclosed = recorded["points"]
    assert len(enclosed) == 13 * 13
    assert np.all(enclosed[:, 2] == FRONT_Z)
    assert enclosed[:, :2].min() == 20.0 and enclosed[:, :2].max() == 80.0
    assert tool.is_idle()


def test_outline_is_made_of_front_surface_cloud_points(document_with_two_surfaces):
    doc = document_with_two_surfaces
    tool = MeasureAreaTool(area_requester=lambda points, on_done: on_done(1.0))
    tool.activate(make_ctx(doc))
    draw_square(tool, 20, 20, 80, 80)

    outline = np.asarray(doc.measurements[0].outline)
    cloud = {tuple(p) for p in doc.layer_manager.original.points}
    assert len(outline) >= 4
    assert all(tuple(p) in cloud for p in outline)
    assert np.all(outline[:, 2] == FRONT_Z)
    # no consecutive duplicates (neighboring samples snapping to one point)
    assert not np.any(np.all(outline == np.roll(outline, 1, axis=0), axis=1))


def test_label_anchor_is_on_the_surface(document_with_two_surfaces):
    doc = document_with_two_surfaces
    tool = MeasureAreaTool(area_requester=lambda points, on_done: on_done(1.0))
    tool.activate(make_ctx(doc))
    draw_square(tool, 20, 20, 80, 80)

    anchor = doc.measurements[0].centroid
    assert anchor == (50.0, 50.0, FRONT_Z)


def test_area_measurement_none_until_callback_fires(document_with_two_surfaces):
    doc = document_with_two_surfaces
    pending_callbacks = []

    tool = MeasureAreaTool(area_requester=lambda points, on_done: pending_callbacks.append(on_done))
    tool.activate(make_ctx(doc))
    draw_square(tool, 20, 20, 80, 80)

    assert doc.measurements[0].area_m2 is None
    pending_callbacks[0](7.0)
    assert doc.measurements[0].area_m2 == 7.0


def test_area_drawn_off_the_cloud_creates_no_measurement(document_with_two_surfaces):
    doc = document_with_two_surfaces
    status_calls = []
    called = {"count": 0}

    def fake_requester(points, on_done):
        called["count"] += 1

    tool = MeasureAreaTool(area_requester=fake_requester)
    tool.activate(make_ctx(doc, status_calls))
    draw_square(tool, 1000, 1000, 1010, 1010)

    assert len(doc.measurements) == 0
    assert called["count"] == 0
    assert "on the point cloud" in status_calls[-1]


def test_hidden_layer_is_ignored(document_with_two_surfaces):
    doc = document_with_two_surfaces
    doc.set_layer_visible(doc.layer_manager.original.id, False)
    status_calls = []

    tool = MeasureAreaTool(area_requester=lambda points, on_done: on_done(1.0))
    tool.activate(make_ctx(doc, status_calls))
    draw_square(tool, 20, 20, 80, 80)

    assert len(doc.measurements) == 0
    assert "on the point cloud" in status_calls[-1]


def test_rectangle_mode_inherited_from_region_select(document_with_two_surfaces):
    doc = document_with_two_surfaces
    recorded = {}

    def fake_requester(points, on_done):
        recorded["n"] = len(points)
        on_done(1.0)

    tool = MeasureAreaTool(area_requester=fake_requester)
    tool.activate(make_ctx(doc))
    tool.mode = RegionMode.RECTANGLE

    tool.handle_pointer(press(20, 20))
    tool.handle_pointer(PointerEvent(kind=PointerEventType.MOVE, x=80, y=80))
    tool.handle_pointer(PointerEvent(kind=PointerEventType.RELEASE, x=80, y=80, button=MouseButton.LEFT))

    assert recorded["n"] == 13 * 13
    assert len(doc.measurements) == 1
