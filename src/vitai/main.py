import ctypes
import logging
import os
import sys
import threading
import time
import traceback

from vitai.encoding import configure_utf8_stdio


def fix_crt_handles_for_pytorch() -> None:
    if sys.platform != "win32" or not getattr(sys, "frozen", False):
        return

    try:
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        kernel32.GetConsoleWindow.restype = ctypes.c_void_p
        kernel32.AllocConsole.restype = ctypes.c_int
        user32.ShowWindow.argtypes = [ctypes.c_void_p, ctypes.c_int]

        console_window = kernel32.GetConsoleWindow()
        if not console_window:
            kernel32.AllocConsole()
            console_window = kernel32.GetConsoleWindow()
        if console_window:
            user32.ShowWindow(console_window, 0)

        if sys.stdin is None:
            sys.stdin = open("CONIN$", "r", encoding="utf-8", errors="replace")
        if sys.stdout is None:
            sys.stdout = open("CONOUT$", "w", encoding="utf-8", errors="replace")
        if sys.stderr is None:
            sys.stderr = open("CONOUT$", "w", encoding="utf-8", errors="replace")
    except Exception:
        pass


fix_crt_handles_for_pytorch()
configure_utf8_stdio()

import torch

from PyQt6.QtCore import QObject, QRect, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QApplication, QInputDialog, QSystemTrayIcon, QMenu

from dotenv import load_dotenv
from pathlib import Path
from pynput import mouse
import os

from vitai.text_capture import get_selected_text
from vitai.mcq import is_mcq, normalize_mcq_answer
from vitai.overlay_vitai import AnswerOverlay
from vitai.llm import LlmClient
from vitai.auto_translate import AutoTranslateWorker
from vitai.capture import capture_rect
from vitai.config import AppConfig, default_config_path, load_config, save_config
from vitai.geometry import content_capture_rect, font_size_for_bbox, translate_capture_bbox_to_overlay
from vitai.history import TranslationHistoryEntry
from vitai.hotkey import HotkeyManager
from vitai.i18n import tr
from vitai.logging_config import configure_logging
from vitai.models import TranslatedBox
from vitai.text_cache import FrameChangeCache, TextResultCache
from vitai.ocr import read_text, warm_up_reader
from vitai.overlay import OverlayWindow
from vitai.resources import resource_path
from vitai.selection import SelectionWindow
from vitai.settings import SettingsWindow
from vitai.startup import restart_as_admin, set_startup
from vitai.translate import TranslationError, translate_texts
from vitai.transtyle import TranstyleProfile, get_profile, save_exact_correction
from vitai.tts import SpeechRunner, SpeechUnavailableError


def set_windows_app_id() -> None:
    if sys.platform != "win32":
        return
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ViTai.App")


class UiBridge(QObject):
    toggle_requested = pyqtSignal()
    boxes_ready = pyqtSignal(object, list)
    status_ready = pyqtSignal(object, str)
    answer_ready = pyqtSignal(str)
    hide_answer_overlay_ready = pyqtSignal(int, int)
    trigger_faa_requested = pyqtSignal()


