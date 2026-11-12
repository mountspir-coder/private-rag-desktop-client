# startup_check.py
from __future__ import annotations

import logging
from PyQt6.QtWidgets import QMessageBox, QWidget

from core.ollama_client import has_model, ping

logger = logging.getLogger(__name__)

REQUIRED_LLM = "llama3"
REQUIRED_EMBED = "nomic-embed-text"


def check_environment(parent: QWidget | None = None) -> bool:
    """
    Run startup checks. Returns True if the app can proceed.
    Shows a QMessageBox on failure with English instructions.
    """
    # 1. Ollama server alive?
    if not ping():
        QMessageBox.critical(
            parent,
            "Ollama is not running",
            "Cannot connect to Ollama at http://127.0.0.1:11434.\n\n"
            "Please install and start the Ollama server:\n"
            "  1. Download: https://ollama.com/download\n"
            "  2. Run it (it starts in the system tray)\n"
            "  3. Re-launch this application.",
        )
        logger.error("Startup check failed: Ollama not reachable.")
        return False

    # 2. Required models present?
    missing: list[str] = []
    if not has_model(REQUIRED_LLM):
        missing.append(REQUIRED_LLM)
    if not has_model(REQUIRED_EMBED):
        missing.append(REQUIRED_EMBED)

    if missing:
        pull_cmds = "\n".join(f"  ollama pull {m}" for m in missing)
        QMessageBox.warning(
            parent,
            "Missing models",
            f"The following Ollama models are required but not found:\n\n"
            f"  {', '.join(missing)}\n\n"
            f"Open a terminal and run:\n\n{pull_cmds}\n\n"
            f"Then restart the application.",
        )
        logger.error("Startup check failed: missing models %s", missing)
        return False

    logger.info("Startup checks passed.")
    return True