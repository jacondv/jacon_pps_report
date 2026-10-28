"""
Real Qt dialogs used as the default implementations of tool "editor"
callbacks (e.g. NoteTool.note_editor). Kept under app/ rather than ui/ for
now since the ui/ package (docks, main window, theme) doesn't exist yet —
these dialogs don't depend on it.
"""

from typing import Optional

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
)


FONT_SIZE_RANGE = (8, 48)


class ColorButton(QPushButton):
    """A swatch showing a color; clicking it opens a color picker."""

    def __init__(self, color: str, dialog_title: str, parent=None):
        super().__init__(parent)
        self._dialog_title = dialog_title
        self.setFixedSize(28, 22)
        self.set_color(color)
        self.clicked.connect(self._choose)

    def color(self) -> str:
        return self._color

    def set_color(self, color: str) -> None:
        self._color = color
        self.setStyleSheet(f"background-color: {color}; border: 1px solid #555;")

    def _choose(self) -> None:
        chosen = QColorDialog.getColor(QColor(self._color), self, self._dialog_title)
        if chosen.isValid():
            self.set_color(chosen.name())


def _font_size_spin(value: int) -> QSpinBox:
    spin = QSpinBox()
    spin.setRange(*FONT_SIZE_RANGE)
    spin.setValue(value)
    return spin


class NoteEditorDialog(QDialog):
    def __init__(self, parent=None, text="", color="#ffd166", font_size=14):
        super().__init__(parent)
        self.setWindowTitle("Note")
        self.setModal(True)
        self.resize(380, 280)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Text:"))
        self.text_edit = QTextEdit(self)
        self.text_edit.setPlainText(text)
        self.text_edit.setMinimumHeight(120)
        layout.addWidget(self.text_edit)

        form = QFormLayout()
        self.color_button = ColorButton(color, "Note color")
        form.addRow("Color:", self.color_button)
        self.font_size_spin = _font_size_spin(font_size)
        form.addRow("Font size:", self.font_size_spin)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self) -> dict:
        return {
            "text": self.text_edit.toPlainText().strip(),
            "color": self.color_button.color(),
            "font_size": self.font_size_spin.value(),
        }


class MeasurementStyleDialog(QDialog):
    """Color (label + line/outline) and label font size of a distance or
    area measurement."""

    def __init__(self, parent=None, title="Measurement", color="#4cc9f0", font_size=14):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.color_button = ColorButton(color, f"{title} color")
        form.addRow("Color:", self.color_button)
        self.font_size_spin = _font_size_spin(font_size)
        form.addRow("Font size:", self.font_size_spin)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self) -> dict:
        return {"color": self.color_button.color(), "font_size": self.font_size_spin.value()}


def open_note_editor(existing=None, screen_pos=None, parent=None) -> Optional[dict]:
    """Show NoteEditorDialog modally; `existing` (a NoteAnnotation or None)
    pre-fills the fields for editing. Returns the chosen {text, color,
    font_size}, or None if cancelled or the text was left empty."""
    if existing is not None:
        dialog = NoteEditorDialog(
            parent, text=existing.text, color=existing.color, font_size=existing.font_size
        )
    else:
        dialog = NoteEditorDialog(parent)

    if dialog.exec() != QDialog.Accepted:
        return None

    values = dialog.values()
    if not values["text"]:
        return None
    return values


def open_measurement_style_editor(measurement, parent=None) -> Optional[dict]:
    """Edit a measurement's {color, font_size}. Returns only the fields that
    changed, or None if cancelled or nothing changed."""
    from pps.scene.measurements import DistanceMeasurement

    title = "Distance" if isinstance(measurement, DistanceMeasurement) else "Area"
    dialog = MeasurementStyleDialog(
        parent, title=title, color=measurement.color, font_size=measurement.font_size
    )
    if dialog.exec() != QDialog.Accepted:
        return None
    changed = {k: v for k, v in dialog.values().items() if getattr(measurement, k) != v}
    return changed or None
