from __future__ import annotations

import threading
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QKeyEvent, QTextCursor
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from vitai.config import AppConfig
from vitai.resources import resource_path
from vitai.ui_log import get_log_bridge, get_ui_log_handler

SETTINGS_STYLESHEET = """
    QDialog {
        background-color: #121214;
        color: #E1E1E6;
        font-family: 'Segoe UI', sans-serif;
        font-size: 13px;
    }
    
    QTabWidget::pane {
        border: 1px solid #29292E;
        border-radius: 8px;
        background-color: #18181B;
        top: -1px;
    }
    
    QTabBar::tab {
        background-color: #121214;
        color: #A1A1AA;
        border: 1px solid #29292E;
        border-bottom: none;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        padding: 8px 20px;
        margin-right: 4px;
        font-weight: 600;
    }
    
    QTabBar::tab:selected {
        background-color: #18181B;
        color: #F4F4F5;
        border-bottom: 2px solid #6366F1;
    }
    
    QTabBar::tab:hover:!selected {
        background-color: #202024;
        color: #D4D4D8;
    }
    
    QGroupBox {
        border: 1px solid #27272A;
        border-radius: 8px;
        margin-top: 14px;
        padding: 14px 12px 12px 12px;
        font-weight: 600;
        font-size: 13px;
        color: #A1A1AA;
    }
    
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 12px;
        padding: 0 6px;
        background-color: #18181B;
    }
    
    QLabel {
        color: #E1E1E6;
        font-size: 13px;
    }
    
    QLineEdit, QComboBox {
        background-color: #202024;
        border: 1px solid #3F3F46;
        border-radius: 6px;
        padding: 5px 8px;
        color: #F4F4F5;
        min-height: 20px;
    }
    
    QComboBox QAbstractItemView {
        background-color: #18181B;
        color: #F4F4F5;
        border: 1px solid #3F3F46;
        selection-background-color: #4F46E5;
        selection-color: #FFFFFF;
        padding: 4px;
        outline: none;
    }
    
    QLineEdit:focus, QComboBox:focus, QComboBox:hover {
        border-color: #6366F1;
    }
    
    QCheckBox {
        spacing: 8px;
        color: #E1E1E6;
        font-size: 13px;
    }
    
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 1px solid #3F3F46;
        background-color: #202024;
    }
    
    QCheckBox::indicator:checked {
        background-color: #6366F1;
        border-color: #6366F1;
    }
    
    QPushButton {
        background-color: #27272A;
        border: 1px solid #3F3F46;
        border-radius: 6px;
        padding: 6px 14px;
        color: #F4F4F5;
        font-weight: 600;
        font-size: 13px;
    }
    
    QPushButton:hover {
        background-color: #3F3F46;
    }
    
    QPushButton#hotkeyButton {
        background-color: #1E1B4B;
        color: #A5B4FC;
        border: 1px solid #6366F1;
        font-size: 13px;
        font-weight: 700;
        padding: 6px 16px;
    }
    
    QPushButton#hotkeyButton:hover {
        background-color: #312E81;
        color: #FFFFFF;
    }

    QPushButton#helpButton {
        background-color: #312E81;
        color: #C7D2FE;
        border: 1px solid #4338CA;
    }
    
    QPushButton#helpButton:hover {
        background-color: #4338CA;
        color: #FFFFFF;
    }
    
    QPushButton#testButton {
        background-color: #1E293B;
        color: #38BDF8;
        border: 1px solid #0284C7;
    }
    
    QPushButton#testButton:hover {
        background-color: #0284C7;
        color: #FFFFFF;
    }

    QPushButton#applyButton {
        background-color: #27272A;
        color: #E1E1E6;
        border: 1px solid #52525B;
    }
    
    QPushButton#applyButton:hover {
        background-color: #3F3F46;
        color: #FFFFFF;
    }
    
    QPushButton#saveButton {
        background-color: #4F46E5;
        color: #FFFFFF;
        border: none;
    }
    
    QPushButton#saveButton:hover {
        background-color: #4338CA;
    }
    
    QPushButton#exitButton {
        background-color: #DC2626;
        color: #FFFFFF;
        border: none;
    }
    
    QPushButton#exitButton:hover {
        background-color: #B91C1C;
    }

    QPlainTextEdit#logView {
        background-color: #0D1117;
        color: #C9D1D9;
        font-family: 'Consolas', 'Fira Code', 'JetBrains Mono', 'Courier New', monospace;
        font-size: 12px;
        border: 1px solid #30363D;
        border-radius: 6px;
        padding: 8px;
        line-height: 1.4;
    }
"""

