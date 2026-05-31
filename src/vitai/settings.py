"""Settings window for ViTai — EVKey-style dialog."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from vitai.capture import capture_provider_available
from vitai.config import AppConfig
from vitai.i18n import tr
from vitai.ocr import ocr_provider_available
from vitai.resources import resource_path
from vitai.transtyle import profile_choices

VERSION = "1.0"

# Language options: (display_name, language_code)
SOURCE_LANGUAGES = [
    ("Tự phát hiện", "auto"),
    ("English", "en"),
    ("Tiếng Việt", "vi"),
    ("日本語 (Japanese)", "ja"),
    ("한국어 (Korean)", "ko"),
    ("中文 (Chinese)", "zh-CN"),
    ("Français", "fr"),
    ("Deutsch", "de"),
]

TARGET_LANGUAGES = [
    ("Tiếng Việt", "vi"),
    ("English", "en"),
    ("日本語 (Japanese)", "ja"),
    ("한국어 (Korean)", "ko"),
    ("中文 (Chinese)", "zh-CN"),
    ("Français", "fr"),
    ("Deutsch", "de"),
]

UI_LANGUAGES = [
    ("Tiếng Việt", "vi"),
    ("English", "en"),
]

TRANSLATOR_PROVIDERS = [
    ("translator_google", "google"),
    ("translator_deepl", "deepl"),
]

CAPTURE_PROVIDERS = [("MSS", "mss"), ("DXCam", "dxcam")]
OCR_PROVIDERS = [("EasyOCR", "easyocr"), ("PaddleOCR", "paddleocr")]
HOTKEY_BACKENDS = [("Auto", "auto"), ("pynput", "pynput"), ("Win32", "win32")]

LLM_PROVIDERS = [
    ("Gemini", "gemini"),
    ("OpenAI", "openai"),
    ("Anthropic", "anthropic"),
    ("DeepSeek", "deepseek"),
]

FONT_CHOICES = [
    ("Arial", "Arial"),
    ("Century Gothic", "Century Gothic"),
    ("Helvetica", "Helvetica"),
    ("sans-serif", "sans-serif"),
    ("Segoe UI", "Segoe UI"),
]

SIZE_CHOICES = [
    ("10 px", 10),
    ("12 px", 12),
    ("14 px", 14),
    ("16 px", 16),
    ("18 px", 18),
    ("20 px", 20),
    ("24 px", 24),
    ("32 px", 32),
]

COLOR_CHOICES = [
    ("Dark (#212529)", "#212529"),
    ("Light (#F4F4F4)", "#F4F4F4"),
    ("White (#FFFFFF)", "#FFFFFF"),
    ("Black (#000000)", "#000000"),
    ("Blue (#0d6efd)", "#0d6efd"),
    ("Red (#dc3545)", "#dc3545"),
    ("Green (#198754)", "#198754"),
]

# Overlay color options: (display_name, key, fill_rgba, border_rgba)
OVERLAY_COLORS = [
    ("🔵 Blue", "blue", (40, 120, 220, 45), (80, 180, 255, 180)),
    ("🟢 Green", "green", (40, 180, 80, 45), (80, 255, 140, 180)),
    ("🔴 Red", "red", (220, 60, 60, 45), (255, 120, 120, 180)),
    ("🟣 Purple", "purple", (140, 60, 220, 45), (180, 120, 255, 180)),
    ("🟠 Orange", "orange", (220, 140, 40, 45), (255, 180, 80, 180)),
    ("⚪ White", "white", (200, 200, 200, 45), (230, 230, 230, 180)),
]

# Hotkey modifiers
HOTKEY_MODIFIERS = [
    ("Alt", "alt"),
    ("Ctrl", "ctrl"),
    ("Shift", "shift"),
    ("Ctrl+Shift", "ctrl+shift"),
    ("Ctrl+Alt", "ctrl+alt"),
]

# Hotkey keys
HOTKEY_KEYS = [
    ("T", "t"),
    ("R", "r"),
    ("Q", "q"),
    ("D", "d"),
    ("W", "w"),
    ("E", "e"),
    ("S", "s"),
    ("F", "f"),
    ("G", "g"),
]

AUTO_INTERVALS = [
    ("100ms", 100),
    ("250ms", 250),
    ("500ms", 500),
    ("1000ms", 1000),
    ("2000ms", 2000),
    ("5000ms", 5000),
]


def _availability_label(display: str, available: bool, language: str) -> str:
    if available:
        return display
    suffix = "unavailable" if language == "en" else "chưa khả dụng"
    return f"{display} ({suffix})"


SETTINGS_STYLESHEET = """
    QDialog {
        background-color: #1e1e2e;
        color: #cdd6f4;
        font-family: 'Segoe UI', sans-serif;
        font-size: 13px;
    }
    QGroupBox {
        border: 1px solid #45475a;
        border-radius: 8px;
        margin-top: 14px;
        padding: 18px 12px 10px 12px;
        font-weight: bold;
        font-size: 13px;
        color: #89b4fa;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 14px;
        padding: 0 6px;
    }
    QLabel {
        color: #cdd6f4;
        font-size: 13px;
    }
    QLabel#statusLabel {
        color: #6c7086;
        font-size: 11px;
        padding: 4px 0;
    }
    QComboBox {
        background-color: #313244;
        border: 1px solid #45475a;
        border-radius: 5px;
        padding: 5px 10px;
        color: #cdd6f4;
        min-width: 160px;
        min-height: 24px;
    }
    QComboBox:hover {
        border-color: #89b4fa;
    }
    QComboBox:focus {
        border-color: #89b4fa;
    }
    QComboBox::drop-down {
        border: none;
        width: 28px;
    }
    QComboBox::down-arrow {
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid #6c7086;
        margin-right: 8px;
    }
    QComboBox QAbstractItemView {
        background-color: #313244;
        border: 1px solid #45475a;
        color: #cdd6f4;
        selection-background-color: #45475a;
        selection-color: #cdd6f4;
        outline: none;
    }
    QCheckBox {
        spacing: 8px;
        color: #cdd6f4;
        font-size: 13px;
    }
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 2px solid #45475a;
        background: #313244;
    }
    QCheckBox::indicator:hover {
        border-color: #89b4fa;
    }
    QCheckBox::indicator:checked {
        background: #89b4fa;
        border-color: #89b4fa;
    }
    QPushButton {
        background-color: #313244;
        border: 1px solid #45475a;
        border-radius: 6px;
        padding: 8px 20px;
        color: #cdd6f4;
        font-weight: bold;
        font-size: 12px;
        min-height: 20px;
    }
    QPushButton:hover {
        background-color: #45475a;
        border-color: #89b4fa;
    }
    QPushButton:pressed {
        background-color: #585b70;
    }
    QPushButton#saveButton {
        background-color: #89b4fa;
        color: #1e1e2e;
        border: none;
    }
    QPushButton#saveButton:hover {
        background-color: #b4d0fb;
    }
    QPushButton#saveButton:pressed {
        background-color: #74a8f7;
    }
    QPushButton#exitButton {
        background-color: #f38ba8;
        color: #1e1e2e;
        border: none;
    }
    QPushButton#exitButton:hover {
        background-color: #eba0ac;
    }
    QPushButton#exitButton:pressed {
        background-color: #e67e99;
    }
    QPushButton#resetButton {
        color: #a6adc8;
        border-color: #45475a;
    }
    QTabWidget::pane {
        border: 1px solid #45475a;
        border-radius: 8px;
        top: -1px;
    }
    QTabBar::tab {
        background-color: #313244;
        border: 1px solid #45475a;
        border-bottom: none;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        color: #a6adc8;
        padding: 8px 16px;
        margin-right: 2px;
        font-weight: bold;
    }
    QTabBar::tab:selected {
        background-color: #45475a;
        color: #cdd6f4;
        border-color: #89b4fa;
    }
    QTabBar::tab:hover {
        background-color: #45475a;
        color: #cdd6f4;
    }
