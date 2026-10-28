"""
Syncs Document measurements (distance/area) to on-screen visuals. Listens
to nothing itself — MainWindow (Phase 6) calls sync_one()/remove()/clear()
from Document's measurement_added/changed/removed/reset signal handlers,
keeping this a pure "data -> actors" mapper like LayerRenderer.
"""

from typing import Dict, Iterable, Tuple, Union

import numpy as np
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkPolyData
from vtkmodules.vtkFiltersSources import vtkLineSource
from vtkmodules.vtkRenderingCore import vtkActor, vtkPolyDataMapper

from pps.render.labels import AnchoredLabel, hex_to_rgb, layer_visible as _layer_visible
from pps.scene.measurements import AreaMeasurement, DistanceMeasurement

Measurement = Union[DistanceMeasurement, AreaMeasurement]

# Depth-buffer units an area outline is pulled toward the camera; enough to
# win against cloud points at the same depth, too little to show through the
# cloud when viewed from behind.
OUTLINE_DEPTH_OFFSET_UNITS = -2000.0


class MeasurementRenderer:
    def __init__(self, plotter, overlay):
        self._plotter = plotter
        self._overlay = overlay
        self._labels: Dict[str, AnchoredLabel] = {}
        # Geometry in the 3D scene: a distance's line or an area's outline.
        self._world_actors: Dict[str, vtkActor] = {}

    def sync_all(self, measurements: Iterable[Measurement], layer_manager=None) -> None:
        measurements = list(measurements)
        wanted_ids = {m.id for m in measurements}
        for stale_id in set(self._labels) - wanted_ids:
            self.remove(stale_id)
        for measurement in measurements:
            self.sync_one(measurement, layer_visible=_layer_visible(layer_manager, measurement.layer_id))

    def sync_one(self, measurement: Measurement, layer_visible: bool = True) -> None:
        self.remove(measurement.id)  # rebuild from scratch: simplest correct approach

        if isinstance(measurement, DistanceMeasurement):
            self._sync_distance(measurement, layer_visible)
        else:
            self._sync_area(measurement, layer_visible)

    def remove(self, measurement_id: str) -> None:
        label = self._labels.pop(measurement_id, None)
        if label is not None:
            label.remove()

        actor = self._world_actors.pop(measurement_id, None)
        if actor is not None:
            try:
                self._plotter.renderer.RemoveActor(actor)
            except Exception:
                pass

    def clear(self) -> None:
        for measurement_id in set(self._labels) | set(self._world_actors):
            self.remove(measurement_id)

    def set_highlighted(self, measurement_id) -> None:
        """Highlight exactly one measurement's label (or none), e.g.
        following selection in the Project dock's tree."""
        for mid, label in self._labels.items():
            label.set_highlighted(mid == measurement_id)

    def move_live(self, measurement_id, offset_px=None) -> None:
        """Move a measurement's label live during a drag. Not currently
        reachable (dragging is only wired up for notes/annotations), kept
        symmetric with NoteRenderer.move_live for when it is."""
        label = self._labels.get(measurement_id)
        if label is not None and offset_px is not None:
            label.set_offset(offset_px)

    # ------------------------------------------------------------------ distance
    def _sync_distance(self, measurement: DistanceMeasurement, layer_visible: bool) -> None:
        visible = measurement.visible and layer_visible
        line_source = vtkLineSource()
        line_source.SetPoint1(*measurement.p1)
        line_source.SetPoint2(*measurement.p2)
        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(line_source.GetOutputPort())
        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*hex_to_rgb(measurement.color))
        actor.GetProperty().SetLineWidth(2.0)
        actor.SetVisibility(visible)
        self._plotter.renderer.AddActor(actor)
        self._world_actors[measurement.id] = actor

        midpoint = _midpoint(measurement.p1, measurement.p2)
        label = AnchoredLabel(
            self._plotter,
            self._overlay,
            anchor=midpoint,
            text=f"{measurement.distance_m:.3f} m",
            offset_px=measurement.label_offset_px,
            color=measurement.color,
            marker_radius=0.0,  # the line itself marks the segment; no extra sphere
        )
        label.set_visible(visible)
        self._labels[measurement.id] = label

    # ------------------------------------------------------------------ area
    def _sync_area(self, measurement: AreaMeasurement, layer_visible: bool) -> None:
        visible = measurement.visible and layer_visible
        if len(measurement.outline) >= 3:
            actor = _outline_actor(measurement.outline, measurement.color)
            actor.SetVisibility(visible)
            self._plotter.renderer.AddActor(actor)
            self._world_actors[measurement.id] = actor

        text = "…" if measurement.area_m2 is None else f"{measurement.area_m2:.2f} m²"
        label = AnchoredLabel(
            self._plotter,
            self._overlay,
            anchor=measurement.centroid,
            text=text,
            offset_px=measurement.label_offset_px,
            color=measurement.color,
        )
        label.set_visible(visible)
        self._labels[measurement.id] = label


def _outline_actor(outline, color: str) -> vtkActor:
    """Closed polyline through the outline's cloud points. It lies exactly
    on the surface, so it is drawn as thick tubes and pulled slightly toward
    the camera to stay visible over the (equally deep) rendered points."""
    points = vtkPoints()
    for p in outline:
        points.InsertNextPoint(*p)
    ring = vtkCellArray()
    ring.InsertNextCell(len(outline) + 1)
    for i in list(range(len(outline))) + [0]:
        ring.InsertCellPoint(i)
    poly = vtkPolyData()
    poly.SetPoints(points)
    poly.SetLines(ring)

    mapper = vtkPolyDataMapper()
    mapper.SetInputData(poly)
    mapper.SetResolveCoincidentTopologyToPolygonOffset()
    mapper.SetRelativeCoincidentTopologyLineOffsetParameters(0.0, OUTLINE_DEPTH_OFFSET_UNITS)

    actor = vtkActor()
    actor.SetMapper(mapper)
    prop = actor.GetProperty()
    prop.SetColor(*hex_to_rgb(color))
    prop.SetLineWidth(3.0)
    prop.SetRenderLinesAsTubes(True)
    return actor


def _midpoint(p1: Tuple[float, float, float], p2: Tuple[float, float, float]) -> Tuple[float, float, float]:
    mid = (np.asarray(p1) + np.asarray(p2)) / 2.0
    return (float(mid[0]), float(mid[1]), float(mid[2]))
