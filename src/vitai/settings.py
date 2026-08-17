from __future__ import annotations

import threading
import time
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCloseEvent, QIcon, QKeyEvent, QMouseEvent, QPixmap, QTextCursor
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from vitai.auth_server import start_oauth_flow_async
from vitai.config import AppConfig
from vitai.model_registry import get_model_registry
from vitai.oauth_provider import get_subscription_display_name, is_oauth_supported
from vitai.proxy import get_local_proxy
from vitai.resources import resource_path
from vitai.token_store import OAuthToken, get_token_store
from vitai.ui_log import get_log_bridge, get_ui_log_handler


def get_stylesheet(theme: str = "dark") -> str:
    if theme == "light":
        return """
        QDialog {
            background-color: #F8FAFC;
            color: #0F172A;
            font-family: 'Segoe UI', system-ui, -apple-system, 'DejaVu Sans', sans-serif;
            font-size: 14px;
        }

        /* Sidebar */
        QFrame#sidebarFrame {
            background-color: #F1F5F9;
            border-right: 1px solid #E2E8F0;
        }

        QLabel#brandTitle {
            color: #0F172A;
            font-size: 16px;
            font-weight: 800;
        }

        QLabel#brandVer {
            color: #64748B;
            font-size: 11px;
            font-weight: 600;
        }

        QListWidget#sidebarMenu {
            background-color: transparent;
            border: none;
            outline: none;
            padding: 4px;
        }

        QListWidget#sidebarMenu::item {
            color: #334155;
            padding: 10px 12px;
            border-radius: 8px;
            margin-bottom: 5px;
            font-weight: 700;
            font-size: 15px;
        }

        QListWidget#sidebarMenu::item:hover {
            background-color: #E2E8F0;
            color: #0F172A;
        }

        QListWidget#sidebarMenu::item:selected {
            background-color: rgba(224, 159, 94, 0.18);
            color: #B45309;
            border-left: 3px solid #E09F5E;
            font-weight: 800;
        }

        /* Cards */
        QFrame#cardFrame {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 10px;
        }

        QLabel#cardTitle {
            color: #0F172A;
            font-weight: 700;
            font-size: 15px;
        }

        QLabel#cardDesc {
            color: #64748B;
            font-size: 13px;
        }

        QLabel#headerTitle {
            color: #0F172A;
            font-size: 20px;
            font-weight: 800;
        }

        QLabel#headerDesc {
            color: #64748B;
            font-size: 13px;
        }

        QLabel {
            color: #1E293B;
            font-size: 14px;
        }

        /* Inputs & Combos */
        QLineEdit, QComboBox {
            background-color: #F8FAFC;
            border: 1px solid #CBD5E1;
            border-radius: 8px;
            padding: 6px 12px;
            color: #0F172A;
            min-height: 28px;
            font-size: 14px;
        }

        QLineEdit:focus, QComboBox:focus, QComboBox:hover {
            border-color: #E09F5E;
        }

        QComboBox QAbstractItemView {
            background-color: #FFFFFF;
            color: #0F172A;
            border: 1px solid #CBD5E1;
            selection-background-color: rgba(224, 159, 94, 0.18);
            selection-color: #B45309;
            padding: 6px;
            outline: none;
        }

        /* Checkbox */
        QCheckBox {
            spacing: 8px;
            color: #1E293B;
            font-size: 14px;
            font-weight: 500;
        }

        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border-radius: 5px;
            border: 1px solid #CBD5E1;
            background-color: #F8FAFC;
        }

        QCheckBox::indicator:checked {
            background-color: #E09F5E;
            border-color: #E09F5E;
        }

        /* Buttons */
        QPushButton {
            background-color: #F1F5F9;
            border: 1px solid #CBD5E1;
            border-radius: 8px;
            padding: 7px 14px;
            color: #0F172A;
            font-weight: 600;
            font-size: 13px;
        }

        QPushButton:hover {
            background-color: #E2E8F0;
            border-color: #94A3B8;
        }

        QPushButton#themeToggleBtn {
            background-color: #FFFFFF;
            border: 1px solid #CBD5E1;
            border-radius: 8px;
            color: #0F172A;
            font-size: 16px;
            padding: 2px;
        }
        QPushButton#themeToggleBtn:hover {
            background-color: #F1F5F9;
            border-color: #E09F5E;
        }

        QPushButton#saveButton {
            background-color: #E09F5E;
            color: #0F172A;
            border: none;
            border-radius: 8px;
            font-weight: 800;
            font-size: 14px;
            padding: 9px 18px;
        }
        QPushButton#saveButton:hover {
            background-color: #ECAB6D;
        }

        QPushButton#applyButton {
            background-color: #F1F5F9;
            color: #B45309;
            border: 1px solid #CBD5E1;
            border-radius: 8px;
            padding: 7px 14px;
            font-weight: 600;
            font-size: 13px;
        }
        QPushButton#applyButton:hover {
            background-color: #E2E8F0;
            border-color: #E09F5E;
        }

        QPushButton#exitButton {
            background-color: transparent;
            color: #DC2626;
            border: 1px solid #FECACA;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            padding: 6px 12px;
        }
        QPushButton#exitButton:hover {
            background-color: #FEE2E2;
            color: #B91C1C;
        }

        QPushButton#oauthButton {
            background-color: rgba(224, 159, 94, 0.14);
            color: #B45309;
            border: 1px solid #E09F5E;
            font-size: 13px;
            font-weight: 700;
            border-radius: 8px;
            padding: 7px 14px;
        }
        QPushButton#oauthButton:hover {
            background-color: #E09F5E;
            color: #0F172A;
        }

        QPushButton#logoutButton {
            background-color: #FEF2F2;
            color: #DC2626;
            border: 1px solid #FECACA;
            border-radius: 8px;
            font-size: 12px;
            padding: 6px 10px;
        }
        QPushButton#logoutButton:hover {
            background-color: #FEE2E2;
        }

        QPushButton#refreshButton {
            background-color: #F1F5F9;
            color: #B45309;
            border: 1px solid #CBD5E1;
            border-radius: 8px;
            font-size: 13px;
            font-weight: bold;
            padding: 6px 12px;
        }
        QPushButton#refreshButton:hover {
            background-color: #E2E8F0;
            border-color: #E09F5E;
        }

        QPushButton#hotkeyButton {
            background-color: #F1F5F9;
            color: #B45309;
            border: 1px solid #CBD5E1;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 700;
            padding: 8px 16px;
        }
        QPushButton#hotkeyButton:hover {
            background-color: #E2E8F0;
            border-color: #E09F5E;
        }

        QPushButton#testButton {
            background-color: rgba(16, 185, 129, 0.12);
            color: #059669;
            border: 1px solid #10B981;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            padding: 7px 14px;
        }
        QPushButton#testButton:hover {
            background-color: #059669;
            color: #FFFFFF;
        }

        QPushButton#helpButton {
            background-color: #F1F5F9;
            color: #4F46E5;
            border: 1px solid #CBD5E1;
            border-radius: 8px;
            font-size: 13px;
            padding: 7px 12px;
        }
        QPushButton#helpButton:hover {
            background-color: #EEF2FF;
            border-color: #6366F1;
        }

        /* Buttons and Elements */

        QPushButton#cardToolBtn {
            background-color: transparent;
            border: none;
            color: #64748B;
            font-size: 12px;
            padding: 2px;
            min-width: 18px;
        }
        QPushButton#cardToolBtn:hover {
            color: #B45309;
            background-color: rgba(224, 159, 94, 0.12);
            border-radius: 4px;
        }

        QPushButton#cardDelBtn {
            background-color: transparent;
            border: none;
            color: #EF4444;
            font-size: 12px;
            padding: 2px;
            min-width: 18px;
        }
        QPushButton#cardDelBtn:hover {
            color: #DC2626;
            background-color: rgba(239, 68, 68, 0.12);
            border-radius: 4px;
        }

        QPushButton#switchBtnOn {
            background-color: #E09F5E;
            color: #0F172A;
            border: 1px solid #E09F5E;
            border-radius: 10px;
            font-size: 11px;
            font-weight: 800;
            padding: 2px 8px;
            min-width: 38px;
        }
        QPushButton#switchBtnOff {
            background-color: #E2E8F0;
            color: #64748B;
            border: 1px solid #CBD5E1;
            border-radius: 10px;
            font-size: 11px;
            font-weight: 700;
            padding: 2px 8px;
            min-width: 38px;
        }

        QProgressBar {
            background-color: #E2E8F0;
            border: none;
            border-radius: 3px;
            max-height: 5px;
            min-height: 5px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #10B981;
            border-radius: 3px;
        }

        QScrollBar:vertical {
            background: transparent;
            width: 6px;
            margin: 0px;
        }
        QScrollBar::handle:vertical {
            background: #CBD5E1;
            border-radius: 3px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background: #94A3B8;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            background: none;
            height: 0px;
        }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
        }

        QPlainTextEdit#logView {
            background-color: #FFFFFF;
            color: #1E293B;
            font-family: 'Consolas', 'Fira Code', 'DejaVu Sans Mono', monospace;
            font-size: 12px;
            border: 1px solid #CBD5E1;
            border-radius: 8px;
            padding: 10px;
            line-height: 1.4;
        }
        """

    # Dark Theme (9Router Carbon & Warm Amber)
    return """
    QDialog {
        background-color: #0C0D0E;
        color: #F1F5F9;
        font-family: 'Segoe UI', system-ui, -apple-system, 'DejaVu Sans', sans-serif;
        font-size: 14px;
    }

    /* Left Sidebar */
    QFrame#sidebarFrame {
        background-color: #121316;
        border-right: 1px solid #1F2228;
    }

    QLabel#brandTitle {
        color: #F8FAFC;
        font-size: 16px;
        font-weight: 800;
    }

    QLabel#brandVer {
        color: #94A3B8;
        font-size: 11px;
        font-weight: 600;
    }

    QListWidget#sidebarMenu {
        background-color: transparent;
        border: none;
        outline: none;
        padding: 4px;
    }

    QListWidget#sidebarMenu::item {
        color: #94A3B8;
        padding: 10px 12px;
        border-radius: 8px;
        margin-bottom: 5px;
        font-weight: 700;
        font-size: 15px;
    }

    QListWidget#sidebarMenu::item:hover {
        background-color: #181A1F;
        color: #F8FAFC;
    }

    QListWidget#sidebarMenu::item:selected {
        background-color: rgba(224, 159, 94, 0.14);
        color: #E09F5E;
        border-left: 3px solid #E09F5E;
        font-weight: 800;
    }

    /* Card Panels */
    QFrame#cardFrame {
        background-color: #181A1F;
        border: 1px solid #23272F;
        border-radius: 10px;
    }

    QLabel#cardTitle {
        color: #F8FAFC;
        font-weight: 700;
        font-size: 15px;
    }

    QLabel#cardDesc {
        color: #94A3B8;
        font-size: 13px;
    }

    QLabel#headerTitle {
        color: #F8FAFC;
        font-size: 20px;
        font-weight: 800;
    }

    QLabel#headerDesc {
        color: #94A3B8;
        font-size: 13px;
    }

    QLabel {
        color: #E2E8F0;
        font-size: 14px;
    }

    /* Inputs and Combos */
    QLineEdit, QComboBox {
        background-color: #111215;
        border: 1px solid #242831;
        border-radius: 8px;
        padding: 6px 12px;
        color: #F1F5F9;
        min-height: 28px;
        font-size: 14px;
    }

    QLineEdit:focus, QComboBox:focus, QComboBox:hover {
        border-color: #E09F5E;
    }

    QComboBox QAbstractItemView {
        background-color: #181A1F;
        color: #F1F5F9;
        border: 1px solid #23272F;
        selection-background-color: rgba(224, 159, 94, 0.2);
        selection-color: #E09F5E;
        padding: 6px;
        outline: none;
    }

    /* Checkboxes / Switches */
    QCheckBox {
        spacing: 8px;
        color: #E2E8F0;
        font-size: 14px;
        font-weight: 500;
    }

    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border-radius: 5px;
        border: 1px solid #333842;
        background-color: #111215;
    }

    QCheckBox::indicator:checked {
        background-color: #E09F5E;
        border-color: #E09F5E;
    }

    /* Buttons */
    QPushButton {
        background-color: #1C1F26;
        border: 1px solid #282D38;
        border-radius: 8px;
        padding: 7px 14px;
        color: #E2E8F0;
        font-weight: 600;
        font-size: 13px;
    }

    QPushButton:hover {
        background-color: #252A34;
        border-color: #475569;
        color: #FFFFFF;
    }

    QPushButton#themeToggleBtn {
        background-color: #181A1F;
        border: 1px solid #23272F;
        border-radius: 8px;
        color: #E09F5E;
        font-size: 16px;
        padding: 2px;
    }
    QPushButton#themeToggleBtn:hover {
        background-color: #23272F;
        border-color: #E09F5E;
    }

    /* Primary Save Button */
    QPushButton#saveButton {
        background-color: #E09F5E;
        color: #0C0D0E;
        border: none;
        border-radius: 8px;
        font-weight: 800;
        font-size: 14px;
        padding: 9px 18px;
    }

    QPushButton#saveButton:hover {
        background-color: #ECAB6D;
    }

    /* Apply Button */
    QPushButton#applyButton {
        background-color: #1C1F26;
        color: #E09F5E;
        border: 1px solid #2D3340;
        border-radius: 8px;
        padding: 7px 14px;
        font-weight: 600;
        font-size: 13px;
    }

    QPushButton#applyButton:hover {
        background-color: #262C37;
        border-color: #E09F5E;
    }

    /* Exit Button */
    QPushButton#exitButton {
        background-color: transparent;
        color: #F87171;
        border: 1px solid #451A1A;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 600;
        padding: 6px 12px;
    }

    QPushButton#exitButton:hover {
        background-color: #451A1A;
        color: #FFFFFF;
    }

    /* OAuth Button */
    QPushButton#oauthButton {
        background-color: rgba(224, 159, 94, 0.14);
        color: #E09F5E;
        border: 1px solid #E09F5E;
        font-size: 13px;
        font-weight: 700;
        border-radius: 8px;
        padding: 7px 14px;
    }

    QPushButton#oauthButton:hover {
        background-color: #E09F5E;
        color: #0C0D0E;
    }

    QPushButton#logoutButton {
        background-color: #2A1820;
        color: #F87171;
        border: 1px solid #5C222E;
        border-radius: 8px;
        font-size: 12px;
        padding: 6px 10px;
    }

    QPushButton#logoutButton:hover {
        background-color: #5C222E;
        color: #FFFFFF;
    }

    QPushButton#refreshButton {
        background-color: #1C1F26;
        color: #E09F5E;
        border: 1px solid #282D38;
        border-radius: 8px;
        font-size: 13px;
        font-weight: bold;
        padding: 6px 12px;
    }

    QPushButton#refreshButton:hover {
        background-color: #252A34;
        border-color: #E09F5E;
    }

    QPushButton#hotkeyButton {
        background-color: #181A1F;
        color: #E09F5E;
        border: 1px solid #23272F;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 700;
        padding: 8px 16px;
    }

    QPushButton#hotkeyButton:hover {
        background-color: #23272F;
        border-color: #E09F5E;
    }

    QPushButton#testButton {
        background-color: rgba(34, 197, 94, 0.12);
        color: #4ADE80;
        border: 1px solid #22C55E;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 600;
        padding: 7px 14px;
    }

    QPushButton#testButton:hover {
        background-color: #22C55E;
        color: #0C0D0E;
    }

    QPushButton#helpButton {
        background-color: #1C1F26;
        color: #A5B4FC;
        border: 1px solid #282D38;
        border-radius: 8px;
        font-size: 13px;
        padding: 7px 12px;
    }

    QPushButton#helpButton:hover {
        background-color: #252A34;
        border-color: #6366F1;
    }

    /* Dark Mode Buttons and Elements */

    QPushButton#cardToolBtn {
        background-color: transparent;
        border: none;
        color: #94A3B8;
        font-size: 12px;
        padding: 2px;
        min-width: 18px;
    }
    QPushButton#cardToolBtn:hover {
        color: #E09F5E;
        background-color: rgba(224, 159, 94, 0.12);
        border-radius: 4px;
    }

    QPushButton#cardDelBtn {
        background-color: transparent;
        border: none;
        color: #EF4444;
        font-size: 12px;
        padding: 2px;
        min-width: 18px;
    }
    QPushButton#cardDelBtn:hover {
        color: #F87171;
        background-color: rgba(239, 68, 68, 0.12);
        border-radius: 4px;
    }

    QPushButton#switchBtnOn {
        background-color: #E09F5E;
        color: #0C0D0E;
        border: 1px solid #E09F5E;
        border-radius: 10px;
        font-size: 11px;
        font-weight: 800;
        padding: 2px 8px;
        min-width: 38px;
    }
    QPushButton#switchBtnOff {
        background-color: #23272F;
        color: #94A3B8;
        border: 1px solid #333842;
        border-radius: 10px;
        font-size: 11px;
        font-weight: 700;
        padding: 2px 8px;
        min-width: 38px;
    }

    QProgressBar {
        background-color: #23272F;
        border: none;
        border-radius: 3px;
        max-height: 5px;
        min-height: 5px;
        text-align: center;
    }
    QProgressBar::chunk {
        background-color: #22C55E;
        border-radius: 3px;
    }

    QScrollBar:vertical {
        background: transparent;
        width: 6px;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background: #2D3340;
        border-radius: 3px;
        min-height: 20px;
    }
    QScrollBar::handle:vertical:hover {
        background: #475569;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        background: none;
        height: 0px;
    }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: none;
    }

    QPlainTextEdit#logView {
        background-color: #08090A;
        color: #CBD5E1;
        font-family: 'JetBrains Mono', 'Consolas', 'Fira Code', monospace;
        font-size: 12px;
        border: 1px solid #1F2228;
        border-radius: 8px;
        padding: 10px;
        line-height: 1.4;
    }
    """


