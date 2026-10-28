"""
Dev-only: list the top-level packages that `import open3d` pulls in, so the
PyInstaller build never excludes something open3d needs at runtime.

Usage (repo root):
    .venv\\Scripts\\python tools\\open3d_deps.py > docs\\dep-slimming\\open3d-imports.txt
"""

import sys


def top_level(names):
    return {n.split(".")[0] for n in names}


def main() -> int:
    import numpy  # noqa: F401  (the app always has numpy loaded already)

    before = set(sys.modules)
    import open3d  # noqa: F401

    added = set(sys.modules) - before
    print("# top-level packages imported by `import open3d`")
    for name in sorted(top_level(added)):
        print(name)
    print("\n# open3d submodules")
    for name in sorted(n for n in added if n.startswith("open3d")):
        print(name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
