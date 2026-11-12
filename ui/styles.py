"""
ui/styles.py — Qt Style Sheet themes (QSS).

Two ready-to-use themes:
    • DARK_THEME  — VS Code Dark+ inspired
    • LIGHT_THEME — clean light counterpart

Switching: MainWindow._apply_theme() calls self.setStyleSheet(...) which
propagates instantly to all child widgets — no restart required.
"""

from __future__ import annotations


# ──────────────────────────── DARK ────────────────────────────

DARK_THEME: str = """
QMainWindow, QWidget {
    background-color: #1e1e1e;
    color: #d4d4d4;
    font-family: "Segoe UI", "Consolas", sans-serif;
    font-size: 10pt;
}

QToolBar {
    background-color: #252526;
    border: none;
    border-bottom: 1px solid #3c3c3c;
    padding: 6px;
    spacing: 8px;
}

QToolBar QLabel {
    background: transparent;
    color: #cccccc;
    padding-right: 4px;
}

QStatusBar {
    background-color: #007acc;
    color: #ffffff;
    font-size: 9pt;
}

QStatusBar::item {
    border: none;
}

QLabel {
    background: transparent;
}

QLabel#sectionLabel {
    font-weight: 600;
    padding: 4px 2px;
    color: #cccccc;
}

QListWidget {
    background-color: #252526;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    padding: 4px;
    outline: none;
}

QListWidget::item {
    padding: 6px 8px;
    border-radius: 3px;
}

QListWidget::item:hover {
    background-color: #2a2d2e;
}

QListWidget::item:selected {
    background-color: #094771;
    color: #ffffff;
}

QPushButton {
    background-color: #0e639c;
    color: #ffffff;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #1177bb;
}

QPushButton:pressed {
    background-color: #094771;
}

QPushButton:disabled {
    background-color: #3c3c3c;
    color: #808080;
}

QPushButton#clearButton {
    background-color: #3c3c3c;
    color: #d4d4d4;
}

QPushButton#clearButton:hover {
    background-color: #5a1d1d;
    color: #f48771;
}

QPushButton#themeButton {
    background-color: transparent;
    color: #d4d4d4;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 13pt;
    min-width: 36px;
}

QPushButton#themeButton:hover {
    background-color: #2a2d2e;
}

QLineEdit {
    background-color: #3c3c3c;
    color: #d4d4d4;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    padding: 8px 12px;
    selection-background-color: #0e639c;
}

QLineEdit:focus {
    border: 1px solid #0e639c;
}

QTextBrowser {
    background-color: #1e1e1e;
    color: #d4d4d4;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    padding: 10px;
    selection-background-color: #0e639c;
}

QComboBox {
    background-color: #3c3c3c;
    color: #d4d4d4;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    padding: 4px 10px;
    min-width: 130px;
}

QComboBox:hover {
    border: 1px solid #0e639c;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox QAbstractItemView {
    background-color: #252526;
    color: #d4d4d4;
    selection-background-color: #094771;
    border: 1px solid #3c3c3c;
    outline: none;
}

QSplitter::handle {
    background-color: #3c3c3c;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QScrollBar:vertical {
    background-color: #1e1e1e;
    width: 12px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #424242;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #4e4e4e;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: none;
}

QMessageBox {
    background-color: #252526;
}

QMessageBox QLabel {
    color: #d4d4d4;
}

QToolTip {
    background-color: #252526;
    color: #d4d4d4;
    border: 1px solid #0e639c;
    padding: 4px;
}
"""


# ──────────────────────────── LIGHT ────────────────────────────

LIGHT_THEME: str = """
QMainWindow, QWidget {
    background-color: #ffffff;
    color: #333333;
    font-family: "Segoe UI", "Consolas", sans-serif;
    font-size: 10pt;
}

QToolBar {
    background-color: #f3f3f3;
    border: none;
    border-bottom: 1px solid #e0e0e0;
    padding: 6px;
    spacing: 8px;
}

QToolBar QLabel {
    background: transparent;
    color: #333333;
    padding-right: 4px;
}

QStatusBar {
    background-color: #0066cc;
    color: #ffffff;
    font-size: 9pt;
}

QStatusBar::item {
    border: none;
}

QLabel {
    background: transparent;
}

QLabel#sectionLabel {
    font-weight: 600;
    padding: 4px 2px;
    color: #333333;
}

QListWidget {
    background-color: #f9f9f9;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    padding: 4px;
    outline: none;
}

QListWidget::item {
    padding: 6px 8px;
    border-radius: 3px;
}

QListWidget::item:hover {
    background-color: #eaf2fb;
}

QListWidget::item:selected {
    background-color: #cce4ff;
    color: #0066cc;
}

QPushButton {
    background-color: #0066cc;
    color: #ffffff;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #1177dd;
}

QPushButton:pressed {
    background-color: #004a99;
}

QPushButton:disabled {
    background-color: #e0e0e0;
    color: #a0a0a0;
}

QPushButton#clearButton {
    background-color: #e8e8e8;
    color: #333333;
}

QPushButton#clearButton:hover {
    background-color: #ffd6d6;
    color: #c62828;
}

QPushButton#themeButton {
    background-color: transparent;
    color: #333333;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 13pt;
    min-width: 36px;
}

QPushButton#themeButton:hover {
    background-color: #eaf2fb;
}

QLineEdit {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    padding: 8px 12px;
    selection-background-color: #0066cc;
}

QLineEdit:focus {
    border: 1px solid #0066cc;
}

QTextBrowser {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    padding: 10px;
    selection-background-color: #0066cc;
}

QComboBox {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    padding: 4px 10px;
    min-width: 130px;
}

QComboBox:hover {
    border: 1px solid #0066cc;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #333333;
    selection-background-color: #cce4ff;
    border: 1px solid #e0e0e0;
    outline: none;
}

QSplitter::handle {
    background-color: #e0e0e0;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QScrollBar:vertical {
    background-color: #ffffff;
    width: 12px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #c8c8c8;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #a8a8a8;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: none;
}

QMessageBox {
    background-color: #f3f3f3;
}

QMessageBox QLabel {
    color: #333333;
}

QToolTip {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #0066cc;
    padding: 4px;
}
"""


THEMES: dict[str, str] = {
    "dark": DARK_THEME,
    "light": LIGHT_THEME,
}