PROVIDER_PRESETS = [
    ("OpenAI Codex (ChatGPT Plus/Pro Subs)", "openai", "https://chatgpt.com/backend-api/codex", "cx/gpt-5.5"),
    ("Google Gemini (Google OAuth / Key)", "gemini", "https://generativelanguage.googleapis.com/v1beta", "gemini-2.5-flash"),
    ("Kiro AI (OAuth / AWS)", "kiro", "https://app.kiro.ai/v1", "kr/claude-sonnet-4.5"),
    ("9Router (Local Proxy :20128)", "9router", "http://localhost:20128/v1", "High"),
    ("OpenRouter (Miễn phí & Đa mô hình)", "openrouter", "https://openrouter.ai/api/v1", "google/gemini-2.0-flash-exp:free"),
    ("Groq (Siêu tốc 500 T/s)", "groq", "https://api.groq.com/openai/v1", "llama-3.3-70b-versatile"),
    ("DeepSeek", "deepseek", "https://api.deepseek.com/v1", "deepseek-chat"),
]

PROVIDER_GUIDES = {
    "9router": {
        "title": "Hướng dẫn sử dụng 9Router",
        "content": """
        <h3 style="color: #E09F5E;">⚡ 9Router — Local Proxy</h3>
        <p><b>9Router</b> là proxy định tuyến AI chạy song song tại cổng <code>http://localhost:20128/v1</code>.</p>
        <p><b>Ưu điểm:</b> Tự động chọn model tối ưu và cân bằng tải.</p>
        """,
    },
    "openai": {
        "title": "Hướng dẫn OpenAI Codex (Subscription)",
        "content": """
        <h3 style="color: #E09F5E;">◈ OpenAI Codex (ChatGPT Plus / Pro / Free)</h3>
        <p><b>Cách 1 (Khuyên dùng):</b> Nhấn nút <b>Đăng nhập OpenAI Codex</b>. Đăng nhập tài khoản ChatGPT của bạn trên trình duyệt để sử dụng miễn phí gói Plus/Pro/Team mà không cần mua API Key!</p>
        <p><b>Cách 2:</b> Nhập API Key thủ công từ <a style="color: #E09F5E;" href="https://platform.openai.com/api-keys">platform.openai.com</a> vào ô API Key fallback.</p>
        """,
    },
    "gemini": {
        "title": "Hướng dẫn Xác thực Google Gemini",
        "content": """
        <h3 style="color: #E09F5E;">◈ Google Gemini AI</h3>
        <p><b>Cách 1:</b> Nhấn nút <b>Đăng nhập Google</b> để authorize tài khoản Google của bạn.</p>
        <p><b>Cách 2:</b> Lấy API Key miễn phí từ <a style="color: #E09F5E;" href="https://aistudio.google.com/">Google AI Studio (aistudio.google.com)</a> và dán vào ô API Key.</p>
        """,
    },
    "kiro": {
        "title": "Hướng dẫn Kiro AI",
        "content": """
        <h3 style="color: #E09F5E;">◈ Kiro AI Authentication</h3>
        <p>Hỗ trợ đăng nhập nhanh qua tài khoản Kiro / AWS Builder ID. Nhấn <b>Đăng nhập Kiro AI</b> để kích hoạt phiên làm việc.</p>
        """,
    },
    "openrouter": {
        "title": "Hướng dẫn OpenRouter",
        "content": """
        <h3 style="color: #E09F5E;">◈ OpenRouter (Hỗ trợ nhiều Model Free)</h3>
        <p>Truy cập <a style="color: #E09F5E;" href="https://openrouter.ai/keys">OpenRouter Keys</a> để tạo key miễn phí.</p>
        <p>Các model có đuôi <code>:free</code> (như <code>google/gemini-2.0-flash-exp:free</code>, <code>deepseek/deepseek-r1:free</code>) có thể sử dụng hoàn toàn miễn phí!</p>
        """,
    },
    "groq": {
        "title": "Hướng dẫn Groq Cloud",
        "content": """
        <h3 style="color: #E09F5E;">◈ Groq Cloud API (~500 tokens/s)</h3>
        <p>Lấy key tại: <a style="color: #E09F5E;" href="https://console.groq.com/keys">Groq Console API Keys</a></p>
        """,
    },
    "deepseek": {
        "title": "Hướng dẫn DeepSeek",
        "content": """
        <h3 style="color: #E09F5E;">◈ DeepSeek Platform</h3>
        <p>Lấy key tại: <a style="color: #E09F5E;" href="https://platform.deepseek.com/api_keys">DeepSeek API Keys</a></p>
        """,
    },
}

