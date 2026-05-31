from __future__ import annotations

import pyperclip
from PyQt6.QtCore import QPoint, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QKeyEvent
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from vitai.config import AppConfig
from vitai.resources import resource_path

class AnswerOverlay(QWidget):
    clicked = pyqtSignal()

    def __init__(self, text: str = "", timeout_ms: int = 0, config: AppConfig | None = None):
        super().__init__()
        self._config = config
        self._answer = text
        self._anchor = QPoint(0, 0)
        self._mode = "answer"
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self._build_ui()
        self.set_answer(text)
        if timeout_ms > 0:
            QTimer.singleShot(timeout_ms, self.close)

    def _build_ui(self) -> None:
        font_family = self._config.font_family if self._config else "Arial"
        font_size = self._config.font_size if self._config else 24
        text_color = self._config.text_color if self._config else "#212529"
        
        self.setStyleSheet(
            f"QWidget#card {{ background: transparent; border: none; }}"
            f"QLabel {{ color: {text_color}; font-size: {font_size}px; font-family: '{font_family}', sans-serif; }}"
        )
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self.card = QWidget(self)
        self.card.setObjectName("card")
        layout = QVBoxLayout(self.card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)



        self.scroll_area = __import__('PyQt6.QtWidgets', fromlist=['QScrollArea']).QScrollArea(self.card)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")
        self.scroll_area.viewport().setStyleSheet("background: transparent;")
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.label = QLabel()
        
        font = QFont(font_family, font_size)
        self.label.setFont(font)
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        self.scroll_area.setWidget(self.label)
        layout.addWidget(self.scroll_area)

        root.addWidget(self.card)

    def mouseDoubleClickEvent(self, event) -> None:
        if self._answer and self._answer != "...":
            pyperclip.copy(self._answer)
            # Show a brief copied message
            old_text = self._answer
            self.label.setText("Đã copy vào clipboard!")
            QTimer.singleShot(1000, lambda: self.label.setText(old_text))

    def set_anchor(self, x: int, y: int) -> None:
        self._anchor = QPoint(x, y)
        self._move_to_anchor()



    def set_answer(self, text: str) -> None:
        self._answer = text
        self.label.setText(text)
        self.adjustSize()
        self.resize(min(max(self.width(), 120), 520), min(max(self.height(), 52), 400))

    def show_message(self, text: str, x: int | None = None, y: int | None = None) -> None:
        self._mode = "answer"
        self.label.show()
        self.set_answer(text)
        if x is not None and y is not None:
            self.set_anchor(x, y)
        else:
            self._move_to_anchor()
        self.show()
        self.raise_()



    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)

    def _move_to_anchor(self) -> None:
        screen = QApplication.screenAt(self._anchor) or QApplication.primaryScreen()
        if screen is None:
            self.move(self._anchor)
            return
        available = screen.availableGeometry()
        x = min(max(available.left(), self._anchor.x() + 10), available.right() - self.width())
        y = min(max(available.top(), self._anchor.y() + 15), available.bottom() - self.height())
        self.move(x, y)