PROVIDER_PRESETS = [
    ("9Router (Free Proxy)", "9router", "https://9router.com/v1", "gemini-2.5-flash"),
    ("Gemini (Google AI)", "gemini", "https://generativelanguage.googleapis.com/v1beta", "gemini-2.5-flash"),
    ("Groq (Siêu tốc)", "groq", "https://api.groq.com/openai/v1", "llama-3.3-70b-versatile"),
    ("Mistral AI", "mistral", "https://api.mistral.ai/v1", "mistral-small-latest"),
    ("Cerebras (Cực nhanh)", "cerebras", "https://api.cerebras.ai/v1", "llama3.1-70b"),
    ("OpenRouter (Đa dạng)", "openrouter", "https://openrouter.ai/api/v1", "google/gemini-2.5-flash-001"),
    ("OpenAI", "openai", "https://api.openai.com/v1", "gpt-4o-mini"),
    ("Anthropic", "anthropic", "https://api.anthropic.com/v1", "claude-3-5-haiku-20241022"),
    ("DeepSeek", "deepseek", "https://api.deepseek.com/v1", "deepseek-chat"),
]

PROVIDER_GUIDES = {
    "9router": {
        "title": "Hướng dẫn sử dụng 9Router",
        "content": """
        <h3 style="color: #6366F1;">🚀 9Router — AI Proxy Miễn Phí</h3>
        <p><b>9Router</b> là dịch vụ Proxy AI miễn phí được tích hợp sẵn trong ViTai.</p>
        <p><b>Ưu điểm:</b> Bạn không cần tạo tài khoản hay dán API Key cá nhân nào!</p>
        <p><b>Cách thiết lập:</b> Giữ nguyên cấu hình và nhấn <b>Lưu</b> để sử dụng ngay lập tức.</p>
        """
    },
    "gemini": {
        "title": "Hướng dẫn lấy API Key Google Gemini",
        "content": """
        <h3 style="color: #6366F1;">✨ Google Gemini API (Miễn phí 15 requests/phút)</h3>
        <ol style="line-height: 1.6;">
            <li>Truy cập trang web: <a style="color: #38BDF8;" href="https://aistudio.google.com/">Google AI Studio (aistudio.google.com)</a></li>
            <li>Đăng nhập tài khoản Google của bạn.</li>
            <li>Nhấn nút <b>Get API key</b> và chọn <b>Create API key</b>.</li>
            <li>Sao chép (Copy) mã API Key được tạo.</li>
            <li>Dán mã vào ô <b>API Key</b> trong ViTai và nhấn <b>Test</b>.</li>
        </ol>
        """
    },
    "groq": {
        "title": "Hướng dẫn lấy API Key Groq Cloud",
        "content": """
        <h3 style="color: #6366F1;">⚡ Groq Cloud API (~500 tokens/giây)</h3>
        <ol style="line-height: 1.6;">
            <li>Truy cập trang: <a style="color: #38BDF8;" href="https://console.groq.com/keys">Groq Console API Keys</a></li>
            <li>Đăng ký/Đăng nhập tài khoản miễn phí.</li>
            <li>Nhấn <b>Create API Key</b>, sao chép chuỗi mã Key.</li>
            <li>Dán vào ô <b>API Key</b> trong ViTai.</li>
        </ol>
        """
    },
    "mistral": {
        "title": "Hướng dẫn lấy API Key Mistral AI",
        "content": """
        <h3 style="color: #6366F1;">🌪️ Mistral AI Console</h3>
        <ol style="line-height: 1.6;">
            <li>Truy cập: <a style="color: #38BDF8;" href="https://console.mistral.ai/api-keys/">Mistral AI Console Keys</a></li>
            <li>Tạo tài khoản và vào mục <b>API Keys</b>.</li>
            <li>Tạo mã key mới và dán vào ô <b>API Key</b> trong ViTai.</li>
        </ol>
        """
    },
    "cerebras": {
        "title": "Hướng dẫn lấy API Key Cerebras AI",
        "content": """
        <h3 style="color: #6366F1;">🧠 Cerebras Developer Cloud</h3>
        <ol style="line-height: 1.6;">
            <li>Truy cập: <a style="color: #38BDF8;" href="https://cloud.cerebras.ai/">Cerebras Cloud Console</a></li>
            <li>Tạo tài khoản và cấp API Key cá nhân.</li>
            <li>Dán mã Key vào ô <b>API Key</b> trong ViTai.</li>
        </ol>
        """
    },
    "openrouter": {
        "title": "Hướng dẫn lấy API Key OpenRouter",
        "content": """
        <h3 style="color: #6366F1;">🌐 OpenRouter (Đa dạng các mô hình AI)</h3>
        <ol style="line-height: 1.6;">
            <li>Truy cập: <a style="color: #38BDF8;" href="https://openrouter.ai/keys">OpenRouter Keys Page</a></li>
            <li>Tạo tài khoản và tạo API Key.</li>
            <li>Dán API Key vào ViTai. Hỗ trợ hàng chục mô hình AI từ miễn phí đến trả phí.</li>
        </ol>
        """
    },
    "openai": {
        "title": "Hướng dẫn lấy API Key OpenAI (ChatGPT)",
        "content": """
        <h3 style="color: #6366F1;">🤖 OpenAI API</h3>
        <ol style="line-height: 1.6;">
            <li>Truy cập: <a style="color: #38BDF8;" href="https://platform.openai.com/api-keys">OpenAI Platform Keys</a></li>
            <li>Đăng nhập tài khoản OpenAI.</li>
            <li>Nhấn <b>Create new secret key</b> và sao chép mã Key.</li>
            <li>Dán vào ô <b>API Key</b> trong ViTai.</li>
        </ol>
        """
    },
    "anthropic": {
        "title": "Hướng dẫn lấy API Key Anthropic (Claude)",
        "content": """
        <h3 style="color: #6366F1;">🎭 Anthropic Claude API</h3>
        <ol style="line-height: 1.6;">
            <li>Truy cập: <a style="color: #38BDF8;" href="https://console.anthropic.com/settings/keys">Anthropic Console Settings</a></li>
            <li>Tạo API Key mới trong mục <b>API Keys</b>.</li>
            <li>Copy API Key và dán vào ô <b>API Key</b> trong ViTai.</li>
        </ol>
        """
    },
    "deepseek": {
        "title": "Hướng dẫn lấy API Key DeepSeek",
        "content": """
        <h3 style="color: #6366F1;">🐳 DeepSeek API Platform</h3>
        <ol style="line-height: 1.6;">
            <li>Truy cập: <a style="color: #38BDF8;" href="https://platform.deepseek.com/api_keys">DeepSeek Platform API Keys</a></li>
            <li>Tạo tài khoản và cấp mã API Key mới.</li>
            <li>Dán vào ô <b>API Key</b> trong ViTai.</li>
        </ol>
        """
    },
}

