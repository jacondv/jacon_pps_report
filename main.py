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
from pps.ui.icons import app_icon  # noqa: E402
from pps.ui.theme import apply_theme  # noqa: E402

logger = logging.getLogger(__name__)


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
    gets immediate feedback even while Windows Defender scans the DLLs.

    A frameless QLabel rather than QSplashScreen: on Windows,
    QSplashScreen.show() blocked for ~1 s every launch (measured), while
    this shows in ~50 ms. Close it with .close() once the window is up."""
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
    from PySide6.QtWidgets import QApplication, QLabel

    pixmap = QPixmap(440, 160)
    pixmap.fill(QColor("#1b1f27"))
    painter = QPainter(pixmap)
    icon = app_icon()
    if not icon.isNull():
        icon.paint(painter, 24, 32, 96, 96)
    painter.setPen(QColor("#e6e9ef"))
    font = QFont()
    font.setPointSize(16)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(140, 32, 280, 96, Qt.AlignmentFlag.AlignVCenter, "Jacon PPS Report")
    font.setPointSize(9)
    font.setBold(False)
    painter.setFont(font)
    painter.setPen(QColor("#9aa3b2"))
    painter.drawText(
        0, 0, 428, 150, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight, "Loading…"
    )
    painter.end()

    splash = QLabel()
    splash.setWindowFlags(
        Qt.WindowType.SplashScreen
        | Qt.WindowType.FramelessWindowHint
        | Qt.WindowType.WindowStaysOnTopHint
    )
    splash.setPixmap(pixmap)
    splash.show()
    splash.repaint()
    QApplication.processEvents()
    return splash


def main() -> None:
    use_persistent_matplotlib_cache()
    log_path = configure_logging()
    _install_excepthook()
    logger.info("Starting Jacon PPS Report — log file: %s", log_path)

    app = create_app(sys.argv)
    logger.info("QApplication created")
    app.setWindowIcon(app_icon())  # title bar + taskbar of every window
    apply_theme(app, AppSettings().theme)
    splash = _show_splash()
    logger.info("Theme applied; loading the main window…")

    from PySide6.QtCore import QTimer

    from pps.app.preload import start_background_preload
    from pps.ui.main_window import MainWindow

    window = MainWindow()
    logger.info("MainWindow constructed; showing…")
    window.showMaximized()
    splash.close()
    logger.info("MainWindow shown; entering event loop")

    start_background_preload(app)
    # Fires once the event loop has processed the window's first paint —
    # the moment the user actually sees it (tools/measure_startup.py waits
    # for this line).
    QTimer.singleShot(0, lambda: logger.info("Event loop running; window painted"))

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
