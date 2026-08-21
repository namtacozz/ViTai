from __future__ import annotations

import logging
import subprocess
import sys
import threading
import time

_log = logging.getLogger("vitai.watcher")


class SelectionWatcher:
    """Thread nền theo dõi sự thay đổi của văn bản bôi đen (PRIMARY selection) trên Wayland/Linux.
    Phục vụ cho Fast Mode: Tự động kích hoạt AI ngay khi người dùng bôi đen mà không cần bấm phím."""

    def __init__(self, on_selection_callback):
        self._callback = on_selection_callback
        self._running = False
        self._enabled = False
        self._thread: threading.Thread | None = None
        self._last_text = ""
        self._debounce_timer: threading.Timer | None = None

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()
        _log.info("[WATCHER] SelectionWatcher đã khởi động")

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        if enabled:
            _log.info("[WATCHER] ⚡ Fast Mode đã BẬT: Đang theo dõi bôi đen tự động")
            self._last_text = self._read_primary() or ""
        else:
            _log.info("[WATCHER] Fast Mode đã TẮT")

    def stop(self) -> None:
        self._running = False
        if self._debounce_timer:
            self._debounce_timer.cancel()

    def _read_primary(self) -> str | None:
        if sys.platform == "win32":
            return None

        # 1. Linux Wayland: wl-paste --primary
        try:
            res = subprocess.run(
                ["wl-paste", "--primary", "--no-newline"],
                capture_output=True,
                text=True,
                timeout=1,
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception:
            pass

        # 2. Linux X11: xclip / xsel
        for cmd in [
            ["xclip", "-selection", "primary", "-o"],
            ["xsel", "--primary", "--output"],
        ]:
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=1)
                if res.returncode == 0 and res.stdout.strip():
                    return res.stdout.strip()
            except Exception:
                continue

        # 3. Qt QClipboard Selection mode (Cross-desktop Linux fallback)
        try:
            from PyQt6.QtGui import QClipboard, QGuiApplication

            app = QGuiApplication.instance()
            if app:
                cb = app.clipboard()
                if cb:
                    sel = cb.text(QClipboard.Mode.Selection)
                    if sel and sel.strip():
                        return sel.strip()
        except Exception:
            pass

        return None

    def _watch_loop(self) -> None:
        while self._running:
            try:
                time.sleep(0.3)
                if not self._enabled:
                    continue

                current = self._read_primary()
                if not current:
                    continue

                # Chỉ quét khi độ dài >= 15 ký tự (tránh quét khi chat/gõ từ ngắn)
                if current != self._last_text and len(current) >= 15:
                    self._last_text = current
                    _log.info(f"[WATCHER] ⚡ Phát hiện câu hỏi bôi đen ({len(current)} chars): '{current[:50]}...'")

                    # Debounce 0.75s: Chờ người dùng nhả chuột và dừng thao tác xong mới quét
                    if self._debounce_timer:
                        self._debounce_timer.cancel()
                    self._debounce_timer = threading.Timer(0.75, self._trigger)
                    self._debounce_timer.start()

            except Exception:
                time.sleep(0.5)

    def _trigger(self) -> None:
        if self._enabled and self._running:
            _log.info("[WATCHER] 🚀 Fast Mode: Tự động gửi câu hỏi bôi đen lên AI")
            self._callback()
