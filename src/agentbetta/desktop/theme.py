"""AgentBetta desktop design system.

A small, opinionated token set plus a single Qt stylesheet. The GUI supports
only System / Light / Dark. The accent colour is taken from the AgentBetta logo
blue. Sizes are in pixels for predictable density (UI 14px, chat/output 12px).
"""

from __future__ import annotations

from dataclasses import dataclass
from string import Template

from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication

THEMES = ("system", "light", "dark")

UI_PX = 14
OUTPUT_PX = 12


@dataclass(frozen=True)
class ThemeTokens:
    name: str
    bg: str
    surface: str
    surface_alt: str
    surface_sunken: str
    border: str
    border_strong: str
    text: str
    text_muted: str
    text_faint: str
    accent: str
    accent_hover: str
    accent_pressed: str
    accent_soft: str
    on_accent: str
    success: str
    success_soft: str
    warning: str
    warning_soft: str
    danger: str
    danger_soft: str
    info: str
    info_soft: str
    selection: str
    scrollbar: str
    scrollbar_hover: str
    user_bubble: str
    user_bubble_text: str
    user_bubble_border: str


LIGHT = ThemeTokens(
    name="light",
    bg="#f5f7fb",
    surface="#ffffff",
    surface_alt="#eef2f8",
    surface_sunken="#e4eaf3",
    border="#d6dce6",
    border_strong="#b3bdca",
    text="#000000",
    text_muted="#333b46",
    text_faint="#5f6875",
    accent="#3b82f6",
    accent_hover="#2f6fe0",
    accent_pressed="#2560c9",
    accent_soft="#e8f1ff",
    on_accent="#ffffff",
    success="#0e7a5f",
    success_soft="#dff3ec",
    warning="#9a6400",
    warning_soft="#fbf0d9",
    danger="#c0392b",
    danger_soft="#fbe7e4",
    info="#3b82f6",
    info_soft="#e8f1ff",
    selection="#d3e4ff",
    scrollbar="#c2cbd8",
    scrollbar_hover="#9fabc0",
    user_bubble="#dbeafe",
    user_bubble_text="#0b2545",
    user_bubble_border="#bfdbfe",
)

DARK = ThemeTokens(
    name="dark",
    bg="#0d1117",
    surface="#161b22",
    surface_alt="#1d242d",
    surface_sunken="#0a0e13",
    border="#2a313b",
    border_strong="#3c4552",
    text="#ffffff",
    text_muted="#cbd3dd",
    text_faint="#96a0ac",
    accent="#6aa4ff",
    accent_hover="#85b6ff",
    accent_pressed="#4f8be6",
    accent_soft="#16294a",
    on_accent="#ffffff",
    success="#3fbf95",
    success_soft="#12302a",
    warning="#e0b341",
    warning_soft="#332912",
    danger="#f07167",
    danger_soft="#3a1f1c",
    info="#6aa4ff",
    info_soft="#16294a",
    selection="#20375c",
    scrollbar="#333c48",
    scrollbar_hover="#4a5666",
    user_bubble="#1d3a5c",
    user_bubble_text="#ffffff",
    user_bubble_border="#2f5c93",
)

_current: ThemeTokens = LIGHT


def tokens(theme: str = "system") -> ThemeTokens:
    return DARK if resolve_theme(theme) == "dark" else LIGHT


def current_tokens() -> ThemeTokens:
    return _current


def system_theme() -> str:
    app = QApplication.instance()
    if app is None:
        return "light"
    window = app.palette().color(QPalette.Window)
    return "dark" if window.lightness() < 128 else "light"


def resolve_theme(theme: str) -> str:
    if theme == "dark":
        return "dark"
    if theme == "light":
        return "light"
    return system_theme()


