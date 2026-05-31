from __future__ import annotations

from collections.abc import Callable
import ctypes
import logging
import sys
import threading

from pynput import keyboard

_LOGGER = logging.getLogger(__name__)


class _PynputHotkeyBackend:
    def __init__(self, combo: str, callback: Callable[[], None]):
        self._listener = keyboard.GlobalHotKeys({combo: callback})

    def start(self) -> None:
        self._listener.start()

    def stop(self) -> None:
        self._listener.stop()


class _Win32HotkeyBackend:
    MODIFIERS = {
        "alt": 0x0001,
        "ctrl": 0x0002,
        "shift": 0x0004,
        "win": 0x0008,
    }
    WM_HOTKEY = 0x0312

    def __init__(self, combo: str, callback: Callable[[], None]):
        if sys.platform != "win32":
            raise RuntimeError("Win32 hotkey backend is only available on Windows")
        self._callback = callback
        self._hotkey_id = 1
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._modifier, self._key_code = self._parse_combo(combo)

    def start(self) -> None:
        user32 = ctypes.windll.user32
        if not user32.RegisterHotKey(None, self._hotkey_id, self._modifier, self._key_code):
            raise RuntimeError("RegisterHotKey failed")
        self._thread = threading.Thread(target=self._message_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        ctypes.windll.user32.UnregisterHotKey(None, self._hotkey_id)
        if self._thread is not None and threading.current_thread() is not self._thread:
            self._thread.join(timeout=0.5)
            self._thread = None

    def _message_loop(self) -> None:
        msg = ctypes.wintypes.MSG()
        user32 = ctypes.windll.user32
        while not self._stop_event.is_set():
            result = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if result == 0 or result == -1:
                return
            if msg.message == self.WM_HOTKEY:
                self._callback()
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

    @classmethod
    def _parse_combo(cls, combo: str) -> tuple[int, int]:
        parts = combo.split("+")
        modifier = 0
        key = parts[-1]
        for part in parts[:-1]:
            name = part.strip("<>").lower()
            modifier |= cls.MODIFIERS.get(name, 0)
        if len(key) != 1:
            raise RuntimeError(f"Unsupported hotkey key: {key}")
        return modifier, ord(key.upper())


class HotkeyManager:
    def __init__(self, modifier: str, key: str, callback: Callable[[], None], backend: str = "auto"):
        self._modifier = modifier
        self._key = key
        self._callback = callback
        self._backend_id = backend
        self._backend: _PynputHotkeyBackend | _Win32HotkeyBackend | None = None

    def start(self) -> None:
        combo = self._build_combo_string()
        self._backend = self._create_backend(combo)
        self._backend.start()

    def stop(self) -> None:
        if self._backend is not None:
            self._backend.stop()
            self._backend = None

    def update(self, modifier: str, key: str, backend: str | None = None) -> None:
        self.stop()
        self._modifier = modifier
        self._key = key
        if backend is not None:
            self._backend_id = backend
        self.start()

    @property
    def display_text(self) -> str:
        parts = self._modifier.split("+")
        return "+".join(p.strip().capitalize() for p in parts) + f"+{self._key.upper()}"

    def _build_combo_string(self) -> str:
        parts = self._modifier.split("+")
        prefix = "+".join(f"<{p.strip()}>" for p in parts)
        return f"{prefix}+{self._key}"

    def _create_backend(self, combo: str):
        if self._backend_id == "pynput":
            return _PynputHotkeyBackend(combo, self._callback)
        if self._backend_id in {"auto", "win32"}:
            try:
                return _Win32HotkeyBackend(combo, self._callback)
            except Exception as exc:
                _LOGGER.warning("Win32 hotkey backend failed, falling back to pynput: %s", exc)
                return _PynputHotkeyBackend(combo, self._callback)
        return _PynputHotkeyBackend(combo, self._callback)
