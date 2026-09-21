"""
Draws the current live selection (Select tool, before it's turned into a
segment) as a highlighted yellow point cloud overlaid on top of the layer(s)
it was picked from. One actor at a time — a fresh selection replaces the
previous highlight entirely.
"""

import pyvista as pv


class SelectionRenderer:
    """Owns the single pyvista actor used to highlight the active selection."""

    def __init__(self, plotter):
        self._plotter = plotter
        self._actor = None

    def sync(self, points, point_size: int) -> None:
        """Replace the highlight with one drawn from `points` (an (N, 3)
        array); an empty/None `points` just clears it."""
        self.clear()
        if points is None or len(points) == 0:
            return
        cloud = pv.PolyData(points)
        self._actor = self._plotter.add_mesh(
            cloud, color="yellow", point_size=point_size + 3,
            render_points_as_spheres=True, opacity=0.9,
        )

    def clear(self) -> None:
        if self._actor is not None:
            try:
                self._plotter.remove_actor(self._actor)
            except Exception:
                pass
            self._actor = None
