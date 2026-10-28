"""
Background preload of heavy libraries the window doesn't need to appear.

open3d is only used by the area calculation, so it isn't imported at startup —
but importing it takes a few seconds (and longer on a cold start, while
Windows Defender scans its DLLs). Importing it on a background thread right
after the window is shown means the user's first Calculate doesn't pay that
cost. Failure here is harmless: the calculation code imports open3d itself.
"""

import importlib
import logging
import time

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QApplication

logger = logging.getLogger(__name__)

PRELOAD_MODULES = ("open3d",)


class PreloadThread(QThread):
    def run(self) -> None:
        for name in PRELOAD_MODULES:
            start = time.perf_counter()
            try:
                importlib.import_module(name)
            except Exception:
                logger.warning("Background preload of %s failed", name, exc_info=True)
                continue
            logger.info("%s preloaded in %.2fs", name, time.perf_counter() - start)


def start_background_preload(app: QApplication) -> PreloadThread:
    """Start preloading on a QThread owned by `app`. The app waits for it on
    quit — an in-progress import can't be interrupted, and destroying a
    running QThread aborts the process."""
    thread = PreloadThread(app)
    app.aboutToQuit.connect(thread.wait)
    thread.start(QThread.Priority.LowPriority)
    return thread
