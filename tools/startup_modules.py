"""
Dev-only: report which heavy modules get imported just by loading the main
window module (i.e. before the window can appear).

Usage (repo root):
    .venv\\Scripts\\python tools\\startup_modules.py
"""

import os
import sys
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "src"))

WATCHED = ("vtkmodules.all", "matplotlib", "jinja2", "pdfkit", "open3d", "scipy", "dash", "plotly")


def main() -> int:
    start = time.perf_counter()
    import pps.app.qt_env  # noqa: F401  (sets QT_API before any Qt import)
    import pps.ui.main_window  # noqa: F401
    elapsed = time.perf_counter() - start

    vtk_modules = sorted(m for m in sys.modules if m.startswith("vtkmodules.vtk"))
    print(f"import pps.ui.main_window: {elapsed:.2f} s")
    print(f"vtkmodules.vtk* loaded: {len(vtk_modules)}")
    for name in WATCHED:
        print(f"  {name:15s} {'LOADED' if name in sys.modules else '-'}")
    if "-v" in sys.argv:
        print("\n".join(vtk_modules))
    return 0


if __name__ == "__main__":
    sys.exit(main())
