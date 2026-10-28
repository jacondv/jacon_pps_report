#!/usr/bin/env python3
"""
Jacon PPS Report — entry point.

Thin on purpose: real app wiring lives in pps.app / pps.ui so it can be
imported and tested without going through this script. Kept at the repo
root (rather than only `python -m pps`) because PyInstaller's build.spec
expects a root-level script.
"""

import logging
import os
import sys

if not getattr(sys, "frozen", False):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from pps.app.application import configure_logging, create_app, use_persistent_matplotlib_cache  # noqa: E402
from pps.app.settings import AppSettings  # noqa: E402
from pps.ui.theme import apply_theme  # noqa: E402

logger = logging.getLogger(__name__)

APP_ICON = os.path.join(
    getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))), "assets", "icon.ico"
)


def _install_excepthook() -> None:
    """Log uncaught exceptions to the file log instead of letting them only
    flash past in a console window the user may not even have open."""
    default_hook = sys.excepthook

    def _hook(exc_type, exc_value, exc_tb):
        logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_tb))
        default_hook(exc_type, exc_value, exc_tb)

    sys.excepthook = _hook


def _show_splash():
    """Show a splash screen before the heavy 3D-viewer imports, so the user
    gets immediate feedback even while Windows Defender scans the DLLs."""
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
    from PySide6.QtWidgets import QApplication, QSplashScreen

    pixmap = QPixmap(440, 160)
    pixmap.fill(QColor("#1b1f27"))
    painter = QPainter(pixmap)
    icon = QIcon(APP_ICON)
    if not icon.isNull():
        icon.paint(painter, 24, 32, 96, 96)
    painter.setPen(QColor("#e6e9ef"))
    font = QFont()
    font.setPointSize(16)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(140, 32, 280, 96, Qt.AlignmentFlag.AlignVCenter, "Jacon PPS Report")
    painter.end()

    splash = QSplashScreen(pixmap)
    splash.show()
    splash.showMessage(
        "Loading…", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight, QColor("#9aa3b2")
    )
    QApplication.processEvents()
    return splash


def main() -> None:
    use_persistent_matplotlib_cache()
    log_path = configure_logging()
    _install_excepthook()
    logger.info("Starting Jacon PPS Report — log file: %s", log_path)

    app = create_app(sys.argv)
    logger.info("QApplication created")
    apply_theme(app, AppSettings().theme)
    splash = _show_splash()
    logger.info("Theme applied; loading the main window…")

    from pps.app.preload import start_background_preload
    from pps.ui.main_window import MainWindow

    window = MainWindow()
    logger.info("MainWindow constructed; showing…")
    window.showMaximized()
    splash.finish(window)
    logger.info("MainWindow shown; entering event loop")

    start_background_preload(app)

    exit_code = app.exec()
    _dump_loaded_modules()
    sys.exit(exit_code)


def _dump_loaded_modules() -> None:
    """Dev aid for trimming the build: with PPS_DUMP_MODULES=<file> set, write
    every module the session imported (see docs/dep-slimming/PLAN.md Phase 4)."""
    path = os.environ.get("PPS_DUMP_MODULES")
    if path:
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(sorted(sys.modules)) + "\n")


if __name__ == "__main__":
    main()
