import os

from PySide6.QtWidgets import QApplication

from pps.app.application import create_app


def test_create_app_reuses_existing_instance(qtbot):
    # pytest-qt's qtbot fixture already created a QApplication; create_app()
    # must not try to construct a second one (PySide6 raises if it does).
    before = QApplication.instance()
    assert before is not None

    app = create_app([])

    assert app is before


def test_persistent_matplotlib_cache_only_in_frozen_app(monkeypatch, tmp_path):
    from pps.app import application

    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setenv("MPLCONFIGDIR", "untouched")
    monkeypatch.delattr("sys.frozen", raising=False)
    application.use_persistent_matplotlib_cache()
    assert os.environ["MPLCONFIGDIR"] == "untouched"

    monkeypatch.setattr("sys.frozen", True, raising=False)
    application.use_persistent_matplotlib_cache()
    expected = os.path.join(str(tmp_path), "TunnelAnalyzer", "matplotlib")
    assert os.environ["MPLCONFIGDIR"] == expected
    assert os.path.isdir(expected)


def test_windows_app_id_only_set_when_running_from_source(monkeypatch):
    import ctypes
    import sys

    from pps.app import application

    calls = []

    class FakeShell32:
        def SetCurrentProcessExplicitAppUserModelID(self, app_id):
            calls.append(app_id)

    class FakeWindll:
        shell32 = FakeShell32()

    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(ctypes, "windll", FakeWindll(), raising=False)

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    application._set_windows_app_id()
    assert calls == []  # the exe keeps its own icon on the taskbar

    monkeypatch.delattr(sys, "frozen")
    application._set_windows_app_id()
    assert calls == [application.WINDOWS_APP_USER_MODEL_ID]