class ViTaiApp:
    def __init__(self):
        if getattr(sys, 'frozen', False):
            base_dir = Path(sys.executable).parent
        else:
            base_dir = Path(os.getcwd())
        load_dotenv(dotenv_path=base_dir / ".env")
        
        configure_logging()
        self.logger = logging.getLogger(__name__)
        self.logger.info("ViTai starting")
        self._install_exception_hooks()
        self.config_path = default_config_path()
        self.config = load_config(self.config_path)
        set_windows_app_id()
        self.qt_app = QApplication(sys.argv)
        self.qt_app.setApplicationName("ViTai")
        self.qt_app.setApplicationDisplayName("ViTai")
        self.qt_app.setDesktopFileName("ViTai")
        self.qt_app.setWindowIcon(QIcon(str(resource_path("assets/icon.ico"))))
        self.qt_app.setQuitOnLastWindowClosed(False)
        self.bridge = UiBridge()
        self.overlays: list[OverlayWindow] = []
        self.auto_workers: dict[OverlayWindow, AutoTranslateWorker] = {}
        self.text_caches: dict[OverlayWindow, TextResultCache] = {}
        self.frame_caches: dict[OverlayWindow, FrameChangeCache] = {}
        self.selection_window: SelectionWindow | None = None
        self.settings_window: SettingsWindow | None = None
        self.answer_overlay: AnswerOverlay | None = None
        self.selection_anchor: tuple[int, int] | None = None
        self.mouse_press_pos: tuple[int, int] | None = None
        self.mouse_listener: mouse.Listener | None = None
        self.ai_text_cache: dict[str, str] = {}
        
        self.tray = self._create_tray()
        self.bridge.toggle_requested.connect(self.toggle_overlay)
        self.bridge.boxes_ready.connect(self._on_boxes_ready)
        self.bridge.status_ready.connect(self._on_status_ready)
        self.bridge.answer_ready.connect(self.show_answer)
        self.bridge.hide_answer_overlay_ready.connect(self.hide_answer_overlay)
        self.bridge.trigger_faa_requested.connect(self._start_answer_request)
        self.ocr_lock = threading.Lock()
        self.ai_worker_lock = threading.Lock()
        self.speech_runner = SpeechRunner()
        self.hotkey_manager = HotkeyManager(
            self.config.hotkey_modifier,
            self.config.hotkey_key,
            self.toggle_overlay_threadsafe,
            backend=self.config.hotkey_backend,
        )
        self.faa_hotkey_manager = HotkeyManager(
            self.config.faa_hotkey_modifier,
            self.config.faa_hotkey_key,
            self.trigger_faa_threadsafe,
            backend=self.config.hotkey_backend,
        )
        QTimer.singleShot(3000, self._start_ocr_warmup)

    def _install_exception_hooks(self) -> None:
        """Install global exception handlers to log crashes instead of dying silently."""
        def _excepthook(exc_type, exc_value, exc_tb):
            self.logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_tb))
            traceback.print_exception(exc_type, exc_value, exc_tb, file=sys.stderr)
        sys.excepthook = _excepthook

    def _on_boxes_ready(self, overlay: OverlayWindow, payload: tuple[list, TranslationHistoryEntry]) -> None:
        if overlay in self.overlays:
            boxes, history_entry = payload
            overlay.set_translated_boxes(boxes, history_entry)

    def _on_status_ready(self, overlay: OverlayWindow, message: str) -> None:
        if overlay in self.overlays:
            overlay.set_status(message)

    def _create_tray(self) -> QSystemTrayIcon:
        tray = QSystemTrayIcon(QIcon(str(resource_path("assets/icon.ico"))), self.qt_app)
        tray.setToolTip("ViTai")
        
        menu = QMenu()
        settings_action = QAction("⚙️ Cài đặt", self.qt_app)
        settings_action.triggered.connect(self.show_settings)
        menu.addAction(settings_action)
        
        exit_action = QAction("❌ Thoát", self.qt_app)
        exit_action.triggered.connect(self.quit)
        menu.addAction(exit_action)
        
        tray.setContextMenu(menu)
        tray.activated.connect(self._tray_activated)
        tray.show()
        return tray

    def _tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_settings()

    def show_settings(self) -> None:
        """Open or bring to front the settings window."""
        if self.settings_window is None:
            self.settings_window = SettingsWindow(self.config)
            self.settings_window.config_changed.connect(self._on_config_changed)
            self.settings_window.exit_requested.connect(self.quit)
        self.settings_window.update_config(self.config)
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def _on_config_changed(self, new_config: AppConfig) -> None:
        old_config = self.config
        self.config = new_config
        save_config(self.config_path, self.config)
        self.logger.info("Settings saved")

        # Update hotkey if changed
        if (old_config.hotkey_modifier != new_config.hotkey_modifier
                or old_config.hotkey_key != new_config.hotkey_key
                or old_config.hotkey_backend != new_config.hotkey_backend):
            self.hotkey_manager.update(new_config.hotkey_modifier, new_config.hotkey_key, new_config.hotkey_backend)
            self.logger.info("Hotkey updated")

        if (old_config.faa_hotkey_modifier != new_config.faa_hotkey_modifier
                or old_config.faa_hotkey_key != new_config.faa_hotkey_key
                or old_config.hotkey_backend != new_config.hotkey_backend):
            self.faa_hotkey_manager.update(new_config.faa_hotkey_modifier, new_config.faa_hotkey_key, new_config.hotkey_backend)
            self.logger.info("FAA Hotkey updated")

        if old_config.overlay_color != new_config.overlay_color:
            for overlay in self.overlays:
                overlay.update_overlay_color(new_config.overlay_color)

        if old_config.ui_language != new_config.ui_language:
            for overlay in self.overlays:
                overlay.set_ui_language(new_config.ui_language)

        if old_config.default_transtyle_id != new_config.default_transtyle_id:
            for overlay in self.overlays:
                overlay.set_transtyle_id(new_config.default_transtyle_id)

        # Handle startup registry
        if old_config.start_with_windows != new_config.start_with_windows:
            set_startup(new_config.start_with_windows)

        # Handle admin elevation (requires restart)
        if new_config.run_as_admin and not old_config.run_as_admin:
            save_config(self.config_path, self.config)
            restart_as_admin()

    def _start_ocr_warmup(self) -> None:
        threading.Thread(target=warm_up_reader, daemon=True).start()

    def run(self) -> int:
        self.hotkey_manager.start()
        self.faa_hotkey_manager.start()
        self.mouse_listener = mouse.Listener(on_click=self._on_mouse_click)
        self.mouse_listener.start()
        return self.qt_app.exec()

    def toggle_overlay_threadsafe(self) -> None:
        self.bridge.toggle_requested.emit()

    def trigger_faa_threadsafe(self) -> None:
        if self.config.ghost_faa_enabled:
            self.bridge.trigger_faa_requested.emit()

    def open_ui(self) -> None:
        self.start_selection()

    def toggle_overlay(self) -> None:
        if self.selection_window is not None and self.selection_window.isVisible():
            self.selection_window.close()
            self.selection_window = None
            return
        self.start_selection()

    def start_selection(self) -> None:
        self.selection_window = SelectionWindow(self.selection_selected, self.selection_cancelled)
        self.selection_window.showFullScreen()
        self.selection_window.raise_()
        self.selection_window.activateWindow()

    def selection_selected(self, rect: QRect) -> None:
        self.selection_window = None
        try:
            overlay = self._create_overlay_for_rect(rect)
        except Exception:
            self.logger.exception("Failed to create overlay")

    def _create_overlay_for_rect(self, rect: QRect) -> OverlayWindow:
        """Create an overlay window at the given rect and wire up callbacks."""
        # Use a container to allow closures to reference the overlay
        # even though it is created after the closures are defined.
        container: list[OverlayWindow] = []

        def translate_current() -> None:
            if container:
                self.translate_overlay(container[0])

        def hide_current() -> None:
            if container:
                self.hide_overlay(container[0])

        def auto_changed(enabled: bool) -> None:
            if container:
                self.set_overlay_auto(container[0], enabled)

        def reset_current() -> None:
            if container:
                cache = self.text_caches.get(container[0])
                if cache is not None:
                    cache.clear()

        def speak_latest(text: str) -> None:
            if container:
                self.speak_overlay_text(container[0], text)

        overlay = OverlayWindow(self.config, translate_current, hide_current, auto_changed, reset_current, speak_latest)
        overlay.correction_requested.connect(lambda box, current_overlay=overlay: self._save_correction(current_overlay, box))
        container.append(overlay)
        overlay.setGeometry(rect)
        self.overlays.append(overlay)
        overlay.show()
        overlay.raise_()
        overlay.activateWindow()
        self.text_caches[overlay] = TextResultCache()
        self.frame_caches[overlay] = FrameChangeCache()
        if overlay.auto_enabled():
            self.set_overlay_auto(overlay, True)
        self.config = self._config_with_overlay_state(overlay)
        save_config(self.config_path, self.config)
        return overlay

    def selection_cancelled(self) -> None:
        self.selection_window = None

    def hide_overlay(self, overlay: OverlayWindow) -> None:
        self._stop_overlay_auto(overlay)
        self.text_caches.pop(overlay, None)
        self.frame_caches.pop(overlay, None)
        self.config = self._config_with_overlay_state(overlay)
        save_config(self.config_path, self.config)
        overlay.hide()
        if overlay in self.overlays:
            self.overlays.remove(overlay)
        overlay.deleteLater()

    def set_overlay_auto(self, overlay: OverlayWindow, enabled: bool) -> None:
        if enabled:
            if overlay in self.auto_workers:
                return
            interval_seconds = max(0.1, min(self.config.auto_translate_interval_ms / 1000, 5.0))
            worker = AutoTranslateWorker(lambda: self._auto_translate_overlay_job(overlay), interval_seconds)
            self.auto_workers[overlay] = worker
            self.text_caches.setdefault(overlay, TextResultCache())
            self.frame_caches.setdefault(overlay, FrameChangeCache())
            self.logger.info("Auto translate started")
            worker.start()
            return

        worker = self.auto_workers.pop(overlay, None)
        if worker is not None:
            worker.stop()
            self.logger.info("Auto translate stopped")

    def _stop_overlay_auto(self, overlay: OverlayWindow) -> None:
        worker = self.auto_workers.pop(overlay, None)
        if worker is not None:
            worker.stop()

    def translate_overlay(self, overlay: OverlayWindow) -> None:
        threading.Thread(target=self._translate_overlay_job, args=(overlay,), daemon=True).start()

    def _translate_overlay_job(self, overlay: OverlayWindow) -> None:
        try:
            overlay_rect = overlay.overlay_rect()
            source_language = overlay.source_language()
            target_language = overlay.target_language()
            capture_area = content_capture_rect(overlay_rect, 0)
            image = capture_rect(capture_area, self.config.capture_provider)
            with self.ocr_lock:
                ocr_results = read_text(image, provider_id=self.config.ocr_provider)
            if overlay not in self.overlays:
                return
            if not ocr_results:
                self.bridge.status_ready.emit(overlay, "No text found")
                self.logger.info("OCR found no text")
                return

            profile = get_profile(overlay.transtyle_id(), self.config.transtyle_profiles)
            translated_texts = translate_texts(
                [result.text for result in ocr_results],
                target_language=target_language,
                source_language=source_language,
                profile=profile,
                provider_id=self.config.translator_provider,
                deepl_api_key=self.config.deepl_api_key,
                failover_enabled=self.config.translator_failover_enabled,
            )
            if overlay not in self.overlays:
                return
            boxes = [
                TranslatedBox(
                    original=result.text,
                    translated=translated,
                    bbox=translate_capture_bbox_to_overlay(result.bbox, 0, 0),
                    font_size=font_size_for_bbox(result.bbox),
                    source_language=source_language,
                    target_language=target_language,
                    transtyle_id=profile.id,
                )
                for result, translated in zip(ocr_results, translated_texts, strict=True)
            ]
            history_entry = TranslationHistoryEntry(
                original="\n".join(result.text for result in ocr_results if result.text.strip()),
                translated="\n".join(text for text in translated_texts if text.strip()),
                timestamp=time.time(),
            )
            self.bridge.boxes_ready.emit(overlay, (boxes, history_entry))
        except TranslationError as exc:
            if overlay in self.overlays:
                self.logger.warning("Translation failed: %s", exc)
                self.bridge.status_ready.emit(overlay, f"Translation failed: {exc}")
        except Exception as exc:
            if overlay in self.overlays:
                self.logger.exception("ViTai failed")
                self.bridge.status_ready.emit(overlay, f"ViTai failed: {exc}")

    def _auto_translate_overlay_job(self, overlay: OverlayWindow) -> None:
        try:
            if overlay not in self.overlays:
                return
            overlay_rect = overlay.overlay_rect()
            source_language = overlay.source_language()
            target_language = overlay.target_language()
            capture_area = content_capture_rect(overlay_rect, 0)
            image = capture_rect(capture_area, self.config.capture_provider)
            frame_cache = self.frame_caches.setdefault(overlay, FrameChangeCache())
            if not frame_cache.has_changed(image):
                return
            with self.ocr_lock:
                ocr_results = read_text(image, provider_id=self.config.ocr_provider)
            if overlay not in self.overlays:
                return
            if not ocr_results:
                self.bridge.status_ready.emit(overlay, "No text found")
                self.logger.info("Auto OCR found no text")
                return
            cache = self.text_caches.setdefault(overlay, TextResultCache())
            if cache.is_duplicate([result.text for result in ocr_results]):
                return
            profile = get_profile(overlay.transtyle_id(), self.config.transtyle_profiles)
            translated_texts = translate_texts(
                [result.text for result in ocr_results],
                target_language=target_language,
                source_language=source_language,
                profile=profile,
                provider_id=self.config.translator_provider,
                deepl_api_key=self.config.deepl_api_key,
                failover_enabled=self.config.translator_failover_enabled,
            )
            if overlay not in self.overlays:
                return
            boxes = [
                TranslatedBox(
                    original=result.text,
                    translated=translated,
                    bbox=translate_capture_bbox_to_overlay(result.bbox, 0, 0),
                    font_size=font_size_for_bbox(result.bbox),
                    source_language=source_language,
                    target_language=target_language,
                    transtyle_id=profile.id,
                )
                for result, translated in zip(ocr_results, translated_texts, strict=True)
            ]
            history_entry = TranslationHistoryEntry(
                original="\n".join(result.text for result in ocr_results if result.text.strip()),
                translated="\n".join(text for text in translated_texts if text.strip()),
                timestamp=time.time(),
            )
            self.bridge.boxes_ready.emit(overlay, (boxes, history_entry))
        except TranslationError as exc:
            if overlay in self.overlays:
                self.logger.warning("Auto translation failed: %s", exc)
                self.bridge.status_ready.emit(overlay, f"Translation failed: {exc}")
        except Exception:
            if overlay in self.overlays:
                self.logger.exception("Auto translate failed")
                self.bridge.status_ready.emit(overlay, "ViTai auto failed")

    def _save_correction(self, overlay: OverlayWindow, box: TranslatedBox) -> None:
        corrected, ok = QInputDialog.getText(
            None,
            "Sửa bản dịch",
            f"Văn bản gốc: {box.original}\nBản dịch hiện tại: {box.translated}\nBản dịch đúng:",
            text=box.translated,
        )
        if not ok:
            return
        if not corrected.strip():
            return

        base_profile = get_profile(box.transtyle_id, {})
        profile = self.config.transtyle_profiles.get(box.transtyle_id)
        if profile is None:
            profile = TranstyleProfile(
                id=base_profile.id,
                display_name=base_profile.display_name,
                enabled_rules=list(base_profile.enabled_rules),
            )
        elif not profile.enabled_rules:
            profile = TranstyleProfile(
                id=profile.id,
                display_name=profile.display_name,
                enabled_rules=list(base_profile.enabled_rules),
                glossary=dict(profile.glossary),
                pronoun_rules=dict(profile.pronoun_rules),
                term_rules=dict(profile.term_rules),
                regex_rules=list(profile.regex_rules),
                corrections=dict(profile.corrections),
                version=profile.version,
            )
        updated_profile = save_exact_correction(profile, box.source_language, box.target_language, box.original, corrected)
        profiles = dict(self.config.transtyle_profiles)
        profiles[updated_profile.id] = updated_profile
        self.config = AppConfig(
            x=self.config.x,
            y=self.config.y,
            width=self.config.width,
            height=self.config.height,
            target_language=self.config.target_language,
            source_language=self.config.source_language,
            default_transtyle_id=self.config.default_transtyle_id,
            transtyle_profiles=profiles,
            auto_translate_enabled=self.config.auto_translate_enabled,
            auto_translate_interval_ms=self.config.auto_translate_interval_ms,
            overlay_color=self.config.overlay_color,
            ui_language=self.config.ui_language,
            hotkey_modifier=self.config.hotkey_modifier,
            hotkey_key=self.config.hotkey_key,
            hotkey_backend=self.config.hotkey_backend,
            capture_provider=self.config.capture_provider,
            ocr_provider=self.config.ocr_provider,
            update_check_enabled=self.config.update_check_enabled,
            update_check_owner=self.config.update_check_owner,
            update_check_repo=self.config.update_check_repo,
            offline_translation_enabled=self.config.offline_translation_enabled,
            run_as_admin=self.config.run_as_admin,
            start_with_windows=self.config.start_with_windows,
            translator_provider=self.config.translator_provider,
            deepl_api_key=self.config.deepl_api_key,
            translator_failover_enabled=self.config.translator_failover_enabled,
            ghost_faa_enabled=self.config.ghost_faa_enabled,
            provider=self.config.provider,
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            model=self.config.model,
            font_family=self.config.font_family,
            font_size=self.config.font_size,
            text_color=self.config.text_color,
            cache_enabled=self.config.cache_enabled,
        )
        save_config(self.config_path, self.config)
        updated_boxes = [
            TranslatedBox(
                original=item.original,
                translated=corrected if item is box else item.translated,
                bbox=item.bbox,
                font_size=item.font_size,
                source_language=item.source_language,
                target_language=item.target_language,
                transtyle_id=item.transtyle_id,
            )
            for item in overlay._translated_boxes
        ]
        overlay.set_translated_boxes(updated_boxes)

    def _config_with_overlay_state(self, overlay: OverlayWindow) -> AppConfig:
        geometry = overlay.geometry()
        return AppConfig(
            x=geometry.x(),
            y=geometry.y(),
            width=geometry.width(),
            height=geometry.height(),
            target_language=overlay.target_language(),
            source_language=overlay.source_language(),
            auto_translate_enabled=self.config.auto_translate_enabled,
            auto_translate_interval_ms=self.config.auto_translate_interval_ms,
            overlay_color=self.config.overlay_color,
            ui_language=self.config.ui_language,
            hotkey_modifier=self.config.hotkey_modifier,
            hotkey_key=self.config.hotkey_key,
            hotkey_backend=self.config.hotkey_backend,
            capture_provider=self.config.capture_provider,
            ocr_provider=self.config.ocr_provider,
            update_check_enabled=self.config.update_check_enabled,
            update_check_owner=self.config.update_check_owner,
            update_check_repo=self.config.update_check_repo,
            offline_translation_enabled=self.config.offline_translation_enabled,
            run_as_admin=self.config.run_as_admin,
            start_with_windows=self.config.start_with_windows,
            default_transtyle_id=self.config.default_transtyle_id,
            transtyle_profiles=self.config.transtyle_profiles,
            translator_provider=self.config.translator_provider,
            deepl_api_key=self.config.deepl_api_key,
            translator_failover_enabled=self.config.translator_failover_enabled,
            ghost_faa_enabled=self.config.ghost_faa_enabled,
            provider=self.config.provider,
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            model=self.config.model,
            font_family=self.config.font_family,
            font_size=self.config.font_size,
            text_color=self.config.text_color,
            cache_enabled=self.config.cache_enabled,
        )

    def speak_overlay_text(self, overlay: OverlayWindow, text: str) -> None:
        try:
            self.speech_runner.speak(text)
        except SpeechUnavailableError as exc:
            self.logger.warning("TTS unavailable: %s", exc)
            if overlay in self.overlays:
                self.bridge.status_ready.emit(overlay, tr("tts_unavailable", self.config.ui_language))
        except Exception:
            self.logger.exception("TTS failed")
            if overlay in self.overlays:
                self.bridge.status_ready.emit(overlay, tr("tts_unavailable", self.config.ui_language))

    def _on_mouse_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        if not self.config.ghost_faa_enabled:
            return
        if button != mouse.Button.left:
            return
        if pressed:
            self.mouse_press_pos = (x, y)
            self.bridge.hide_answer_overlay_ready.emit(x, y)
            return
        start = self.mouse_press_pos
        self.mouse_press_pos = None
        if start is None:
            return
        if abs(x - start[0]) < 8 and abs(y - start[1]) < 8:
            return
        self.selection_anchor = (x, y)

        if self.config.ghost_faa_enabled:
            # Wait 150ms for Windows to finish the mouse up event before copying
            threading.Timer(0.15, self._start_answer_request).start()

    def _start_answer_request(self) -> None:
        threading.Thread(target=self._process_selection, daemon=True).start()

    def _process_selection(self) -> None:
        if not self.ai_worker_lock.acquire(blocking=False):
            self.bridge.answer_ready.emit("Đang xử lý câu trước.")
            return
        try:
            selected_text = get_selected_text()
            if not selected_text:
                self.bridge.answer_ready.emit("Không tìm thấy text bôi đen")
                return
                
            if self.config.cache_enabled and selected_text in self.ai_text_cache:
                self.bridge.answer_ready.emit(self.ai_text_cache[selected_text])
                return

            self.bridge.answer_ready.emit("...")

            api_key = self.config.api_key
            if not api_key:
                import os
                api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")

            if not api_key:
                self.bridge.answer_ready.emit("Chưa có API Key")
                return

            question_is_mcq = is_mcq(selected_text)
            client = LlmClient(
                self.config.provider,
                api_key,
                self.config.base_url,
                self.config.model,
            )
            answer = client.ask(selected_text, question_is_mcq)
            if question_is_mcq:
                answer = normalize_mcq_answer(answer)
                
            final_answer = answer or "Không có phản hồi"
            if self.config.cache_enabled:
                self.ai_text_cache[selected_text] = final_answer
                
            self.bridge.answer_ready.emit(final_answer)
        except Exception as exc:
            self.logger.exception("Failed to answer selection")
            self.bridge.answer_ready.emit(f"Lỗi kết nối API: {exc}")
        finally:
            self.ai_worker_lock.release()

    def hide_answer_overlay(self, x: int, y: int) -> None:
        if self.answer_overlay is None or not self.answer_overlay.isVisible():
            return
        rect = self.answer_overlay.geometry()
        if not rect.contains(x, y):
            self.answer_overlay.close()

    def show_answer(self, text: str, x: int | None = None, y: int | None = None) -> None:
        if text == "Chưa có API Key":
            if not self._prompt_for_auth_token():
                text = "Chưa có API Key"
            else:
                self._start_answer_request()
                return
        if self.answer_overlay is None or not self.answer_overlay.isVisible():
            self.answer_overlay = AnswerOverlay(text, config=self.config)
            self.answer_overlay.clicked.connect(self._start_answer_request)
        anchor = self.selection_anchor if x is None or y is None else (x, y)
        if anchor is None:
            self.answer_overlay.show_message(text)
            return
        self.answer_overlay.show_message(text, anchor[0], anchor[1])

    def _prompt_for_auth_token(self) -> bool:
        from dataclasses import replace
        auth_token, ok = QInputDialog.getText(None, "ViTai", "Nhập API KEY của bạn:")
        auth_token = auth_token.strip()
        if not ok or not auth_token:
            return False
        self.config = replace(self.config, api_key=auth_token)
        save_config(self.config_path, self.config)
        return True

    def quit(self) -> None:
        for overlay in list(self.auto_workers):
            self._stop_overlay_auto(overlay)
        if self.overlays:
            self.config = self._config_with_overlay_state(self.overlays[-1])
            save_config(self.config_path, self.config)
        self.speech_runner.stop()
        self.hotkey_manager.stop()
        self.faa_hotkey_manager.stop()
        if self.mouse_listener is not None:
            self.mouse_listener.stop()
        self.tray.hide()
        self.logger.info("ViTai quitting")
        self.qt_app.quit()


def main() -> int:
    app = ViTaiApp()
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
