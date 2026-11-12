"""
main.py — Application entry point.

Bootstraps:
    • logging to app.log (rotating) + console
    • QApplication
    • custom excepthook — uncaught exceptions are logged, not swallowed
    • MainWindow
"""

from __future__ import annotations

import logging
import sys
import traceback
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow


LOG_FILE: Path = Path(__file__).resolve().parent / "app.log"
LOG_FORMAT: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def setup_logging() -> None:
    """Configure root logger: rotating file + console."""
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # Rotating file handler — keeps app.log bounded.
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root.addHandler(file_handler)

    # Console handler — useful during development.
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    root.addHandler(console)


def _excepthook(exc_type, exc_value, exc_tb) -> None:
    """Log uncaught exceptions to app.log and stderr — do not kill silently."""
    logging.getLogger("uncaught").critical(
        "Unhandled exception:\n%s",
        "".join(traceback.format_exception(exc_type, exc_value, exc_tb)),
    )
    sys.stderr.write("Unhandled exception:\n")
    traceback.print_exception(exc_type, exc_value, exc_tb)


def main() -> int:
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("=== Application starting ===")
    logger.info("Log file: %s", LOG_FILE)

    sys.excepthook = _excepthook

    app = QApplication(sys.argv)
    app.setApplicationName("Private RAG Desktop Client")

    window = MainWindow()
    window.show()

    exit_code = app.exec()
    logger.info("=== Application exited (code=%d) ===", exit_code)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())