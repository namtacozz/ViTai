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

SETTINGS_STYLESHEET = """
    QDialog {
        background-color: #f8f9fa;
        color: #212529;
        font-family: 'Segoe UI', sans-serif;
        font-size: 13px;
    }
    QGroupBox {
        border: 1px solid #dee2e6;
        border-radius: 8px;
        margin-top: 14px;
        padding: 18px 12px 10px 12px;
        font-weight: bold;
        font-size: 13px;
        color: #495057;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 14px;
        padding: 0 6px;
    }
    QLabel {
        color: #212529;
        font-size: 13px;
    }
    QComboBox {
        background-color: #ffffff;
        border: 1px solid #ced4da;
        border-radius: 5px;
        padding: 5px 10px;
        color: #495057;
        min-width: 160px;
        min-height: 24px;
    }
    QComboBox:hover {
        border-color: #86b7fe;
    }
    QCheckBox {
        spacing: 8px;
        color: #212529;
        font-size: 13px;
    }
    QPushButton {
        background-color: #ffffff;
        border: 1px solid #ced4da;
        border-radius: 6px;
        padding: 8px 20px;
        color: #495057;
        font-weight: bold;
        font-size: 12px;
        min-height: 20px;
    }
    QPushButton:hover {
        background-color: #e9ecef;
    }
    QPushButton#saveButton {
        background-color: #0d6efd;
        color: #ffffff;
        border: none;
    }
    QPushButton#saveButton:hover {
        background-color: #0b5ed7;
    }
    QPushButton#exitButton {
        background-color: #dc3545;
        color: #ffffff;
        border: none;
    }
    QPushButton#exitButton:hover {
        background-color: #bb2d3b;
    }
"""

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

class SettingsWindow(QDialog):
    config_changed = pyqtSignal(AppConfig)
    exit_requested = pyqtSignal()

    def __init__(self, config: AppConfig, parent: QWidget | None = None):
        super().__init__(parent)
        self._config = config
        self.setWindowTitle("ViTai Settings")
        try:
            self.setWindowIcon(QIcon(str(resource_path("assets/logo.ico"))))
        except Exception:
            pass
        self.setFixedSize(400, 360)
        self.setWindowFlags(
            Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowMinimizeButtonHint
        )
        self.setStyleSheet(SETTINGS_STYLESHEET)
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
        color_label = QLabel("Màu chữ:")
        color_label.setMinimumWidth(100)
        color_row.addWidget(color_label)
        self.color_combo = QComboBox()
        for display, code in COLOR_CHOICES:
            self.color_combo.addItem(display, code)
        color_row.addWidget(self.color_combo, 1)
        ag_layout.addLayout(color_row)
        
        layout.addWidget(appearance_group)

        # System Group
        system_group = QGroupBox("Hệ thống")
        sg_layout = QVBoxLayout(system_group)
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
        self._set_combo_by_data(self.color_combo, config.text_color)
        self.startup_check.setChecked(config.start_with_windows)

    def _build_config_from_ui(self) -> AppConfig:
        from dataclasses import replace
        return replace(
            self._config,
            font_family=str(self.font_combo.currentData()),
            font_size=int(self.size_combo.currentData()),
            text_color=str(self.color_combo.currentData()),
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
