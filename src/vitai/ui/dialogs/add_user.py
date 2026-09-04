from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QFrame
)
from vitai.ui.theme import get_stylesheet
from vitai.user_store import UserStore

class AddUserDialog(QDialog):
    def __init__(self, parent=None, theme: str = "dark", store: UserStore | None = None):
        super().__init__(parent)
        self.store = store or get_user_store()
        self.theme = theme
        self.setWindowTitle("Thêm Người Dùng Mới")
        self.setFixedSize(380, 320)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.setStyleSheet(get_stylesheet(theme))
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title_lbl = QLabel("Tạo Tài Khoản Mới")
        title_lbl.setStyleSheet(
            "font-size: 16px; font-weight: 800; color: " + ("#F1F5F9" if self.theme == "dark" else "#0F172A") + ";"
        )
        layout.addWidget(title_lbl)

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Tên đăng nhập mới...")
        layout.addWidget(self.user_input)

        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Mật khẩu khởi tạo...")
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.pass_input)

        role_row = QHBoxLayout()
        role_lbl = QLabel("Vai trò:")
        role_lbl.setFixedWidth(60)
        role_row.addWidget(role_lbl)

        self.role_combo = QComboBox()
        self.role_combo.addItem("Người Dùng (user)", "user")
        self.role_combo.addItem("Quản Trị Viên (admin)", "admin")
        role_row.addWidget(self.role_combo, 1)
        layout.addLayout(role_row)

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

        save_btn = QPushButton("Tạo Người Dùng")
        save_btn.setObjectName("saveButton")
        save_btn.clicked.connect(self._on_submit)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _on_submit(self) -> None:
        username = self.user_input.text().strip()
        pwd = self.pass_input.text().strip()
        role = str(self.role_combo.currentData())
        if not username or not pwd:
            self.err_lbl.setText("Vui lòng nhập đầy đủ tên và mật khẩu!")
            self.err_lbl.setVisible(True)
            return

        ok, msg = self.store.create_user(username, pwd, role)
        if ok:
            self.accept()
        else:
            self.err_lbl.setText(f"{msg}")
            self.err_lbl.setVisible(True)


