from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QPushButton
from vitai.ui.theme import get_stylesheet

class ProviderHelpDialog(QDialog):
    def __init__(self, provider_code: str, theme: str = "dark", parent: QWidget | None = None):
        super().__init__(parent)
        guide = PROVIDER_GUIDES.get(provider_code, PROVIDER_GUIDES["gemini"])
        self.setWindowTitle(guide["title"])
        self.setFixedSize(460, 320)
        self.setStyleSheet(get_stylesheet(theme))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        content_label = QLabel(guide["content"])
        content_label.setWordWrap(True)
        content_label.setOpenExternalLinks(True)
        content_label.setStyleSheet("font-size: 13px; line-height: 1.5;")
        layout.addWidget(content_label, 1)

        close_btn = QPushButton("Đóng Hướng Dẫn")
        close_btn.setObjectName("saveButton")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


