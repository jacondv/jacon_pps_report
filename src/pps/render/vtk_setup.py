"""
Register the VTK object-factory overrides the renderer needs.

The render package imports VTK classes from their own `vtkmodules.*` modules
instead of `import vtk` — that umbrella module loads all ~150 VTK libraries,
and Windows Defender scans each one on first load, which made cold start very
slow. Without it, the OpenGL backend, font rendering and interactor styles are
only registered if something imports their modules. pyvista currently does,
but import them here explicitly so rendering never depends on that.
"""

import vtkmodules.vtkInteractionStyle  # noqa: F401
import vtkmodules.vtkRenderingContextOpenGL2  # noqa: F401
import vtkmodules.vtkRenderingFreeType  # noqa: F401
import vtkmodules.vtkRenderingOpenGL2  # noqa: F401
