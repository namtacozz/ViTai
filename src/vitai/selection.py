from collections.abc import Callable

from PyQt6.QtCore import QPoint, QRect, Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QApplication, QWidget

MIN_SELECTION_WIDTH = 80
MIN_SELECTION_HEIGHT = 60


class SelectionWindow(QWidget):
    def __init__(self, on_selected: Callable[[QRect], None], on_cancelled: Callable[[], None]):
        super().__init__()
        self._on_selected = on_selected
        self._on_cancelled = on_cancelled
        self._start: QPoint | None = None
        self._current: QPoint | None = None
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setMouseTracking(True)
        self.setGeometry(QApplication.primaryScreen().geometry())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._start = event.globalPosition().toPoint()
            self._current = self._start
            self.update()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._start is not None:
            self._current = event.globalPosition().toPoint()
            self.update()
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton or self._start is None:
            return
        self._current = event.globalPosition().toPoint()
        rect = self._selection_rect()
        # Hide first so the overlay isn't drawn over this window,
        # then fire the callback, then schedule destruction.
        self.hide()
        if rect.width() >= MIN_SELECTION_WIDTH and rect.height() >= MIN_SELECTION_HEIGHT:
            self._on_selected(rect)
        else:
            self._on_cancelled()
        self.deleteLater()
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            self._on_cancelled()
            self.deleteLater()
            event.accept()

    def _selection_rect(self) -> QRect:
        if self._start is None or self._current is None:
            return QRect()
        return QRect(self._start, self._current).normalized()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 70))
        rect = self._selection_rect()
        if rect.isNull():
            return
        painter.fillRect(rect, QColor(40, 120, 220, 35))
        painter.setPen(QPen(QColor(80, 180, 255), 2))
        painter.drawRect(rect.adjusted(0, 0, -1, -1))
