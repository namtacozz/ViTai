from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame
)
from vitai.ui.theme import get_stylesheet
from vitai.user_store import UserStore

class ChangeUserPasswordDialog(QDialog):
    def __init__(self, username: str, parent=None, theme: str = "dark", store: UserStore | None = None):
        super().__init__(parent)
        self.username = username
        self.store = store or get_user_store()
        self.theme = theme
        self.setWindowTitle(f"Đổi Mật Khẩu: {username}")
        self.setFixedSize(360, 240)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.setStyleSheet(get_stylesheet(theme))
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title_lbl = QLabel(f"Đổi Mật Khẩu cho: {self.username}")
        title_lbl.setStyleSheet(
            "font-size: 15px; font-weight: 800; color: " + ("#F1F5F9" if self.theme == "dark" else "#0F172A") + ";"
        )
        layout.addWidget(title_lbl)

        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Nhập mật khẩu mới...")
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.pass_input)

        self.err_lbl = QLabel("")
        self.err_lbl.setStyleSheet("color: #EF4444; font-size: 11px; font-weight: 600;")
        self.err_lbl.setVisible(False)
        layout.addWidget(self.err_lbl)

        layout.addStretch()

        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Hủy")
        cancel_btn.setObjectName("helpButton")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("Lưu Mật Khẩu")
        save_btn.setObjectName("saveButton")
        save_btn.clicked.connect(self._on_submit)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _on_submit(self) -> None:
        pwd = self.pass_input.text().strip()
        if not pwd:
            self.err_lbl.setText("Mật khẩu không được để trống!")
            self.err_lbl.setVisible(True)
            return
        ok, msg = self.store.update_password(self.username, pwd)
        if ok:
            self.accept()
        else:
            self.err_lbl.setText(f"{msg}")
            self.err_lbl.setVisible(True)