_QSS = Template(
    """
* { outline: 0; }

QWidget {
    background-color: transparent;
    color: $text;
    font-size: ${ui}px;
}

QMainWindow, QDialog { background-color: $bg; }
#AppRoot, #CenterPane { background-color: $bg; }

#HeaderBar { background-color: $surface; border-bottom: 1px solid $border; }
#HeaderBar QLabel { background: transparent; }
#BrandLogo { background: transparent; }
#BrandName { font-size: 18px; font-weight: 800; background: transparent; }
#BrandTag { color: $text_muted; font-size: 12px; background: transparent; }

#Sidebar { background-color: $surface; border-right: 1px solid $border; }
#NavSection {
    color: $text_faint; font-size: 12px; font-weight: 700;
    padding: 12px 16px 6px 16px; background: transparent;
}

QListWidget#NavList {
    background: transparent; border: none; padding: 4px 8px 8px 8px;
    font-size: 15px; font-weight: 600;
}
QListWidget#NavList::item {
    color: $text_muted; padding: 9px 12px; border-radius: 8px; margin: 2px 0;
    border: 1px solid transparent;
}
QListWidget#NavList::item:hover { background-color: $surface_alt; color: $text; }
QListWidget#NavList::item:selected {
    background-color: $accent_soft; color: $accent; border: 1px solid $accent;
}

#CenterPane { background-color: $bg; }
#Inspector { background-color: $surface; border-left: 1px solid $border; }

QFrame#Card { background-color: $surface; border: 1px solid $border; border-radius: 12px; }
QFrame#Card[flat="true"] { background-color: $surface_alt; border: 1px solid $border; }
#CardTitle { font-size: 15px; font-weight: 700; background: transparent; }
#CardSubtitle { color: $text_muted; font-size: 12px; background: transparent; }

QLabel { background: transparent; }
QLabel#H1 { font-size: 20px; font-weight: 800; }
QLabel#H2 { font-size: 17px; font-weight: 700; }
QLabel#H3 { font-size: 15px; font-weight: 700; }
QLabel#Muted { color: $text_muted; }
QLabel#Faint { color: $text_faint; font-size: 12px; }
QLabel#FieldLabel { color: $text_muted; font-size: 13px; font-weight: 600; }
QLabel#StatValue { font-size: 22px; font-weight: 800; }

QLabel#Badge {
    border-radius: 10px; padding: 3px 10px; font-size: 12px; font-weight: 700;
    background-color: $surface_alt; color: $text_muted; border: 1px solid $border;
}
QLabel#Badge[tone="accent"]  { background-color: $accent_soft;  color: $accent;  border-color: $accent; }
QLabel#Badge[tone="success"] { background-color: $success_soft; color: $success; border-color: $success; }
QLabel#Badge[tone="warning"] { background-color: $warning_soft; color: $warning; border-color: $warning; }
QLabel#Badge[tone="danger"]  { background-color: $danger_soft;  color: $danger;  border-color: $danger; }
QLabel#Badge[tone="info"]    { background-color: $info_soft;    color: $info;    border-color: $info; }
QLabel#Badge[tone="muted"]   { background-color: $surface_alt;  color: $text_muted; border-color: $border; }

QPushButton {
    background-color: $surface; color: $text; border: 1px solid $border_strong;
    border-radius: 8px; padding: 7px 14px; font-weight: 600; font-size: 14px;
}
QPushButton:hover { background-color: $accent_soft; border-color: $accent; color: $accent; }
QPushButton:pressed { background-color: $surface_sunken; }
QPushButton:disabled { color: $text_faint; border-color: $border; background-color: $surface_alt; }

QPushButton#Primary { background-color: $accent; color: $on_accent; border: 1px solid $accent; font-weight: 700; }
QPushButton#Primary:hover { background-color: $accent_hover; border-color: $accent_hover; color: $on_accent; }
QPushButton#Primary:pressed { background-color: $accent_pressed; }
QPushButton#Primary:disabled { background-color: $border; color: $text_faint; border-color: $border; }

QPushButton#Danger { background-color: $danger_soft; color: $danger; border: 1px solid $danger; }
QPushButton#Danger:hover { background-color: $danger; color: #ffffff; border-color: $danger; }

QPushButton#Ghost { background: transparent; border: 1px solid $border; color: $text_muted; }
QPushButton#Ghost:hover { background-color: $accent_soft; color: $accent; border-color: $accent; }
QPushButton#Ghost:checked { background-color: $accent_soft; color: $accent; border-color: $accent; }

QPushButton#Link { background: transparent; border: none; color: $info; padding: 2px 4px; text-align: left; font-weight: 600; }
QPushButton#Link:hover { color: $accent; }

QToolButton {
    background: transparent; border: 1px solid $border; border-radius: 8px;
    padding: 5px 10px; color: $text_muted; font-weight: 600; font-size: 14px;
}
QToolButton:hover { background-color: $accent_soft; color: $accent; border-color: $accent; }
QToolButton:checked { background-color: $accent_soft; color: $accent; border-color: $accent; }

QLineEdit, QPlainTextEdit, QTextEdit, QTextBrowser, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: $surface; color: $text; border: 1px solid $border_strong;
    border-radius: 8px; padding: 6px 9px;
    selection-background-color: $accent; selection-color: $on_accent;
}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus { border: 1px solid $accent; }
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled { color: $text_faint; background-color: $surface_alt; }

QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView {
    background-color: $surface; border: 1px solid $accent;
    selection-background-color: $accent_soft; selection-color: $accent; outline: 0;
}

QCheckBox { spacing: 8px; background: transparent; font-weight: 600; font-size: 14px; }
QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid $border_strong; border-radius: 5px; background-color: $surface; }
QCheckBox::indicator:checked { background-color: $accent; border-color: $accent; }
QCheckBox::indicator:hover { border-color: $accent; }

QTableWidget, QTableView {
    background-color: $surface; alternate-background-color: $surface_alt;
    border: 1px solid $border; border-radius: 10px; gridline-color: $border;
    selection-background-color: $accent_soft; selection-color: $accent;
}
QTableWidget::item { padding: 6px 9px; border: none; }
QHeaderView::section {
    background-color: $surface_alt; color: $text; border: none;
    border-bottom: 1px solid $border; padding: 8px 9px; font-weight: 700; font-size: 13px;
}
QTableCornerButton::section { background-color: $surface_alt; border: none; }

QListWidget { background-color: $surface; border: 1px solid $border; border-radius: 10px; padding: 4px; }
QListWidget::item { padding: 7px 9px; border-radius: 7px; color: $text; }
QListWidget::item:hover { background-color: $surface_alt; }
QListWidget::item:selected { background-color: $accent_soft; color: $accent; border: 1px solid $accent; }

QTabWidget::pane { border: 1px solid $border; border-radius: 10px; background-color: $surface; top: -1px; }
QTabBar::tab {
    background: transparent; color: $text_muted; padding: 8px 14px;
    border: 1px solid transparent; border-bottom: 2px solid transparent;
    margin-right: 2px; font-size: 14px; font-weight: 600;
}
QTabBar::tab:hover { color: $accent; background-color: $accent_soft; border-radius: 7px; }
QTabBar::tab:selected { color: $accent; border-bottom: 2px solid $accent; font-weight: 700; }

QProgressBar { background-color: $surface_alt; border: 1px solid $border; border-radius: 5px; height: 8px; text-align: center; color: transparent; }
QProgressBar::chunk { background-color: $accent; border-radius: 4px; }

QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { background: transparent; width: 12px; margin: 2px; }
QScrollBar::handle:vertical { background: $scrollbar; border-radius: 5px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: $scrollbar_hover; }
QScrollBar:horizontal { background: transparent; height: 12px; margin: 2px; }
QScrollBar::handle:horizontal { background: $scrollbar; border-radius: 5px; min-width: 30px; }
QScrollBar::handle:horizontal:hover { background: $scrollbar_hover; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

QSplitter::handle { background-color: $border; }
QSplitter::handle:horizontal { width: 1px; }
QSplitter::handle:vertical { height: 1px; }

QToolTip { background-color: $surface_sunken; color: $text; border: 1px solid $border_strong; border-radius: 6px; padding: 5px 8px; }

QStatusBar { background-color: $surface; color: $text_muted; border-top: 1px solid $border; font-size: 13px; }
QStatusBar::item { border: none; }

QMenu { background-color: $surface; border: 1px solid $border_strong; border-radius: 8px; padding: 4px; }
QMenu::item { padding: 6px 18px; border-radius: 5px; }
QMenu::item:selected { background-color: $accent_soft; color: $accent; }

QGroupBox { border: 1px solid $border; border-radius: 8px; margin-top: 12px; padding: 10px; background-color: $surface; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; color: $text_muted; font-weight: 700; }

#Divider { background-color: $border; max-height: 1px; min-height: 1px; border: none; }
#EmptyState { color: $text_faint; }

/* ---- chat transcript ---- */
#ChatScroll { background-color: $bg; border: none; }
#ChatBubbleUser { background-color: $user_bubble; border: 1px solid $user_bubble_border; border-radius: 14px; }
#ChatBubbleUser QTextBrowser { background: transparent; border: none; color: $user_bubble_text; padding: 0; font-size: ${output}px; }
#ChatBubbleAgent { background-color: $surface; border: 1px solid $border; border-radius: 14px; }
#ChatBubbleAgent QTextBrowser { background: transparent; border: none; color: $text; padding: 0; font-size: ${output}px; }
#ChatBubbleAgent QTextBrowser a { color: $info; }
#ChatBubbleUser QTextBrowser a { color: $user_bubble_text; }
QTextBrowser#ChatBody { background: transparent; border: none; font-size: ${output}px; }
#ChatStatus { color: $text_faint; font-size: 12px; font-weight: 600; }
#ChatRoleUser { color: $text_muted; font-size: 12px; font-weight: 700; }
#ChatRoleAgent { color: $accent; font-size: 12px; font-weight: 700; }

QToolButton#ChatAction {
    border: none; background: transparent; padding: 3px; border-radius: 6px;
}
QToolButton#ChatAction:hover { background-color: $surface_alt; }
QToolButton#ChatAction:checked { background-color: $accent_soft; }
"""
)


