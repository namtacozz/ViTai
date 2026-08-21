from __future__ import annotations

from PyQt6.QtCore import QPoint, Qt, QTimer
from PyQt6.QtGui import QFont, QMouseEvent
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QWidget,
)

from vitai.config import AppConfig


import re
import sys

def _clean_color(color_val: str | None) -> str:
    if not color_val:
        return "#E09F5E"
    hex_match = re.search(r"#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})", color_val)
    if hex_match:
        return hex_match.group(0).upper()
    return color_val.strip()


class AnswerOverlay(QWidget):
    def __init__(self, text: str = "", timeout_ms: int = 0, config: AppConfig | None = None):
        super().__init__()
        self._config = config
        self._anchor = QPoint(0, 0)

        # Cửa sổ hoàn toàn trong suốt, không viền, luôn nổi trên cùng mọi ứng dụng (Ghost Overlay)
        # Sử dụng Tool | WindowStaysOnTopHint | WindowTransparentForInput
        # để đảm bảo hiển thị nổi lập tức trên toàn màn hình và không bao giờ xuất hiện trong Alt+Tab / Cmd+Tab
        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
        )
        if sys.platform != "darwin":
            flags |= Qt.WindowType.BypassWindowManagerHint
        if sys.platform.startswith("linux"):
            flags |= Qt.WindowType.X11BypassWindowManagerHint

        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setStyleSheet("background: transparent; border: none;")

        self._build_ui()
        self.set_answer(text)

        if timeout_ms > 0:
            QTimer.singleShot(timeout_ms, self.hide_overlay)

    def update_config(self, config: AppConfig) -> None:
        self._config = config
        self._apply_style()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        self._apply_style()

    def _apply_style(self) -> None:
        font_family = "Arial"
        try:
            font_size = self._config.font_size if self._config and self._config.font_size else 18
        except Exception:
            font_size = 18

        raw_color = self._config.text_color if self._config else "#E09F5E"
        text_color = _clean_color(raw_color)

        font = QFont(font_family, font_size, QFont.Weight.Bold)
        self.label.setFont(font)

        self.label.setStyleSheet(
            f"""
            QLabel {{
                color: {text_color};
                font-size: {font_size}px;
                font-family: Arial, sans-serif;
                font-weight: bold;
                background: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }}
            """
        )

    def set_anchor(self, x: int, y: int) -> None:
        self._anchor = QPoint(x, y)
        self._move_to_anchor()

    def set_answer(self, text: str) -> None:
        cleaned = text.strip()
        self._apply_style()
        self.label.setText(cleaned)
        self.label.adjustSize()
        self.adjustSize()

    def show_message(self, text: str, x: int | None = None, y: int | None = None) -> None:
        self.set_answer(text)
        if x is not None and y is not None:
            self.set_anchor(x, y)
        else:
            self._move_to_anchor()
        self.show()
        self.raise_()

    def _move_to_anchor(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()

        # Đặt chữ cái ngay sát cạnh đuôi phần bôi đen (ngay góc phải con trỏ chuột)
        x = self._anchor.x() + 8
        y = self._anchor.y() - self.height() + 2

        if x + self.width() > geo.right() - 5:
            x = geo.right() - self.width() - 5
        if x < geo.left() + 5:
            x = geo.left() + 5

        if y < geo.top() + 5:
            y = self._anchor.y() + 16
        if y + self.height() > geo.bottom() - 5:
            y = geo.bottom() - self.height() - 5

        self.move(x, y)

    def hide_overlay(self) -> None:
        self.hide()
        self.label.clear()

    def mousePressEvent(self, a0: QMouseEvent | None) -> None:
        self.hide_overlay()
