"""A small "About" dialog: app logo, name, version and feature summary."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)

from pps import __version__
from pps.ui.icons import app_icon

_APP_NAME = "Jacon PPS Report"
_LOGO_SIZE = 64

_FEATURES = [
    "Load and visualize Point Cloud scan data (.ply)",
    "Region selection, segment extraction/crop, distance and area measurement",
    "Notes and Annotations placed directly on the 3D model",
    "Thickness statistics against a configurable Target Min/Max range",
    "PDF report export with a 3D snapshot and full data tables",
]


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About")
        self.setFixedWidth(420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(14)

        header = QHBoxLayout()
        header.setSpacing(14)
        logo = QLabel()
        logo.setPixmap(app_icon().pixmap(_LOGO_SIZE, _LOGO_SIZE))
        header.addWidget(logo)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel(_APP_NAME)
        title_font = title.font()
        title_font.setPointSize(title_font.pointSize() + 3)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setWordWrap(True)
        subtitle = QLabel(f"Version {__version__}")
        subtitle.setStyleSheet("color: #8a94a6;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box, 1)
        layout.addLayout(header)

        desc = QLabel(
            "Generates shotcrete thickness reports from Point Cloud data "
            "captured by the PPS scanner, covering the full workflow from "
            "measurement and annotation to PDF reporting."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        features = QLabel("<br>".join(f"&bull;&nbsp;&nbsp;{f}" for f in _FEATURES))
        features.setWordWrap(True)
        features.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(features)

        credit = QLabel("Jacon Equipment")
        credit.setStyleSheet("color: #8a94a6; margin-top: 4px;")
        layout.addWidget(credit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)


def show_about(parent=None) -> None:
    AboutDialog(parent).exec()
