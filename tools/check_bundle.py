"""
Dev-only: verify a PyInstaller build contains every module the app imports
at runtime, before anyone clicks through the GUI.

Compares the recorded runtime module lists (docs/dep-slimming/used-modules-*.txt,
produced via PPS_DUMP_MODULES — see PLAN.md Phase 4) against the frozen
build: pure-Python modules inside the exe's PYZ archive, extension modules
(.pyd) and built-in modules. Test-only modules are ignored.

Usage (repo root):
    .venv\\Scripts\\python tools\\check_bundle.py "dist\\Jacon PPS Report" [used-modules.txt ...]

Run it with the venv the build was made from. If that venv's package versions
differ from the ones the committed lists were recorded with, record fresh
lists in it (PPS_DUMP_MODULES) and pass them as extra arguments.
"""

import glob
import importlib.util
import os
import sys
import zipfile

from PyInstaller.archive.readers import CArchiveReader

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USED_LISTS = glob.glob(os.path.join(REPO_ROOT, "docs", "dep-slimming", "used-modules-*.txt"))

# Imported only by the test runner / its plugins, never by the app.
TEST_ONLY_PREFIXES = (
    "pytest", "_pytest", "pytestqt", "pluggy", "iniconfig", "py", "tools",
    "dash.testing", "conftest", "test_", "PySide6.QtTest", "_pyrepl",
)


def frozen_modules(dist_dir):
    exe = next(p for p in glob.glob(os.path.join(dist_dir, "*.exe")))
    carchive = CArchiveReader(exe)
    # Modules the bootloader needs (e.g. struct) sit directly in the exe archive.
    names = set(carchive.toc)
    for entry_name in carchive.toc:
        if entry_name.endswith("PYZ.pyz") or entry_name == "PYZ-00.pyz" or entry_name.startswith("PYZ"):
            pyz = carchive.open_embedded_archive(entry_name)
            names.update(pyz.toc.keys())
    internal = os.path.join(dist_dir, "_internal")
    # The stdlib modules Python needs to boot live in base_library.zip.
    with zipfile.ZipFile(os.path.join(internal, "base_library.zip")) as z:
        for name in z.namelist():
            if name.endswith(".pyc"):
                mod = name[: -len(".pyc")].replace("/", ".")
                names.add(mod[: -len(".__init__")] if mod.endswith(".__init__") else mod)
    for root, _, files in os.walk(internal):
        for f in files:
            if f.endswith(".pyd"):
                rel = os.path.relpath(os.path.join(root, f), internal)
                mod = rel.split(".")[0].replace(os.sep, ".")
                names.add(mod)
    return names


def _has_own_file(module_name):
    try:
        spec = importlib.util.find_spec(module_name)
    except (ImportError, ValueError):
        return False
    if spec is None or not spec.origin or spec.origin in ("built-in", "frozen"):
        return False
    if module_name == "_virtualenv" or not os.path.isfile(spec.origin):
        return False
    # An alias (os.path -> ntpath, requests.packages.urllib3 -> urllib3)
    # resolves to a file whose path doesn't match the alias name.
    stem = os.path.splitext(os.path.normcase(spec.origin))[0]
    stem = stem.split(".")[0]  # foo.cp310-win_amd64.pyd -> foo
    if stem.endswith(os.sep + "__init__"):
        stem = stem[: -len(os.sep + "__init__")]
    return stem.endswith(os.sep + os.path.normcase(module_name.replace(".", os.sep)))


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    dist_dir = sys.argv[1]
    used = set()
    for path in sys.argv[2:] or USED_LISTS:
        with open(path, encoding="utf-8") as f:
            used.update(line.strip() for line in f if line.strip())
    used = {m for m in used if not m.startswith(TEST_ONLY_PREFIXES)}

    have = frozen_modules(dist_dir)
    builtin = set(sys.builtin_module_names)
    # Packages are present if any of their modules is; "__main__"/"main" is the script.
    missing = sorted(
        m for m in used
        if m not in have and m not in builtin and m not in ("__main__", "main")
        and not any(h.startswith(m + ".") for h in have)
    )
    # Many recorded names have no file of their own: submodules registered by
    # an extension module (open3d.camera, shibokensupport.*), aliases
    # (requests.packages.*), virtualenv shims. Only a module backed by a real
    # file in the dev environment can be missing from the build.
    missing = [m for m in missing if _has_own_file(m)]
    print(f"runtime modules checked: {len(used)}, bundled: {len(have)}")
    if missing:
        print(f"MISSING ({len(missing)}):")
        print("\n".join(f"  {m}" for m in missing))
        return 1
    print("OK: every recorded runtime module is in the build")
    return 0


if __name__ == "__main__":
    sys.exit(main())