SIZE_CHOICES = [
    ("12 px", 12),
    ("14 px", 14),
    ("16 px", 16),
    ("18 px", 18),
    ("20 px", 20),
    ("22 px", 22),
    ("24 px", 24),
    ("28 px", 28),
]

COLOR_CHOICES = [
    ("Warm Amber (#E09F5E)", "#E09F5E"),
    ("Warm Tan (#D2B48C)", "#D2B48C"),
    ("Pure White (#FFFFFF)", "#FFFFFF"),
    ("Light Gray (#E0E0E0)", "#E0E0E0"),
    ("Emerald Green (#4ADE80)", "#4ADE80"),
    ("Sky Blue (#38BDF8)", "#38BDF8"),
    ("Soft Yellow (#FDE047)", "#FDE047"),
    ("Vibrant Pink (#F472B6)", "#F472B6"),
]


import re


def extract_hex_color(text: str | None, default: str = "#E09F5E") -> str:
    if not text:
        return default
    text = text.strip()
    match = re.search(r"#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})", text)
    if match:
        return match.group(0).upper()
    for disp, code in COLOR_CHOICES:
        if text == disp or text == code or code.lower() in text.lower():
            return code
    return default





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
        self.setText(f"⌨  {disp}  (Nhấn để đổi)")

    def _start_recording(self) -> None:
        self.recording = True
        self.setText("● Bấm tổ hợp phím mới...")
        self.grabKeyboard()

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if not a0:
            return
        if not self.recording:
            super().keyPressEvent(a0)
            return

        key_code = a0.key()
        if key_code in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta):
            return

        modifiers = []
        if a0.modifiers() & Qt.KeyboardModifier.ControlModifier:
            modifiers.append("ctrl")
        if a0.modifiers() & Qt.KeyboardModifier.AltModifier:
            modifiers.append("alt")
        if a0.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            modifiers.append("shift")

        if not modifiers:
            modifiers.append("alt")

        text = a0.text().lower()
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


