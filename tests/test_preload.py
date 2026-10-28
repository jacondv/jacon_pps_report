import logging
import sys

from pps.app import preload


def test_preload_imports_module_and_logs_time(qapp, monkeypatch, caplog):
    monkeypatch.setattr(preload, "PRELOAD_MODULES", ("json",))
    thread = preload.PreloadThread()
    with caplog.at_level(logging.INFO, logger=preload.__name__):
        thread.start()
        assert thread.wait(30000)
    assert "json" in sys.modules
    assert "json preloaded in" in caplog.text


def test_preload_failure_is_logged_not_raised(qapp, monkeypatch, caplog):
    monkeypatch.setattr(preload, "PRELOAD_MODULES", ("pps_no_such_module_xyz",))
    thread = preload.PreloadThread()
    with caplog.at_level(logging.WARNING, logger=preload.__name__):
        thread.start()
        assert thread.wait(30000)
    assert "Background preload of pps_no_such_module_xyz failed" in caplog.text


def test_start_background_preload_waits_on_quit(qapp, monkeypatch):
    monkeypatch.setattr(preload, "PRELOAD_MODULES", ())
    thread = preload.start_background_preload(qapp)
    assert thread.wait(30000)
    assert thread.parent() is qapp