def build_stylesheet(theme: str) -> str:
    values = dict(tokens(theme).__dict__)
    values["ui"] = UI_PX
    values["output"] = OUTPUT_PX
    return _QSS.substitute(values)


def document_stylesheet(theme: str | None = None) -> str:
    """CSS for QTextDocument content (chat output: headings, code, tables)."""

    t = _current if theme is None else tokens(theme)
    return (
        f"body {{ color: {t.text}; font-size: {OUTPUT_PX}px; }}"
        f"h1 {{ font-size: 18px; font-weight: 800; margin: 10px 0 6px 0; }}"
        f"h2 {{ font-size: 16px; font-weight: 700; margin: 8px 0 4px 0; }}"
        f"h3 {{ font-size: 14px; font-weight: 700; margin: 6px 0 3px 0; }}"
        f"p {{ margin: 4px 0; }}"
        f"ul, ol {{ margin: 4px 0 4px 18px; }}"
        f"code {{ background-color: {t.surface_alt}; color: {t.text};"
        f" font-family: Consolas, 'Courier New', monospace; }}"
        f"pre {{ background-color: {t.surface_alt}; color: {t.text}; padding: 8px;"
        f" border: 1px solid {t.border}; font-family: Consolas, 'Courier New', monospace; }}"
        f"blockquote {{ color: {t.text_muted}; border-left: 3px solid {t.accent};"
        f" margin: 6px 0; padding-left: 8px; }}"
        f"a {{ color: {t.info}; }}"
        f"th, td {{ border: 1px solid {t.border}; padding: 4px 8px; }}"
        f"th {{ background-color: {t.surface_alt}; }}"
    )


