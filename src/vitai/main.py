from __future__ import annotations

# pyright: reportMissingModuleSource=false

import ctypes
import logging
import os
import sys
import threading
import traceback
from dataclasses import replace
from pathlib import Path
from typing import Any

try:
    from pynput import mouse  # type: ignore
except Exception:
    mouse = None  # type: ignore
from PyQt6.QtCore import QEvent, QObject, pyqtSignal
from PyQt6.QtGui import QAction, QCursor, QIcon
from PyQt6.QtWidgets import QApplication, QInputDialog

from vitai.capture import get_selected_text
from vitai.config import AppConfig, default_config_path, load_config, save_config
from vitai.encoding import configure_utf8_stdio
from vitai.gnome_shortcuts import register_gnome_hotkey, register_gnome_menu_hotkey, unregister_gnome_hotkey
from vitai.hotkey import HotkeyManager
from vitai.ipc import IpcServer, send_trigger, send_menu_trigger
from vitai.logging_config import configure_logging
from vitai.mcq import is_mcq, normalize_mcq_answer
from vitai.mouse_tracker import (
    get_last_selection_end_pos,
    get_mouse_position,
    register_click_callback,
    start_mouse_tracker,
)
from vitai.overlay import AnswerOverlay
from vitai.resources import resource_path
from vitai.selection_watcher import SelectionWatcher
from vitai.settings import SettingsWindow
from vitai.startup import install_linux_desktop_file, set_startup
from vitai.ui_log import install_ui_logging

configure_utf8_stdio()


def _load_env_file(env_path: Path) -> None:
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv(dotenv_path=env_path)
    except Exception:
        if env_path.is_file():
            try:
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k and k not in os.environ:
                            os.environ[k] = v
            except Exception:
                pass


def set_windows_app_id() -> None:
    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ViTai.App")


class ViTaiQApplication(QApplication):
    reopen_requested = pyqtSignal()

    def event(self, a0: QEvent | None) -> bool:
        if a0 is not None and a0.type() in (QEvent.Type.ApplicationActivate, QEvent.Type.FileOpen):
            self.reopen_requested.emit()
        return super().event(a0) if a0 is not None else False


class UiBridge(QObject):
    hotkey_pressed = pyqtSignal()
    menu_hotkey_pressed = pyqtSignal()
    answer_ready = pyqtSignal(str)
    hide_overlay_if_outside_ready = pyqtSignal(int, int)
    show_settings_requested = pyqtSignal()


