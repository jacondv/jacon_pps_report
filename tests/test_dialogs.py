from PySide6.QtWidgets import QDialog

from pps.app import dialogs
from pps.app.dialogs import MeasurementStyleDialog, open_measurement_style_editor
from pps.scene.measurements import DistanceMeasurement


def test_style_dialog_prefills_and_reports_values(qtbot):
    dialog = MeasurementStyleDialog(title="Distance", color="#112233", font_size=18)
    qtbot.addWidget(dialog)
    assert dialog.values() == {"color": "#112233", "font_size": 18}

    dialog.color_button.set_color("#abcdef")
    dialog.font_size_spin.setValue(30)
    assert dialog.values() == {"color": "#abcdef", "font_size": 30}


def _accept_with(monkeypatch, color=None, font_size=None):
    def fake_exec(self):
        if color is not None:
            self.color_button.set_color(color)
        if font_size is not None:
            self.font_size_spin.setValue(font_size)
        return QDialog.Accepted

    monkeypatch.setattr(dialogs.MeasurementStyleDialog, "exec", fake_exec)


def test_editor_returns_only_changed_fields(qtbot, monkeypatch):
    measurement = DistanceMeasurement(p1=(0, 0, 0), p2=(1, 0, 0))
    _accept_with(monkeypatch, font_size=20)
    assert open_measurement_style_editor(measurement) == {"font_size": 20}


def test_editor_returns_none_when_unchanged_or_cancelled(qtbot, monkeypatch):
    measurement = DistanceMeasurement(p1=(0, 0, 0), p2=(1, 0, 0))
    _accept_with(monkeypatch)
    assert open_measurement_style_editor(measurement) is None

    monkeypatch.setattr(dialogs.MeasurementStyleDialog, "exec", lambda self: QDialog.Rejected)
    assert open_measurement_style_editor(measurement) is None


def test_app_icon_is_the_bundled_logo(qtbot):
    from pps.ui.icons import APP_ICON_PATH, app_icon

    assert APP_ICON_PATH.endswith("app.ico")
    assert not app_icon().isNull()
    assert max(size.width() for size in app_icon().availableSizes()) >= 256
