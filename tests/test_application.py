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
