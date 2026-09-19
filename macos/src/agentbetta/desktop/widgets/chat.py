"""Chat-style transcript: message bubbles with per-message actions."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QTextBrowser,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from agentbetta.desktop.assets import logo_pixmap
from agentbetta.desktop.icons import icon
from agentbetta.desktop.theme import current_tokens, document_stylesheet


class ChatTranscript(QScrollArea):
    """A scrollable transcript of user / agent / status messages."""

    copyText = Signal(str)
    rate = Signal(str, int)      # message id, 1 (like) or -1 (dislike)
    regenerate = Signal()        # try again on the last agent turn
    editUser = Signal(str)       # edit a user message
    resendUser = Signal(str)     # resend a user message

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self.setObjectName("ChatScroll")
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._plain: list[str] = []
        self._rating_buttons: dict[str, tuple[QToolButton, QToolButton]] = {}
        self._thinking_row: QWidget | None = None
        self._thinking_label: QLabel | None = None
        self._thinking_timer: QTimer | None = None
        self._thinking_dots = 0

        container = QWidget()
        self._layout = QVBoxLayout(container)
        self._layout.setContentsMargins(6, 10, 6, 10)
        self._layout.setSpacing(12)
        self._layout.addStretch(1)
        self.setWidget(container)
        self._container = container

    # -- layout helpers ---------------------------------------------------
    def _content_width(self) -> int:
        width = self.viewport().width() if self.viewport() else 720
        return max(320, min(int(width * 0.72), 720))

    def _fit(self, browser: QTextBrowser, width: int) -> None:
        browser.document().setDefaultStyleSheet(document_stylesheet())
        browser.document().setTextWidth(width)
        height = int(browser.document().size().height()) + 8
        browser.setFixedWidth(width)
        browser.setFixedHeight(height)

    def _append(self, row: QWidget) -> None:
        self._layout.insertWidget(self._layout.count() - 1, row)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self) -> None:
        QTimer.singleShot(0, lambda: self.verticalScrollBar().setValue(
            self.verticalScrollBar().maximum()
        ))

    def _make_bubble(self, role: str) -> tuple[QFrame, QTextBrowser]:
        frame = QFrame()
        frame.setObjectName("ChatBubbleUser" if role == "user" else "ChatBubbleAgent")
        frame.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)
        label = QLabel("You" if role == "user" else "AgentBetta")
        label.setObjectName("ChatRoleUser" if role == "user" else "ChatRoleAgent")
        browser = QTextBrowser()
        browser.setObjectName("ChatBody")
        browser.setFrameShape(QFrame.NoFrame)
        browser.setOpenExternalLinks(True)
        browser.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        browser.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout.addWidget(label)
        layout.addWidget(browser)
        return frame, browser

    # -- actions ----------------------------------------------------------
    def _copy(self, text: str) -> None:
        QApplication.clipboard().setText(text)
        self.copyText.emit(text)

    def _action(self, name: str, tip: str, slot: Any, active: bool = False) -> QToolButton:
        tokens = current_tokens()
        button = QToolButton()
        button.setObjectName("ChatAction")
        button.setCursor(Qt.PointingHandCursor)
        button.setIcon(icon(name, tokens.accent if active else tokens.text_faint, 16))
        button.setToolTip(tip)
        button.clicked.connect(slot)
        return button

    def _actions(self, role: str, text: str, message_id: str, rating: int | None) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(2, 0, 2, 0)
        layout.setSpacing(2)
        if role == "user":
            layout.addWidget(self._action("copy", "Copy", lambda: self._copy(text)))
            layout.addWidget(self._action("edit", "Edit & resend", lambda: self.editUser.emit(text)))
            layout.addWidget(self._action("send", "Resend", lambda: self.resendUser.emit(text)))
        else:
            layout.addWidget(self._action("copy", "Copy", lambda: self._copy(text)))
            like = self._action("like", "Good response", lambda: self._set_rating(message_id, 1), rating == 1)
            dislike = self._action(
                "dislike", "Bad response", lambda: self._set_rating(message_id, -1), rating == -1
            )
            layout.addWidget(like)
            layout.addWidget(dislike)
            layout.addWidget(self._action("refresh", "Try again", lambda: self.regenerate.emit()))
            if message_id:
                self._rating_buttons[message_id] = (like, dislike)
        return row

    def _set_rating(self, message_id: str, value: int) -> None:
        buttons = self._rating_buttons.get(message_id)
        if not buttons:
            return
        like, dislike = buttons
        tokens = current_tokens()
        current = 1 if like.toolTip() == "__on__" else (-1 if dislike.toolTip() == "__on__" else None)
        new_value = 0 if current == value else value
        like.setIcon(icon("like", tokens.accent if new_value == 1 else tokens.text_faint, 16))
        dislike.setIcon(icon("dislike", tokens.accent if new_value == -1 else tokens.text_faint, 16))
        like.setToolTip("__on__" if new_value == 1 else "Good response")
        dislike.setToolTip("__on__" if new_value == -1 else "Bad response")
        self.rate.emit(message_id, new_value)

    # -- public API -------------------------------------------------------
    def add_user(self, text: str, *, message_id: str = "") -> None:
        self._plain.append(text)
        width = self._content_width()
        frame, browser = self._make_bubble("user")
        frame.setFixedWidth(width)
        browser.setMarkdown(text)
        self._fit(browser, width - 28)
        frame.layout().addWidget(self._actions("user", text, message_id, None))
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch(1)
        layout.addWidget(frame)
        self._append(row)

    def add_agent(self, markdown: str, *, message_id: str = "", rating: int | None = None,
                  avatar: bool = True, actions: bool = True) -> None:
        self._plain.append(markdown)
        width = self._content_width()
        frame, browser = self._make_bubble("agent")
        frame.setFixedWidth(width)
        browser.setMarkdown(markdown or "_(no content)_")
        self._fit(browser, width - 28)
        if actions:
            frame.layout().addWidget(self._actions("agent", markdown, message_id, rating))
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        if avatar:
            logo = QLabel()
            logo.setPixmap(logo_pixmap(26))
            logo.setFixedSize(28, 28)
            logo.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
            layout.addWidget(logo, 0, Qt.AlignTop)
        layout.addWidget(frame)
        layout.addStretch(1)
        self._append(row)

    def add_status(self, text: str) -> None:
        self._plain.append(text)
        label = QLabel(text)
        label.setObjectName("ChatStatus")
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignCenter)
        self._append(label)

    def show_thinking(self) -> None:
        if self._thinking_row is not None:
            return
        self._thinking_label = QLabel("AgentBetta is thinking")
        self._thinking_label.setObjectName("ChatStatus")
        self._thinking_label.setAlignment(Qt.AlignCenter)
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch(1)
        layout.addWidget(self._thinking_label)
        layout.addStretch(1)
        self._thinking_row = row
        self._append(row)
        self._thinking_timer = QTimer(self)
        self._thinking_timer.setInterval(400)
        self._thinking_timer.timeout.connect(self._tick_thinking)
        self._thinking_timer.start()

    def _tick_thinking(self) -> None:
        self._thinking_dots = (self._thinking_dots + 1) % 4
        if self._thinking_label is not None:
            self._thinking_label.setText("AgentBetta is thinking" + "." * self._thinking_dots)

    def hide_thinking(self) -> None:
        if self._thinking_timer is not None:
            self._thinking_timer.stop()
            self._thinking_timer = None
        if self._thinking_row is not None:
            self._thinking_row.setParent(None)
            self._thinking_row.deleteLater()
            self._thinking_row = None
        self._thinking_label = None

    def clear(self) -> None:
        self.hide_thinking()
        self._plain.clear()
        self._rating_buttons.clear()
        while self._layout.count() > 1:
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

    # -- compatibility ----------------------------------------------------
    def toPlainText(self) -> str:  # noqa: N802 - mirrors QTextBrowser API
        return "\n\n".join(self._plain)
