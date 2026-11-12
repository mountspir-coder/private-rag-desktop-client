"""
ui/workers.py — Background workers (QThread) for GUI integration.

Stage 5 changes:
    • ChatWorker now uses `rag_engine.ask_stream()` — emits chunk_received
      for every token fragment from the model, enabling ChatGPT-like typing.
    • IndexingWorker is unchanged from Stage 4.

Signals:
    IndexingWorker:
        progress(str)          — human-readable status text
        indexed(str, int)      — (filename, chunk_count) on success
        error(str)             — English error message on failure
        finished()             — QThread built-in, always emitted after run()

    ChatWorker:
        chunk_received(str)    — a fragment of the answer (token / few tokens)
        error(str)             — English error message on failure
        finished()             — QThread built-in, always emitted after run()
"""

from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from core.rag_engine import ask_stream, index_document
from parsers.document_parser import extract_text


logger = logging.getLogger(__name__)


# ──────────────────────── Indexing ────────────────────────

class IndexingWorker(QThread):
    """Parse a document, chunk it, embed it, and store it in ChromaDB."""

    progress = pyqtSignal(str)
    indexed = pyqtSignal(str, int)   # filename, chunk_count
    error = pyqtSignal(str)

    def __init__(self, file_path: str, parent=None) -> None:
        super().__init__(parent)
        self._file_path: str = file_path
        self._filename: str = Path(file_path).name

    def run(self) -> None:
        try:
            self.progress.emit(f"Parsing {self._filename}...")
            logger.info("Indexing started: %s", self._filename)

            text = extract_text(self._file_path)

            self.progress.emit(f"Indexing {self._filename}...")
            n_chunks = index_document(text, self._filename)

            logger.info(
                "Indexed '%s': %d chunks, %d chars",
                self._filename, n_chunks, len(text),
            )
            self.indexed.emit(self._filename, n_chunks)

        except Exception as exc:
            logger.exception("Indexing failed for '%s'", self._filename)
            self.error.emit(str(exc))


# ──────────────────────── Chat (streaming) ────────────────────────

class ChatWorker(QThread):
    """
    Stream a RAG-grounded answer token-by-token.

    Stage 5: uses `rag_engine.ask_stream()` which yields fragments from
             Ollama's stream=True mode. Each fragment is emitted via
             `chunk_received`. An empty database yields a single notice
             fragment instead of hanging.
    """

    chunk_received = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(
        self,
        question: str,
        model: str,
        top_k: int = 3,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._question: str = question
        self._model: str = model
        self._top_k: int = top_k

    def run(self) -> None:
        try:
            logger.info("Chat (streaming) request: model=%s top_k=%d", self._model, self._top_k)

            fragment_count = 0
            for fragment in ask_stream(self._question, model=self._model, top_k=self._top_k):
                if fragment:
                    fragment_count += 1
                    self.chunk_received.emit(fragment)

            logger.info("Chat stream finished (%d fragments)", fragment_count)

        except Exception as exc:
            logger.exception("Chat stream failed")
            self.error.emit(str(exc))