"""


def _color_preview_icon(r: int, g: int, b: int, size: int = 16) -> QIcon:
    """Create a small colored circle icon for combobox items."""
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(r, g, b))
    painter.setPen(QColor(r, g, b, 200))
    path = QPainterPath()
    path.addRoundedRect(1, 1, size - 2, size - 2, 3, 3)
    painter.fillPath(path, QColor(r, g, b))
    painter.end()
    return QIcon(pixmap)


class SettingsWindow(QDialog):
    """EVKey-style settings dialog for ViTai."""

    config_changed = pyqtSignal(AppConfig)
    exit_requested = pyqtSignal()

    def __init__(self, config: AppConfig, parent: QWidget | None = None):
        super().__init__(parent)
        self._config = config
        self.setWindowTitle(tr("settings_title", config.ui_language))
        self.setWindowIcon(QIcon(str(resource_path("assets/icon.ico"))))
        self.setFixedSize(560, 560)
        self.setWindowFlags(
            Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowMinimizeButtonHint
        )
        self.setStyleSheet(SETTINGS_STYLESHEET)
        self._build_ui()
        self._load_from_config(config)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 12, 16, 12)
        content_layout.setSpacing(8)

        self.translate_group = QGroupBox(tr("translation_group", self._config.ui_language))
        tg_layout = QVBoxLayout(self.translate_group)
        tg_layout.setSpacing(10)

        src_row = QHBoxLayout()
        src_row.setSpacing(12)
        self.source_label = QLabel(tr("source_language", self._config.ui_language))
        self.source_label.setMinimumWidth(120)
        src_row.addWidget(self.source_label)
        self.source_combo = QComboBox()
        for display, code in SOURCE_LANGUAGES:
            self.source_combo.addItem(display, code)
        src_row.addWidget(self.source_combo, 1)
        tg_layout.addLayout(src_row)

        tgt_row = QHBoxLayout()
        tgt_row.setSpacing(12)
        self.target_label = QLabel(tr("target_language", self._config.ui_language))
        self.target_label.setMinimumWidth(120)
        tgt_row.addWidget(self.target_label)
        self.target_combo = QComboBox()
        for display, code in TARGET_LANGUAGES:
            self.target_combo.addItem(display, code)
        tgt_row.addWidget(self.target_combo, 1)
        tg_layout.addLayout(tgt_row)

        content_layout.addWidget(self.translate_group)

        self.tabs = QTabWidget()

        self.basic_tab = QWidget()
        bg_layout = QVBoxLayout(self.basic_tab)
        bg_layout.setContentsMargins(12, 12, 12, 12)
        bg_layout.setSpacing(10)

        color_row = QHBoxLayout()
        color_row.setSpacing(12)
        self.color_label = QLabel(tr("overlay_color", self._config.ui_language))
        self.color_label.setMinimumWidth(120)
        color_row.addWidget(self.color_label)
        self.color_combo = QComboBox()
        for display, key, fill_rgba, _border in OVERLAY_COLORS:
            icon = _color_preview_icon(fill_rgba[0], fill_rgba[1], fill_rgba[2])
            self.color_combo.addItem(icon, display, key)
        color_row.addWidget(self.color_combo, 1)
        bg_layout.addLayout(color_row)

        ui_language_row = QHBoxLayout()
        ui_language_row.setSpacing(12)
        self.ui_language_label = QLabel(tr("ui_language", self._config.ui_language))
        self.ui_language_label.setMinimumWidth(120)
        ui_language_row.addWidget(self.ui_language_label)
        self.ui_language_combo = QComboBox()
        for display, code in UI_LANGUAGES:
            self.ui_language_combo.addItem(display, code)
        ui_language_row.addWidget(self.ui_language_combo, 1)
        self.ui_language_combo.currentIndexChanged.connect(self._on_ui_language_changed)
        bg_layout.addLayout(ui_language_row)

        hotkey_row = QHBoxLayout()
        hotkey_row.setSpacing(12)
        self.hotkey_label = QLabel(tr("hotkey", self._config.ui_language))
        self.hotkey_label.setMinimumWidth(120)
        hotkey_row.addWidget(self.hotkey_label)

        self.modifier_combo = QComboBox()
        self.modifier_combo.setMinimumWidth(90)
        for display, code in HOTKEY_MODIFIERS:
            self.modifier_combo.addItem(display, code)
        hotkey_row.addWidget(self.modifier_combo)

        plus_label = QLabel("+")
        plus_label.setFixedWidth(16)
        plus_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hotkey_row.addWidget(plus_label)

        self.key_combo = QComboBox()
        self.key_combo.setMinimumWidth(60)
        for display, code in HOTKEY_KEYS:
            self.key_combo.addItem(display, code)
        self.modifier_combo.currentIndexChanged.connect(self._update_status_text)
        self.key_combo.currentIndexChanged.connect(self._update_status_text)
        hotkey_row.addWidget(self.key_combo)

        hotkey_row.addStretch()
        bg_layout.addLayout(hotkey_row)

        self.auto_check = QCheckBox(tr("auto_translate_default", self._config.ui_language))
        bg_layout.addWidget(self.auto_check)

        interval_row = QHBoxLayout()
        interval_row.setSpacing(12)
        self.interval_label = QLabel(tr("auto_interval", self._config.ui_language))
        self.interval_label.setMinimumWidth(120)
        interval_row.addWidget(self.interval_label)
        self.auto_interval_combo = QComboBox()
        for display, value in AUTO_INTERVALS:
            self.auto_interval_combo.addItem(display, value)
        interval_row.addWidget(self.auto_interval_combo, 1)
        bg_layout.addLayout(interval_row)
        bg_layout.addStretch()

        self.transtyle_tab = QWidget()
        ts_layout = QVBoxLayout(self.transtyle_tab)
        ts_layout.setContentsMargins(12, 12, 12, 12)
        ts_layout.setSpacing(8)

        transtyle_row = QHBoxLayout()
        transtyle_row.setSpacing(12)
        self.transtyle_label = QLabel(tr("translation_style", self._config.ui_language))
        self.transtyle_label.setMinimumWidth(120)
        transtyle_row.addWidget(self.transtyle_label)
        self.transtyle_combo = QComboBox()
        for display, profile_id in profile_choices():
            self.transtyle_combo.addItem(display, profile_id)
        transtyle_row.addWidget(self.transtyle_combo, 1)
        ts_layout.addLayout(transtyle_row)

        self.transtyle_rules_label = QLabel(tr("transtyle_rules_summary", self._config.ui_language))
        self.transtyle_mvp_label = QLabel(tr("transtyle_mvp_summary", self._config.ui_language))
        self.transtyle_editor_btn = QPushButton(tr("edit_transtyle", self._config.ui_language))
        self.transtyle_editor_btn.clicked.connect(self._open_transtyle_editor)
        ts_layout.addWidget(self.transtyle_rules_label)
        ts_layout.addWidget(self.transtyle_mvp_label)
        ts_layout.addWidget(self.transtyle_editor_btn)
        ts_layout.addStretch()

        self.ai_tab = QWidget()
        ai_layout = QVBoxLayout(self.ai_tab)
        ai_layout.setContentsMargins(12, 12, 12, 12)
        ai_layout.setSpacing(10)

        self.ghost_faa_check = QCheckBox("Ghost FAA (Tự động AI khi bôi đen text)")
        ai_layout.addWidget(self.ghost_faa_check)
        
        self.ai_cache_check = QCheckBox("Lưu bộ nhớ tạm (nhớ đáp án đã trả lời)")
        ai_layout.addWidget(self.ai_cache_check)

        ai_provider_row = QHBoxLayout()
        ai_provider_label = QLabel("LLM Provider:")
        ai_provider_label.setMinimumWidth(100)
        ai_provider_row.addWidget(ai_provider_label)
        self.ai_provider_combo = QComboBox()
        for display, code in LLM_PROVIDERS:
            self.ai_provider_combo.addItem(display, code)
        ai_provider_row.addWidget(self.ai_provider_combo, 1)
        ai_layout.addLayout(ai_provider_row)

        ai_font_row = QHBoxLayout()
        ai_font_label = QLabel("Font chữ AI:")
        ai_font_label.setMinimumWidth(100)
        ai_font_row.addWidget(ai_font_label)
        self.ai_font_combo = QComboBox()
        for display, code in FONT_CHOICES:
            self.ai_font_combo.addItem(display, code)
        ai_font_row.addWidget(self.ai_font_combo, 1)
        ai_layout.addLayout(ai_font_row)

        ai_size_row = QHBoxLayout()
        ai_size_label = QLabel("Cỡ chữ AI:")
        ai_size_label.setMinimumWidth(100)
        ai_size_row.addWidget(ai_size_label)
        self.ai_size_combo = QComboBox()
        for display, code in SIZE_CHOICES:
            self.ai_size_combo.addItem(display, code)
        ai_size_row.addWidget(self.ai_size_combo, 1)
        ai_layout.addLayout(ai_size_row)

        ai_color_row = QHBoxLayout()
        ai_color_label = QLabel("Màu chữ AI:")
        ai_color_label.setMinimumWidth(100)
        ai_color_row.addWidget(ai_color_label)
        self.ai_color_combo = QComboBox()
        self.ai_color_combo.setEditable(True)
        for display, code in COLOR_CHOICES:
            self.ai_color_combo.addItem(display, code)
        ai_color_row.addWidget(self.ai_color_combo, 1)
        ai_layout.addLayout(ai_color_row)
        
        ai_layout.addStretch()

        self.advanced_tab = QWidget()
        adv_layout = QVBoxLayout(self.advanced_tab)
        adv_layout.setContentsMargins(12, 12, 12, 12)
        adv_layout.setSpacing(10)

        provider_row = QHBoxLayout()
        provider_row.setSpacing(12)
        self.provider_label = QLabel(tr("translator_provider", self._config.ui_language))
        self.provider_label.setMinimumWidth(120)
        provider_row.addWidget(self.provider_label)
        self.provider_combo = QComboBox()
        for label_key, code in TRANSLATOR_PROVIDERS:
            self.provider_combo.addItem(tr(label_key, self._config.ui_language), code)
        provider_row.addWidget(self.provider_combo, 1)
        adv_layout.addLayout(provider_row)

        self.failover_check = QCheckBox(tr("translator_failover", self._config.ui_language))
        adv_layout.addWidget(self.failover_check)

        capture_row = QHBoxLayout()
        capture_row.setSpacing(12)
        self.capture_label = QLabel(tr("capture_engine", self._config.ui_language))
        self.capture_label.setMinimumWidth(120)
        capture_row.addWidget(self.capture_label)
        self.capture_combo = QComboBox()
        for display, code in CAPTURE_PROVIDERS:
            label = _availability_label(display, capture_provider_available(code), self._config.ui_language)
            self.capture_combo.addItem(label, code)
        capture_row.addWidget(self.capture_combo, 1)
        adv_layout.addLayout(capture_row)

        ocr_row = QHBoxLayout()
        ocr_row.setSpacing(12)
        self.ocr_label = QLabel(tr("ocr_engine", self._config.ui_language))
        self.ocr_label.setMinimumWidth(120)
        ocr_row.addWidget(self.ocr_label)
        self.ocr_combo = QComboBox()
        for display, code in OCR_PROVIDERS:
            label = _availability_label(display, ocr_provider_available(code), self._config.ui_language)
            self.ocr_combo.addItem(label, code)
        ocr_row.addWidget(self.ocr_combo, 1)
        adv_layout.addLayout(ocr_row)

        hotkey_backend_row = QHBoxLayout()
        hotkey_backend_row.setSpacing(12)
        self.hotkey_backend_label = QLabel(tr("hotkey_backend", self._config.ui_language))
        self.hotkey_backend_label.setMinimumWidth(120)
        hotkey_backend_row.addWidget(self.hotkey_backend_label)
        self.hotkey_backend_combo = QComboBox()
        for display, code in HOTKEY_BACKENDS:
            self.hotkey_backend_combo.addItem(display, code)
        hotkey_backend_row.addWidget(self.hotkey_backend_combo, 1)
        adv_layout.addLayout(hotkey_backend_row)
        adv_layout.addStretch()

        self.system_tab = QWidget()
        sg_layout = QVBoxLayout(self.system_tab)
        sg_layout.setContentsMargins(12, 12, 12, 12)
        sg_layout.setSpacing(8)

        self.admin_check = QCheckBox(tr("run_as_admin", self._config.ui_language))
        sg_layout.addWidget(self.admin_check)

        self.startup_check = QCheckBox(tr("start_with_windows", self._config.ui_language))
        sg_layout.addWidget(self.startup_check)
        sg_layout.addStretch()

        self.tabs.addTab(self.basic_tab, tr("basic_group", self._config.ui_language))
        self.tabs.addTab(self.transtyle_tab, tr("transtyle_tab", self._config.ui_language))
        self.tabs.addTab(self.ai_tab, "AI Assistant")
        self.tabs.addTab(self.advanced_tab, tr("advanced_group", self._config.ui_language))
        self.tabs.addTab(self.system_tab, tr("system_group", self._config.ui_language))
        content_layout.addWidget(self.tabs, 1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.save_btn = QPushButton(tr("save", self._config.ui_language))
        self.save_btn.setObjectName("saveButton")
        self.save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(self.save_btn)

        self.reset_btn = QPushButton(tr("reset", self._config.ui_language))
        self.reset_btn.setObjectName("resetButton")
        self.reset_btn.clicked.connect(self._on_reset)
        btn_row.addWidget(self.reset_btn)

        btn_row.addStretch()

        self.exit_btn = QPushButton(tr("exit", self._config.ui_language))
        self.exit_btn.setObjectName("exitButton")
        self.exit_btn.clicked.connect(self._on_exit)
        btn_row.addWidget(self.exit_btn)

        content_layout.addLayout(btn_row)

        self.status_label = QLabel()
        self.status_label.setObjectName("statusLabel")
        self._update_status_text()
        content_layout.addWidget(self.status_label)

        layout.addWidget(content, 1)

    def _load_from_config(self, config: AppConfig) -> None:
        """Populate UI controls from an AppConfig."""
        self._set_combo_by_data(self.source_combo, config.source_language)
        self._set_combo_by_data(self.target_combo, config.target_language)
        self._set_combo_by_data(self.provider_combo, config.translator_provider)
        self.failover_check.setChecked(config.translator_failover_enabled)
        self._set_combo_by_data(self.transtyle_combo, config.default_transtyle_id)
        self._set_combo_by_data(self.color_combo, config.overlay_color)
        self._set_combo_by_data(self.ui_language_combo, config.ui_language)
        self._set_combo_by_data(self.modifier_combo, config.hotkey_modifier)
        self._set_combo_by_data(self.key_combo, config.hotkey_key)
        self._set_combo_by_data(self.hotkey_backend_combo, config.hotkey_backend)
        self._set_combo_by_data(self.capture_combo, config.capture_provider)
        self._set_combo_by_data(self.ocr_combo, config.ocr_provider)
        self.auto_check.setChecked(config.auto_translate_enabled)
        self._set_combo_by_data(self.auto_interval_combo, config.auto_translate_interval_ms)
        self.admin_check.setChecked(config.run_as_admin)
        self.startup_check.setChecked(config.start_with_windows)
        self.ghost_faa_check.setChecked(config.ghost_faa_enabled)
        self.ai_cache_check.setChecked(config.cache_enabled)
        self._set_combo_by_data(self.ai_provider_combo, config.provider)
        self._set_combo_by_data(self.ai_font_combo, config.font_family)
        self._set_combo_by_data(self.ai_size_combo, config.font_size)
        self.ai_color_combo.setCurrentText(config.text_color)
        self._update_texts(config.ui_language)
        self._update_status_text()

    def _build_config_from_ui(self) -> AppConfig:
        """Build an AppConfig from current UI state (preserving geometry from original)."""
        return AppConfig(
            x=self._config.x,
            y=self._config.y,
            width=self._config.width,
            height=self._config.height,
            target_language=str(self.target_combo.currentData()),
            source_language=str(self.source_combo.currentData()),
            translator_provider=str(self.provider_combo.currentData()),
            deepl_api_key=self._config.deepl_api_key,
            translator_failover_enabled=self.failover_check.isChecked(),
            auto_translate_enabled=self.auto_check.isChecked(),
            auto_translate_interval_ms=int(self.auto_interval_combo.currentData()),
            overlay_color=str(self.color_combo.currentData()),
            ui_language=str(self.ui_language_combo.currentData()),
            default_transtyle_id=str(self.transtyle_combo.currentData()),
            transtyle_profiles=self._config.transtyle_profiles,
            hotkey_modifier=str(self.modifier_combo.currentData()),
            hotkey_key=str(self.key_combo.currentData()),
            hotkey_backend=str(self.hotkey_backend_combo.currentData()),
            capture_provider=str(self.capture_combo.currentData()),
            ocr_provider=str(self.ocr_combo.currentData()),
            update_check_enabled=self._config.update_check_enabled,
            update_check_owner=self._config.update_check_owner,
            update_check_repo=self._config.update_check_repo,
            offline_translation_enabled=self._config.offline_translation_enabled,
            run_as_admin=self.admin_check.isChecked(),
            start_with_windows=self.startup_check.isChecked(),
            ghost_faa_enabled=self.ghost_faa_check.isChecked(),
            cache_enabled=self.ai_cache_check.isChecked(),
            provider=str(self.ai_provider_combo.currentData()),
            font_family=str(self.ai_font_combo.currentData()),
            font_size=int(self.ai_size_combo.currentData()),
            text_color=self._get_ai_color(),
            api_key=self._config.api_key,
            base_url=self._config.base_url,
            model=self._config.model,
        )

    def _get_ai_color(self) -> str:
        color_text = self.ai_color_combo.currentText().strip()
        for disp, code in COLOR_CHOICES:
            if color_text == disp or color_text == code:
                return code
        return color_text

    def update_config(self, config: AppConfig) -> None:
        """Update the internal config reference and refresh UI."""
        self._config = config
        self._load_from_config(config)

    def _on_save(self) -> None:
        new_config = self._build_config_from_ui()

        # Warn about admin changes
        if new_config.run_as_admin and not self._config.run_as_admin:
            reply = QMessageBox.warning(
                self,
                tr("admin_warning_title", self._config.ui_language),
                tr("admin_warning_message", self._config.ui_language),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                self.admin_check.setChecked(False)
                return

        self._config = new_config
        self.config_changed.emit(new_config)
        self._update_status_text()

    def _on_reset(self) -> None:
        defaults = AppConfig(
            x=self._config.x,
            y=self._config.y,
            width=self._config.width,
            height=self._config.height,
        )
        self._load_from_config(defaults)

    def _on_exit(self) -> None:
        self.exit_requested.emit()

    def _open_transtyle_editor(self) -> None:
        from vitai.transtyle_editor import TranstyleEditorDialog

        dialog = TranstyleEditorDialog(self._config.transtyle_profiles, str(self.transtyle_combo.currentData()), self)
        if dialog.exec() != QDialog.DialogCode.Accepted or dialog.selected_profile is None:
            return
        profiles = dict(self._config.transtyle_profiles)
        profiles[dialog.selected_profile.id] = dialog.selected_profile
        self._config = AppConfig(
            x=self._config.x,
            y=self._config.y,
            width=self._config.width,
            height=self._config.height,
            target_language=self._config.target_language,
            source_language=self._config.source_language,
            translator_provider=self._config.translator_provider,
            deepl_api_key=self._config.deepl_api_key,
            translator_failover_enabled=self._config.translator_failover_enabled,
            default_transtyle_id=dialog.selected_profile.id,
            transtyle_profiles=profiles,
            auto_translate_enabled=self._config.auto_translate_enabled,
            auto_translate_interval_ms=self._config.auto_translate_interval_ms,
            overlay_color=self._config.overlay_color,
            ui_language=self._config.ui_language,
            hotkey_modifier=self._config.hotkey_modifier,
            hotkey_key=self._config.hotkey_key,
            hotkey_backend=self._config.hotkey_backend,
            capture_provider=self._config.capture_provider,
            ocr_provider=self._config.ocr_provider,
            update_check_enabled=self._config.update_check_enabled,
            update_check_owner=self._config.update_check_owner,
            update_check_repo=self._config.update_check_repo,
            offline_translation_enabled=self._config.offline_translation_enabled,
            run_as_admin=self._config.run_as_admin,
            start_with_windows=self._config.start_with_windows,
        )
        self._set_combo_by_data(self.transtyle_combo, dialog.selected_profile.id)

    def _on_ui_language_changed(self) -> None:
        language = str(self.ui_language_combo.currentData())
        self._update_texts(language)
        self._update_status_text()

    def _update_texts(self, language: str) -> None:
        self.setWindowTitle(tr("settings_title", language))
        self.translate_group.setTitle(tr("translation_group", language))
        self.source_label.setText(tr("source_language", language))
        self.target_label.setText(tr("target_language", language))
        self.provider_label.setText(tr("translator_provider", language))
        for index, (label_key, _code) in enumerate(TRANSLATOR_PROVIDERS):
            self.provider_combo.setItemText(index, tr(label_key, language))
        self.failover_check.setText(tr("translator_failover", language))
        self.tabs.setTabText(0, tr("basic_group", language))
        self.tabs.setTabText(1, tr("transtyle_tab", language))
        self.tabs.setTabText(2, tr("advanced_group", language))
        self.tabs.setTabText(3, tr("system_group", language))
        self.transtyle_label.setText(tr("translation_style", language))
        self.transtyle_rules_label.setText(tr("transtyle_rules_summary", language))
        self.transtyle_mvp_label.setText(tr("transtyle_mvp_summary", language))
        self.transtyle_editor_btn.setText(tr("edit_transtyle", language))
        self.capture_label.setText(tr("capture_engine", language))
        self.ocr_label.setText(tr("ocr_engine", language))
        for index, (display, code) in enumerate(CAPTURE_PROVIDERS):
            self.capture_combo.setItemText(index, _availability_label(display, capture_provider_available(code), language))
        for index, (display, code) in enumerate(OCR_PROVIDERS):
            self.ocr_combo.setItemText(index, _availability_label(display, ocr_provider_available(code), language))
        self.hotkey_backend_label.setText(tr("hotkey_backend", language))
        self.color_label.setText(tr("overlay_color", language))
        self.ui_language_label.setText(tr("ui_language", language))
        self.hotkey_label.setText(tr("hotkey", language))
        self.auto_check.setText(tr("auto_translate_default", language))
        self.interval_label.setText(tr("auto_interval", language))
        self.admin_check.setText(tr("run_as_admin", language))
        self.startup_check.setText(tr("start_with_windows", language))
        self.save_btn.setText(tr("save", language))
        self.reset_btn.setText(tr("reset", language))
        self.exit_btn.setText(tr("exit", language))

    def _update_status_text(self) -> None:
        modifier = self.modifier_combo.currentText() if hasattr(self, "modifier_combo") else "Alt"
        key = self.key_combo.currentText() if hasattr(self, "key_combo") else "T"
        language = str(self.ui_language_combo.currentData()) if hasattr(self, "ui_language_combo") else self._config.ui_language
        self.status_label.setText(
            f"ViTai v{VERSION}  ·  {modifier}+{key} {tr('hotkey_display', language)}"
        )

    def closeEvent(self, event) -> None:
        """Hide to tray instead of closing."""
        self.hide()
        event.ignore()

    @staticmethod
    def _set_combo_by_data(combo: QComboBox, value: str) -> None:
        for i in range(combo.count()):
            if combo.itemData(i) == value:
                combo.setCurrentIndex(i)
                return
        combo.setCurrentIndex(0)
