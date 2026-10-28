"""
Dev-only pytest plugin: at the end of the session, write every imported
module name to the file named by PPS_DUMP_MODULES. Running the full suite
exercises loading, all tools, the calculation and the PDF export, so the
result is the set of modules the app really uses — the input for trimming
the PyInstaller build (see docs/dep-slimming/PLAN.md Phase 4).

Usage (repo root):
    set PPS_DUMP_MODULES=docs\\dep-slimming\\used-modules-tests.txt
    .venv\\Scripts\\python -m pytest -p tools.dump_modules_plugin
"""

import os
import sys


def pytest_sessionfinish(session, exitstatus):
    path = os.environ.get("PPS_DUMP_MODULES")
    if path:
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(sorted(sys.modules)) + "\n")
