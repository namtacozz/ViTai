from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from vitai.config import AppConfig
from vitai.resources import resource_path

SETTINGS_STYLESHEET_LIGHT = """
    QDialog { background-color: #f8f9fa; color: #212529; font-family: 'Segoe UI', sans-serif; font-size: 13px; }
    QGroupBox { border: 1px solid #dee2e6; border-radius: 8px; margin-top: 14px; padding: 18px 12px 10px 12px; font-weight: bold; font-size: 13px; color: #495057; }
    QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 14px; padding: 0 6px; }
    QLabel { color: #212529; font-size: 13px; }
    QComboBox { background-color: #ffffff; border: 1px solid #ced4da; border-radius: 5px; padding: 5px 10px; color: #495057; min-width: 140px; min-height: 24px; }
    QComboBox:hover { border-color: #86b7fe; }
    QCheckBox { spacing: 8px; color: #212529; font-size: 13px; }
    QPushButton { background-color: #ffffff; border: 1px solid #ced4da; border-radius: 6px; padding: 8px 20px; color: #495057; font-weight: bold; font-size: 12px; min-height: 20px; }
    QPushButton:hover { background-color: #e9ecef; }
    QPushButton#saveButton { background-color: #0d6efd; color: #ffffff; border: none; }
    QPushButton#saveButton:hover { background-color: #0b5ed7; }
    QPushButton#exitButton { background-color: #dc3545; color: #ffffff; border: none; }
    QPushButton#exitButton:hover { background-color: #bb2d3b; }
"""

SETTINGS_STYLESHEET_DARK = """
    QDialog { background-color: #202020; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; font-size: 13px; }
    QGroupBox { border: 1px solid #444444; border-radius: 8px; margin-top: 14px; padding: 18px 12px 10px 12px; font-weight: bold; font-size: 13px; color: #cccccc; }
    QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 14px; padding: 0 6px; }
    QLabel { color: #e0e0e0; font-size: 13px; }
    QComboBox { background-color: #333333; border: 1px solid #555555; border-radius: 5px; padding: 5px 10px; color: #e0e0e0; min-width: 140px; min-height: 24px; }
    QComboBox:hover { border-color: #0d6efd; }
    QCheckBox { spacing: 8px; color: #e0e0e0; font-size: 13px; }
    QPushButton { background-color: #333333; border: 1px solid #555555; border-radius: 6px; padding: 8px 20px; color: #e0e0e0; font-weight: bold; font-size: 12px; min-height: 20px; }
    QPushButton:hover { background-color: #444444; }
    QPushButton#saveButton { background-color: #0d6efd; color: #ffffff; border: none; }
    QPushButton#saveButton:hover { background-color: #0b5ed7; }
    QPushButton#exitButton { background-color: #dc3545; color: #ffffff; border: none; }
    QPushButton#exitButton:hover { background-color: #bb2d3b; }
"""

def is_dark_mode() -> bool:
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return value == 0
    except Exception:
        return True

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
    ("36 px", 36),
    ("48 px", 48),
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

HOTKEY_MODIFIERS = [("Alt", "alt"), ("Ctrl", "ctrl"), ("Shift", "shift"), ("Ctrl+Shift", "ctrl+shift")]
HOTKEY_KEYS = [(chr(i), chr(i).lower()) for i in range(65, 91)] # A-Z

