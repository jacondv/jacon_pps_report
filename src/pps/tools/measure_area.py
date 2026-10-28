"""
MeasureAreaTool: the user draws a frame exactly like RegionSelectTool
(polygon / rectangle / lasso); on close it

1. drapes the frame onto the visible cloud surface, giving a 3D outline made
   of cloud points — drawn in the scene, so it rotates/zooms with the cloud;
2. takes the points the outline encloses, in 3D (pps.core.surface_region),
   so the result doesn't depend on the view and never includes a surface
   hidden behind the region;
3. computes their area with the same BPA method/radii as the PDF report, via
   an injectable `area_requester` so the QThread work (AreaMeasureWorker)
   stays owned by MainWindow and this tool is testable without Qt threads.
"""

from typing import Callable, List

import numpy as np

from pps.core.analysis import compute_area_m2
from pps.core.layers import SourceRef
from pps.core.surface_region import nearest_point, points_inside_outline
from pps.render.picking import drape_on_surface, resample_closed_polyline
from pps.scene.commands import AddMeasurementCommand
from pps.scene.measurements import AreaMeasurement
from pps.tools.region_select import Point2D, RegionMode, RegionSelectTool

AreaRequester = Callable[[np.ndarray, Callable[[float], None]], None]

# Screen spacing of the outline samples draped onto the cloud: dense enough
# to follow the drawn frame closely, cheap enough to stay interactive.
OUTLINE_SAMPLE_STEP_PX = 6.0


def _synchronous_area_requester(points: np.ndarray, on_done: Callable[[float], None]) -> None:
    on_done(compute_area_m2(points))


class MeasureAreaTool(RegionSelectTool):
    id = "measure_area"
    label = "Measure Area"
    shortcut = "A"
    cursor = "cross"

    def __init__(self, area_requester: AreaRequester = None):
        super().__init__()
        self.area_requester = area_requester or _synchronous_area_requester

    def status_hint(self) -> str:
        names = {
            RegionMode.POLYGON: "Polygon",
            RegionMode.RECTANGLE: "Rectangle",
            RegionMode.LASSO: "Lasso",
        }
        return f"{names[self.mode]} area measurement  |  Esc: cancel"

    def _apply(self, screen_polygon: List[Point2D], shift: bool, ctrl: bool) -> None:
        document = self.ctx.document
        plotter = self.ctx.viewport.plotter
        layers = document.layer_manager.visible_layers()
        self._reset()

        # 1. Drape the drawn frame onto the visible cloud surface.
        visible_points = (
            np.concatenate([layer.points for layer in layers]) if layers else np.empty((0, 3))
        )
        samples = resample_closed_polyline(screen_polygon, OUTLINE_SAMPLE_STEP_PX)
        outline = drape_on_surface(samples, visible_points, plotter)
        if len(outline) < 3:
            self.ctx.set_status("Draw the area on the point cloud.")
            return

        # 2. Take the points the outline encloses, in 3D (camera-independent).
        sources = []
        points_parts = []
        for layer in layers:
            indices = np.flatnonzero(points_inside_outline(layer.points, outline)).astype(np.uint32)
            if len(indices):
                sources.append(SourceRef(layer_id=layer.id, indices=indices))
                points_parts.append(layer.points[indices])
        if not points_parts:
            self.ctx.set_status("No points inside the drawn area.")
            return

        enclosed = np.concatenate(points_parts)
        measurement = AreaMeasurement(
            outline=outline,
            sources=sources,
            centroid=nearest_point(enclosed, enclosed.mean(axis=0)),
            area_m2=None,
            layer_id=sources[0].layer_id,
        )
        self.ctx.undo_stack.push(AddMeasurementCommand(document, measurement))
        self.ctx.set_status("Calculating area…")
        self.ctx.finish_command()

        measurement_id = measurement.id

        def on_done(area_m2: float) -> None:
            # Not wrapped in a command: this fulfills a pending calculation
            # for a measurement that already exists, it isn't a new
            # user-undoable action, and undo shouldn't revert area back to
            # "unknown".
            document._update_measurement(measurement_id, area_m2=area_m2)

        self.area_requester(enclosed, on_done)
