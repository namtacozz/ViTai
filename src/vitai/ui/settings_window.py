from __future__ import annotations

import os
import sys
import threading
import time
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QCloseEvent, QIcon, QKeyEvent, QMouseEvent, QPixmap, QResizeEvent, QTextCursor
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from vitai.auth_server import start_oauth_flow_async
from vitai.color_wheel import CircularColorPickerDialog
from vitai.config import AppConfig
from vitai.hotkey import format_key_display
from vitai.model_registry import get_model_registry
from vitai.oauth_provider import get_subscription_display_name, is_oauth_supported
from vitai.proxy import get_local_proxy
from vitai.resources import resource_path
from vitai.sepay import (
    DEFAULT_BANK_ACC,
    DEFAULT_BANK_ID,
    DEFAULT_BANK_NAME,
    DEFAULT_REGISTRATION_PRICE,
    DEFAULT_SEPAY_TOKEN,
    check_sepay_payment,
    generate_order_code,
    get_vietqr_url,
)
from vitai.token_store import OAuthToken, get_token_store
from vitai.ui_log import get_log_bridge, get_ui_log_handler
from vitai.user_store import (
    CloudAuthClient,
    CloudConfig,
    User,
    UserStore,
    clear_session,
    get_current_session,
    get_mac_address,
    get_user_store,
    load_cloud_config,
    save_cloud_config,
    save_session,
    verify_password,
)
from vitai.ui.theme import get_stylesheet
from vitai.ui.constants import (
    PROVIDER_PRESETS,
    PROVIDER_GUIDES,
    SIZE_CHOICES,
    COLOR_CHOICES,
    extract_hex_color,
)
from vitai.ui.components.hotkey_button import HotkeyInputButton
from vitai.ui.dialogs.provider_help import ProviderHelpDialog
from vitai.ui.dialogs.login import LoginDialog
from vitai.ui.dialogs.add_user import AddUserDialog
from vitai.ui.dialogs.change_password import ChangeUserPasswordDialog
from vitai.ui.dialogs.cloud_config import CloudConfigDialog
from vitai.ui.dialogs.unsaved_changes import UnsavedChangesDialog
from vitai.ui.dialogs.register_payment import RegisterPaymentDialog


def _fetch_user_store() -> UserStore:
    try:
        import vitai.settings as s
        getter = getattr(s, "get_user_store", get_user_store)
        return getter()
    except Exception:
        return get_user_store()


def _fetch_current_session(store: UserStore | None = None) -> User | None:
    try:
        import vitai.settings as s
        getter = getattr(s, "get_current_session", get_current_session)
        return getter(store)
    except Exception:
        return get_current_session(store)


def _execute_save_session(user: User, path=None) -> None:
    try:
        import vitai.settings as s
        saver = getattr(s, "save_session", save_session)
        saver(user, path)
    except Exception:
        save_session(user, path)


