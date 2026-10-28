# build.spec — PyInstaller spec for the PySide6 app under src/pps.
#
# Two different resource-lookup conventions are bundled here on purpose,
# matching how the code actually looks things up at runtime:
#   1. pps.utils.path_helper.resource_path() (used by the PDF report code
#      for report/assets, report/templates, report/packages/wkhtmltox) and
#      _find_wkhtmltopdf() both look for a TOP-LEVEL "report/" folder next
#      to the exe (or under _internal/) — NOT nested under "pps/".
#   2. pps.ui.icons.load_icon() and pps.ui.dialogs.user_guide.open_user_guide()
#      resolve their files relative to their own module's __file__, so
#      those must be bundled at the matching in-package path
#      ("pps/ui/icons/svg", "pps/ui/help") so the frozen module's __file__
#      based join still finds them under _internal/.
#
# See src/pps/utils/path_helper.py and src/pps/ui/icons.py for the exact
# lookup logic if either of these ever need to change.

import os

from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

SRC = os.path.join("src", "pps")

datas = [
    (os.path.join(SRC, "report", "assets"), os.path.join("report", "assets")),
    (os.path.join(SRC, "report", "templates"), os.path.join("report", "templates")),
    (os.path.join(SRC, "report", "packages"), os.path.join("report", "packages")),
    (os.path.join(SRC, "ui", "icons", "svg"), os.path.join("pps", "ui", "icons", "svg")),
    (os.path.join(SRC, "ui", "help"), os.path.join("pps", "ui", "help")),
    (os.path.join("sample", "*.ply"), "sample"),
    ("assets", "assets"),
]

# open3d is only used for the BPA surface area. Its resources/ folder
# (~39 MB of fonts/materials) and the Jupyter/notebook extensions belong to
# open3d's own GUI viewer, which the app never opens. Keep the rest
# (tbb12.dll, ml/visualization data that `import open3d` loads).
_OPEN3D_UNUSED_DATA = {"resources", "labextension", "nbextension", "examples"}


def _open3d_subdir(dst):
    """'open3d/resources/x' -> 'resources'; files directly in open3d/ -> ''."""
    parts = dst.replace(os.sep, "/").split("/")
    return parts[1] if len(parts) > 1 else ""


datas += [
    (src, dst)
    for src, dst in collect_data_files("open3d")
    if _open3d_subdir(dst) not in _OPEN3D_UNUSED_DATA
]

hiddenimports = [
    "PySide6.QtSvg",
    "PySide6.QtPrintSupport",
    "pyvista",
    "pyvistaqt",
    "open3d",
    "pdfkit",
    "jinja2",
    "matplotlib",
    "matplotlib.backends.backend_agg",
    "plyfile",
]
hiddenimports += collect_submodules("open3d")

# Never imported at runtime (checked against docs/dep-slimming/used-modules-*.txt
# and open3d-imports.txt). Without these excludes PyInstaller still follows
# static imports into them. Do NOT exclude IPython/jedi/dash/flask/plotly:
# `import open3d` loads them.
excludes = [
    "PyQt5",
    "PyQt6",
    "tkinter",
    "scipy",
    "reportlab",
    "pytest",
    "_pytest",
    "nbformat",
    "jsonschema",
    "docutils",
    "vtk",
    "vtkmodules.all",
    "vtkmodules.web",
    "vtkmodules.test",
    "pyvista.trame",
    "pyvista.ext",
    "pyvista.examples",
    "pyvista.demos",
]

a = Analysis(
    ["main.py"],
    pathex=[".", "src"],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=["."],
    runtime_hooks=[],
    excludes=excludes,
    cipher=block_cipher,
)

# jedi is only here because `import open3d` imports IPython. Its type stubs
# (jedi/third_party: typeshed + django-stubs, ~5,500 .pyi files) are for code
# completion, which the app never does; newer hook versions collect them.
a.datas = [
    entry for entry in a.datas
    if not entry[0].replace("\\", "/").startswith("jedi/third_party/")
]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="Jacon PPS Report",
    debug=False,
    # No console window: everything is logged to
    # %LOCALAPPDATA%\TunnelAnalyzer\logs\app.log (see pps.app.application).
    console=False,
    # UPX-packed binaries are slower to load and more likely to be flagged
    # by antivirus.
    upx=False,
    icon="assets/icon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    upx=False,
    name="Jacon PPS Report",
)
