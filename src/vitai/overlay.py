from collections.abc import Callable

from PyQt6.QtCore import QPoint, QRect, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QFont, QIcon, QPainter
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QMenu, QPushButton, QVBoxLayout, QWidget

from vitai.config import AppConfig
from vitai.history import TranslationHistory, TranslationHistoryEntry
from vitai.i18n import tr
from vitai.models import Rect, TranslatedBox
from vitai.resources import resource_path
from vitai.transtyle import profile_choices

TOP_BAR_HEIGHT = 0
RESIZE_MARGIN = 8

OVERLAY_COLORS: dict[str, tuple[QColor, QColor]] = {
    "blue": (QColor(40, 120, 220, 160), QColor(80, 180, 255, 200)),
    "green": (QColor(40, 180, 80, 160), QColor(80, 255, 140, 200)),
    "red": (QColor(220, 60, 60, 160), QColor(255, 120, 120, 200)),
    "purple": (QColor(140, 60, 220, 160), QColor(180, 120, 255, 200)),
    "orange": (QColor(220, 140, 40, 160), QColor(255, 180, 80, 200)),
    "white": (QColor(200, 200, 200, 160), QColor(230, 230, 230, 200)),
}

SOURCE_LANGUAGES = [
    ("Tự phát hiện", "auto"),
    ("English", "en"),
    ("Tiếng Việt", "vi"),
    ("日本語", "ja"),
    ("한국어", "ko"),
    ("中文", "zh-CN"),
    ("Français", "fr"),
    ("Deutsch", "de"),
]

TARGET_LANGUAGES = [
    ("Tiếng Việt", "vi"),
    ("English", "en"),
    ("日本語", "ja"),
    ("한국어", "ko"),
    ("中文", "zh-CN"),
    ("Français", "fr"),
    ("Deutsch", "de"),
]