SIZE_CHOICES = [
    ("12 px", 12),
    ("14 px", 14),
    ("16 px", 16),
    ("18 px", 18),
    ("20 px", 20),
    ("24 px", 24),
]

COLOR_CHOICES = [
    ("Light Gray (#E0E0E0)", "#E0E0E0"),
    ("Pure White (#FFFFFF)", "#FFFFFF"),
    ("Soft Green (#A7F3D0)", "#A7F3D0"),
    ("Soft Blue (#93C5FD)", "#93C5FD"),
    ("Soft Yellow (#FDE047)", "#FDE047"),
]


class HotkeyInputButton(QPushButton):
    hotkey_changed = pyqtSignal(str, str)

    def __init__(self, modifier: str = "alt", key: str = "q", parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("hotkeyButton")
        self.modifier = modifier
        self.key = key
        self.recording = False
        self._update_text()
        self.clicked.connect(self._start_recording)

    def set_hotkey(self, modifier: str, key: str) -> None:
        self.modifier = modifier
        self.key = key
        self._update_text()

    def _update_text(self) -> None:
        parts = self.modifier.split("+")
        disp = "+".join(p.capitalize() for p in parts) + f"+{self.key.upper()}"
        self.setText(f"⌨️ {disp}  (Nhấn để đổi)")

    def _start_recording(self) -> None:
        self.recording = True
        self.setText("🔴 Bấm tổ hợp phím mới...")
        self.grabKeyboard()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if not self.recording:
            super().keyPressEvent(event)
            return

        key_code = event.key()
        if key_code in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta):
            return

        modifiers = []
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            modifiers.append("ctrl")
        if event.modifiers() & Qt.KeyboardModifier.AltModifier:
            modifiers.append("alt")
        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            modifiers.append("shift")

        if not modifiers:
            modifiers.append("alt")

        text = event.text().lower()
        if text and text.isalpha():
            key_char = text
        else:
            if 65 <= key_code <= 90:
                key_char = chr(key_code).lower()
            else:
                key_char = "q"

        self.modifier = "+".join(modifiers)
        self.key = key_char
        self.recording = False
        self.releaseKeyboard()
        self._update_text()
        self.hotkey_changed.emit(self.modifier, self.key)


