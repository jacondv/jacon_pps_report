import os

# Force pytest-qt and qtpy/pyvistaqt to use PySide6 before any Qt import,
# in case another Qt binding is also present in the environment.
os.environ.setdefault("QT_API", "pyside6")
os.environ.setdefault("PYTEST_QT_API", "pyside6")

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_PLY = os.path.join(
    REPO_ROOT, "sample", "2_thickness_01#20260203_093652#cloud_compared_07.ply"
)


@pytest.fixture(scope="session")
def sample_ply_path():
    return SAMPLE_PLY


# Modules that construct QSettings("TunnelAnalyzer", ...) — the app's real
# per-user settings (the Windows registry). Without this, tests overwrote the
# user's theme, point size and recent-projects list.
_QSETTINGS_USERS = ("pps.app.settings", "pps.ui.main_window")


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path, monkeypatch):
    """Point every QSettings the app creates at a fresh per-test INI file."""
    import sys

    from PySide6.QtCore import QSettings

    ini_path = str(tmp_path / "settings.ini")

    def make_settings(*_args, **_kwargs):
        return QSettings(ini_path, QSettings.Format.IniFormat)

    for name in _QSETTINGS_USERS:
        module = sys.modules.get(name)
        if module is not None:
            monkeypatch.setattr(module, "QSettings", make_settings)
    return ini_path
