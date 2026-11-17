"""
Maps a Layer's thickness values to RGB colors and keeps a pyvista actor per
layer in sync with the Document.

Color thresholds replicate PointCloudViewer.assign_colors() from the old
gui/viewer_3d.py, collapsed to exactly 3 bands (below / within / above) —
this must not change without an explicit decision, since it affects report
screenshots. Points above the maximum measurable thickness (noise, left out
of every thickness figure) get a fourth, separate color. Every layer (original AND segments) is colored this way — a
segment is a subset of the same thickness data, so it gets the same
red/green/blue classification instead of an arbitrary flat color, and the
below/within/above colors are user-configurable (Settings).
"""

from typing import Dict, Optional, Tuple

import numpy as np
import pyvista as pv

from pps.core.calculator import DEFAULT_MAX_MEASURABLE_MM
from pps.core.layers import Layer

ColorRGB = Tuple[float, float, float]

DEFAULT_COLOR_BELOW: ColorRGB = (1.0, 0.0, 0.0)
DEFAULT_COLOR_WITHIN: ColorRGB = (0.0, 1.0, 0.0)
DEFAULT_COLOR_ABOVE: ColorRGB = (0.0, 0.0, 1.0)
DEFAULT_COLOR_OUT_OF_RANGE: ColorRGB = (135 / 255, 206 / 255, 250 / 255)  # light blue


def threshold_colors(
    distances: np.ndarray,
    target_min: float,
    target_max: float,
    color_below: ColorRGB = DEFAULT_COLOR_BELOW,
    color_within: ColorRGB = DEFAULT_COLOR_WITHIN,
    color_above: ColorRGB = DEFAULT_COLOR_ABOVE,
    max_measurable_mm: float = DEFAULT_MAX_MEASURABLE_MM,
    color_out_of_range: ColorRGB = DEFAULT_COLOR_OUT_OF_RANGE,
) -> np.ndarray:
    colors = np.zeros((len(distances), 3), dtype=np.float32)
    colors[distances < target_min] = color_below
    colors[(distances >= target_min) & (distances <= target_max)] = color_within
    colors[distances > target_max] = color_above
    colors[distances > max_measurable_mm] = color_out_of_range
    return colors


class LayerRenderer:
    """Owns the pyvista actor for each visible Layer inside one plotter."""

    def __init__(self, plotter):
        self._plotter = plotter
        self._actors: Dict[str, object] = {}
        self._color_below = DEFAULT_COLOR_BELOW
        self._color_within = DEFAULT_COLOR_WITHIN
        self._color_above = DEFAULT_COLOR_ABOVE
        self._color_out_of_range = DEFAULT_COLOR_OUT_OF_RANGE
        self._max_measurable_mm = DEFAULT_MAX_MEASURABLE_MM

    def set_classification_colors(
        self,
        color_below: ColorRGB,
        color_within: ColorRGB,
        color_above: ColorRGB,
        color_out_of_range: ColorRGB = DEFAULT_COLOR_OUT_OF_RANGE,
    ) -> None:
        """Update the RGB colors used by `sync()` (does not itself re-sync
        existing actors — call sync() again for that)."""
        self._color_below = color_below
        self._color_within = color_within
        self._color_above = color_above
        self._color_out_of_range = color_out_of_range

    def set_max_measurable(self, max_measurable_mm: float) -> None:
        """Points above this get the out-of-range color on the next sync()."""
        self._max_measurable_mm = max_measurable_mm

    def sync(
        self,
        layer: Layer,
        target_min: float,
        target_max: float,
        point_size: int = 3,
    ):
        """(Re)build the actor for `layer` from scratch and return it."""
        self.remove(layer.id)

        cloud = pv.PolyData(layer.points)
        cloud["thickness"] = layer.distances
        cloud["colors"] = threshold_colors(
            layer.distances,
            target_min,
            target_max,
            color_below=self._color_below,
            color_within=self._color_within,
            color_above=self._color_above,
            max_measurable_mm=self._max_measurable_mm,
            color_out_of_range=self._color_out_of_range,
        )

        actor = self._plotter.add_mesh(
            cloud,
            scalars="colors",
            rgb=True,
            point_size=point_size,
            render_points_as_spheres=True,
            show_scalar_bar=False,
            name=f"layer_{layer.id}",
        )
        actor.SetVisibility(layer.visible)
        self._actors[layer.id] = actor
        return actor

    def set_visible(self, layer_id: str, visible: bool) -> None:
        actor = self._actors.get(layer_id)
        if actor is not None:
            actor.SetVisibility(visible)

    def remove(self, layer_id: str) -> None:
        actor = self._actors.pop(layer_id, None)
        if actor is not None:
            try:
                self._plotter.remove_actor(actor)
            except Exception:
                pass

    def clear(self) -> None:
        for layer_id in list(self._actors):
            self.remove(layer_id)

    def get(self, layer_id: str) -> Optional[object]:
        return self._actors.get(layer_id)