def _palette(t: ThemeTokens) -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(t.bg))
    palette.setColor(QPalette.WindowText, QColor(t.text))
    palette.setColor(QPalette.Base, QColor(t.surface))
    palette.setColor(QPalette.AlternateBase, QColor(t.surface_alt))
    palette.setColor(QPalette.Text, QColor(t.text))
    palette.setColor(QPalette.Button, QColor(t.surface))
    palette.setColor(QPalette.ButtonText, QColor(t.text))
    palette.setColor(QPalette.ToolTipBase, QColor(t.surface))
    palette.setColor(QPalette.ToolTipText, QColor(t.text))
    palette.setColor(QPalette.PlaceholderText, QColor(t.text_faint))
    palette.setColor(QPalette.Highlight, QColor(t.accent))
    palette.setColor(QPalette.HighlightedText, QColor(t.on_accent))
    palette.setColor(QPalette.Link, QColor(t.info))
    return palette


def _base_font() -> QFont:
    font = QFont("Segoe UI Variable Text")
    if not font.exactMatch():
        font = QFont("Segoe UI")
    font.setPixelSize(UI_PX)
    font.setWeight(QFont.Weight.Medium)
    return font


def apply_theme(app: QApplication, theme: str = "system") -> str:
    """Apply the AgentBetta stylesheet and return the resolved theme name."""

    global _current
    resolved = resolve_theme(theme)
    _current = tokens(resolved)

    app.setStyle("Fusion")
    app.setPalette(_palette(_current))
    app.setStyleSheet(build_stylesheet(resolved))
    app.setFont(_base_font())
    return resolved
