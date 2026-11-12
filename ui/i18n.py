"""
ui/i18n.py — Minimal localization layer.

Usage:
    from ui.i18n import I18n
    i18n = I18n(lang="en")
    i18n.tr("send")          # -> "Send"

Default language is English. Russian is provided as a ready stub.
Adding a new language = adding a new key to _STRINGS.
"""

from __future__ import annotations


DEFAULT_LANGUAGE: str = "en"


_STRINGS: dict[str, dict[str, str]] = {
    "en": {
        # Window / app
        "app_title":            "Private RAG Desktop Client",
        # Left panel
        "documents":            "Documents",
        "add_document":         "Add Document",
        "clear_database":       "Clear Database",
        "no_documents":         "(no documents yet)",
        # Right panel / chat
        "send":                 "Send",
        "input_placeholder":    "Ask a question about your documents...",
        "you":                  "You",
        "bot":                  "Bot",
        "chat_welcome":         "Welcome! Add a document on the left, then ask a question.",
        "stub_response":        "This is a stub response. RAG logic arrives in Stage 4.",
        # Toolbar
        "model_label":          "Model:",
        "theme_switch_to_light": "Switch to light theme",
        "theme_switch_to_dark":  "Switch to dark theme",
        # Dialogs
        "file_dialog_caption":  "Add Document",
        "file_dialog_filter":   "Documents (*.pdf *.docx *.txt)",
        "confirm_clear_title":  "Confirm",
        "confirm_clear_msg":    "Clear all documents from the list?\n(The vector database will also be cleared.)",
        # Status bar
        "status_ready":         "Ready",
    },
    "ru": {
        # Russian stub — ready to use, not wired to any UI switcher yet.
        "app_title":            "Приватный RAG-клиент",
        "documents":            "Документы",
        "add_document":         "Добавить документ",
        "clear_database":       "Очистить базу",
        "no_documents":         "(документов пока нет)",
        "send":                 "Отправить",
        "input_placeholder":    "Задайте вопрос по документам...",
        "you":                  "Вы",
        "bot":                  "Бот",
        "chat_welcome":         "Добро пожаловать! Добавьте документ слева и задайте вопрос.",
        "stub_response":        "Это заглушка. Логика RAG появится на Этапе 4.",
        "model_label":          "Модель:",
        "theme_switch_to_light": "Переключить на светлую тему",
        "theme_switch_to_dark":  "Переключить на тёмную тему",
        "file_dialog_caption":  "Добавить документ",
        "file_dialog_filter":   "Документы (*.pdf *.docx *.txt)",
        "confirm_clear_title":  "Подтверждение",
        "confirm_clear_msg":    "Очистить список документов?\n(Векторная база также будет очищена.)",
        "status_ready":         "Готово",
    },
}


class I18n:
    """Tiny dictionary-based localization helper."""

    def __init__(self, lang: str = DEFAULT_LANGUAGE) -> None:
        if lang not in _STRINGS:
            lang = DEFAULT_LANGUAGE
        self._lang: str = lang

    @property
    def language(self) -> str:
        return self._lang

    def set_language(self, lang: str) -> None:
        """Switch language. Falls back to default if the language is unknown."""
        if lang in _STRINGS:
            self._lang = lang

    def tr(self, key: str) -> str:
        """Translate a key. Unknown keys are returned as-is (visible in UI)."""
        return _STRINGS.get(self._lang, {}).get(key, key)