from __future__ import annotations

import ctypes
import logging
import os
import sys
import threading
import traceback
from dataclasses import replace

from dotenv import load_dotenv
from pynput import mouse
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QApplication, QInputDialog, QMenu, QSystemTrayIcon

from vitai.capture import get_selected_text
from vitai.config import AppConfig, default_config_path, load_config, save_config
from vitai.encoding import configure_utf8_stdio
from vitai.hotkey import HotkeyManager
from vitai.llm import AnthropicProxyClient
from vitai.logging_config import configure_logging
from vitai.mcq import is_mcq, normalize_mcq_answer
from vitai.overlay import AnswerOverlay
from vitai.resources import resource_path

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
        load_dotenv()
        configure_logging()
        self.logger = logging.getLogger(__name__)
        self._install_exception_hooks()
        self.config_path = default_config_path()
        self.config = self._load_config_with_env()
        set_windows_app_id()

        self.qt_app = QApplication(sys.argv)
        self.qt_app.setApplicationName("ViTai")
        self.qt_app.setApplicationDisplayName("ViTai")
        self.qt_app.setWindowIcon(QIcon(str(resource_path("assets/icon.ico"))))
        self.qt_app.setQuitOnLastWindowClosed(False)

        self.bridge = UiBridge()
        self.bridge.hotkey_pressed.connect(self.handle_hotkey)
        self.bridge.answer_ready.connect(self.show_answer)
        self.bridge.hide_overlay_if_outside_ready.connect(self.hide_overlay_if_outside)
        self.overlay: AnswerOverlay | None = None
        self.worker_lock = threading.Lock()
        self.preview_lock = threading.Lock()
        self.mouse_press_pos: tuple[int, int] | None = None

        self.selection_anchor: tuple[int, int] | None = None
        self.mouse_listener: mouse.Listener | None = None
        self.tray = self._create_tray()
        self.hotkey_manager = HotkeyManager(
            self.config.hotkey_modifier,
            self.config.hotkey_key,
            self._emit_hotkey,
            backend=self.config.hotkey_backend,
        )

    def _load_config_with_env(self) -> AppConfig:
        config = load_config(self.config_path)
        auth_token = os.getenv("ANTHROPIC_AUTH_TOKEN", "").strip()
        base_url = os.getenv("ANTHROPIC_BASE_URL", "").strip()
        model = os.getenv("ANTHROPIC_DEFAULT_SONNET_MODEL", "").strip()
        if auth_token and not config.anthropic_auth_token:
            config = replace(config, anthropic_auth_token=auth_token)
        if base_url:
            config = replace(config, anthropic_base_url=base_url)
        if model:
            config = replace(config, model=model)
        return config

    def _install_exception_hooks(self) -> None:
        def _excepthook(exc_type, exc_value, exc_tb):
            self.logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_tb))
            traceback.print_exception(exc_type, exc_value, exc_tb, file=sys.stderr)

        sys.excepthook = _excepthook

    def _create_tray(self) -> QSystemTrayIcon:
        tray = QSystemTrayIcon(QIcon(str(resource_path("assets/icon.ico"))), self.qt_app)
        tray.setToolTip("ViTai")
        menu = QMenu()
        show_action = QAction("Show", menu)
        show_action.triggered.connect(lambda: self.show_answer("ViTai đang chạy. Bôi đen text rồi nhấn Alt+Q."))
        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(self.quit)
        menu.addAction(show_action)
        menu.addAction(quit_action)
        tray.setContextMenu(menu)
        tray.activated.connect(self._tray_activated)
        tray.show()
        return tray

    def _tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_answer("ViTai đang chạy. Bôi đen text rồi nhấn Alt+Q.")

    def _emit_hotkey(self) -> None:
        self.bridge.hotkey_pressed.emit()

    def handle_hotkey(self) -> None:
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
        self.selection_anchor = (min(start[0], x), min(start[1], y))


    def _process_selection(self) -> None:
        if not self.worker_lock.acquire(blocking=False):
            self.bridge.answer_ready.emit("Đang xử lý câu trước.")
            return
        try:
            selected_text = get_selected_text()
            if not selected_text:
                self.bridge.answer_ready.emit("Không tìm thấy text bôi đen")
                return

            self.bridge.answer_ready.emit("...")

            if not self.config.anthropic_auth_token:
                self.bridge.answer_ready.emit("Chưa có Anthropic proxy token")
                return

            question_is_mcq = is_mcq(selected_text)
            client = AnthropicProxyClient(
                self.config.anthropic_auth_token,
                self.config.anthropic_base_url,
                self.config.model,
            )
            answer = client.ask(selected_text, question_is_mcq)
            if question_is_mcq:
                answer = normalize_mcq_answer(answer)
            self.bridge.answer_ready.emit(answer or "Không có phản hồi")
        except Exception as exc:
            self.logger.exception("Failed to answer selection")
            self.bridge.answer_ready.emit(f"Lỗi kết nối API: {exc}")
        finally:
            self.worker_lock.release()

    def hide_overlay_if_outside(self, x: int, y: int) -> None:
        if self.overlay is None or not self.overlay.isVisible():
            return
        rect = self.overlay.geometry()
        if not rect.contains(x, y):
            self.overlay.close()

    def show_answer(self, text: str, x: int | None = None, y: int | None = None) -> None:
        if text == "Chưa có Anthropic proxy token":
            if not self._prompt_for_auth_token():
                text = "Chưa có Anthropic proxy token"
            else:
                self.handle_hotkey()
                return
        if self.overlay is None or not self.overlay.isVisible():
            self.overlay = AnswerOverlay(text)
            self.overlay.clicked.connect(self._start_answer_request)
        anchor = self.selection_anchor if x is None or y is None else (x, y)
        if anchor is None:
            self.overlay.show_message(text)
            return
        self.overlay.show_message(text, anchor[0], anchor[1])

    def _prompt_for_auth_token(self) -> bool:
        auth_token, ok = QInputDialog.getText(None, "ViTai", "Nhập ANTHROPIC_AUTH_TOKEN:")
        auth_token = auth_token.strip()
        if not ok or not auth_token:
            return False
        self.config = replace(self.config, anthropic_auth_token=auth_token)
        save_config(self.config_path, self.config)
        return True

    def run(self) -> int:
        self.hotkey_manager.start()
        self.mouse_listener = mouse.Listener(on_click=self._on_mouse_click)
        self.mouse_listener.start()
        return self.qt_app.exec()

    def quit(self) -> None:
        self.hotkey_manager.stop()
        if self.mouse_listener is not None:
            self.mouse_listener.stop()
        self.tray.hide()
        self.qt_app.quit()


def main() -> int:
    app = ViTaiApp()
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
