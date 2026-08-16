from __future__ import annotations

from PyQt6.QtCore import QPoint, Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QWidget,
)

from vitai.config import AppConfig


class AnswerOverlay(QWidget):
    def __init__(self, text: str = "", timeout_ms: int = 0, config: AppConfig | None = None):
        super().__init__()
        self._config = config
        self._anchor = QPoint(0, 0)

        # Cửa sổ hoàn toàn trong suốt, không viền, luôn nổi trên cùng, không chiếm focus
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setStyleSheet("background: transparent; border: none;")

        self._build_ui()
        self.set_answer(text)

        if timeout_ms > 0:
            QTimer.singleShot(timeout_ms, self.close)

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
        font_size = self._config.font_size if self._config else 16
        text_color = self._config.text_color if self._config else "#E0E0E0"

        # Dùng font thanh thoát (Normal weight, không bôi đậm)
        font = QFont(font_family, font_size, QFont.Weight.Normal)
        self.label.setFont(font)

        # Màu sắc tinh khiết, nền trong suốt 100%, không bóng đổ gây cháy màu
        self.label.setStyleSheet(
            f"""
            QLabel {{
                color: {text_color};
                font-size: {font_size}px;
                font-family: Arial, sans-serif;
                font-weight: normal;
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

        # Tự động ẩn sau 5 giây để không làm phiền màn hình
        if hasattr(self, "_hide_timer") and self._hide_timer:
            self._hide_timer.stop()
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.close)
        self._hide_timer.start(5000)

    def _move_to_anchor(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()

        # Đặt chữ cái ngay góc trên bên phải của con trỏ chuột
        x = self._anchor.x() + 10
        y = self._anchor.y() - self.height() - 4

        if x + self.width() > geo.right() - 5:
            x = geo.right() - self.width() - 5
        if x < geo.left() + 5:
            x = geo.left() + 5

        if y < geo.top() + 5:
            y = self._anchor.y() + 16
        if y + self.height() > geo.bottom() - 5:
            y = geo.bottom() - self.height() - 5

        self.move(x, y)

    def mousePressEvent(self, event) -> None:
        self.close()
