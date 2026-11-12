"""
ui/main_window.py — Main window of the Private RAG Desktop Client.

Stage 5 (streaming, no flicker):
    • Chat is stored in `_chat_history`.
    • Full re-render (with Markdown) happens only on:
        - welcome / theme switch / language switch / finalization / error.
    • During streaming we append ONLY the delta to the current bot message
      via QTextCursor.insertText() — no clear(), no scroll jump, no flicker.
    • Auto-scroll is applied on each delta flush if user was at the bottom.
    • Blinking caret "▊" is shown while a stream is in progress.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QTextCursor, QTextDocumentFragment
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from core.rag_engine import clear_collection
from ui.i18n import I18n
from ui.styles import THEMES
from ui.workers import ChatWorker, IndexingWorker


logger = logging.getLogger(__name__)


AVAILABLE_MODELS: list[str] = ["llama3", "mistral", "phi3"]

THEME_DARK: str = "dark"
THEME_LIGHT: str = "light"

LEFT_PANEL_WIDTH: int = 260
WINDOW_DEFAULT_SIZE = (1100, 720)

STREAM_FLUSH_MS: int = 30   # how often we flush accumulated delta to the widget
STREAMING_CARET: str = "▊"


class MainWindow(QMainWindow):
    """Application main window."""

    def __init__(self) -> None:
        super().__init__()
        self.i18n: I18n = I18n(lang="en")
        self._current_theme: str = THEME_DARK

        # Worker handles — held as attributes so Python GC does not
        # collect them while the thread is still running.
        self._indexing_worker: IndexingWorker | None = None
        self._chat_worker: ChatWorker | None = None

        # Chat history: list of {"role": "user"|"bot", "text": str, "streaming": bool}
        self._chat_history: list[dict[str, Any]] = []

        # How many characters of the current streaming bot message have
        # already been drawn in the widget. Only the remaining tail is
        # flushed incrementally — that's what eliminates flicker.
        self._streaming_rendered_len: int = 0

        # Streaming flusher (coalesces rapid chunks into one draw).
        self._stream_timer = QTimer(self)
        self._stream_timer.setSingleShot(True)
        self._stream_timer.setInterval(STREAM_FLUSH_MS)
        self._stream_timer.timeout.connect(self._flush_streaming)

        self._build_ui()
        self._apply_theme(self._current_theme)
        self._retranslate_ui()
        self._show_welcome_message()

    # ──────────────────────── UI construction ────────────────────────

    def _build_ui(self) -> None:
        self.setMinimumSize(*WINDOW_DEFAULT_SIZE)
        self._build_toolbar()
        self._build_central_area()
        self._build_status_bar()

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        self.model_label = QLabel(self.i18n.tr("model_label"))
        toolbar.addWidget(self.model_label)

        self.model_combo = QComboBox(self)
        self.model_combo.addItems(AVAILABLE_MODELS)
        self.model_combo.setToolTip("Select the Ollama model for chat")
        toolbar.addWidget(self.model_combo)

        toolbar.addSeparator()

        self.theme_button = QPushButton("☀", self)
        self.theme_button.setObjectName("themeButton")
        self.theme_button.setToolTip(self.i18n.tr("theme_switch_to_light"))
        self.theme_button.clicked.connect(self._on_toggle_theme)
        toolbar.addWidget(self.theme_button)

    def _build_central_area(self) -> None:
        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.addWidget(self._build_left_panel())
        splitter.addWidget(self._build_right_panel())
        splitter.setSizes([LEFT_PANEL_WIDTH, WINDOW_DEFAULT_SIZE[0] - LEFT_PANEL_WIDTH])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)

    def _build_left_panel(self) -> QWidget:
        panel = QWidget(self)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self.documents_label = QLabel(self.i18n.tr("documents"), panel)
        self.documents_label.setObjectName("sectionLabel")
        layout.addWidget(self.documents_label)

        self.file_list = QListWidget(panel)
        layout.addWidget(self.file_list, stretch=1)

        self.add_button = QPushButton(self.i18n.tr("add_document"), panel)
        self.add_button.setObjectName("addButton")
        self.add_button.clicked.connect(self._on_add_document)
        layout.addWidget(self.add_button)

        self.clear_button = QPushButton(self.i18n.tr("clear_database"), panel)
        self.clear_button.setObjectName("clearButton")
        self.clear_button.clicked.connect(self._on_clear_database)
        layout.addWidget(self.clear_button)

        return panel

    def _build_right_panel(self) -> QWidget:
        panel = QWidget(self)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self.chat_browser = QTextBrowser(panel)
        self.chat_browser.setOpenExternalLinks(True)
        layout.addWidget(self.chat_browser, stretch=1)

        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.input_field = QLineEdit(panel)
        self.input_field.setPlaceholderText(self.i18n.tr("input_placeholder"))
        self.input_field.returnPressed.connect(self._on_send)
        input_row.addWidget(self.input_field, stretch=1)

        self.send_button = QPushButton(self.i18n.tr("send"), panel)
        self.send_button.clicked.connect(self._on_send)
        input_row.addWidget(self.send_button)

        layout.addLayout(input_row)
        return panel

    def _build_status_bar(self) -> None:
        self.statusBar().showMessage(self.i18n.tr("status_ready"))

    # ──────────────────────── Localization ────────────────────────

    def _retranslate_ui(self) -> None:
        self.setWindowTitle(self.i18n.tr("app_title"))
        self.documents_label.setText(self.i18n.tr("documents"))
        self.add_button.setText(self.i18n.tr("add_document"))
        self.clear_button.setText(self.i18n.tr("clear_database"))
        self.send_button.setText(self.i18n.tr("send"))
        self.input_field.setPlaceholderText(self.i18n.tr("input_placeholder"))
        self.model_label.setText(self.i18n.tr("model_label"))
        self._update_theme_tooltip()
        self.statusBar().showMessage(self.i18n.tr("status_ready"))

    def set_language(self, lang: str) -> None:
        self.i18n.set_language(lang)
        self._retranslate_ui()
        self._render_chat()

    # ──────────────────────── Theme ────────────────────────

    def _apply_theme(self, theme_name: str) -> None:
        if theme_name not in THEMES:
            theme_name = THEME_DARK
        self._current_theme = theme_name
        self.setStyleSheet(THEMES[theme_name])
        self.theme_button.setText("☀" if theme_name == THEME_DARK else "☾")
        self._update_theme_tooltip()
        self._render_chat()

    def _update_theme_tooltip(self) -> None:
        key = (
            "theme_switch_to_light"
            if self._current_theme == THEME_DARK
            else "theme_switch_to_dark"
        )
        self.theme_button.setToolTip(self.i18n.tr(key))

    def _on_toggle_theme(self) -> None:
        new_theme = THEME_LIGHT if self._current_theme == THEME_DARK else THEME_DARK
        self._apply_theme(new_theme)

    # ──────────────────────── Chat history ────────────────────────

    def _show_welcome_message(self) -> None:
        self._chat_history = []
        self._chat_history.append({
            "role": "bot",
            "text": self.i18n.tr("chat_welcome"),
            "streaming": False,
        })
        self._render_chat()

    def _append_user_message(self, text: str) -> None:
        self._chat_history.append({"role": "user", "text": text, "streaming": False})

    def _begin_bot_message(self) -> None:
        """Add an empty streaming bot message — chunks will fill it."""
        self._chat_history.append({"role": "bot", "text": "", "streaming": True})
        self._streaming_rendered_len = 0

    def _finalize_last_bot_message(self) -> None:
        if self._chat_history and self._chat_history[-1]["role"] == "bot":
            self._chat_history[-1]["streaming"] = False
        self._streaming_rendered_len = 0
        self._render_chat()

    # ──────────────────────── Full re-render ────────────────────────
    # Used for: welcome, theme/language switch, finalization, errors.
    # NOT used during streaming (see _flush_streaming).

    def _render_chat(self) -> None:
        """Rebuild the whole chat. Only called outside the streaming loop."""
        was_at_bottom = self._is_at_bottom()
        self.chat_browser.clear()

        for msg in self._chat_history:
            self._insert_message(msg)

        # If we re-rendered while a stream was in progress (theme switch etc.),
        # sync the counter so the next flush only adds the new tail.
        if self._chat_history and self._chat_history[-1].get("streaming"):
            self._streaming_rendered_len = len(self._chat_history[-1]["text"])
        else:
            self._streaming_rendered_len = 0

        if was_at_bottom:
            QTimer.singleShot(0, self._scroll_to_bottom)

    def _insert_message(self, msg: dict[str, Any]) -> None:
        """Insert one message via QTextCursor — no HTML string assembly."""
        cursor = self.chat_browser.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        role = msg.get("role", "bot")
        text = msg.get("text", "")
        streaming = bool(msg.get("streaming", False))

        if role == "bot":
            name_color = "#4ec9b0" if self._current_theme == THEME_DARK else "#0a7a5c"
            display_name = self.i18n.tr("bot")
        else:
            name_color = "#569cd6" if self._current_theme == THEME_DARK else "#0066cc"
            display_name = self.i18n.tr("you")

        # Name label
        cursor.insertHtml(
            f'<span style="color:{name_color}; font-weight:600;">{display_name}:</span>'
        )
        cursor.insertBlock()

        # Body — markdown-aware via QTextDocumentFragment (no HTML round-trip).
        if text:
            try:
                fragment = QTextDocumentFragment.fromMarkdown(text)
                cursor.insertFragment(fragment)
            except Exception:
                logger.warning(
                    "Markdown render failed for role=%s — falling back to plain text",
                    role, exc_info=True,
                )
                cursor.insertText(text)

        # Streaming caret (only shown when streaming)
        if streaming:
            self._insert_caret(cursor)

        # Message separator
        cursor.insertBlock()

    def _insert_caret(self, cursor: QTextCursor) -> None:
        caret_color = "#4ec9b0" if self._current_theme == THEME_DARK else "#0a7a5c"
        cursor.insertHtml(
            f'<span style="color:{caret_color};">{STREAMING_CARET}</span>'
        )

    # ──────────────────────── Streaming ────────────────────────

    def _on_chat_chunk(self, chunk: str) -> None:
        """Accumulate a chunk in history; schedule a delta flush."""
        if not self._chat_history or self._chat_history[-1]["role"] != "bot":
            return
        self._chat_history[-1]["text"] += chunk
        if not self._stream_timer.isActive():
            self._stream_timer.start()
        self.statusBar().showMessage("Receiving answer...")

    def _flush_streaming(self) -> None:
        """
        Append ONLY the new delta to the widget.

        No clear(), no full re-render — this is what kills the flicker.
        The current bot message keeps its plain text during streaming;
        on _finalize_last_bot_message() the chat is re-rendered once with
        proper Markdown.
        """
        if not self._chat_history or not self._chat_history[-1].get("streaming"):
            return

        full_text: str = self._chat_history[-1]["text"]
        if len(full_text) <= self._streaming_rendered_len:
            return

        delta = full_text[self._streaming_rendered_len:]
        was_at_bottom = self._is_at_bottom()

        cursor = self.chat_browser.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # Remove the caret at the end (if present), then insert delta, then re-add.
        if self.chat_browser.toPlainText().endswith(STREAMING_CARET):
            cursor.deletePreviousChar()

        cursor.insertText(delta)
        self._insert_caret(cursor)

        self._streaming_rendered_len = len(full_text)

        if was_at_bottom:
            self._scroll_to_bottom()

    # ──────────────────────── Scroll helpers ────────────────────────

    def _is_at_bottom(self) -> bool:
        sb = self.chat_browser.verticalScrollBar()
        return sb.value() >= (sb.maximum() - 4)

    def _scroll_to_bottom(self) -> None:
        sb = self.chat_browser.verticalScrollBar()
        sb.setValue(sb.maximum())
        self.chat_browser.ensureCursorVisible()

    # ──────────────────────── UI busy state ────────────────────────

    def _set_ui_busy(self, busy: bool) -> None:
        self.add_button.setEnabled(not busy)
        self.clear_button.setEnabled(not busy)
        self.send_button.setEnabled(not busy)
        self.input_field.setEnabled(not busy)
        self.model_combo.setEnabled(not busy)

    # ──────────────────────── Add Document ────────────────────────

    def _on_add_document(self) -> None:
        if self._indexing_worker is not None:
            return

        try:
            path, _ = QFileDialog.getOpenFileName(
                self,
                self.i18n.tr("file_dialog_caption"),
                "",
                self.i18n.tr("file_dialog_filter"),
            )
        except Exception as exc:
            logger.exception("File dialog failed")
            QMessageBox.warning(self, "Error", f"File dialog failed: {exc}")
            return

        if not path:
            return

        filename = Path(path).name
        if self._file_is_listed(filename):
            QMessageBox.information(
                self, "Info",
                f"'{filename}' is already in the list.\n"
                f"Re-indexing will overwrite its chunks.",
            )
            return

        self._set_ui_busy(True)
        self.statusBar().showMessage(f"Parsing {filename}...")

        worker = IndexingWorker(path, parent=self)
        worker.progress.connect(self._on_indexing_progress)
        worker.indexed.connect(self._on_indexing_indexed)
        worker.error.connect(self._on_indexing_error)
        worker.finished.connect(self._on_indexing_finished)
        self._indexing_worker = worker
        worker.start()

    def _file_is_listed(self, filename: str) -> bool:
        for i in range(self.file_list.count()):
            if self.file_list.item(i).text() == filename:
                return True
        return False

    def _on_indexing_progress(self, message: str) -> None:
        self.statusBar().showMessage(message)

    def _on_indexing_indexed(self, filename: str, n_chunks: int) -> None:
        self.file_list.addItem(filename)
        self.statusBar().showMessage(f"Indexed '{filename}' ({n_chunks} chunks)")

    def _on_indexing_error(self, message: str) -> None:
        self.statusBar().showMessage("Indexing failed")
        QMessageBox.critical(self, "Indexing error", message)

    def _on_indexing_finished(self) -> None:
        self._set_ui_busy(False)
        self._indexing_worker = None

    # ──────────────────────── Clear Database ────────────────────────

    def _on_clear_database(self) -> None:
        if self.file_list.count() == 0:
            return

        reply = QMessageBox.question(
            self,
            self.i18n.tr("confirm_clear_title"),
            self.i18n.tr("confirm_clear_msg"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            clear_collection()
            self.file_list.clear()
            self.statusBar().showMessage("Database cleared")
            logger.info("ChromaDB collection cleared")
        except Exception as exc:
            logger.exception("Failed to clear collection")
            QMessageBox.critical(self, "Error", f"Failed to clear database: {exc}")

    # ──────────────────────── Send (streaming chat) ────────────────────────

    def _on_send(self) -> None:
        if self._chat_worker is not None:
            return

        text = self.input_field.text().strip()
        if not text:
            return

        self._append_user_message(text)
        self._begin_bot_message()
        self._render_chat()
        self.input_field.clear()

        self._set_ui_busy(True)
        self.send_button.setText("...")
        self.statusBar().showMessage("Thinking...")

        worker = ChatWorker(
            question=text,
            model=self.model_combo.currentText(),
            parent=self,
        )
        worker.chunk_received.connect(self._on_chat_chunk)
        worker.error.connect(self._on_chat_error)
        worker.finished.connect(self._on_chat_finished)
        self._chat_worker = worker
        worker.start()

    def _on_chat_error(self, message: str) -> None:
        if self._chat_history and self._chat_history[-1]["role"] == "bot":
            self._chat_history[-1]["text"] = f"[error] {message}"
            self._chat_history[-1]["streaming"] = False
        self._streaming_rendered_len = 0
        self._render_chat()
        self.statusBar().showMessage("Chat failed")
        QMessageBox.critical(self, "Chat error", message)

    def _on_chat_finished(self) -> None:
        # Flush any remaining delta that arrived after the last timer tick.
        self._flush_streaming()
        self._finalize_last_bot_message()
        self._set_ui_busy(False)
        self.send_button.setText(self.i18n.tr("send"))
        self.statusBar().showMessage(self.i18n.tr("status_ready"))
        self._chat_worker = None