class ViTaiApp:
    def __init__(self):
        if getattr(sys, "frozen", False):
            base_dir = Path(sys.executable).parent
        else:
            base_dir = Path(os.getcwd())
        env_path = base_dir / ".env"
        _load_env_file(env_path)

        configure_logging()
        install_ui_logging()
        self.logger = logging.getLogger("vitai.main")
        self.logger.info("Vì Người Tài starting")
        self._install_exception_hooks()
        install_linux_desktop_file()

        self.config_path = default_config_path()
        self.config = self._load_config_with_env()
        set_windows_app_id()

        if sys.platform.startswith("linux") and "QT_QPA_PLATFORM" not in os.environ:
            os.environ["QT_QPA_PLATFORM"] = "xcb"

        existing_app = QApplication.instance()
        if existing_app is not None and isinstance(existing_app, QApplication):
            self.qt_app = existing_app
        else:
            self.qt_app = ViTaiQApplication(sys.argv)
        self.qt_app.setApplicationName("Vì Người Tài")
        self.qt_app.setApplicationDisplayName("Vì Người Tài")
        self.qt_app.setDesktopFileName("vitai")
        self.qt_app.setWindowIcon(QIcon(str(resource_path("assets/icon.ico"))))
        self.qt_app.setQuitOnLastWindowClosed(False)
        if isinstance(self.qt_app, ViTaiQApplication):
            self.qt_app.reopen_requested.connect(self.show_settings)

        self.bridge = UiBridge()
        self.bridge.hotkey_pressed.connect(self.handle_hotkey)
        self.bridge.menu_hotkey_pressed.connect(self.show_settings)
        self.bridge.answer_ready.connect(self.show_answer)
        self.bridge.hide_overlay_if_outside_ready.connect(self.hide_overlay_if_outside)
        self.bridge.show_settings_requested.connect(self.show_settings)

        from vitai.user_store import get_current_session, get_user_store
        self.user_store = get_user_store()

        self.overlay: AnswerOverlay | None = None
        self.settings_window: SettingsWindow | None = None
        self.worker_lock = threading.Lock()
        self.mouse_press_pos: tuple[int, int] | None = None
        self.text_cache: dict[str, str] = {}
        self.selection_anchor: tuple[int, int] | None = None
        self.mouse_listener: Any = None

        # 1. Hotkey Answer Trigger (Mặc định: Alt + Q)
        self.hotkey_manager = HotkeyManager(
            self.config.hotkey_modifier,
            self.config.hotkey_key,
            self._emit_hotkey,
            backend=self.config.hotkey_backend,
        )

        # 2. Hotkey Menu Settings (Mặc định: Ctrl + Alt + V)
        self.menu_hotkey_manager = HotkeyManager(
            "ctrl+alt",
            "v",
            self._emit_menu_hotkey,
            backend=self.config.hotkey_backend,
        )
        
        # 3. IPC Server & GNOME Global Shortcuts (cho Linux Wayland/GNOME & Windows)
        self.ipc_server = IpcServer(self._emit_hotkey, on_menu_callback=self._emit_menu_hotkey)
        self.ipc_server.start()
        register_gnome_hotkey(self.config.hotkey_modifier, self.config.hotkey_key)
        register_gnome_menu_hotkey("ctrl+alt", "v")

        # 4. Selection Watcher cho Fast Mode (bôi đen tự động trên Wayland/Linux)
        self.watcher = SelectionWatcher(self._start_answer_request)
        self.watcher.start()
        self.watcher.set_enabled(self.config.auto_translate)

        # 5. Kernel Mouse Tracker (cho Wayland/Linux)
        register_click_callback(self._on_kernel_mouse_click)
        start_mouse_tracker()

        # 7. Background proactive OAuth token refresher
        self._start_token_refresh_timer()

        # 8. Local AI Proxy Server (OpenAI-compatible & Subs Router on port 14555)
        from vitai.proxy import get_local_proxy
        self.local_proxy = get_local_proxy()
        self.local_proxy.start()

        set_startup(self.config.start_with_windows)

    def _start_token_refresh_timer(self) -> None:
        def _refresh_worker():
            import time
            from vitai.oauth_provider import refresh_oauth_token
            from vitai.token_store import get_token_store

            store = get_token_store()
            for provider, token in list(store._tokens.items()):
                if token.refresh_token and token.is_expired(buffer_seconds=300):
                    try:
                        self.logger.info(f"[OAuth] Proactively refreshing token for '{provider}'...")
                        new_token = refresh_oauth_token(token)
                        store.save_token(new_token)
                        self.logger.info(f"[OAuth] Successfully refreshed token for '{provider}'")
                    except Exception as e:
                        self.logger.warning(f"[OAuth] Could not refresh token for '{provider}': {e}")

        timer = threading.Timer(600.0, self._schedule_token_refresh)
        timer.daemon = True
        timer.start()

    def _schedule_token_refresh(self) -> None:
        try:
            from vitai.oauth_provider import refresh_oauth_token
            from vitai.token_store import get_token_store

            store = get_token_store()
            for provider, token in list(store._tokens.items()):
                if token.refresh_token and token.is_expired(buffer_seconds=300):
                    try:
                        self.logger.info(f"[OAuth] Refreshing token for '{provider}'...")
                        new_token = refresh_oauth_token(token)
                        store.save_token(new_token)
                    except Exception as e:
                        self.logger.warning(f"[OAuth] Failed to refresh token for '{provider}': {e}")
        finally:
            timer = threading.Timer(600.0, self._schedule_token_refresh)
            timer.daemon = True
            timer.start()

    def _load_config_with_env(self) -> AppConfig:
        config = load_config(self.config_path)
        provider = os.getenv("PROVIDER", config.provider).strip().lower()

        provider_env_map = {
            "anthropic": ("ANTHROPIC_API_KEY", "ANTHROPIC_BASE_URL", "ANTHROPIC_MODEL", "", ""),
            "openai": ("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL", "https://chatgpt.com/backend-api/codex", "cx/gpt-5.5"),
            "gemini": ("GEMINI_API_KEY", "GEMINI_BASE_URL", "GEMINI_MODEL", "https://generativelanguage.googleapis.com/v1beta", "gemini-2.5-flash"),
            "deepseek": ("DEEPSEEK_API_KEY", "DEEPSEEK_BASE_URL", "DEEPSEEK_MODEL", "https://api.deepseek.com/v1", "deepseek-chat"),
            "kiro": ("KIRO_API_KEY", "KIRO_BASE_URL", "KIRO_MODEL", "https://app.kiro.ai/v1", "kr/claude-sonnet-4.5"),
            "9router": ("NINEROUTER_API_KEY", "NINEROUTER_BASE_URL", "NINEROUTER_MODEL", "http://localhost:20128/v1", "High"),
        }

        if provider in provider_env_map:
            k_env, u_env, m_env, def_url, def_model = provider_env_map[provider]
            api_key = os.getenv(k_env, config.api_key).strip()
            base_url = os.getenv(u_env, config.base_url or def_url).strip()
            model = os.getenv(m_env, "").strip() or config.model or def_model
        else:
            api_key = config.api_key
            base_url = config.base_url
            model = config.model

        return replace(
            config,
            provider=provider,
            api_key=api_key,
            base_url=base_url,
            model=model,
        )

    def _install_exception_hooks(self) -> None:
        def _excepthook(exc_type, exc_value, exc_tb):
            self.logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_tb))
            traceback.print_exception(exc_type, exc_value, exc_tb, file=sys.stderr)

        sys.excepthook = _excepthook

    def _emit_menu_hotkey(self) -> None:
        self.bridge.menu_hotkey_pressed.emit()

    def toggle_settings(self) -> None:
        from vitai.user_store import get_current_session
        if self.settings_window is None:
            self.settings_window = SettingsWindow(self.config)
            self.settings_window.config_changed.connect(self._on_config_changed)
            self.settings_window.exit_requested.connect(self.quit)
        
        self.settings_window.current_user = get_current_session(self.user_store)
        self.settings_window._update_auth_ui()

        if self.settings_window.isVisible():
            if hasattr(self.settings_window, "_maybe_confirm_close"):
                if self.settings_window._maybe_confirm_close():
                    self.settings_window.hide()
            else:
                self.settings_window.hide()
        else:
            self.show_settings()

    def show_settings(self) -> None:
        from vitai.user_store import get_current_session
        if self.settings_window is None:
            self.settings_window = SettingsWindow(self.config)
            self.settings_window.config_changed.connect(self._on_config_changed)
            self.settings_window.exit_requested.connect(self.quit)
        
        self.settings_window.current_user = get_current_session(self.user_store)
        self.settings_window._update_auth_ui()
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def _on_config_changed(self, new_config: AppConfig) -> None:
        old_config = self.config
        self.config = new_config
        save_config(self.config_path, self.config)
        set_startup(self.config.start_with_windows)

        if self.overlay is not None:
            self.overlay.update_config(new_config)

        self.watcher.set_enabled(new_config.auto_translate)

        if not self.config.cache_enabled:
            self.text_cache.clear()

        if old_config.hotkey_modifier != new_config.hotkey_modifier or old_config.hotkey_key != new_config.hotkey_key:
            self.hotkey_manager.stop()
            self.hotkey_manager = HotkeyManager(
                self.config.hotkey_modifier,
                self.config.hotkey_key,
                self._emit_hotkey,
                backend=self.config.hotkey_backend,
            )
            self.hotkey_manager.start()
            register_gnome_hotkey(new_config.hotkey_modifier, new_config.hotkey_key)

    def _emit_hotkey(self) -> None:
        self.bridge.hotkey_pressed.emit()

    def handle_hotkey(self) -> None:
        self.logger.info("[MAIN] Nhận tín hiệu kích hoạt → Bắt đầu xử lý")
        cur_pos = get_mouse_position()
        if cur_pos and cur_pos != (0, 0):
            self.selection_anchor = cur_pos
        self._start_answer_request()

    def _start_answer_request(self) -> None:
        from vitai.user_store import get_current_session
        current_user = get_current_session(self.user_store)
        if current_user is None:
            self.logger.warning("[MAIN] 🔒 Ứng dụng đang bị khóa. Yêu cầu đăng nhập trước khi sử dụng!")
            self.bridge.show_settings_requested.emit()
            return
        threading.Thread(target=self._process_selection, daemon=True).start()

    def _is_hotkey_mouse_button(self, button: Any) -> bool:
        if not self.config.hotkey_key.startswith("mouse_") or mouse is None or button is None:
            return False
        mouse_btn = getattr(mouse, "Button", None)
        if mouse_btn is None:
            return False
        if button == mouse_btn.right and self.config.hotkey_key == "mouse_right":
            return True
        if button == mouse_btn.middle and self.config.hotkey_key == "mouse_middle":
            return True
        if button == mouse_btn.left and self.config.hotkey_key == "mouse_left":
            return True
        if button == getattr(mouse_btn, "x1", None) and self.config.hotkey_key in ("mouse_x1", "mouse_side"):
            return True
        if button == getattr(mouse_btn, "x2", None) and self.config.hotkey_key in ("mouse_x2", "mouse_extra"):
            return True
        return False

    def _on_kernel_mouse_click(self, x: int, y: int, pressed: bool) -> None:
        if pressed:
            if not self.config.hotkey_key.startswith("mouse_"):
                self.bridge.hide_overlay_if_outside_ready.emit(x, y)
        else:
            self.selection_anchor = (x, y)

    def _on_mouse_click(self, x: int, y: int, button: Any, pressed: bool) -> None:
        mouse_btn = getattr(mouse, "Button", None) if mouse is not None else None
        if pressed:
            if not self._is_hotkey_mouse_button(button):
                self.bridge.hide_overlay_if_outside_ready.emit(x, y)
            if mouse_btn is not None and button == mouse_btn.left:
                self.mouse_press_pos = (x, y)
            return
        if mouse_btn is not None and button != mouse_btn.left:
            return
        # Luôn ghi nhận vị trí nhả chuột trái là đuôi của vùng văn bản vừa bôi đen
        self.selection_anchor = (x, y)
        self.mouse_press_pos = None

    def _process_selection(self) -> None:
        if not self.worker_lock.acquire(blocking=False):
            self.logger.warning("[MAIN] Đang xử lý câu hỏi trước, bỏ qua request mới")
            return
        try:
            self.logger.info("[MAIN] Đang đọc text được bôi đen...")
            selected_text = get_selected_text()
            if not selected_text:
                self.logger.warning("[MAIN] ❌ Không tìm thấy văn bản bôi đen nào")
                return

            self.logger.info(f"[MAIN] ✅ Đã lấy được text ({len(selected_text)} chars): '{selected_text[:60]}...'")

            if self.config.cache_enabled and selected_text in self.text_cache:
                cached_ans = self.text_cache[selected_text]
                self.logger.info(f"[MAIN] ⚡ Trả về từ Cache: '{cached_ans[:40]}...'")
                self.bridge.answer_ready.emit(cached_ans)
                return

            from vitai.token_store import get_token_store
            token_store = get_token_store()

            api_key = self.config.api_key
            is_oauth_auth = token_store.is_authenticated(self.config.provider)

            if not api_key and not is_oauth_auth:
                if self.config.provider in ("9router", "openrouter"):
                    api_key = "dummy_free_key"
                else:
                    self.logger.warning(f"[MAIN] Chưa cấu hình API Key hoặc OAuth cho {self.config.provider}")
                    return

            question_is_mcq = is_mcq(selected_text)
            from vitai.llm import LlmClient

            client = LlmClient(
                self.config.provider,
                api_key,
                self.config.base_url,
                self.config.model,
                auth_method=self.config.auth_method,
            )
            self.logger.info(f"[MAIN] Gửi câu hỏi tới AI ({self.config.provider}/{self.config.model})...")
            answer = client.ask(selected_text, question_is_mcq)
            if question_is_mcq:
                answer = normalize_mcq_answer(answer)

            final_answer = (answer or "").strip()
            if not final_answer:
                self.logger.warning("[MAIN] ❌ Không nhận được câu trả lời từ AI")
                return

            self.logger.info(f"[MAIN] ✅ Nhận kết quả từ AI: '{final_answer[:60]}...'")
            if self.config.cache_enabled:
                self.text_cache[selected_text] = final_answer

            self.bridge.answer_ready.emit(final_answer)
        except Exception as exc:
            self.logger.exception(f"[MAIN] ❌ Lỗi trong luồng xử lý: {exc}")
        finally:
            self.worker_lock.release()

    def hide_overlay_if_outside(self, x: int, y: int) -> None:
        if self.overlay is not None and self.overlay.isVisible():
            self.logger.info(f"[MAIN] 🖱️ Phát hiện click chuột tại ({x}, {y}) → Tắt Ghost Overlay")
            self.overlay.hide_overlay()

    def show_answer(self, text: str, x: int | None = None, y: int | None = None) -> None:
        if not text or text.startswith("Lỗi"):
            return

        if self.overlay is None:
            self.overlay = AnswerOverlay(text, config=self.config)
        else:
            self.overlay.update_config(self.config)

        last_end = get_last_selection_end_pos()
        pos = get_mouse_position()
        if x is not None and y is not None:
            anchor_x, anchor_y = x, y
        elif self.selection_anchor is not None:
            anchor_x, anchor_y = self.selection_anchor
        elif last_end is not None:
            anchor_x, anchor_y = last_end
        else:
            anchor_x, anchor_y = pos

        self.logger.info(f"[MAIN] Hiển thị đáp án tại ({anchor_x}, {anchor_y}): '{text}'")
        self.overlay.show_message(text, anchor_x, anchor_y)

    def run(self) -> int:
        self.hotkey_manager.start()
        self.menu_hotkey_manager.start()
        if mouse is not None:
            listener_cls = getattr(mouse, "Listener", None)
            if listener_cls is not None:
                self.mouse_listener = listener_cls(on_click=self._on_mouse_click)
                if self.mouse_listener is not None and hasattr(self.mouse_listener, "start"):
                    self.mouse_listener.start()
        return self.qt_app.exec()

    def quit(self) -> None:
        if hasattr(self, "local_proxy") and self.local_proxy:
            self.local_proxy.stop()
        self.watcher.stop()
        self.ipc_server.stop()
        self.hotkey_manager.stop()
        self.menu_hotkey_manager.stop()
        if self.mouse_listener is not None and hasattr(self.mouse_listener, "stop"):
            self.mouse_listener.stop()
        self.qt_app.quit()


def main() -> int:
    if "--trigger" in sys.argv:
        if send_trigger():
            return 0
        else:
            print("⚠️ Vì Người Tài chưa chạy. Vui lòng mở Vì Người Tài trước.")
            return 1

    if "--menu" in sys.argv or "--settings" in sys.argv:
        if send_menu_trigger():
            return 0

    # Nếu ứng dụng đã chạy ngầm từ trước, chuyển giao diện Cài đặt lên phía trước
    if send_menu_trigger():
        return 0

    app = ViTaiApp()
    app.show_settings()
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