class SettingsWindow(QDialog):
    config_changed = pyqtSignal(AppConfig)
    exit_requested = pyqtSignal()

    def __init__(self, config: AppConfig, parent: QWidget | None = None):
        super().__init__(parent)
        self._config = config
        self.setWindowTitle("ViTai Settings")
        try:
            self.setWindowIcon(QIcon(str(resource_path("assets/icon.ico"))))
        except Exception:
            pass
        self.setFixedSize(450, 480)
        self.setWindowFlags(
            Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowMinimizeButtonHint
        )
        self.setStyleSheet(SETTINGS_STYLESHEET_DARK if is_dark_mode() else SETTINGS_STYLESHEET_LIGHT)
        self._build_ui()
        self._load_from_config(config)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        
        # Appearance Group
        appearance_group = QGroupBox("Giao diện")
        ag_layout = QVBoxLayout(appearance_group)
        ag_layout.setSpacing(12)
        
        # Font Row
        font_row = QHBoxLayout()
        font_label = QLabel("Font chữ:")
        font_label.setMinimumWidth(100)
        font_row.addWidget(font_label)
        self.font_combo = QComboBox()
        for display, code in FONT_CHOICES:
            self.font_combo.addItem(display, code)
        font_row.addWidget(self.font_combo, 1)
        ag_layout.addLayout(font_row)

        # Size Row
        size_row = QHBoxLayout()
        size_label = QLabel("Cỡ chữ:")
        size_label.setMinimumWidth(100)
        size_row.addWidget(size_label)
        self.size_combo = QComboBox()
        for display, code in SIZE_CHOICES:
            self.size_combo.addItem(display, code)
        size_row.addWidget(self.size_combo, 1)
        ag_layout.addLayout(size_row)

        # Color Row
        color_row = QHBoxLayout()
        color_label = QLabel("Màu chữ (Hex):")
        color_label.setMinimumWidth(100)
        color_row.addWidget(color_label)
        self.color_combo = QComboBox()
        self.color_combo.setEditable(True)
        for display, code in COLOR_CHOICES:
            self.color_combo.addItem(display, code)
        color_row.addWidget(self.color_combo, 1)
        ag_layout.addLayout(color_row)
        
        layout.addWidget(appearance_group)

        # Hotkey & System Group
        system_group = QGroupBox("Hệ thống & Tự động")
        sg_layout = QVBoxLayout(system_group)
        sg_layout.setSpacing(12)
        
        hotkey_row = QHBoxLayout()
        hotkey_label = QLabel("Phím tắt gọi App:")
        hotkey_label.setMinimumWidth(100)
        hotkey_row.addWidget(hotkey_label)
        self.modifier_combo = QComboBox()
        for display, code in HOTKEY_MODIFIERS:
            self.modifier_combo.addItem(display, code)
        hotkey_row.addWidget(self.modifier_combo)
        hotkey_row.addWidget(QLabel(" + "))
        self.key_combo = QComboBox()
        for display, code in HOTKEY_KEYS:
            self.key_combo.addItem(display, code)
        hotkey_row.addWidget(self.key_combo, 1)
        sg_layout.addLayout(hotkey_row)

        self.auto_check = QCheckBox("Tự động trả lời ngay khi bôi đen text")
        sg_layout.addWidget(self.auto_check)

        self.cache_check = QCheckBox("Lưu bộ nhớ tạm (nhớ đáp án đã trả lời)")
        sg_layout.addWidget(self.cache_check)

        self.startup_check = QCheckBox("Khởi động cùng Windows")
        sg_layout.addWidget(self.startup_check)
        
        layout.addWidget(system_group)
        
        layout.addStretch()

        # Buttons
        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("Lưu")
        self.save_btn.setObjectName("saveButton")
        self.save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(self.save_btn)
        
        btn_row.addStretch()
        
        self.exit_btn = QPushButton("Thoát App")
        self.exit_btn.setObjectName("exitButton")
        self.exit_btn.clicked.connect(self._on_exit)
        btn_row.addWidget(self.exit_btn)
        
        layout.addLayout(btn_row)

    def _load_from_config(self, config: AppConfig) -> None:
        self._set_combo_by_data(self.font_combo, config.font_family)
        self._set_combo_by_data(self.size_combo, config.font_size)
        self.color_combo.setCurrentText(config.text_color)
        self._set_combo_by_data(self.modifier_combo, config.hotkey_modifier)
        self._set_combo_by_data(self.key_combo, config.hotkey_key)
        self.auto_check.setChecked(config.auto_translate)
        self.cache_check.setChecked(config.cache_enabled)
        self.startup_check.setChecked(config.start_with_windows)

    def _build_config_from_ui(self) -> AppConfig:
        from dataclasses import replace
        
        # Lấy dữ liệu màu (ưu tiên custom text nếu có)
        color_text = self.color_combo.currentText().strip()
        # Tìm xem text này có trong các choices không (nếu người dùng chọn từ menu)
        matched_color = None
        for disp, code in COLOR_CHOICES:
            if color_text == disp or color_text == code:
                matched_color = code
                break
        final_color = matched_color if matched_color else color_text

        return replace(
            self._config,
            font_family=str(self.font_combo.currentData()),
            font_size=int(self.size_combo.currentData()),
            text_color=final_color,
            hotkey_modifier=str(self.modifier_combo.currentData()),
            hotkey_key=str(self.key_combo.currentData()),
            auto_translate=self.auto_check.isChecked(),
            cache_enabled=self.cache_check.isChecked(),
            start_with_windows=self.startup_check.isChecked()
        )

    def _on_save(self) -> None:
        new_config = self._build_config_from_ui()
        self._config = new_config
        self.config_changed.emit(new_config)
        self.hide()

    def _on_exit(self) -> None:
        self.exit_requested.emit()

    def closeEvent(self, event) -> None:
        self.hide()
        event.ignore()

    @staticmethod
    def _set_combo_by_data(combo: QComboBox, value) -> None:
        for i in range(combo.count()):
            if combo.itemData(i) == value:
                combo.setCurrentIndex(i)
                return
        combo.setCurrentIndex(0)
