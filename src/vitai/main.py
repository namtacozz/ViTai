from __future__ import annotations

import ctypes
import logging
import os
import sys
import threading
import traceback
from dataclasses import replace
from pathlib import Path

from pynput import mouse
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QAction, QCursor, QIcon
from PyQt6.QtWidgets import QApplication, QInputDialog, QMenu, QSystemTrayIcon

from vitai.capture import get_selected_text
from vitai.config import AppConfig, default_config_path, load_config, save_config
from vitai.encoding import configure_utf8_stdio
from vitai.gnome_shortcuts import register_gnome_hotkey, unregister_gnome_hotkey
from vitai.hotkey import HotkeyManager
from vitai.ipc import IpcServer, send_trigger
from vitai.logging_config import configure_logging
from vitai.mcq import is_mcq, normalize_mcq_answer
from vitai.mouse_tracker import get_mouse_position, start_mouse_tracker
from vitai.overlay import AnswerOverlay
from vitai.resources import resource_path
from vitai.selection_watcher import SelectionWatcher
from vitai.settings import SettingsWindow
from vitai.startup import install_linux_desktop_file, set_startup
from vitai.ui_log import install_ui_logging
from dotenv import load_dotenv

configure_utf8_stdio()


def set_windows_app_id() -> None:
    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ViTai.App")


class UiBridge(QObject):
    hotkey_pressed = pyqtSignal()
    answer_ready = pyqtSignal(str)
    hide_overlay_if_outside_ready = pyqtSignal(int, int)


