from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame
)
from vitai.ui.theme import get_stylesheet
from vitai.user_store import UserStore, verify_password, save_session

class LoginDialog(QDialog):
    def __init__(self, parent=None, theme: str = "dark", store: UserStore | None = None):
        super().__init__(parent)
        self.store = store or get_user_store()
        self.theme = theme
        self.logged_in_user: User | None = None
        self.current_mac = get_mac_address()

        self.setWindowTitle("Đăng Nhập ViTai")
        self.setFixedSize(420, 360)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.setStyleSheet(get_stylesheet(theme))
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        # Header Title
        title_lbl = QLabel("Xác Thực Tài Khoản")
        title_lbl.setStyleSheet(
            "font-size: 18px; font-weight: 800; color: " + ("#F1F5F9" if self.theme == "dark" else "#0F172A") + ";"
        )
        layout.addWidget(title_lbl)

        # MAC Badge & Policy Note
        mac_badge = QLabel(f"Thiết bị này (MAC): {self.current_mac}")
        mac_badge.setStyleSheet(
            "font-size: 11px; font-weight: 600; color: #E09F5E; "
            "background-color: rgba(224, 159, 94, 0.12); padding: 5px 8px; border-radius: 6px;"
        )
        layout.addWidget(mac_badge)

        desc_lbl = QLabel("Tài khoản sẽ được tự động khóa cố định vào phần cứng thiết bị này trong lần đăng nhập đầu tiên.")
        desc_lbl.setStyleSheet("font-size: 11px; color: #94A3B8;")
        desc_lbl.setWordWrap(True)
        layout.addWidget(desc_lbl)

        # Form Inputs
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Tên đăng nhập...")
        layout.addWidget(self.user_input)

        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Mật khẩu...")
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.returnPressed.connect(self._on_submit)
        layout.addWidget(self.pass_input)

        self.err_lbl = QLabel("")
        self.err_lbl.setStyleSheet("color: #EF4444; font-size: 11px; font-weight: 600;")
        self.err_lbl.setWordWrap(True)
        self.err_lbl.setVisible(False)
        layout.addWidget(self.err_lbl)

        layout.addStretch()

        # Action Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.cancel_btn = QPushButton("Thoát")
        self.cancel_btn.setObjectName("exitButton")
        self.cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.cancel_btn)

        self.login_btn = QPushButton("Đăng Nhập")
        self.login_btn.setObjectName("saveButton")
        self.login_btn.clicked.connect(self._on_submit)
        btn_row.addWidget(self.login_btn)

        layout.addLayout(btn_row)

    def _on_submit(self) -> None:
        user_str = self.user_input.text().strip()
        pwd_str = self.pass_input.text().strip()

        if not user_str or not pwd_str:
            self.err_lbl.setText("Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu!")
            self.err_lbl.setVisible(True)
            return

        ok, user_obj, err_msg = self.store.authenticate(user_str, pwd_str, self.current_mac)
        if ok and user_obj:
            self.logged_in_user = user_obj
            save_session(user_obj)
            self.accept()
        else:
            self.err_lbl.setText(f"{err_msg}")
            self.err_lbl.setVisible(True)
            self.pass_input.clear()
            self.pass_input.setFocus()