class OverlayWindow(QWidget):
    correction_requested = pyqtSignal(object)

    def __init__(
        self,
        config: AppConfig,
        on_translate: Callable[[], None],
        on_hide: Callable[[], None],
        on_auto_changed: Callable[[bool], None],
        on_reset: Callable[[], None],
        on_speak: Callable[[str], None] | None = None,
    ):
        super().__init__()
        self._on_translate = on_translate
        self._on_hide = on_hide
        self._on_auto_changed = on_auto_changed
        self._on_reset = on_reset
        self._on_speak = on_speak or (lambda _text: None)
        self._drag_position: QPoint | None = None
        self._resize_edges: set[str] = set()
        self._resize_start_pos: QPoint | None = None
        self._resize_start_geometry: QRect | None = None
        self._translated_boxes: list[TranslatedBox] = []
        self._status = ""
        self._auto_enabled = config.auto_translate_enabled
        self._overlay_color = config.overlay_color
        self._ui_language = config.ui_language
        self._source_language = config.source_language
        self._target_language = config.target_language
        self._transtyle_id = config.default_transtyle_id
        self._history = TranslationHistory()
        self._latest_translation_text = ""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self._build_ui()
        self.setMinimumSize(QSize(32, 24))
        self.setGeometry(config.x, config.y, config.width, config.height)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addStretch(1)
        row = QHBoxLayout()
        row.addStretch(1)

        self.translate_button = QPushButton(self)
        self.translate_button.setIcon(QIcon(str(resource_path("assets/logo.ico"))))
        self.translate_button.setFixedSize(32, 32)
        self.translate_button.setIconSize(QSize(22, 22))
        self.translate_button.setStyleSheet(
            "QPushButton { background: rgba(20, 20, 20, 150); border: 1px solid rgba(255, 255, 255, 140); border-radius: 16px; }"
            "QPushButton:hover { background: rgba(40, 40, 40, 190); }"
        )
        self.translate_button.clicked.connect(self._start_translate)
        row.addWidget(self.translate_button)

        self.auto_button = QPushButton(tr("auto", self._ui_language), self)
        self.auto_button.setCheckable(True)
        self.auto_button.setChecked(self._auto_enabled)
        self.auto_button.setFixedSize(54, 32)
        self.auto_button.setStyleSheet(
            "QPushButton { background: rgba(20, 20, 20, 150); border: 1px solid rgba(255, 255, 255, 140); border-radius: 16px; color: white; font-size: 11px; }"
            "QPushButton:hover { background: rgba(40, 40, 40, 190); }"
            "QPushButton:checked { background: rgba(40, 180, 80, 190); }"
        )
        self.auto_button.toggled.connect(self._set_auto_enabled)
        row.addSpacing(6)
        row.addWidget(self.auto_button)

        self.history_button = QPushButton(tr("history", self._ui_language), self)
        self.history_button.setCheckable(True)
        self.history_button.setFixedSize(72, 32)
        self.history_button.setStyleSheet(
            "QPushButton { background: rgba(20, 20, 20, 150); border: 1px solid rgba(255, 255, 255, 140); border-radius: 16px; color: white; font-size: 11px; }"
            "QPushButton:hover { background: rgba(40, 40, 40, 190); }"
            "QPushButton:checked { background: rgba(60, 100, 180, 190); }"
        )
        self.history_button.toggled.connect(self._set_history_visible)
        row.addSpacing(6)
        row.addWidget(self.history_button)

        self.speak_button = QPushButton(tr("speak", self._ui_language), self)
        self.speak_button.setFixedSize(54, 32)
        self.speak_button.setEnabled(False)
        self.speak_button.setStyleSheet(
            "QPushButton { background: rgba(20, 20, 20, 150); border: 1px solid rgba(255, 255, 255, 140); border-radius: 16px; color: white; font-size: 11px; }"
            "QPushButton:hover { background: rgba(40, 40, 40, 190); }"
            "QPushButton:disabled { color: rgba(255, 255, 255, 90); }"
        )
        self.speak_button.clicked.connect(self._speak_latest)
        row.addSpacing(6)
        row.addWidget(self.speak_button)

        row.addStretch(1)
        root.addLayout(row)

        self.history_panel = QWidget(self)
        self.history_panel.setVisible(False)
        self.history_panel.setStyleSheet(
            "QWidget { background: rgba(20, 20, 20, 185); border: 1px solid rgba(255, 255, 255, 120); border-radius: 8px; }"
        )
        panel_layout = QVBoxLayout(self.history_panel)
        panel_layout.setContentsMargins(8, 6, 8, 6)
        self.history_label = QLabel(tr("no_translation_yet", self._ui_language), self.history_panel)
        self.history_label.setStyleSheet("QLabel { color: white; font-size: 12px; border: none; }")
        self.history_label.setWordWrap(True)
        panel_layout.addWidget(self.history_label)
        root.addWidget(self.history_panel)
        root.addStretch(1)

    def _start_translate(self) -> None:
        self.translate_button.hide()
        self._on_translate()

    def source_language(self) -> str:
        return self._source_language

    def target_language(self) -> str:
        return self._target_language

    def transtyle_id(self) -> str:
        return self._transtyle_id

    def set_transtyle_id(self, transtyle_id: str) -> None:
        if self._transtyle_id == transtyle_id:
            return
        self._transtyle_id = transtyle_id
        self._reset_translation_ui()

    def auto_enabled(self) -> bool:
        return self._auto_enabled

    def set_ui_language(self, language: str) -> None:
        self._ui_language = language
        self.auto_button.setText(tr("auto", language))
        self.history_button.setText(tr("history", language))
        self.speak_button.setText(tr("speak", language))
        self._update_history_panel()

    def set_auto_enabled(self, enabled: bool) -> None:
        if self._auto_enabled == enabled:
            return
        self._auto_enabled = enabled
        self.auto_button.setChecked(enabled)
        self._on_auto_changed(enabled)

    def _set_auto_enabled(self, enabled: bool) -> None:
        if self._auto_enabled == enabled:
            return
        self._auto_enabled = enabled
        self._on_auto_changed(enabled)

    def overlay_rect(self) -> Rect:
        geometry = self.geometry()
        return Rect(x=geometry.x(), y=geometry.y(), width=geometry.width(), height=geometry.height())

    def update_overlay_color(self, color_name: str) -> None:
        self._overlay_color = color_name
        self.update()

    def set_translated_boxes(self, boxes: list[TranslatedBox], history_entry: TranslationHistoryEntry | None = None) -> None:
        self._status = ""
        self._translated_boxes = boxes
        if history_entry is not None:
            self._history.add([history_entry.original], [history_entry.translated], now=history_entry.timestamp)
            self._latest_translation_text = history_entry.translated
        elif boxes:
            self._latest_translation_text = "\n".join(box.translated for box in boxes if box.translated.strip())
        else:
            self._latest_translation_text = ""
        self.speak_button.setEnabled(bool(self._latest_translation_text))
        self._update_history_panel()
        self.translate_button.hide()
        self.update()

    def _set_history_visible(self, visible: bool) -> None:
        self.history_panel.setVisible(visible)
        self._update_translate_button_visibility()

    def _speak_latest(self) -> None:
        if not self._latest_translation_text:
            self.set_status(tr("no_translation_yet", self._ui_language))
            return
        self._on_speak(self._latest_translation_text)

    def _update_history_panel(self) -> None:
        entries = self._history.entries
        if not entries:
            self.history_label.setText(tr("no_translation_yet", self._ui_language))
            return
        lines = []
        for entry in entries:
            lines.append(f"{entry.original}\n→ {entry.translated}")
        self.history_label.setText("\n\n".join(lines))

    def set_status(self, message: str) -> None:
        self._status = message
        self._translated_boxes = []
        self.translate_button.show()
        self.update()

    def clear_results(self) -> None:
        self._reset_translation_ui()

    def request_correction_at(self, x: int, y: int) -> None:
        box = self._translated_box_at(QPoint(x, y))
        if box is not None:
            self.correction_requested.emit(box)

    def contextMenuEvent(self, event) -> None:
        menu = QMenu(self)

        box = self._translated_box_at(event.pos())
        if box is not None:
            correction_action = QAction("Sửa bản dịch này", menu)
            correction_action.triggered.connect(lambda _checked=False, item=box: self.correction_requested.emit(item))
            menu.addAction(correction_action)
            menu.addSeparator()

        source_menu = menu.addMenu("Nguồn")
        self._add_language_actions(source_menu, SOURCE_LANGUAGES, self._source_language, self._set_source_language)

        target_menu = menu.addMenu("Đích")
        self._add_language_actions(target_menu, TARGET_LANGUAGES, self._target_language, self._set_target_language)

        transtyle_menu = menu.addMenu("Transtyle")
        self._add_transtyle_actions(transtyle_menu)

        menu.addSeparator()
        close_action = QAction("Tắt", menu)
        close_action.triggered.connect(self._on_hide)
        menu.addAction(close_action)
        menu.exec(event.globalPos())

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return

        edges = self._edges_at(event.position().toPoint())
        if edges:
            self._resize_edges = edges
            self._resize_start_pos = event.globalPosition().toPoint()
            self._resize_start_geometry = self.geometry()
            event.accept()
            return

        if not self.translate_button.geometry().contains(event.position().toPoint()):
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._resize_edges and self._resize_start_pos is not None and self._resize_start_geometry is not None:
            self._resize_to(event.globalPosition().toPoint())
            event.accept()
            return

        if self._drag_position is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()
            return

        self._update_cursor(self._edges_at(event.position().toPoint()))

    def mouseReleaseEvent(self, event):
        changed = self._resize_start_geometry is not None or self._drag_position is not None
        self._drag_position = None
        self._resize_edges = set()
        self._resize_start_pos = None
        self._resize_start_geometry = None
        self._update_cursor(self._edges_at(event.position().toPoint()))
        if changed:
            self._reset_translation_ui()
        event.accept()

    def leaveEvent(self, event):
        if not self._resize_edges:
            self.unsetCursor()

    def resizeEvent(self, event) -> None:
        self._update_translate_button_visibility()
        super().resizeEvent(event)

    def _add_language_actions(
        self,
        menu: QMenu,
        languages: list[tuple[str, str]],
        current: str,
        setter: Callable[[str], None],
    ) -> None:
        for label, code in languages:
            action = QAction(label, menu)
            action.setCheckable(True)
            action.setChecked(code == current)
            action.triggered.connect(lambda _checked=False, value=code: setter(value))
            menu.addAction(action)

    def _add_transtyle_actions(self, menu: QMenu) -> None:
        for label, profile_id in profile_choices():
            action = QAction(label, menu)
            action.setCheckable(True)
            action.setChecked(profile_id == self._transtyle_id)
            action.triggered.connect(lambda _checked=False, value=profile_id: self.set_transtyle_id(value))
            menu.addAction(action)

    def _set_source_language(self, language: str) -> None:
        if self._source_language == language:
            return
        self._source_language = language
        self._reset_translation_ui()

    def _set_target_language(self, language: str) -> None:
        if self._target_language == language:
            return
        self._target_language = language
        self._reset_translation_ui()

    def _reset_translation_ui(self) -> None:
        self._status = ""
        self._translated_boxes = []
        self._latest_translation_text = ""
        self.speak_button.setEnabled(False)
        self._update_translate_button_visibility()
        self.update()
        self._on_reset()

    def _update_translate_button_visibility(self) -> None:
        show_controls = self.width() >= 96 and self.height() >= 40
        self.auto_button.setVisible(show_controls)
        self.history_button.setVisible(show_controls)
        self.speak_button.setVisible(show_controls)
        if self._status or self._translated_boxes:
            self.translate_button.hide()
        elif show_controls:
            self.translate_button.show()
        else:
            self.translate_button.hide()

    def _edges_at(self, position: QPoint) -> set[str]:
        edges: set[str] = set()
        if position.x() <= RESIZE_MARGIN:
            edges.add("left")
        elif position.x() >= self.width() - RESIZE_MARGIN:
            edges.add("right")

        if position.y() <= RESIZE_MARGIN:
            edges.add("top")
        elif position.y() >= self.height() - RESIZE_MARGIN:
            edges.add("bottom")

        return edges

    def _update_cursor(self, edges: set[str]) -> None:
        if edges in ({"left", "top"}, {"right", "bottom"}):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif edges in ({"right", "top"}, {"left", "bottom"}):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif edges & {"left", "right"}:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif edges & {"top", "bottom"}:
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        else:
            self.unsetCursor()

    def _resize_to(self, global_position: QPoint) -> None:
        if self._resize_start_pos is None or self._resize_start_geometry is None:
            return

        delta = global_position - self._resize_start_pos
        geometry = QRect(self._resize_start_geometry)
        minimum = self.minimumSize()

        if "left" in self._resize_edges:
            new_left = min(geometry.right() - minimum.width() + 1, geometry.left() + delta.x())
            geometry.setLeft(new_left)
        if "right" in self._resize_edges:
            new_right = max(geometry.left() + minimum.width() - 1, geometry.right() + delta.x())
            geometry.setRight(new_right)
        if "top" in self._resize_edges:
            new_top = min(geometry.bottom() - minimum.height() + 1, geometry.top() + delta.y())
            geometry.setTop(new_top)
        if "bottom" in self._resize_edges:
            new_bottom = max(geometry.top() + minimum.height() - 1, geometry.bottom() + delta.y())
            geometry.setBottom(new_bottom)

        self.setGeometry(geometry)

    def _translated_box_at(self, position: QPoint) -> TranslatedBox | None:
        for item in self._translated_boxes:
            rect = QRect(item.bbox.x, item.bbox.y, item.bbox.width, max(item.bbox.height, item.font_size + 4))
            if rect.contains(position):
                return item
        return None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        fill_color, border_color = OVERLAY_COLORS.get(
            self._overlay_color, OVERLAY_COLORS["blue"]
        )
        painter.fillRect(self.rect(), fill_color)
        painter.setPen(border_color)
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

        if self._status:
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Segoe UI", 12))
            painter.drawText(
                QRect(12, 12, self.width() - 24, 60),
                Qt.AlignmentFlag.AlignLeft,
                self._status,
            )

        for item in self._translated_boxes:
            rect = QRect(item.bbox.x, item.bbox.y, item.bbox.width, max(item.bbox.height, item.font_size + 4))
            painter.setFont(QFont("Segoe UI", item.font_size))
            painter.setPen(QColor(0, 0, 0, 160))
            painter.drawText(
                rect.adjusted(1, 1, 1, 1),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextWordWrap,
                item.translated,
            )
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(
                rect,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextWordWrap,
                item.translated,
            )
