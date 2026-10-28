"""
Guards against startup regressions: loading the main window module must not
pull in heavy libraries the window doesn't need yet. Windows Defender scans
every DLL on first load (and again after each reboot), so each extra library
costs real seconds on a cold start.

Runs in a fresh subprocess so modules imported by other tests don't leak in.
"""

import json
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# pyvista + pyvistaqt need ~62 vtkmodules.vtk* modules (measured 2026-10-28,
# vtk 9.6.1 / pyvista 0.47.3); `import vtk` would load ~153.
MAX_VTK_MODULES = 70

_PROBE = """
import json, sys
import pps.app.qt_env
import pps.ui.main_window
print(json.dumps({
    "vtk_modules": sum(1 for m in sys.modules if m.startswith("vtkmodules.vtk")),
    "loaded": sorted(m for m in sys.modules if "." not in m),
}))
"""


# Only needed for the calculation / PDF export — loaded on demand (open3d
# also by a background preload after the window is shown).
NOT_AT_STARTUP = ("jinja2", "pdfkit", "open3d", "scipy", "dash", "plotly")

# matplotlib isn't listed: pyvista requires it and imports it on load.


def _run_probe(code: str) -> str:
    env = dict(os.environ, PYTHONPATH=os.path.join(REPO_ROOT, "src"))
    return subprocess.run(
        [sys.executable, "-c", code], cwd=REPO_ROOT, env=env,
        capture_output=True, text=True, timeout=600, check=True,
    ).stdout.strip().splitlines()[-1]


def _probe_startup_imports():
    return json.loads(_run_probe(_PROBE))


def test_main_window_import_loads_only_needed_vtk_modules():
    result = _probe_startup_imports()
    assert result["vtk_modules"] <= MAX_VTK_MODULES, result["vtk_modules"]


def test_main_window_import_defers_report_and_calculation_libraries():
    loaded = set(_probe_startup_imports()["loaded"])
    assert not loaded.intersection(NOT_AT_STARTUP), sorted(loaded.intersection(NOT_AT_STARTUP))

