"""Opens the bundled HTML user guide in the system's default browser.

The guide (user_guide.html + images/) is built from docs/manual/ — see
docs/manual/build_manual.py. Do not edit user_guide.html by hand; edit the
Markdown sections instead and rebuild."""

import os

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QMessageBox

_GUIDE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "help", "user_guide.html")


def open_user_guide(parent=None) -> None:
    path = os.path.normpath(_GUIDE_PATH)
    if not os.path.isfile(path):
        QMessageBox.warning(parent, "User Guide", f"Guide file not found:\n{path}")
        return
    QDesktopServices.openUrl(QUrl.fromLocalFile(path))
