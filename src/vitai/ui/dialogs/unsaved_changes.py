from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from vitai.ui.theme import get_stylesheet

class UnsavedChangesDialog(QDialog):
    SAVE_AND_CLOSE = 1
    DISCARD_AND_CLOSE = 2
    CANCEL = 0

    def __init__(self, parent=None, theme: str = "dark"):
        super().__init__(parent)
        self.setWindowTitle("Chưa lưu cài đặt")
        self.setFixedSize(400, 180)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.theme = theme
        self.setStyleSheet(get_stylesheet(theme))
        self.user_choice = self.CANCEL
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(12)

        title_lbl = QLabel("Thay đổi chưa được lưu")
        title_lbl.setStyleSheet(
            "font-size: 15px; font-weight: 800; color: #E09F5E;"
        )
        layout.addWidget(title_lbl)

        desc_lbl = QLabel("Bạn có các thiết lập mới chưa được lưu. Bạn có muốn lưu lại trước khi đóng cửa sổ?")
        desc_lbl.setStyleSheet(
            "font-size: 12px; color: " + ("#94A3B8" if self.theme == "dark" else "#475569") + ";"
        )
        desc_lbl.setWordWrap(True)
        layout.addWidget(desc_lbl)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        cancel_btn = QPushButton("Hủy")
        cancel_btn.setObjectName("helpButton")
        cancel_btn.clicked.connect(self._on_cancel)
        btn_row.addWidget(cancel_btn)

        discard_btn = QPushButton("Bỏ thay đổi")
        discard_btn.setObjectName("exitButton")
        discard_btn.clicked.connect(self._on_discard)
        btn_row.addWidget(discard_btn)

        save_btn = QPushButton("Lưu & Đóng")
        save_btn.setObjectName("saveButton")
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)

    def _on_cancel(self) -> None:
        self.user_choice = self.CANCEL
        self.reject()

    def _on_discard(self) -> None:
        self.user_choice = self.DISCARD_AND_CLOSE
        self.accept()

    def _on_save(self) -> None:
        self.user_choice = self.SAVE_AND_CLOSE
        self.accept()