class AdminLoginDialog(QDialog):
    def __init__(self, parent=None, theme: str = "dark"):
        super().__init__(parent)
        self.setWindowTitle("Xác thực Quản Trị Viên")
        self.setFixedSize(380, 260)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.theme = theme
        self.setStyleSheet(get_stylesheet(theme))
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title_lbl = QLabel("Khóa Quản Trị Viên")
        title_lbl.setStyleSheet(
            "font-size: 16px; font-weight: 800; color: " + ("#F1F5F9" if self.theme == "dark" else "#0F172A") + ";"
        )
        layout.addWidget(title_lbl)

        desc_lbl = QLabel("Nhập tài khoản và mật khẩu admin để mở khóa thẻ Nhật Ký:")
        desc_lbl.setStyleSheet("font-size: 12px; color: #94A3B8;")
        desc_lbl.setWordWrap(True)
        layout.addWidget(desc_lbl)

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Tên tài khoản admin...")
        layout.addWidget(self.user_input)

        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Mật khẩu...")
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.returnPressed.connect(self._on_submit)
        layout.addWidget(self.pass_input)

        self.err_lbl = QLabel("")
        self.err_lbl.setStyleSheet("color: #EF4444; font-size: 11px; font-weight: 600;")
        self.err_lbl.setVisible(False)
        layout.addWidget(self.err_lbl)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.cancel_btn = QPushButton("Hủy")
        self.cancel_btn.setObjectName("helpButton")
        self.cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.cancel_btn)

        self.login_btn = QPushButton("Mở khóa")
        self.login_btn.setObjectName("saveButton")
        self.login_btn.clicked.connect(self._on_submit)
        btn_row.addWidget(self.login_btn)

        layout.addLayout(btn_row)

    def _on_submit(self) -> None:
        user = self.user_input.text().strip()
        pwd = self.pass_input.text().strip()
        if user == "vinguoitai" and pwd == "vit24052005":
            self.accept()
        else:
            self.err_lbl.setText("⚠️ Sai tài khoản hoặc mật khẩu Quản Trị Viên!")
            self.err_lbl.setVisible(True)
            self.pass_input.clear()
            self.pass_input.setFocus()


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

        title_lbl = QLabel("⚠️ Thay đổi chưa được lưu")
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


