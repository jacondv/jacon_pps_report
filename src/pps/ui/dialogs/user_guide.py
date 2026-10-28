"""Opens the bundled user guide (HTML in the system browser, or a PDF copy
in the system's default PDF viewer).

The guide (user_guide.html + images/ + User_Guide.pdf) is built from
docs/manual/ — see docs/manual/build_manual.py. Do not edit user_guide.html
by hand; edit the Markdown sections instead and rebuild."""

import os

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QMessageBox

_HELP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "help")
_GUIDE_PATH = os.path.join(_HELP_DIR, "user_guide.html")
_GUIDE_PDF_PATH = os.path.join(_HELP_DIR, "User_Guide.pdf")


def _open(path: str, parent=None) -> None:
    path = os.path.normpath(path)
    if not os.path.isfile(path):
        QMessageBox.warning(parent, "User Guide", f"Guide file not found:\n{path}")
        return
    QDesktopServices.openUrl(QUrl.fromLocalFile(path))


def open_user_guide(parent=None) -> None:
    _open(_GUIDE_PATH, parent)


def open_user_guide_pdf(parent=None) -> None:
    _open(_GUIDE_PDF_PATH, parent)