class ViTaiApp:
    def __init__(self):
        if getattr(sys, "frozen", False):
            base_dir = Path(sys.executable).parent
        else:
            base_dir = Path(os.getcwd())
        env_path = base_dir / ".env"
        load_dotenv(dotenv_path=env_path)

        configure_logging()
        install_ui_logging()
        self.logger = logging.getLogger("vitai.main")
        self.logger.info("ViTai starting")
        self._install_exception_hooks()
        install_linux_desktop_file()

        self.config_path = default_config_path()
        self.config = self._load_config_with_env()
        set_windows_app_id()

        self.qt_app = QApplication(sys.argv)
        self.qt_app.setApplicationName("ViTai")
        self.qt_app.setApplicationDisplayName("ViTai")
        self.qt_app.setDesktopFileName("vitai")
        self.qt_app.setWindowIcon(QIcon(str(resource_path("assets/icon.ico"))))
        self.qt_app.setQuitOnLastWindowClosed(False)

        self.bridge = UiBridge()
        self.bridge.hotkey_pressed.connect(self.handle_hotkey)
        self.bridge.answer_ready.connect(self.show_answer)
        self.bridge.hide_overlay_if_outside_ready.connect(self.hide_overlay_if_outside)

        self.overlay: AnswerOverlay | None = None
        self.settings_window: SettingsWindow | None = None
        self.worker_lock = threading.Lock()
        self.mouse_press_pos: tuple[int, int] | None = None
        self.text_cache: dict[str, str] = {}
        self.selection_anchor: tuple[int, int] | None = None
        self.mouse_listener: mouse.Listener | None = None

        self.tray = self._create_tray()
        
        # 1. Hotkey qua pynput (hoạt động tốt trên Windows/X11)
        self.hotkey_manager = HotkeyManager(
            self.config.hotkey_modifier,
            self.config.hotkey_key,
            self._emit_hotkey,
            backend=self.config.hotkey_backend,
        )
        
        # 2. IPC Server & GNOME Global Shortcuts (cho Linux Wayland/GNOME)
        self.ipc_server = IpcServer(self._emit_hotkey)
        self.ipc_server.start()
        register_gnome_hotkey(self.config.hotkey_modifier, self.config.hotkey_key)

        # 3. Selection Watcher cho Fast Mode (bôi đen tự động trên Wayland/Linux)
        self.watcher = SelectionWatcher(self._start_answer_request)
        self.watcher.start()
        self.watcher.set_enabled(self.config.auto_translate)

        # 4. Kernel Mouse Tracker (cho Wayland/Linux)
        start_mouse_tracker()

        set_startup(self.config.start_with_windows)

    def _load_config_with_env(self) -> AppConfig:
        config = load_config(self.config_path)

        provider = os.getenv("PROVIDER", config.provider).strip().lower()
        if provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY", config.api_key).strip()
            base_url = os.getenv("ANTHROPIC_BASE_URL", config.base_url).strip()
            model = os.getenv("ANTHROPIC_MODEL", config.model).strip()
        elif provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY", "").strip()
            base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
        elif provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY", "").strip()
            base_url = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta").strip()
            model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
        elif provider == "deepseek":
            api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
            base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1").strip()
            model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip()
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

    def _create_tray(self) -> QSystemTrayIcon:
        tray = QSystemTrayIcon(QIcon(str(resource_path("assets/icon.ico"))), self.qt_app)
        tray.setToolTip("ViTai — AI Assistant")
        menu = QMenu()
        settings_action = QAction("⚙️ Cài đặt", menu)
        settings_action.triggered.connect(self.show_settings)
        quit_action = QAction("❌ Thoát", menu)
        quit_action.triggered.connect(self.quit)
        menu.addAction(settings_action)
        menu.addAction(quit_action)
        tray.setContextMenu(menu)
        tray.activated.connect(self._tray_activated)
        tray.show()
        return tray

    def _tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.DoubleClick,
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.MiddleClick,
        ):
            self.show_settings()

    def show_settings(self) -> None:
        if self.settings_window is None:
            self.settings_window = SettingsWindow(self.config)
            self.settings_window.config_changed.connect(self._on_config_changed)
            self.settings_window.exit_requested.connect(self.quit)
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
        self._start_answer_request()

    def _start_answer_request(self) -> None:
        threading.Thread(target=self._process_selection, daemon=True).start()

    def _on_mouse_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        if button != mouse.Button.left:
            return
        if pressed:
            self.mouse_press_pos = (x, y)
            self.bridge.hide_overlay_if_outside_ready.emit(x, y)
            return
        start = self.mouse_press_pos
        self.mouse_press_pos = None
        if start is None:
            return
        if abs(x - start[0]) < 8 and abs(y - start[1]) < 8:
            return
        self.selection_anchor = (x, y)

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

            api_key = self.config.api_key
            if not api_key:
                if self.config.provider == "9router":
                    api_key = "dummy_free_key"
                else:
                    self.logger.warning("[MAIN] Chưa cấu hình API Key")
                    return

            question_is_mcq = is_mcq(selected_text)
            from vitai.llm import LlmClient

            client = LlmClient(
                self.config.provider,
                api_key,
                self.config.base_url,
                self.config.model,
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
        if self.overlay is None or not self.overlay.isVisible():
            return
        rect = self.overlay.geometry()
        if not rect.contains(x, y):
            self.overlay.close()

    def show_answer(self, text: str, x: int | None = None, y: int | None = None) -> None:
        if not text or text.startswith("Lỗi"):
            return

        if self.overlay is None:
            self.overlay = AnswerOverlay(text, config=self.config)
        else:
            self.overlay.update_config(self.config)

        pos = get_mouse_position()
        anchor_x = x if x is not None else (self.selection_anchor[0] if self.selection_anchor else pos[0])
        anchor_y = y if y is not None else (self.selection_anchor[1] if self.selection_anchor else pos[1])

        self.logger.info(f"[MAIN] Hiển thị đáp án tại ({anchor_x}, {anchor_y}): '{text}'")
        self.overlay.show_message(text, anchor_x, anchor_y)

    def run(self) -> int:
        self.hotkey_manager.start()
        self.mouse_listener = mouse.Listener(on_click=self._on_mouse_click)
        self.mouse_listener.start()
        return self.qt_app.exec()

    def quit(self) -> None:
        self.watcher.stop()
        self.ipc_server.stop()
        self.hotkey_manager.stop()
        if self.mouse_listener is not None:
            self.mouse_listener.stop()
        self.tray.hide()
        self.qt_app.quit()


def main() -> int:
    if "--trigger" in sys.argv:
        if send_trigger():
            return 0
        else:
            print("⚠️ ViTai chưa chạy. Vui lòng mở ViTai trước.")
            return 1

    app = ViTaiApp()
    if "--settings" in sys.argv or (not app.config.api_key and app.config.provider != "9router"):
        app.show_settings()
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