class SettingsWindow(QDialog):
    config_changed = pyqtSignal(AppConfig)
    exit_requested = pyqtSignal()
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
        self.is_admin = False
        self._logo_click_times: list[float] = []

        self.setWindowTitle("Vì Người Tài")
        try:
            self.setWindowIcon(QIcon(str(resource_path("assets/icon.ico"))))
        except Exception:
            pass
        self.resize(740, 530)
        self.setMinimumSize(700, 480)
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
        # 1. LEFT SIDEBAR (Width: 140px)
        # ==========================================
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("sidebarFrame")
        sidebar_frame.setFixedWidth(140)
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(10, 14, 10, 14)
        sidebar_layout.setSpacing(8)

        # Brand / Logo Header (Click 3 times consecutively to unlock Admin tab)
        self.brand_widget = QWidget()
        self.brand_widget.setCursor(Qt.CursorShape.PointingHandCursor)
        self.brand_widget.setToolTip("Nhấn 3 lần để mở khóa Nhật Ký (Admin)")
        self.brand_widget.mousePressEvent = self._on_brand_clicked
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
        brand_ver = QLabel("v3.0.0 • AI")
        brand_ver.setObjectName("brandVer")
        brand_text_layout.addWidget(brand_title)
        brand_text_layout.addWidget(brand_ver)
        brand_layout.addLayout(brand_text_layout)
        brand_layout.addStretch()

        sidebar_layout.addWidget(self.brand_widget)
        sidebar_layout.addSpacing(6)

        # Sidebar Menu with 3 Tabs:
        # Tab 0: Vỏ, Tab 1: Lõi, Tab 2: Nhật Ký (Admin only)
        self.sidebar_menu = QListWidget()
        self.sidebar_menu.setObjectName("sidebarMenu")

        menu_items = [
            ("Vỏ", "Cấu hình phím tắt, chế độ làm việc và xem trước hiển thị"),
            ("Lõi", "Cấu hình AI Provider, Model, Xác thực và API Key"),
            ("Nhật Ký", "Nhật ký hoạt động và kết nối hệ thống (Quyền Admin)"),
        ]
        for title, tooltip in menu_items:
            item = QListWidgetItem(title)
            item.setToolTip(tooltip)
            self.sidebar_menu.addItem(item)

        # Nhật Ký tab is hidden by default until 3 logo clicks + admin login
        log_menu_item = self.sidebar_menu.item(2)
        if log_menu_item is not None:
            log_menu_item.setHidden(True)

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
        lbl_hk_desc = QLabel("Bôi đen câu hỏi và nhấn phím tắt:")
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

        self.auto_check = QCheckBox("⚡ Fast Mode (Tự động khi bôi đen)")
        self.cache_check = QCheckBox("💾 Cache Saver (Lưu phản hồi 0ms)")
        m_layout.addWidget(self.auto_check)
        m_layout.addWidget(self.cache_check)
        hk_mode_row.addWidget(card_modes, 1)

        page_shell_layout.addLayout(hk_mode_row)

        # Card 2: Overlay Appearance (With Color Swatch)
        card_overlay = QFrame()
        card_overlay.setObjectName("cardFrame")
        ov_layout = QVBoxLayout(card_overlay)
        ov_layout.setContentsMargins(14, 12, 14, 12)
        ov_layout.setSpacing(8)

        lbl_ov_title = QLabel("Cửa sổ phản hồi (Ghost Overlay Style)")
        lbl_ov_title.setObjectName("cardTitle")
        lbl_ov_desc = QLabel("Tùy chỉnh cỡ chữ và bảng màu hiển thị cho đáp án:")
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

        # Color Swatch Indicator (30x30 box)
        self.color_swatch = QLabel()
        self.color_swatch.setFixedSize(30, 30)
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
        lbl_prev_title = QLabel("👁️ Xem trước (Ghost Overlay)")
        lbl_prev_title.setObjectName("cardTitle")
        prev_title_row.addWidget(lbl_prev_title)
        prev_title_row.addStretch()

        live_badge = QLabel("● Xem trước")
        live_badge.setStyleSheet(
            "color: #4ADE80; font-size: 11px; font-weight: 700; "
            "background-color: rgba(34, 197, 94, 0.12); padding: 3px 8px; border-radius: 6px;"
        )
        prev_title_row.addWidget(live_badge)
        prev_layout.addLayout(prev_title_row)

        lbl_prev_desc = QLabel("Mô phỏng chữ cái đáp án hiển thị:")
        lbl_prev_desc.setObjectName("cardDesc")
        prev_layout.addWidget(lbl_prev_desc)

        # Clean Centered Stage Box with ONLY the letter 'A'
        preview_stage = QFrame()
        preview_stage.setStyleSheet(
            "background-color: #08090B; border: 1px dashed #2E333D; border-radius: 8px; min-height: 85px;"
        )
        stage_layout = QVBoxLayout(preview_stage)
        stage_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stage_layout.setContentsMargins(16, 14, 16, 14)

        self.preview_ghost_tag = QLabel("A")
        self.preview_ghost_tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stage_layout.addWidget(self.preview_ghost_tag, 0, Qt.AlignmentFlag.AlignCenter)

        prev_layout.addWidget(preview_stage)
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
        # TAB 2: NHẬT KÝ (Activity Logs)
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

    def _on_tab_changed(self, row: int) -> None:
        if row == 2 and not self.is_admin:
            self.sidebar_menu.setCurrentRow(0)
            return

        self.stack.setCurrentIndex(row)
        headers = [
            ("Vỏ", "Tuỳ chỉnh phím tắt kích hoạt, chế độ làm việc và xem trước chữ đáp án."),
            ("Lõi", "Cấu hình AI Provider, đăng nhập OAuth Codex, API Key và Model AI."),
            ("Nhật Ký", "Theo dõi nhật ký kết nối, thời gian phản hồi và sự kiện hệ thống (Admin)."),
        ]
        if 0 <= row < len(headers):
            title, desc = headers[row]
            self.header_title.setText(title)
            self.header_desc.setText(desc)

    def _on_brand_clicked(self, a0: QMouseEvent | None) -> None:
        now = time.time()
        self._logo_click_times.append(now)
        self._logo_click_times = [t for t in self._logo_click_times if now - t <= 2.0]
        if len(self._logo_click_times) >= 3:
            self._logo_click_times.clear()
            self._handle_admin_unlock()

    def _handle_admin_unlock(self) -> None:
        if self.is_admin:
            item = self.sidebar_menu.item(2)
            if item:
                new_state = not item.isHidden()
                item.setHidden(new_state)
                if not new_state:
                    self.sidebar_menu.setCurrentRow(2)
        else:
            dlg = AdminLoginDialog(parent=self, theme=getattr(self, "current_theme", "dark"))
            if dlg.exec() == QDialog.DialogCode.Accepted:
                self.is_admin = True
                item = self.sidebar_menu.item(2)
                if item:
                    item.setHidden(False)
                    self.sidebar_menu.setCurrentRow(2)

    def _on_overlay_style_changed(self) -> None:
        self._update_overlay_preview()

    def _get_current_color_hex(self) -> str:
        idx = self.color_combo.currentIndex()
        if idx >= 0:
            data = self.color_combo.itemData(idx)
            if data:
                return extract_hex_color(str(data))
        return extract_hex_color(self.color_combo.currentText())

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
            if data == clean_hex:
                self.color_combo.setCurrentIndex(i)
                return
        self.color_combo.setCurrentText(clean_hex)

    def _update_overlay_preview(self) -> None:
        try:
            color_hex = self._get_current_color_hex()
            font_size = self._get_current_font_size()

            if hasattr(self, "color_swatch"):
                self.color_swatch.setStyleSheet(
                    f"background-color: {color_hex}; border: 1px solid #3F3F46; border-radius: 6px;"
                )
            if hasattr(self, "preview_ghost_tag"):
                self.preview_ghost_tag.setStyleSheet(
                    f"color: {color_hex}; font-size: {font_size}px; font-weight: bold; "
                    f"font-family: Arial, sans-serif; background: transparent; border: none; padding: 4px;"
                )
        except Exception:
            pass

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
        if 0 <= index < len(PROVIDER_PRESETS):
            _, code, base, default_model = PROVIDER_PRESETS[index]
            self.url_input.setText(base)
            self._update_oauth_ui_state(code)
            self._populate_models(code, default_model)

    def _populate_models(self, provider: str, default_model: str = "") -> None:
        registry = get_model_registry()
        models = registry.get_models(provider)

        current_val = self.model_combo.currentText().strip() or default_model
        self.model_combo.clear()
        for m in models:
            self.model_combo.addItem(m)

        if current_val:
            idx = self.model_combo.findText(current_val)
            if idx >= 0:
                self.model_combo.setCurrentIndex(idx)
            else:
                self.model_combo.setCurrentText(current_val)
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
            self.test_status_label.setText(f"● {preview}")
        else:
            self.test_status_label.setStyleSheet("color: #EF4444; font-size: 12px; font-weight: 600;")
            self.test_status_label.setText(f"✕ {message[:25]}")

    def _set_dirty(self, dirty: bool) -> None:
        if self._is_loading:
            return
        self._is_dirty = dirty
        if dirty:
            self.status_badge.setText("● Chưa lưu")
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
            self.status_badge.setText("✓ Đã lưu")
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

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        if self._maybe_confirm_close():
            self.hide()
            if a0:
                a0.accept()
        else:
            if a0:
                a0.ignore()

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0 and a0.key() == Qt.Key.Key_Escape:
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