class SettingsWindow(QDialog):
    config_changed = pyqtSignal(AppConfig)
    exit_requested = pyqtSignal()
    window_hidden = pyqtSignal()
    test_result_signal = pyqtSignal(bool, str)
    oauth_result_signal = pyqtSignal(bool, str, str)
    models_fetched_signal = pyqtSignal(list)

    def __init__(self, config: AppConfig, parent: QWidget | None = None):
        super().__init__(parent)
        self._config = config
        self._saved_config = config
        self._is_dirty = False
        self._is_loading = False
        self.current_theme = getattr(config, "theme", "dark") or "dark"
        self.user_store = _fetch_user_store()
        self.current_user = _fetch_current_session(self.user_store)
        self.is_admin = (self.current_user.role == "admin") if self.current_user else False

        self.setWindowTitle("Vì Người Tài")
        try:
            self.setWindowIcon(QIcon(str(resource_path("assets/icon.ico"))))
        except Exception:
            pass
        self.resize(850, 580)
        self.setMinimumSize(800, 520)
        self.setWindowFlags(
            Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowMinimizeButtonHint
        )

        self.test_result_signal.connect(self._on_test_result)
        self.oauth_result_signal.connect(self._on_oauth_result)
        self.models_fetched_signal.connect(self._on_models_fetched)

        self._build_ui()
        self._apply_theme()
        self._load_from_config(config)
        self._connect_log_stream()
        self._update_auth_ui()

    def _apply_theme(self) -> None:
        self.setStyleSheet(get_stylesheet(self.current_theme))
        if self.current_theme == "dark":
            self.theme_btn.setText("☼")
            self.theme_btn.setToolTip("Chuyển sang Giao diện Sáng (Light Mode)")
        else:
            self.theme_btn.setText("☾")
            self.theme_btn.setToolTip("Chuyển sang Giao diện Tối (Dark Mode)")
        self._update_overlay_preview()

    def _toggle_theme(self) -> None:
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self._apply_theme()
        self._mark_dirty()

    def _build_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ==========================================
        # 1. LEFT SIDEBAR (Width: 145px)
        # ==========================================
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("sidebarFrame")
        sidebar_frame.setFixedWidth(145)
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(10, 14, 10, 14)
        sidebar_layout.setSpacing(8)

        # Brand / Header with ViTai Logo
        self.brand_widget = QWidget()
        brand_layout = QHBoxLayout(self.brand_widget)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(8)

        logo_box = QLabel()
        logo_box.setFixedSize(28, 28)
        try:
            icon_p = resource_path("assets/icon.ico")
            if not icon_p.exists():
                icon_p = resource_path("assets/logo.png")
            pix = QIcon(str(icon_p)).pixmap(28, 28)
            if not pix.isNull():
                logo_box.setPixmap(pix)
                logo_box.setScaledContents(True)
        except Exception:
            logo_box.setText("VT")
            logo_box.setStyleSheet(
                "background-color: #E09F5E; color: #0C0D0E; border-radius: 6px; font-weight: 900;"
            )
            logo_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_layout.addWidget(logo_box)

        brand_text_layout = QVBoxLayout()
        brand_text_layout.setSpacing(1)
        brand_title = QLabel("ViTai")
        brand_title.setObjectName("brandTitle")
        brand_ver = QLabel("v3.1.1 • AI")
        brand_ver.setObjectName("brandVer")
        brand_text_layout.addWidget(brand_title)
        brand_text_layout.addWidget(brand_ver)
        brand_layout.addLayout(brand_text_layout)
        brand_layout.addStretch()

        sidebar_layout.addWidget(self.brand_widget)
        sidebar_layout.addSpacing(6)

        # Sidebar Menu with 5 Tabs:
        # Tab 0: Vỏ, Tab 1: Lõi, Tab 2: Tài Khoản, Tab 3: Quản Trị (Admin), Tab 4: Nhật Ký (Admin)
        self.sidebar_menu = QListWidget()
        self.sidebar_menu.setObjectName("sidebarMenu")

        menu_items = [
            ("Vỏ", "Cấu hình phím tắt, chuột, màu sắc và xem trước hiển thị"),
            ("Lõi", "Cấu hình AI Provider, Model, Xác thực và API Key"),
            ("Tài Khoản", "Thông tin tài khoản, khóa thiết bị MAC, đổi mật khẩu và đăng xuất"),
            ("Quản Trị", "Quản trị danh sách người dùng, phân quyền và reset thiết bị MAC (Admin)"),
            ("Nhật Ký", "Nhật ký hoạt động và kết nối hệ thống (Admin)"),
        ]
        for title, tooltip in menu_items:
            item = QListWidgetItem(title)
            item.setToolTip(tooltip)
            self.sidebar_menu.addItem(item)

        self.sidebar_menu.currentRowChanged.connect(self._on_tab_changed)
        sidebar_layout.addWidget(self.sidebar_menu, 1)

        # Sidebar Bottom Action Buttons: Trạng thái, Lưu, Áp dụng, Thoát
        sidebar_layout.addSpacing(6)

        self.status_badge = QLabel("✓ Đã lưu")
        self.status_badge.setObjectName("statusBadge")
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_badge.setStyleSheet(
            """
            QLabel#statusBadge {
                font-size: 11px;
                font-weight: 700;
                color: #64748B;
                padding: 4px 6px;
                border-radius: 6px;
                background: transparent;
            }
            """
        )
        sidebar_layout.addWidget(self.status_badge)

        self.save_btn = QPushButton("Lưu")
        self.save_btn.setObjectName("saveButton")
        self.save_btn.clicked.connect(self._on_save)
        sidebar_layout.addWidget(self.save_btn)

        self.apply_btn = QPushButton("Áp dụng")
        self.apply_btn.setObjectName("applyButton")
        self.apply_btn.clicked.connect(self._on_apply)
        sidebar_layout.addWidget(self.apply_btn)

        self.exit_btn = QPushButton("Thoát")
        self.exit_btn.setObjectName("exitButton")
        self.exit_btn.clicked.connect(self._on_exit)
        sidebar_layout.addWidget(self.exit_btn)

        main_layout.addWidget(sidebar_frame)

        # ==========================================
        # 2. RIGHT CONTENT AREA (QStackedWidget)
        # ==========================================
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(20, 16, 20, 16)
        content_layout.setSpacing(12)

        # Dynamic Header Row (Title + Description + Theme Toggle Button)
        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        header_text_layout = QVBoxLayout()
        header_text_layout.setSpacing(2)
        self.header_title = QLabel("Vỏ")
        self.header_title.setObjectName("headerTitle")
        self.header_desc = QLabel("Tuỳ chỉnh phím tắt kích hoạt, chế độ làm việc và xem trước chữ đáp án.")
        self.header_desc.setObjectName("headerDesc")
        header_text_layout.addWidget(self.header_title)
        header_text_layout.addWidget(self.header_desc)
        header_row.addLayout(header_text_layout, 1)

        # Theme Switcher Button (Sun / Moon)
        self.theme_btn = QPushButton("☼")
        self.theme_btn.setObjectName("themeToggleBtn")
        self.theme_btn.setFixedSize(36, 36)
        self.theme_btn.clicked.connect(self._toggle_theme)
        header_row.addWidget(self.theme_btn)

        content_layout.addLayout(header_row)

        self.stack = QStackedWidget()

        # ------------------------------------------
        # TAB 0: VỎ (Interface, Hotkey & Minimalist 'A' Preview)
        # ------------------------------------------
        page_shell = QWidget()
        page_shell_layout = QVBoxLayout(page_shell)
        page_shell_layout.setContentsMargins(0, 0, 0, 0)
        page_shell_layout.setSpacing(10)

        # Card 1: Hotkey & Modes Row (Side-by-Side)
        hk_mode_row = QHBoxLayout()
        hk_mode_row.setSpacing(10)

        # Hotkey Sub-card
        card_hotkey = QFrame()
        card_hotkey.setObjectName("cardFrame")
        hk_layout = QVBoxLayout(card_hotkey)
        hk_layout.setContentsMargins(14, 12, 14, 12)
        hk_layout.setSpacing(6)

        lbl_hk_title = QLabel("Phím tắt kích hoạt")
        lbl_hk_title.setObjectName("cardTitle")
        lbl_hk_desc = QLabel("Bôi đen câu hỏi và nhấn phím hoặc chuột:")
        lbl_hk_desc.setObjectName("cardDesc")
        hk_layout.addWidget(lbl_hk_title)
        hk_layout.addWidget(lbl_hk_desc)

        self.hotkey_btn = HotkeyInputButton("alt", "q")
        hk_layout.addWidget(self.hotkey_btn)

        hk_mode_row.addWidget(card_hotkey, 1)

        # Modes Sub-card
        card_modes = QFrame()
        card_modes.setObjectName("cardFrame")
        m_layout = QVBoxLayout(card_modes)
        m_layout.setContentsMargins(14, 12, 14, 12)
        m_layout.setSpacing(6)

        lbl_m_title = QLabel("Chế độ thông minh")
        lbl_m_title.setObjectName("cardTitle")
        m_layout.addWidget(lbl_m_title)

        self.auto_check = QCheckBox("Fast Mode (Tự động khi bôi đen)")
        self.cache_check = QCheckBox("Cache Saver (Lưu phản hồi 0ms)")
        m_layout.addWidget(self.auto_check)
        m_layout.addWidget(self.cache_check)
        hk_mode_row.addWidget(card_modes, 1)

        page_shell_layout.addLayout(hk_mode_row)

        # Card 2: Overlay Appearance (With Clickable Color Swatch opening Circular Color Picker)
        card_overlay = QFrame()
        card_overlay.setObjectName("cardFrame")
        ov_layout = QVBoxLayout(card_overlay)
        ov_layout.setContentsMargins(14, 12, 14, 12)
        ov_layout.setSpacing(8)

        lbl_ov_title = QLabel("Cửa sổ phản hồi (Ghost Overlay Style)")
        lbl_ov_title.setObjectName("cardTitle")
        lbl_ov_desc = QLabel("Tùy chỉnh cỡ chữ và phổ màu 360° như Photoshop / Aseprite:")
        lbl_ov_desc.setObjectName("cardDesc")
        ov_layout.addWidget(lbl_ov_title)
        ov_layout.addWidget(lbl_ov_desc)

        ov_row = QHBoxLayout()
        ov_row.setSpacing(10)

        lbl_sz = QLabel("Cỡ chữ:")
        lbl_sz.setFixedWidth(55)
        ov_row.addWidget(lbl_sz)

        self.size_combo = QComboBox()
        for display, code in SIZE_CHOICES:
            self.size_combo.addItem(display, code)
        self.size_combo.currentIndexChanged.connect(self._on_overlay_style_changed)
        ov_row.addWidget(self.size_combo)

        ov_row.addSpacing(12)

        lbl_cl = QLabel("Màu sắc:")
        lbl_cl.setFixedWidth(60)
        ov_row.addWidget(lbl_cl)

        # Color Swatch Indicator (Clickable 32x32 button that opens 360° Color Wheel)
        self.color_swatch = QLabel()
        self.color_swatch.setFixedSize(32, 32)
        self.color_swatch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.color_swatch.setToolTip("Nhấn để mở Bảng màu tròn 360° (Photoshop / Aseprite style)")
        self.color_swatch.mousePressEvent = lambda ev: self._open_color_wheel()
        self.color_swatch.setStyleSheet(
            "background-color: #E09F5E; border: 1px solid #3F3F46; border-radius: 6px;"
        )
        ov_row.addWidget(self.color_swatch)

        self.color_combo = QComboBox()
        self.color_combo.setEditable(True)
        for display, code in COLOR_CHOICES:
            self.color_combo.addItem(display, code)
        self.color_combo.currentIndexChanged.connect(self._on_overlay_style_changed)
        self.color_combo.currentTextChanged.connect(self._on_overlay_style_changed)
        ov_row.addWidget(self.color_combo, 1)

        ov_layout.addLayout(ov_row)
        page_shell_layout.addWidget(card_overlay)

        # Card 3: Minimalist Ghost Overlay Preview (Only the 'A' tag)
        card_preview = QFrame()
        card_preview.setObjectName("cardFrame")
        prev_layout = QVBoxLayout(card_preview)
        prev_layout.setContentsMargins(14, 14, 14, 14)
        prev_layout.setSpacing(10)

        prev_title_row = QHBoxLayout()
        lbl_prev_title = QLabel("Xem trước (Ghost Overlay)")
        lbl_prev_title.setObjectName("cardTitle")
        prev_title_row.addWidget(lbl_prev_title)
        prev_title_row.addStretch()

        self._preview_bg_mode = "dark"
        self.preview_bg_btn = QPushButton("Nền: Đen")
        self.preview_bg_btn.setObjectName("helpButton")
        self.preview_bg_btn.setToolTip("Chuyển đổi nền mô phỏng giữa Đen và Trắng để kiểm tra độ tương phản màu sắc")
        self.preview_bg_btn.setFixedHeight(24)
        self.preview_bg_btn.setStyleSheet("font-size: 11px; padding: 2px 10px; font-weight: 700;")
        self.preview_bg_btn.clicked.connect(self._toggle_preview_bg)
        prev_title_row.addWidget(self.preview_bg_btn)

        live_badge = QLabel("Xem trước")
        live_badge.setStyleSheet(
            "color: #4ADE80; font-size: 11px; font-weight: 700; "
            "background-color: rgba(34, 197, 94, 0.12); padding: 3px 8px; border-radius: 6px;"
        )
        prev_title_row.addWidget(live_badge)
        prev_layout.addLayout(prev_title_row)

        lbl_prev_desc = QLabel("Mô phỏng chữ cái đáp án hiển thị (bấm nút để thử trên nền Đen/Trắng):")
        lbl_prev_desc.setObjectName("cardDesc")
        prev_layout.addWidget(lbl_prev_desc)

        # Clean Centered Stage Box with ONLY the letter 'A'
        self.preview_stage = QFrame()
        self.preview_stage.setStyleSheet(
            "background-color: #08090B; border: 1px dashed #2E333D; border-radius: 8px; min-height: 85px;"
        )
        stage_layout = QVBoxLayout(self.preview_stage)
        stage_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stage_layout.setContentsMargins(16, 14, 16, 14)

        self.preview_ghost_tag = QLabel("A")
        self.preview_ghost_tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stage_layout.addWidget(self.preview_ghost_tag, 0, Qt.AlignmentFlag.AlignCenter)

        prev_layout.addWidget(self.preview_stage)
        page_shell_layout.addWidget(card_preview)

        page_shell_layout.addStretch()
        self.stack.addWidget(page_shell)

        # ------------------------------------------
        # TAB 1: LÕI (AI Engine, Authentication & Models)
        # ------------------------------------------
        page_core = QWidget()
        page_core_layout = QVBoxLayout(page_core)
        page_core_layout.setContentsMargins(0, 0, 0, 0)
        page_core_layout.setSpacing(10)

        LABEL_W = 85

        # Card 1: Provider & Endpoint
        card_prov = QFrame()
        card_prov.setObjectName("cardFrame")
        cp_layout = QVBoxLayout(card_prov)
        cp_layout.setContentsMargins(14, 10, 14, 10)
        cp_layout.setSpacing(6)

        # Provider row
        p_row = QHBoxLayout()
        lbl_p = QLabel("Provider:")
        lbl_p.setFixedWidth(LABEL_W)
        p_row.addWidget(lbl_p)

        self.provider_combo = QComboBox()
        for display, code, base, model in PROVIDER_PRESETS:
            self.provider_combo.addItem(display, code)
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        p_row.addWidget(self.provider_combo, 1)
        cp_layout.addLayout(p_row)

        # Base URL row
        url_row = QHBoxLayout()
        lbl_u = QLabel("Base URL:")
        lbl_u.setFixedWidth(LABEL_W)
        url_row.addWidget(lbl_u)

        self.url_input = QLineEdit()
        url_row.addWidget(self.url_input, 1)
        cp_layout.addLayout(url_row)

        page_core_layout.addWidget(card_prov)

        # Card 2: Authentication (OAuth / API Key)
        card_auth = QFrame()
        card_auth.setObjectName("cardFrame")
        ca_layout = QVBoxLayout(card_auth)
        ca_layout.setContentsMargins(14, 10, 14, 10)
        ca_layout.setSpacing(6)

        # OAuth Row
        self.oauth_container = QWidget()
        oauth_layout = QHBoxLayout(self.oauth_container)
        oauth_layout.setContentsMargins(0, 0, 0, 0)
        oauth_layout.setSpacing(10)

        lbl_oauth = QLabel("Xác thực:")
        lbl_oauth.setFixedWidth(LABEL_W)
        oauth_layout.addWidget(lbl_oauth)

        self.oauth_btn = QPushButton("Đăng nhập OAuth")
        self.oauth_btn.setObjectName("oauthButton")
        self.oauth_btn.clicked.connect(self._on_oauth_login)
        oauth_layout.addWidget(self.oauth_btn)

        self.oauth_status_lbl = QLabel("")
        self.oauth_status_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #94A3B8;")
        oauth_layout.addWidget(self.oauth_status_lbl, 1)

        self.oauth_logout_btn = QPushButton("Đăng xuất")
        self.oauth_logout_btn.setObjectName("logoutButton")
        self.oauth_logout_btn.clicked.connect(self._on_oauth_logout)
        oauth_layout.addWidget(self.oauth_logout_btn)

        ca_layout.addWidget(self.oauth_container)

        # API Key Fallback Row
        self.key_container = QWidget()
        key_layout = QHBoxLayout(self.key_container)
        key_layout.setContentsMargins(0, 0, 0, 0)
        key_layout.setSpacing(10)

        self.lbl_k = QLabel("API Key:")
        self.lbl_k.setFixedWidth(LABEL_W)
        key_layout.addWidget(self.lbl_k)

        self.key_input = QLineEdit()
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setPlaceholderText("Dán API Key (hoặc dùng OAuth phía trên)...")
        key_layout.addWidget(self.key_input, 1)

        self.toggle_key_btn = QPushButton("Ẩn/Hiện")
        self.toggle_key_btn.setFixedWidth(78)
        self.toggle_key_btn.clicked.connect(self._toggle_key_visibility)
        key_layout.addWidget(self.toggle_key_btn)

        ca_layout.addWidget(self.key_container)
        page_core_layout.addWidget(card_auth)

        # Card 3: Model Configuration & Connectivity Test
        card_model = QFrame()
        card_model.setObjectName("cardFrame")
        cm_layout = QVBoxLayout(card_model)
        cm_layout.setContentsMargins(14, 10, 14, 10)
        cm_layout.setSpacing(6)

        model_row = QHBoxLayout()
        lbl_m = QLabel("Model AI:")
        lbl_m.setFixedWidth(LABEL_W)
        model_row.addWidget(lbl_m)

        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        model_row.addWidget(self.model_combo, 1)

        self.refresh_models_btn = QPushButton("Làm mới")
        self.refresh_models_btn.setObjectName("refreshButton")
        self.refresh_models_btn.setToolTip("Cập nhật danh sách model từ API")
        self.refresh_models_btn.clicked.connect(self._on_refresh_models)
        model_row.addWidget(self.refresh_models_btn)
        cm_layout.addLayout(model_row)

        # Test and Help Action Row
        action_row = QHBoxLayout()
        self.test_btn = QPushButton("Test")
        self.test_btn.setObjectName("testButton")
        self.test_btn.clicked.connect(self._on_test_ai)
        action_row.addWidget(self.test_btn)

        self.help_btn = QPushButton("Hướng dẫn")
        self.help_btn.setObjectName("helpButton")
        self.help_btn.clicked.connect(self._show_provider_help)
        action_row.addWidget(self.help_btn)

        self.test_status_label = QLabel("")
        self.test_status_label.setStyleSheet("font-size: 12px; font-weight: 600;")
        action_row.addWidget(self.test_status_label, 1)

        cm_layout.addLayout(action_row)
        page_core_layout.addWidget(card_model)
        page_core_layout.addStretch()

        self.stack.addWidget(page_core)

        # ------------------------------------------
        # TAB 2: TÀI KHOẢN (Account & MAC Security)
        # ------------------------------------------
        page_account = QWidget()
        page_acc_layout = QVBoxLayout(page_account)
        page_acc_layout.setContentsMargins(0, 0, 0, 0)
        page_acc_layout.setSpacing(10)

        # Card 1: User Details
        card_user_info = QFrame()
        card_user_info.setObjectName("cardFrame")
        cui_layout = QVBoxLayout(card_user_info)
        cui_layout.setContentsMargins(14, 12, 14, 12)
        cui_layout.setSpacing(8)

        lbl_ui_title = QLabel("Thông Tin Tài Khoản")
        lbl_ui_title.setObjectName("cardTitle")
        cui_layout.addWidget(lbl_ui_title)

        self.acc_username_lbl = QLabel("Tài khoản: --")
        self.acc_username_lbl.setStyleSheet("font-size: 13px; font-weight: bold;")
        cui_layout.addWidget(self.acc_username_lbl)

        self.acc_role_lbl = QLabel("Vai trò: --")
        self.acc_role_lbl.setStyleSheet("font-size: 12px; color: #E09F5E;")
        cui_layout.addWidget(self.acc_role_lbl)

        self.acc_mac_lbl = QLabel(f"Địa chỉ MAC thiết bị này: {get_mac_address()}")
        self.acc_mac_lbl.setStyleSheet("font-size: 12px; color: #94A3B8;")
        cui_layout.addWidget(self.acc_mac_lbl)

        self.acc_status_badge = QLabel("Đã kích hoạt phần cứng trên thiết bị này")
        self.acc_status_badge.setStyleSheet(
            "color: #4ADE80; font-size: 11px; font-weight: 700; "
            "background-color: rgba(34, 197, 94, 0.12); padding: 3px 8px; border-radius: 6px;"
        )
        cui_layout.addWidget(self.acc_status_badge)

        page_acc_layout.addWidget(card_user_info)

        # Card 2: Change Password
        card_pwd = QFrame()
        card_pwd.setObjectName("cardFrame")
        cpwd_layout = QVBoxLayout(card_pwd)
        cpwd_layout.setContentsMargins(14, 12, 14, 12)
        cpwd_layout.setSpacing(8)

        lbl_pwd_title = QLabel("Đổi Mật Khẩu Cá Nhân")
        lbl_pwd_title.setObjectName("cardTitle")
        cpwd_layout.addWidget(lbl_pwd_title)

        self.old_pwd_input = QLineEdit()
        self.old_pwd_input.setPlaceholderText("Mật khẩu hiện tại...")
        self.old_pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        cpwd_layout.addWidget(self.old_pwd_input)

        self.new_pwd_input = QLineEdit()
        self.new_pwd_input.setPlaceholderText("Mật khẩu mới...")
        self.new_pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        cpwd_layout.addWidget(self.new_pwd_input)

        self.cfm_pwd_input = QLineEdit()
        self.cfm_pwd_input.setPlaceholderText("Xác nhận mật khẩu mới...")
        self.cfm_pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        cpwd_layout.addWidget(self.cfm_pwd_input)

        self.pwd_status_lbl = QLabel("")
        self.pwd_status_lbl.setStyleSheet("font-size: 11px; font-weight: 600;")
        cpwd_layout.addWidget(self.pwd_status_lbl)

        pwd_btn_row = QHBoxLayout()
        self.update_pwd_btn = QPushButton("Cập Nhật Mật Khẩu")
        self.update_pwd_btn.setObjectName("saveButton")
        self.update_pwd_btn.clicked.connect(self._on_change_password)
        pwd_btn_row.addWidget(self.update_pwd_btn)
        pwd_btn_row.addStretch()
        cpwd_layout.addLayout(pwd_btn_row)

        page_acc_layout.addWidget(card_pwd)

        # Card 3: Logout Action
        card_logout = QFrame()
        card_logout.setObjectName("cardFrame")
        clog_layout = QHBoxLayout(card_logout)
        clog_layout.setContentsMargins(14, 10, 14, 10)
        clog_layout.setSpacing(10)

        lbl_log_desc = QLabel("Đăng xuất tài khoản khỏi ứng dụng trên máy này:")
        lbl_log_desc.setStyleSheet("font-size: 12px; color: #94A3B8;")
        clog_layout.addWidget(lbl_log_desc, 1)

        self.user_logout_btn = QPushButton("Đăng Xuất")
        self.user_logout_btn.setObjectName("exitButton")
        self.user_logout_btn.clicked.connect(self._on_user_logout)
        clog_layout.addWidget(self.user_logout_btn)

        page_acc_layout.addWidget(card_logout)
        page_acc_layout.addStretch()
        self.stack.addWidget(page_account)

        # ------------------------------------------
        # TAB 3: QUẢN TRỊ (Admin User Management)
        # ------------------------------------------
        page_admin = QWidget()
        page_admin_layout = QVBoxLayout(page_admin)
        page_admin_layout.setContentsMargins(0, 0, 0, 0)
        page_admin_layout.setSpacing(10)

        card_admin = QFrame()
        card_admin.setObjectName("cardFrame")
        cadmin_layout = QVBoxLayout(card_admin)
        cadmin_layout.setContentsMargins(14, 12, 14, 12)
        cadmin_layout.setSpacing(8)

        lbl_adm_title = QLabel("Quản Trị Người Dùng & Khóa MAC")
        lbl_adm_title.setObjectName("cardTitle")
        lbl_adm_desc = QLabel("Xem danh sách người dùng, reset địa chỉ MAC khi người dùng đổi máy, khóa hoặc thêm tài khoản:")
        lbl_adm_desc.setObjectName("cardDesc")
        cadmin_layout.addWidget(lbl_adm_title)
        cadmin_layout.addWidget(lbl_adm_desc)

        # Cloud Sync Status & Config Toolbar
        cloud_bar = QHBoxLayout()
        cloud_bar.setSpacing(8)
        self.cloud_status_lbl = QLabel("Chế độ Cục Bộ")
        self.cloud_status_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #E09F5E;")
        cloud_bar.addWidget(self.cloud_status_lbl)
        cloud_bar.addStretch()

        self.btn_adm_refresh = QPushButton("Làm Mới")
        self.btn_adm_refresh.clicked.connect(self._refresh_admin_user_table)
        cloud_bar.addWidget(self.btn_adm_refresh)

        self.btn_adm_cloud = QPushButton("Cấu Hình Cloud Sync")
        self.btn_adm_cloud.setObjectName("helpButton")
        self.btn_adm_cloud.setToolTip("Cấu hình kết nối Supabase / Firebase để đồng bộ online giữa các máy tính")
        self.btn_adm_cloud.clicked.connect(self._on_admin_cloud_config)
        cloud_bar.addWidget(self.btn_adm_cloud)
        cadmin_layout.addLayout(cloud_bar)

        # User Table
        self.admin_user_table = QTableWidget()
        self.admin_user_table.setColumnCount(6)
        self.admin_user_table.setHorizontalHeaderLabels(["Tài Khoản", "Mật Khẩu", "Vai Trò", "Địa Chỉ MAC Đã Khóa", "Trạng Thái", "Ngày Tạo"])
        v_header = self.admin_user_table.verticalHeader()
        if v_header is not None:
            v_header.setVisible(False)
        header = self.admin_user_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.admin_user_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.admin_user_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        cadmin_layout.addWidget(self.admin_user_table, 1)

        # Action Toolbar
        adm_act_row = QHBoxLayout()
        adm_act_row.setSpacing(8)

        self.btn_adm_add = QPushButton("Thêm User")
        self.btn_adm_add.setObjectName("saveButton")
        self.btn_adm_add.clicked.connect(self._on_admin_add_user)
        adm_act_row.addWidget(self.btn_adm_add)

        self.btn_adm_reset_mac = QPushButton("Reset MAC")
        self.btn_adm_reset_mac.setObjectName("helpButton")
        self.btn_adm_reset_mac.setToolTip("Xóa địa chỉ MAC cũ để người dùng đăng nhập trên máy mới")
        self.btn_adm_reset_mac.clicked.connect(self._on_admin_reset_mac)
        adm_act_row.addWidget(self.btn_adm_reset_mac)

        self.btn_adm_change_pwd = QPushButton("Đổi Mật Khẩu")
        self.btn_adm_change_pwd.setObjectName("helpButton")
        self.btn_adm_change_pwd.clicked.connect(self._on_admin_change_user_password)
        adm_act_row.addWidget(self.btn_adm_change_pwd)

        self.btn_adm_toggle = QPushButton("Khóa/Mở")
        self.btn_adm_toggle.setObjectName("helpButton")
        self.btn_adm_toggle.clicked.connect(self._on_admin_toggle_active)
        adm_act_row.addWidget(self.btn_adm_toggle)

        self.btn_adm_del = QPushButton("Xóa User")
        self.btn_adm_del.setObjectName("exitButton")
        self.btn_adm_del.clicked.connect(self._on_admin_delete_user)
        adm_act_row.addWidget(self.btn_adm_del)

        adm_act_row.addStretch()

        cadmin_layout.addLayout(adm_act_row)
        page_admin_layout.addWidget(card_admin)
        self.stack.addWidget(page_admin)

        # ------------------------------------------
        # TAB 4: NHẬT KÝ (Activity Logs - Admin Only)
        # ------------------------------------------
        page_log = QWidget()
        page_log_layout = QVBoxLayout(page_log)
        page_log_layout.setContentsMargins(0, 0, 0, 0)
        page_log_layout.setSpacing(10)

        card_log = QFrame()
        card_log.setObjectName("cardFrame")
        cl_layout = QVBoxLayout(card_log)
        cl_layout.setContentsMargins(14, 12, 14, 12)
        cl_layout.setSpacing(8)

        self.log_text = QPlainTextEdit()
        self.log_text.setObjectName("logView")
        self.log_text.setReadOnly(True)
        cl_layout.addWidget(self.log_text, 1)

        log_btn_row = QHBoxLayout()
        self.clear_log_btn = QPushButton("Xóa Log")
        self.clear_log_btn.clicked.connect(self._on_clear_log)
        log_btn_row.addWidget(self.clear_log_btn)

        self.copy_log_btn = QPushButton("Sao Chép Log")
        self.copy_log_btn.clicked.connect(self._on_copy_log)
        log_btn_row.addWidget(self.copy_log_btn)
        log_btn_row.addStretch()

        cl_layout.addLayout(log_btn_row)
        page_log_layout.addWidget(card_log)

        self.stack.addWidget(page_log)

        # Add Stack to Content
        content_layout.addWidget(self.stack, 1)
        main_layout.addWidget(content_container, 1)

        # Set default tab
        self.sidebar_menu.setCurrentRow(0)

        # Wire change tracking for unsaved indicator
        self.hotkey_btn.hotkey_changed.connect(lambda *_: self._mark_dirty())
        self.auto_check.toggled.connect(lambda *_: self._mark_dirty())
        self.cache_check.toggled.connect(lambda *_: self._mark_dirty())
        self.provider_combo.currentIndexChanged.connect(lambda *_: self._mark_dirty())
        self.key_input.textChanged.connect(lambda *_: self._mark_dirty())
        self.url_input.textChanged.connect(lambda *_: self._mark_dirty())
        self.model_combo.currentTextChanged.connect(lambda *_: self._mark_dirty())
        self.size_combo.currentIndexChanged.connect(lambda *_: self._mark_dirty())
        self.color_combo.currentIndexChanged.connect(lambda *_: self._mark_dirty())
        self.color_combo.currentTextChanged.connect(lambda *_: self._mark_dirty())

        # ==========================================
        # 3. FULL-SCREEN LOGIN GATE OVERLAY (Frosted Glass Barrier)
        # ==========================================
        self.login_gate_overlay = QFrame(self)
        self.login_gate_overlay.setObjectName("loginGateOverlay")
        gate_layout = QVBoxLayout(self.login_gate_overlay)
        gate_layout.setContentsMargins(40, 24, 40, 24)
        gate_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Centered Login Card
        login_card = QFrame()
        login_card.setObjectName("loginCard")
        login_card.setFixedSize(460, 450)
        card_layout = QVBoxLayout(login_card)
        card_layout.setContentsMargins(32, 28, 32, 28)
        card_layout.setSpacing(12)

        # Header Icon & Title
        title_box = QLabel("ĐĂNG NHẬP HỆ THỐNG ViTai")
        title_box.setStyleSheet("font-size: 17px; font-weight: 900; color: #E09F5E;")
        title_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title_box)

        sub_box = QLabel("Vui lòng xác thực tài khoản để mở khóa và sử dụng ứng dụng")
        sub_box.setStyleSheet("font-size: 12px; color: #94A3B8;")
        sub_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_box.setWordWrap(True)
        card_layout.addWidget(sub_box)

        card_layout.addSpacing(4)

        # Hardware MAC Lock Badge
        self.gate_mac_lbl = QLabel(f"Khóa Thiết Bị (MAC): {get_mac_address()}")
        self.gate_mac_lbl.setStyleSheet(
            "font-size: 11px; font-weight: 700; color: #E09F5E; "
            "background-color: rgba(224, 159, 94, 0.12); padding: 5px 8px; border-radius: 6px;"
        )
        self.gate_mac_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.gate_mac_lbl)

        # Cloud Sync Badge
        self.gate_cloud_lbl = QLabel("Supabase Cloud: Đang kết nối Online")
        self.gate_cloud_lbl.setStyleSheet(
            "font-size: 11px; font-weight: 600; color: #4ADE80; "
            "background-color: rgba(74, 222, 128, 0.12); padding: 5px 8px; border-radius: 6px;"
        )
        self.gate_cloud_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.gate_cloud_lbl)

        card_layout.addSpacing(4)

        # Input fields
        self.gate_user_input = QLineEdit()
        self.gate_user_input.setPlaceholderText("Tên đăng nhập...")
        card_layout.addWidget(self.gate_user_input)

        self.gate_pass_input = QLineEdit()
        self.gate_pass_input.setPlaceholderText("Mật khẩu...")
        self.gate_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.gate_pass_input.returnPressed.connect(self._on_gate_login)
        card_layout.addWidget(self.gate_pass_input)

        # Error label
        self.gate_err_lbl = QLabel("")
        self.gate_err_lbl.setStyleSheet("color: #EF4444; font-size: 11px; font-weight: 600;")
        self.gate_err_lbl.setWordWrap(True)
        self.gate_err_lbl.setVisible(False)
        card_layout.addWidget(self.gate_err_lbl)

        card_layout.addStretch()

        # Action Buttons
        btn_gate_row = QHBoxLayout()
        btn_gate_row.setSpacing(10)

        self.gate_exit_btn = QPushButton("Thoát")
        self.gate_exit_btn.setObjectName("exitButton")
        self.gate_exit_btn.clicked.connect(self._on_gate_exit)
        btn_gate_row.addWidget(self.gate_exit_btn)

        self.gate_login_btn = QPushButton("Đăng Nhập Ngay")
        self.gate_login_btn.setObjectName("saveButton")
        self.gate_login_btn.clicked.connect(self._on_gate_login)
        btn_gate_row.addWidget(self.gate_login_btn)

        card_layout.addLayout(btn_gate_row)

        self.gate_reg_btn = QPushButton("Đăng Ký Tài Khoản (Quét QR 50.000đ)")
        self.gate_reg_btn.setObjectName("helpButton")
        self.gate_reg_btn.setStyleSheet("color: #E09F5E; font-weight: 700; border: 1px solid rgba(224, 159, 94, 0.4);")
        self.gate_reg_btn.clicked.connect(self._on_gate_register_payment)
        card_layout.addWidget(self.gate_reg_btn)

        gate_layout.addWidget(login_card)

        self.login_gate_overlay.setGeometry(self.rect())
        if self.current_user is None:
            self.login_gate_overlay.show()
            self.login_gate_overlay.raise_()
        else:
            self.login_gate_overlay.hide()

    def _on_gate_register_payment(self) -> None:
        dlg = RegisterPaymentDialog(self.user_store, parent=self, theme=self.current_theme)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if dlg.created_username and dlg.created_password:
                client_mac = get_mac_address()
                ok, user_obj, err_msg = self.user_store.authenticate(dlg.created_username, dlg.created_password, client_mac)
                if ok and user_obj:
                    _execute_save_session(user_obj)
                    self.current_user = user_obj
                    self.is_admin = (user_obj.role == "admin")
                    self.login_gate_overlay.hide()
                    self._update_auth_ui()

    def _toggle_preview_bg(self) -> None:
        if getattr(self, "_preview_bg_mode", "dark") == "dark":
            self._preview_bg_mode = "light"
            self.preview_bg_btn.setText("Nền: Trắng")
            if hasattr(self, "preview_stage") and self.preview_stage is not None:
                self.preview_stage.setStyleSheet(
                    "background-color: #FFFFFF; border: 1.5px solid #CBD5E1; border-radius: 8px; min-height: 85px;"
                )
        else:
            self._preview_bg_mode = "dark"
            self.preview_bg_btn.setText("Nền: Đen")
            if hasattr(self, "preview_stage") and self.preview_stage is not None:
                self.preview_stage.setStyleSheet(
                    "background-color: #08090B; border: 1px dashed #2E333D; border-radius: 8px; min-height: 85px;"
                )
        self._update_overlay_preview()

    def _open_color_wheel(self) -> None:
        current_hex = self._get_current_color_hex()
        new_hex = CircularColorPickerDialog.get_color_hex(
            initial_color=current_hex,
            theme=self.current_theme,
            parent=self,
        )
        if new_hex:
            self._load_color_into_combo(new_hex)
            self._update_overlay_preview()
            self._mark_dirty()

    def _on_gate_login(self) -> None:
        user_str = self.gate_user_input.text().strip()
        pwd_str = self.gate_pass_input.text().strip()

        if not user_str or not pwd_str:
            self.gate_err_lbl.setText("Vui lòng nhập đầy đủ tài khoản và mật khẩu!")
            self.gate_err_lbl.setVisible(True)
            return

        self.gate_login_btn.setText("Đang xác thực...")
        self.gate_login_btn.setEnabled(False)
        QApplication.processEvents()

        try:
            client_mac = get_mac_address()
            ok, user_obj, err_msg = self.user_store.authenticate(user_str, pwd_str, client_mac)
            if ok and user_obj:
                self.current_user = user_obj
                _execute_save_session(user_obj)
                self.gate_err_lbl.setVisible(False)
                self.gate_user_input.clear()
                self.gate_pass_input.clear()
                self._update_auth_ui()
                self.login_gate_overlay.hide()
                self.sidebar_menu.setCurrentRow(0)
            else:
                self.gate_err_lbl.setText(f"{err_msg}")
                self.gate_err_lbl.setVisible(True)
                self.gate_pass_input.clear()
                self.gate_pass_input.setFocus()
        finally:
            self.gate_login_btn.setText("Đăng Nhập Ngay")
            self.gate_login_btn.setEnabled(True)

    def _on_gate_exit(self) -> None:
        self.exit_requested.emit()
        self.close()

    def _update_auth_ui(self) -> None:
        self.is_admin = (self.current_user.role == "admin") if self.current_user else False

        # Hide or show Admin & Log tabs
        admin_item = self.sidebar_menu.item(3)
        log_item = self.sidebar_menu.item(4)
        if admin_item:
            admin_item.setHidden(not self.is_admin)
        if log_item:
            log_item.setHidden(not self.is_admin)

        if self.current_user:
            self.acc_username_lbl.setText(f"Tài khoản: {self.current_user.username}")
            role_title = "Quản Trị Viên (Admin)" if self.is_admin else "Người Dùng (User)"
            self.acc_role_lbl.setText(f"Vai trò: {role_title}")
            if self.is_admin:
                self.acc_mac_lbl.setText(f"Địa chỉ MAC thiết bị này: {get_mac_address()} (Tài khoản Admin - Tự do mọi thiết bị)")
            else:
                bound_str = self.current_user.bound_mac if self.current_user.bound_mac else "Chưa liên kết"
                self.acc_mac_lbl.setText(f"Địa chỉ MAC thiết bị này: {get_mac_address()} (Đã khóa: {bound_str})")
            if hasattr(self, "login_gate_overlay"):
                self.login_gate_overlay.hide()
        else:
            self.acc_username_lbl.setText("Tài khoản: Chưa đăng nhập")
            self.acc_role_lbl.setText("Vai trò: --")
            if hasattr(self, "login_gate_overlay"):
                self.login_gate_overlay.setGeometry(self.rect())
                self.login_gate_overlay.show()
                self.login_gate_overlay.raise_()
                self.gate_user_input.setFocus()

        if self.is_admin:
            self._refresh_admin_user_table()

    def _on_change_password(self) -> None:
        if not self.current_user:
            self.pwd_status_lbl.setText("Bạn chưa đăng nhập.")
            self.pwd_status_lbl.setStyleSheet("color: #EF4444; font-size: 11px;")
            return

        old_pwd = self.old_pwd_input.text().strip()
        new_pwd = self.new_pwd_input.text().strip()
        cfm_pwd = self.cfm_pwd_input.text().strip()

        if not old_pwd or not new_pwd or not cfm_pwd:
            self.pwd_status_lbl.setText("Vui lòng điền đầy đủ các ô mật khẩu!")
            self.pwd_status_lbl.setStyleSheet("color: #EF4444; font-size: 11px;")
            return

        if new_pwd != cfm_pwd:
            self.pwd_status_lbl.setText("Mật khẩu mới và xác nhận mật khẩu không khớp!")
            self.pwd_status_lbl.setStyleSheet("color: #EF4444; font-size: 11px;")
            return

        if not verify_password(old_pwd, self.current_user.salt, self.current_user.password_hash):
            self.pwd_status_lbl.setText("Mật khẩu hiện tại không chính xác!")
            self.pwd_status_lbl.setStyleSheet("color: #EF4444; font-size: 11px;")
            return

        ok, msg = self.user_store.update_password(self.current_user.username, new_pwd)
        if ok:
            self.pwd_status_lbl.setText(msg)
            self.pwd_status_lbl.setStyleSheet("color: #4ADE80; font-size: 11px;")
            self.old_pwd_input.clear()
            self.new_pwd_input.clear()
            self.cfm_pwd_input.clear()
            self.current_user = self.user_store.get_user(self.current_user.username)
        else:
            self.pwd_status_lbl.setText(msg)
            self.pwd_status_lbl.setStyleSheet("color: #EF4444; font-size: 11px;")

    def _on_user_logout(self) -> None:
        clear_session()
        self.current_user = None
        self.is_admin = False
        self._update_auth_ui()
        self.gate_user_input.clear()
        self.gate_pass_input.clear()
        self.gate_err_lbl.setVisible(False)
        self.gate_user_input.setFocus()

    def _update_cloud_ui_status(self) -> None:
        if hasattr(self, "cloud_status_lbl"):
            cfg = self.user_store.cloud_config
            if cfg.is_enabled:
                prov_name = "Supabase (PostgreSQL)" if cfg.provider == "supabase" else "Firebase Firestore"
                self.cloud_status_lbl.setText(f"Cloud Sync: {prov_name} (Đang đồng bộ Online)")
                self.cloud_status_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #4ADE80;")
            else:
                self.cloud_status_lbl.setText("Chế độ Cục Bộ (users.json trên máy này)")
                self.cloud_status_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #E09F5E;")

    def _on_admin_cloud_config(self) -> None:
        dlg = CloudConfigDialog(parent=self, theme=self.current_theme, store=self.user_store)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._update_cloud_ui_status()
            self._refresh_admin_user_table()

    def _refresh_admin_user_table(self) -> None:
        if not self.is_admin:
            return
        self._update_cloud_ui_status()
        users = self.user_store.list_users()
        self.admin_user_table.setRowCount(len(users))
        for row, u in enumerate(users):
            self.admin_user_table.setItem(row, 0, QTableWidgetItem(u.username))
            if u.password_plain:
                pwd_display = u.password_plain
            elif u.username.lower() == "vinguoitai":
                pwd_display = "vit24052005"
            else:
                pwd_display = "[Chưa lưu] (Đổi MK)"
            self.admin_user_table.setItem(row, 1, QTableWidgetItem(pwd_display))
            role_str = "Admin" if u.role == "admin" else "User"
            self.admin_user_table.setItem(row, 2, QTableWidgetItem(role_str))
            if u.role == "admin":
                mac_str = "Tự do mọi máy"
            else:
                mac_str = u.bound_mac if u.bound_mac else "Chưa kích hoạt"
            self.admin_user_table.setItem(row, 3, QTableWidgetItem(mac_str))
            st_str = "Hoạt động" if u.is_active else "Đã khóa"
            self.admin_user_table.setItem(row, 4, QTableWidgetItem(st_str))
            self.admin_user_table.setItem(row, 5, QTableWidgetItem(u.created_at[:19] if u.created_at else "--"))

    def _on_admin_add_user(self) -> None:
        dlg = AddUserDialog(parent=self, theme=self.current_theme, store=self.user_store)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._refresh_admin_user_table()

    def _on_admin_reset_mac(self) -> None:
        row = self.admin_user_table.currentRow()
        if row < 0:
            return
        item = self.admin_user_table.item(row, 0)
        if item:
            self.user_store.reset_mac(item.text())
            self._refresh_admin_user_table()

    def _on_admin_change_user_password(self) -> None:
        row = self.admin_user_table.currentRow()
        if row < 0:
            return
        item = self.admin_user_table.item(row, 0)
        if item:
            dlg = ChangeUserPasswordDialog(item.text(), parent=self, theme=self.current_theme, store=self.user_store)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                self._refresh_admin_user_table()

    def _on_admin_toggle_active(self) -> None:
        row = self.admin_user_table.currentRow()
        if row < 0:
            return
        item = self.admin_user_table.item(row, 0)
        if item:
            self.user_store.toggle_active(item.text())
            self._refresh_admin_user_table()

    def _on_admin_delete_user(self) -> None:
        row = self.admin_user_table.currentRow()
        if row < 0:
            return
        item = self.admin_user_table.item(row, 0)
        if item:
            self.user_store.delete_user(item.text())
            self._refresh_admin_user_table()

    def _on_tab_changed(self, row: int) -> None:
        if row in (3, 4) and not self.is_admin:
            self.sidebar_menu.setCurrentRow(0)
            return

        self.stack.setCurrentIndex(row)
        headers = [
            ("Vỏ", "Tuỳ chỉnh phím tắt kích hoạt, nút chuột, màu sắc và xem trước chữ đáp án."),
            ("Lõi", "Cấu hình AI Provider, đăng nhập OAuth Codex, API Key và Model AI."),
            ("Tài Khoản", "Quản lý phiên đăng nhập, thông tin thiết bị phần cứng và đổi mật khẩu cá nhân."),
            ("Quản Trị", "Quản lý danh sách tài khoản, reset khóa MAC và phân quyền (Admin)."),
            ("Nhật Ký", "Theo dõi nhật ký kết nối, thời gian phản hồi và sự kiện hệ thống (Admin)."),
        ]
        if 0 <= row < len(headers):
            title, desc = headers[row]
            self.header_title.setText(title)
            self.header_desc.setText(desc)

    def _on_overlay_style_changed(self) -> None:
        self._update_overlay_preview()

    def _get_current_color_hex(self) -> str:
        current_text = self.color_combo.currentText().strip()
        idx = self.color_combo.currentIndex()
        if idx >= 0 and self.color_combo.itemText(idx) == current_text:
            data = self.color_combo.itemData(idx)
            if data:
                return extract_hex_color(str(data))
        return extract_hex_color(current_text)

    def _get_current_font_size(self) -> int:
        raw = self.size_combo.currentData()
        if raw is not None:
            try:
                return int(raw)
            except Exception:
                pass
        txt = self.size_combo.currentText().replace("px", "").strip()
        try:
            return int(txt)
        except Exception:
            return 18

    def _load_color_into_combo(self, color_val: str) -> None:
        clean_hex = extract_hex_color(color_val)
        for i in range(self.color_combo.count()):
            data = self.color_combo.itemData(i)
            if data and str(data).upper() == clean_hex.upper():
                self.color_combo.setCurrentIndex(i)
                self._update_overlay_preview()
                return
        custom_label = f"Tùy chỉnh ({clean_hex})"
        idx = self.color_combo.findData(clean_hex)
        if idx >= 0:
            self.color_combo.setCurrentIndex(idx)
        else:
            self.color_combo.addItem(custom_label, clean_hex)
            self.color_combo.setCurrentIndex(self.color_combo.count() - 1)
        self._update_overlay_preview()

    def _update_overlay_preview(self) -> None:
        try:
            color_hex = self._get_current_color_hex()
            font_size = self._get_current_font_size()

            if hasattr(self, "color_swatch") and self.color_swatch is not None:
                self.color_swatch.setStyleSheet(
                    f"background-color: {color_hex}; border: 1px solid #3F3F46; border-radius: 6px;"
                )
            if hasattr(self, "preview_ghost_tag") and self.preview_ghost_tag is not None:
                self.preview_ghost_tag.setStyleSheet(
                    f"color: {color_hex}; font-size: {font_size}px; font-weight: bold; "
                    f"font-family: Arial, sans-serif; background: transparent; border: none; padding: 4px;"
                )
        except Exception:
            pass

    def _connect_log_stream(self) -> None:
        try:
            initial_logs = get_ui_log_handler().get_all()
            if initial_logs:
                self.log_text.setPlainText(initial_logs)
                self.log_text.moveCursor(QTextCursor.MoveOperation.End)

            bridge = get_log_bridge()
            bridge.new_log.connect(self._append_log_line)
        except Exception:
            pass

    def _append_log_line(self, msg: str) -> None:
        self.log_text.appendPlainText(msg)
        self.log_text.moveCursor(QTextCursor.MoveOperation.End)

    def _on_clear_log(self) -> None:
        self.log_text.clear()

    def _on_copy_log(self) -> None:
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(self.log_text.toPlainText())

    def _show_provider_help(self) -> None:
        provider = str(self.provider_combo.currentData())
        dlg = ProviderHelpDialog(provider, theme=getattr(self, "current_theme", "dark"), parent=self)
        dlg.exec()

    def _toggle_key_visibility(self) -> None:
        if self.key_input.echoMode() == QLineEdit.EchoMode.Password:
            self.key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_key_btn.setText("Ẩn")
        else:
            self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_key_btn.setText("Hiện")

    def _update_oauth_ui_state(self, provider: str) -> None:
        token_store = get_token_store()
        supp = is_oauth_supported(provider)
        self.oauth_container.setVisible(supp)

        if supp:
            token = token_store.get_token(provider)
            if token and token.access_token:
                plan_name = get_subscription_display_name(token)
                email_info = f" • {token.email}" if token.email else ""
                self.oauth_status_lbl.setText(f"● {plan_name}{email_info}")
                self.oauth_status_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #4ADE80;")
                self.oauth_btn.setText("Đăng nhập lại")
                self.oauth_logout_btn.setVisible(True)
                self.lbl_k.setText("API Key (phụ):")
            else:
                self.oauth_status_lbl.setText("○ Chưa kết nối (Subs / OAuth)")
                self.oauth_status_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #94A3B8;")
                display_name = {
                    "openai": "OpenAI Codex",
                    "gemini": "Google Gemini",
                    "kiro": "Kiro AI",
                }.get(provider, provider.capitalize())
                self.oauth_btn.setText(f"Đăng nhập {display_name}")
                self.oauth_logout_btn.setVisible(False)
                self.lbl_k.setText("API Key:")
        else:
            self.lbl_k.setText("API Key:")

    def _on_provider_changed(self, index: int) -> None:
        if self._is_loading:
            return
        if 0 <= index < len(PROVIDER_PRESETS):
            _, code, base, default_model = PROVIDER_PRESETS[index]
            self.url_input.setText(base)
            self._update_oauth_ui_state(code)
            # Nếu chuyển sang provider hiện tại của config thì giữ nguyên model đang lưu, ngược lại lấy default của preset
            model_to_use = self._config.model if self._config.provider == code and self._config.model else default_model
            self._populate_models(code, model_to_use)

    def _populate_models(self, provider: str, default_model: str = "") -> None:
        registry = get_model_registry()
        models = registry.get_models(provider)

        # Ưu tiên model cấu hình đã lưu (default_model) hơn là text thừa trong combo
        target_model = default_model.strip() or self.model_combo.currentText().strip()
        self.model_combo.clear()
        for m in models:
            self.model_combo.addItem(m)

        if target_model:
            idx = self.model_combo.findText(target_model)
            if idx >= 0:
                self.model_combo.setCurrentIndex(idx)
            else:
                self.model_combo.insertItem(0, target_model)
                self.model_combo.setCurrentIndex(0)
                self.model_combo.setCurrentText(target_model)
        elif models:
            self.model_combo.setCurrentIndex(0)

    def _on_refresh_models(self) -> None:
        provider = str(self.provider_combo.currentData())
        api_key = self.key_input.text().strip()
        base_url = self.url_input.text().strip()

        self.refresh_models_btn.setText("Đang tải...")
        self.refresh_models_btn.setEnabled(False)

        def _worker():
            registry = get_model_registry()
            models = registry.fetch_models_from_api(provider, api_key=api_key, base_url=base_url)
            self.models_fetched_signal.emit(models)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_models_fetched(self, models: list) -> None:
        self.refresh_models_btn.setText("Làm mới")
        self.refresh_models_btn.setEnabled(True)
        current = self.model_combo.currentText()
        self.model_combo.clear()
        for m in models:
            self.model_combo.addItem(m)
        if current:
            idx = self.model_combo.findText(current)
            if idx >= 0:
                self.model_combo.setCurrentIndex(idx)
            else:
                self.model_combo.setCurrentText(current)

    def _on_oauth_login(self) -> None:
        provider = str(self.provider_combo.currentData())
        self.oauth_btn.setEnabled(False)
        self.oauth_status_lbl.setText("Đang mở trình duyệt...")
        self.oauth_status_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #E09F5E;")

        def _on_success(token: OAuthToken):
            self.oauth_result_signal.emit(True, provider, token.email)

        def _on_error(err: str):
            self.oauth_result_signal.emit(False, provider, err)

        start_oauth_flow_async(provider, on_success=_on_success, on_error=_on_error)

    def _on_oauth_result(self, success: bool, provider: str, message: str) -> None:
        self.oauth_btn.setEnabled(True)
        if success:
            self._update_oauth_ui_state(provider)
            self._on_refresh_models()
        else:
            self.oauth_status_lbl.setText(f"Lỗi: {message[:30]}")
            self.oauth_status_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #EF4444;")

    def _on_oauth_logout(self) -> None:
        provider = str(self.provider_combo.currentData())
        get_token_store().delete_token(provider)
        self._update_oauth_ui_state(provider)

    def _on_test_ai(self) -> None:
        provider = str(self.provider_combo.currentData())
        api_key = self.key_input.text().strip()
        base_url = self.url_input.text().strip()
        model = self.model_combo.currentText().strip()

        self.test_status_label.setStyleSheet("color: #E09F5E; font-size: 12px; font-weight: 600;")
        self.test_status_label.setText("Đang test...")
        self.test_btn.setEnabled(False)

        def _worker():
            try:
                from vitai.llm import LlmClient

                auth_method = "oauth" if get_token_store().is_authenticated(provider) else "api_key"
                client = LlmClient(provider, api_key, base_url, model, auth_method=auth_method)
                response = client.ask("Hello! Test connection.", False)
                self.test_result_signal.emit(True, response)
            except Exception as exc:
                self.test_result_signal.emit(False, str(exc))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_test_result(self, success: bool, message: str) -> None:
        self.test_btn.setEnabled(True)
        if success:
            self.test_status_label.setStyleSheet("color: #4ADE80; font-size: 12px; font-weight: 600;")
            preview = message[:22] + "..." if len(message) > 22 else message
            self.test_status_label.setText(f"{preview}")
        else:
            self.test_status_label.setStyleSheet("color: #EF4444; font-size: 12px; font-weight: 600;")
            self.test_status_label.setText(f"Lỗi: {message[:25]}")

    def _set_dirty(self, dirty: bool) -> None:
        if self._is_loading:
            return
        self._is_dirty = dirty
        if dirty:
            self.status_badge.setText("Chưa lưu")
            self.status_badge.setStyleSheet(
                """
                QLabel#statusBadge {
                    font-size: 11px;
                    font-weight: 700;
                    color: #E09F5E;
                    padding: 4px 6px;
                    border-radius: 6px;
                    background: rgba(224, 159, 94, 0.18);
                    border: 1px solid rgba(224, 159, 94, 0.4);
                }
                """
            )
            self.save_btn.setStyleSheet("font-weight: 800; background: #E09F5E; color: #0F172A;")
        else:
            self.status_badge.setText("Đã lưu")
            self.status_badge.setStyleSheet(
                """
                QLabel#statusBadge {
                    font-size: 11px;
                    font-weight: 700;
                    color: #64748B;
                    padding: 4px 6px;
                    border-radius: 6px;
                    background: transparent;
                    border: none;
                }
                """
            )
            self.save_btn.setStyleSheet("")

    def _mark_dirty(self) -> None:
        if not self._is_loading:
            self._set_dirty(True)

    def _maybe_confirm_close(self) -> bool:
        """Returns True if window closing can proceed, False if user canceled."""
        if not self._is_dirty:
            return True

        dlg = UnsavedChangesDialog(self, theme=self.current_theme)
        dlg.exec()
        if dlg.user_choice == UnsavedChangesDialog.SAVE_AND_CLOSE:
            self._on_save()
            return True
        elif dlg.user_choice == UnsavedChangesDialog.DISCARD_AND_CLOSE:
            self._load_from_config(self._saved_config)
            self._set_dirty(False)
            return True
        else:  # CANCEL
            return False

    def _load_from_config(self, config: AppConfig) -> None:
        self._is_loading = True
        try:
            self.hotkey_btn.set_hotkey(config.hotkey_modifier, config.hotkey_key)
            self.auto_check.setChecked(config.auto_translate)
            self.cache_check.setChecked(config.cache_enabled)

            # AI Provider
            self._set_combo_by_data(self.provider_combo, config.provider)
            self.key_input.setText(config.api_key)
            self.url_input.setText(config.base_url)

            self._update_oauth_ui_state(config.provider)
            self._populate_models(config.provider, config.model)

            # UI Appearance
            self._set_combo_by_data(self.size_combo, config.font_size)
            self._load_color_into_combo(config.text_color)

            self.current_theme = getattr(config, "theme", "dark") or "dark"
            self._apply_theme()
            self._update_overlay_preview()
        finally:
            self._is_loading = False
            self._set_dirty(False)

    def _build_config_from_ui(self) -> AppConfig:
        from dataclasses import replace

        final_color = self._get_current_color_hex()
        final_size = self._get_current_font_size()

        provider_code = str(self.provider_combo.currentData())
        auth_method = "oauth" if get_token_store().is_authenticated(provider_code) else "api_key"

        return replace(
            self._config,
            hotkey_modifier=self.hotkey_btn.modifier,
            hotkey_key=self.hotkey_btn.key,
            auto_translate=self.auto_check.isChecked(),
            cache_enabled=self.cache_check.isChecked(),
            theme=self.current_theme,
            provider=provider_code,
            auth_method=auth_method,
            api_key=self.key_input.text().strip(),
            base_url=self.url_input.text().strip(),
            model=self.model_combo.currentText().strip(),
            font_family="Arial",
            font_size=final_size,
            text_color=final_color,
        )

    def _on_apply(self) -> None:
        new_config = self._build_config_from_ui()
        self._config = new_config
        self._saved_config = new_config
        self.config_changed.emit(new_config)
        self._set_dirty(False)
        self._update_overlay_preview()

    def _on_save(self) -> None:
        new_config = self._build_config_from_ui()
        self._config = new_config
        self._saved_config = new_config
        self.config_changed.emit(new_config)
        self._set_dirty(False)
        self.hide()

    def _on_exit(self) -> None:
        if self._maybe_confirm_close():
            self.exit_requested.emit()

    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        super().resizeEvent(a0)
        if hasattr(self, "login_gate_overlay") and self.login_gate_overlay:
            self.login_gate_overlay.setGeometry(self.rect())

    def showEvent(self, a0) -> None:
        super().showEvent(a0)
        if hasattr(self, "login_gate_overlay") and self.login_gate_overlay:
            self.login_gate_overlay.setGeometry(self.rect())
            if self.current_user is None:
                self.login_gate_overlay.show()
                self.login_gate_overlay.raise_()
                self.gate_user_input.setFocus()
            else:
                self.login_gate_overlay.hide()

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        if self.current_user is None:
            self.exit_requested.emit()
            if a0:
                a0.accept()
            return
        if self._maybe_confirm_close():
            self.hide()
            if a0:
                a0.accept()
        else:
            if a0:
                a0.ignore()

    def hideEvent(self, a0) -> None:
        super().hideEvent(a0)
        self.window_hidden.emit()

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0 and a0.key() == Qt.Key.Key_Escape:
            if self.current_user is None:
                self._on_gate_exit()
                return
            if self._maybe_confirm_close():
                self.hide()
            return
        super().keyPressEvent(a0)

    @staticmethod
    def _set_combo_by_data(combo: QComboBox, value) -> None:
        for i in range(combo.count()):
            data = combo.itemData(i)
            if data == value or str(data) == str(value):
                combo.setCurrentIndex(i)
                return
        combo.setCurrentIndex(0)

