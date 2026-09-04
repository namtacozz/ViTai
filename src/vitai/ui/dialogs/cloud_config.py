from __future__ import annotations

import threading
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QCheckBox, QPushButton, QFrame, QApplication
)
from vitai.ui.theme import get_stylesheet
from vitai.user_store import CloudConfig, CloudAuthClient, load_cloud_config, save_cloud_config, UserStore

class CloudConfigDialog(QDialog):
    """Hộp thoại cấu hình kết nối Cloud Database (Supabase / Firebase Firestore)."""

    def __init__(self, parent=None, theme: str = "dark", store: UserStore | None = None):
        super().__init__(parent)
        self.store = store or get_user_store()
        self.theme = theme
        self.setWindowTitle("Cấu Hình Cloud Database (Supabase / Firebase)")
        self.setFixedSize(540, 560)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.setStyleSheet(get_stylesheet(theme))
        self._build_ui()
        self._load_current_config()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # Title
        title_lbl = QLabel("Đồng Bộ Cloud Database")
        title_lbl.setStyleSheet(
            "font-size: 16px; font-weight: 800; color: " + ("#F1F5F9" if self.theme == "dark" else "#0F172A") + ";"
        )
        layout.addWidget(title_lbl)

        desc_lbl = QLabel(
            "Đồng bộ danh sách người dùng và địa chỉ MAC khóa máy tính theo thời gian thực "
            "giữa máy Admin và tất cả các máy người dùng mua app qua Supabase / Firebase."
        )
        desc_lbl.setStyleSheet("font-size: 11px; color: #94A3B8;")
        desc_lbl.setWordWrap(True)
        layout.addWidget(desc_lbl)

        # Enable Checkbox
        self.chk_enable = QCheckBox("Bật đồng bộ hóa Cloud Database (Online)")
        self.chk_enable.setStyleSheet("font-size: 13px; font-weight: bold; color: #E09F5E;")
        self.chk_enable.toggled.connect(self._on_enable_toggled)
        layout.addWidget(self.chk_enable)

        # Provider Selector
        row_prov = QHBoxLayout()
        lbl_prov = QLabel("Nhà cung cấp Cloud:")
        lbl_prov.setFixedWidth(140)
        row_prov.addWidget(lbl_prov)

        self.combo_provider = QComboBox()
        self.combo_provider.addItem("Supabase (PostgreSQL REST - Khuyên Dùng)", "supabase")
        self.combo_provider.addItem("Firebase Firestore REST", "firebase")
        self.combo_provider.currentIndexChanged.connect(self._on_provider_changed)
        row_prov.addWidget(self.combo_provider, 1)
        layout.addLayout(row_prov)

        # Supabase Form Container
        self.supabase_container = QFrame()
        sb_layout = QVBoxLayout(self.supabase_container)
        sb_layout.setContentsMargins(0, 4, 0, 4)
        sb_layout.setSpacing(8)

        sb_url_row = QHBoxLayout()
        lbl_url = QLabel("Project URL:")
        lbl_url.setFixedWidth(140)
        sb_url_row.addWidget(lbl_url)
        self.txt_supabase_url = QLineEdit()
        self.txt_supabase_url.setPlaceholderText("https://xxxx.supabase.co")
        sb_url_row.addWidget(self.txt_supabase_url, 1)
        sb_layout.addLayout(sb_url_row)

        sb_key_row = QHBoxLayout()
        lbl_key = QLabel("API Key (Anon/Service):")
        lbl_key.setFixedWidth(140)
        sb_key_row.addWidget(lbl_key)
        self.txt_supabase_key = QLineEdit()
        self.txt_supabase_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_supabase_key.setPlaceholderText("eyJhbGciOiJIUzI1NiIsInR5cCI6...")
        sb_key_row.addWidget(self.txt_supabase_key, 1)
        sb_layout.addLayout(sb_key_row)

        layout.addWidget(self.supabase_container)

        # Firebase Form Container
        self.firebase_container = QFrame()
        fb_layout = QVBoxLayout(self.firebase_container)
        fb_layout.setContentsMargins(0, 4, 0, 4)
        fb_layout.setSpacing(8)

        fb_proj_row = QHBoxLayout()
        lbl_fb_proj = QLabel("Project ID:")
        lbl_fb_proj.setFixedWidth(140)
        fb_proj_row.addWidget(lbl_fb_proj)
        self.txt_firebase_proj = QLineEdit()
        self.txt_firebase_proj.setPlaceholderText("vitai-auth-prod")
        fb_proj_row.addWidget(self.txt_firebase_proj, 1)
        fb_layout.addLayout(fb_proj_row)

        fb_key_row = QHBoxLayout()
        lbl_fb_key = QLabel("Web API Key:")
        lbl_fb_key.setFixedWidth(140)
        fb_key_row.addWidget(lbl_fb_key)
        self.txt_firebase_key = QLineEdit()
        self.txt_firebase_key.setPlaceholderText("AIzaSy...")
        fb_key_row.addWidget(self.txt_firebase_key, 1)
        fb_layout.addLayout(fb_key_row)

        layout.addWidget(self.firebase_container)
        self.firebase_container.setVisible(False)

        # Test Connection & Quick SQL Buttons
        act_box = QHBoxLayout()
        act_box.setSpacing(8)

        self.btn_test = QPushButton("Kiểm Tra Kết Nối")
        self.btn_test.setObjectName("helpButton")
        self.btn_test.clicked.connect(self._on_test_connection)
        act_box.addWidget(self.btn_test)

        self.btn_copy_sql = QPushButton("Copy SQL Tạo Bảng Supabase")
        self.btn_copy_sql.clicked.connect(self._on_copy_sql)
        act_box.addWidget(self.btn_copy_sql)

        act_box.addStretch()
        layout.addLayout(act_box)

        # Status Label
        self.status_lbl = QLabel("")
        self.status_lbl.setWordWrap(True)
        self.status_lbl.setStyleSheet("font-size: 11px; font-weight: 600;")
        layout.addWidget(self.status_lbl)

        # SQL Guide Box
        guide_box = QFrame()
        guide_box.setObjectName("cardFrame")
        guide_layout = QVBoxLayout(guide_box)
        guide_layout.setContentsMargins(10, 8, 10, 8)
        guide_text = QLabel(
            "<b>Hướng dẫn nhanh Supabase:</b><br>"
            "1. Vào Supabase Dashboard → <b>SQL Editor</b> → Paste câu lệnh SQL bằng nút copy bên trên.<br>"
            "2. Lấy <b>Project URL</b> và <b>anon public key</b> trong <i>Project Settings → API</i> dán vào đây."
        )
        guide_text.setStyleSheet("font-size: 11px; color: #94A3B8; line-height: 1.4;")
        guide_text.setWordWrap(True)
        guide_layout.addWidget(guide_text)
        layout.addWidget(guide_box)

        layout.addStretch()

        # Bottom Buttons
        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Hủy")
        cancel_btn.setObjectName("helpButton")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("Lưu Cấu Hình")
        save_btn.setObjectName("saveButton")
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)

    def _load_current_config(self) -> None:
        cfg = self.store.cloud_config
        self.chk_enable.setChecked(cfg.is_enabled)
        idx = self.combo_provider.findData(cfg.provider)
        if idx >= 0:
            self.combo_provider.setCurrentIndex(idx)
        self.txt_supabase_url.setText(cfg.supabase_url)
        self.txt_supabase_key.setText(cfg.supabase_key)
        self.txt_firebase_proj.setText(cfg.firebase_project_id)
        self.txt_firebase_key.setText(cfg.firebase_api_key)
        self._on_provider_changed()
        self._on_enable_toggled(cfg.is_enabled)

    def _on_enable_toggled(self, enabled: bool) -> None:
        self.combo_provider.setEnabled(enabled)
        self.supabase_container.setEnabled(enabled)
        self.firebase_container.setEnabled(enabled)
        self.btn_test.setEnabled(enabled)

    def _on_provider_changed(self) -> None:
        prov = str(self.combo_provider.currentData())
        self.supabase_container.setVisible(prov == "supabase")
        self.firebase_container.setVisible(prov == "firebase")

    def _build_cloud_config(self) -> CloudConfig:
        return CloudConfig(
            provider=str(self.combo_provider.currentData()),
            supabase_url=self.txt_supabase_url.text().strip(),
            supabase_key=self.txt_supabase_key.text().strip(),
            firebase_project_id=self.txt_firebase_proj.text().strip(),
            firebase_api_key=self.txt_firebase_key.text().strip(),
            table_name="vitai_users",
            is_enabled=self.chk_enable.isChecked(),
        )

    def _on_test_connection(self) -> None:
        cfg = self._build_cloud_config()
        client = CloudAuthClient(cfg)
        self.status_lbl.setText("Đang kết nối thử nghiệm đến Cloud...")
        self.status_lbl.setStyleSheet("color: #E09F5E; font-size: 11px;")
        QApplication.processEvents()

        ok, msg = client.test_connection()
        if ok:
            self.status_lbl.setText(f"{msg}")
            self.status_lbl.setStyleSheet("color: #4ADE80; font-size: 11px; font-weight: bold;")
        else:
            self.status_lbl.setText(f"{msg}")
            self.status_lbl.setStyleSheet("color: #EF4444; font-size: 11px; font-weight: bold;")

    def _on_copy_sql(self) -> None:
        sql = (
            "create table if not exists vitai_users (\n"
            "    username text primary key,\n"
            "    password_hash text not null,\n"
            "    salt text not null,\n"
            "    role text default 'user',\n"
            "    bound_mac text,\n"
            "    created_at text,\n"
            "    is_active boolean default true\n"
            ");\n"
            "alter table vitai_users enable row level security;\n"
            "create policy \"Allow all operations\" on vitai_users for all using (true) with check (true);"
        )
        cb = QApplication.clipboard()
        if cb:
            cb.setText(sql)
            self.status_lbl.setText("Đã sao chép SQL tạo bảng vào bộ nhớ tạm (Clipboard)!")
            self.status_lbl.setStyleSheet("color: #4ADE80; font-size: 11px;")

    def _on_save(self) -> None:
        cfg = self._build_cloud_config()
        self.store.set_cloud_config(cfg)
        self.accept()