class ProviderHelpDialog(QDialog):
    def __init__(self, provider_code: str, parent: QWidget | None = None):
        super().__init__(parent)
        guide = PROVIDER_GUIDES.get(provider_code, PROVIDER_GUIDES["gemini"])
        self.setWindowTitle(guide["title"])
        self.setFixedSize(420, 300)
        self.setStyleSheet(SETTINGS_STYLESHEET)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        content_label = QLabel(guide["content"])
        content_label.setWordWrap(True)
        content_label.setOpenExternalLinks(True)
        content_label.setStyleSheet("font-size: 13px; line-height: 1.5; color: #E1E1E6;")
        layout.addWidget(content_label, 1)

        close_btn = QPushButton("Đóng Hướng Dẫn")
        close_btn.setObjectName("saveButton")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


class SettingsWindow(QDialog):
    config_changed = pyqtSignal(AppConfig)
    exit_requested = pyqtSignal()
    test_result_signal = pyqtSignal(bool, str)

    def __init__(self, config: AppConfig, parent: QWidget | None = None):
        super().__init__(parent)
        self._config = config
        self.setWindowTitle("ViTai")
        try:
            self.setWindowIcon(QIcon(str(resource_path("assets/icon.ico"))))
        except Exception:
            pass
        self.setFixedSize(500, 460)
        self.setWindowFlags(
            Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowMinimizeButtonHint
        )
        self.setStyleSheet(SETTINGS_STYLESHEET)
        self.test_result_signal.connect(self._on_test_result)
        self._build_ui()
        self._load_from_config(config)
        self._connect_log_stream()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(14, 14, 14, 14)
        root_layout.setSpacing(10)

        self.tab_widget = QTabWidget()

        # --- Tab 1: Vỏ ---
        tab_vo = QWidget()
        vo_layout = QVBoxLayout(tab_vo)
        vo_layout.setContentsMargins(10, 10, 10, 10)
        vo_layout.setSpacing(10)

        # Hotkey Group
        hotkey_group = QGroupBox("Phím tắt kích hoạt")
        hk_layout = QHBoxLayout(hotkey_group)
        hk_layout.setContentsMargins(10, 10, 10, 10)
        
        self.hotkey_btn = HotkeyInputButton("alt", "q")
        hk_layout.addWidget(self.hotkey_btn)

        vo_layout.addWidget(hotkey_group)

        # Mode Group (2 columns in 1 row)
        mode_group = QGroupBox("Mode")
        m_layout = QHBoxLayout(mode_group)
        m_layout.setContentsMargins(10, 10, 10, 10)

        self.auto_check = QCheckBox("Fast Mode")
        m_layout.addWidget(self.auto_check)

        self.cache_check = QCheckBox("Cache Saver Mode")
        m_layout.addWidget(self.cache_check)

        vo_layout.addWidget(mode_group)

        # Overlay UI Group
        ui_group = QGroupBox("Giao diện Cửa sổ Phản hồi (Overlay)")
        u_layout = QHBoxLayout(ui_group)
        u_layout.setContentsMargins(10, 10, 10, 10)

        u_layout.addWidget(QLabel("Cỡ chữ:"))
        self.size_combo = QComboBox()
        for display, code in SIZE_CHOICES:
            self.size_combo.addItem(display, code)
        u_layout.addWidget(self.size_combo)

        u_layout.addWidget(QLabel("Màu:"))
        self.color_combo = QComboBox()
        self.color_combo.setEditable(True)
        for display, code in COLOR_CHOICES:
            self.color_combo.addItem(display, code)
        u_layout.addWidget(self.color_combo, 1)

        vo_layout.addWidget(ui_group)
        vo_layout.addStretch()

        self.tab_widget.addTab(tab_vo, "Vỏ")

        # --- Tab 2: Lõi ---
        tab_loi = QWidget()
        loi_layout = QVBoxLayout(tab_loi)
        loi_layout.setContentsMargins(10, 10, 10, 10)
        loi_layout.setSpacing(8)

        ai_group = QGroupBox("AI")
        p_layout = QVBoxLayout(ai_group)
        p_layout.setContentsMargins(10, 10, 10, 10)
        p_layout.setSpacing(8)

        LABEL_WIDTH = 85

        # Provider row
        p_row = QHBoxLayout()
        lbl_p = QLabel("Provider:")
        lbl_p.setFixedWidth(LABEL_WIDTH)
        p_row.addWidget(lbl_p)

        self.provider_combo = QComboBox()
        for display, code, base, model in PROVIDER_PRESETS:
            self.provider_combo.addItem(display, code)
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        p_row.addWidget(self.provider_combo, 1)
        p_layout.addLayout(p_row)

        # API Key row
        key_row = QHBoxLayout()
        lbl_k = QLabel("API Key:")
        lbl_k.setFixedWidth(LABEL_WIDTH)
        key_row.addWidget(lbl_k)

        self.key_input = QLineEdit()
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setPlaceholderText("Dán API Key tại đây...")
        key_row.addWidget(self.key_input, 1)

        self.toggle_key_btn = QPushButton("👁️")
        self.toggle_key_btn.setFixedWidth(34)
        self.toggle_key_btn.clicked.connect(self._toggle_key_visibility)
        key_row.addWidget(self.toggle_key_btn)
        p_layout.addLayout(key_row)

        # Base URL row
        url_row = QHBoxLayout()
        lbl_u = QLabel("Base URL:")
        lbl_u.setFixedWidth(LABEL_WIDTH)
        url_row.addWidget(lbl_u)

        self.url_input = QLineEdit()
        url_row.addWidget(self.url_input, 1)
        p_layout.addLayout(url_row)

        # Model Name row
        model_row = QHBoxLayout()
        lbl_m = QLabel("Model Name:")
        lbl_m.setFixedWidth(LABEL_WIDTH)
        model_row.addWidget(lbl_m)

        self.model_input = QLineEdit()
        model_row.addWidget(self.model_input, 1)
        p_layout.addLayout(model_row)

        # Test & Hướng dẫn Buttons on 1 row
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
        self.test_status_label.setStyleSheet("font-size: 11px; font-weight: 600;")
        action_row.addWidget(self.test_status_label, 1)

        p_layout.addLayout(action_row)

        loi_layout.addWidget(ai_group)
        loi_layout.addStretch()

        self.tab_widget.addTab(tab_loi, "Lõi")

        # --- Tab 3: Log ---
        tab_log = QWidget()
        log_layout = QVBoxLayout(tab_log)
        log_layout.setContentsMargins(10, 10, 10, 10)
        log_layout.setSpacing(8)

        self.log_text = QPlainTextEdit()
        self.log_text.setObjectName("logView")
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text, 1)

        log_btn_row = QHBoxLayout()
        self.clear_log_btn = QPushButton("Xóa Log")
        self.clear_log_btn.clicked.connect(self._on_clear_log)
        log_btn_row.addWidget(self.clear_log_btn)

        self.copy_log_btn = QPushButton("Sao Chép Log")
        self.copy_log_btn.clicked.connect(self._on_copy_log)
        log_btn_row.addWidget(self.copy_log_btn)

        log_btn_row.addStretch()
        log_layout.addLayout(log_btn_row)

        self.tab_widget.addTab(tab_log, "Log")

        root_layout.addWidget(self.tab_widget)

        # Buttons at bottom
        btn_row = QHBoxLayout()
        
        self.apply_btn = QPushButton("Áp dụng")
        self.apply_btn.setObjectName("applyButton")
        self.apply_btn.clicked.connect(self._on_apply)
        btn_row.addWidget(self.apply_btn)

        self.save_btn = QPushButton("Lưu")
        self.save_btn.setObjectName("saveButton")
        self.save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(self.save_btn)

        btn_row.addStretch()

        self.exit_btn = QPushButton("Thoát")
        self.exit_btn.setObjectName("exitButton")
        self.exit_btn.clicked.connect(self._on_exit)
        btn_row.addWidget(self.exit_btn)

        root_layout.addLayout(btn_row)

    def _connect_log_stream(self) -> None:
        initial_logs = get_ui_log_handler().get_all()
        if initial_logs:
            self.log_text.setPlainText(initial_logs)
            self.log_text.moveCursor(QTextCursor.MoveOperation.End)

        bridge = get_log_bridge()
        bridge.new_log.connect(self._append_log_line)

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
        provider_code = str(self.provider_combo.currentData())
        dialog = ProviderHelpDialog(provider_code, self)
        dialog.exec()

    def _toggle_key_visibility(self) -> None:
        if self.key_input.echoMode() == QLineEdit.EchoMode.Password:
            self.key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_key_btn.setText("🔒")
        else:
            self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_key_btn.setText("👁️")

    def _on_provider_changed(self, index: int) -> None:
        if 0 <= index < len(PROVIDER_PRESETS):
            _, code, base, model = PROVIDER_PRESETS[index]
            self.url_input.setText(base)
            self.model_input.setText(model)

    def _on_test_ai(self) -> None:
        provider = str(self.provider_combo.currentData())
        api_key = self.key_input.text().strip()
        base_url = self.url_input.text().strip()
        model = self.model_input.text().strip()

        self.test_status_label.setStyleSheet("color: #38BDF8; font-size: 11px; font-weight: 600;")
        self.test_status_label.setText("⏳ Đang test...")
        self.test_btn.setEnabled(False)

        def _worker():
            try:
                from vitai.llm import LlmClient
                client = LlmClient(provider, api_key, base_url, model)
                response = client.ask("Hello! Test connection.", False)
                self.test_result_signal.emit(True, response)
            except Exception as exc:
                self.test_result_signal.emit(False, str(exc))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_test_result(self, success: bool, message: str) -> None:
        self.test_btn.setEnabled(True)
        if success:
            self.test_status_label.setStyleSheet("color: #4ADE80; font-size: 11px; font-weight: 600;")
            preview = message[:20] + "..." if len(message) > 20 else message
            self.test_status_label.setText(f"✅ {preview}")
        else:
            self.test_status_label.setStyleSheet("color: #F87171; font-size: 11px; font-weight: 600;")
            self.test_status_label.setText(f"❌ Lỗi: {message[:25]}")

    def _load_from_config(self, config: AppConfig) -> None:
        self.hotkey_btn.set_hotkey(config.hotkey_modifier, config.hotkey_key)
        self.auto_check.setChecked(config.auto_translate)
        self.cache_check.setChecked(config.cache_enabled)

        # AI Provider
        self._set_combo_by_data(self.provider_combo, config.provider)
        self.key_input.setText(config.api_key)
        self.url_input.setText(config.base_url)
        self.model_input.setText(config.model)

        # UI
        self._set_combo_by_data(self.size_combo, config.font_size)
        self.color_combo.setCurrentText(config.text_color)

    def _build_config_from_ui(self) -> AppConfig:
        from dataclasses import replace

        color_text = self.color_combo.currentText().strip()
        matched_color = None
        for disp, code in COLOR_CHOICES:
            if color_text == disp or color_text == code:
                matched_color = code
                break
        final_color = matched_color if matched_color else color_text

        return replace(
            self._config,
            hotkey_modifier=self.hotkey_btn.modifier,
            hotkey_key=self.hotkey_btn.key,
            auto_translate=self.auto_check.isChecked(),
            cache_enabled=self.cache_check.isChecked(),
            provider=str(self.provider_combo.currentData()),
            api_key=self.key_input.text().strip(),
            base_url=self.url_input.text().strip(),
            model=self.model_input.text().strip(),
            font_family="Arial",
            font_size=int(self.size_combo.currentData()),
            text_color=final_color,
        )

    def _on_apply(self) -> None:
        new_config = self._build_config_from_ui()
        self._config = new_config
        self.config_changed.emit(new_config)

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
