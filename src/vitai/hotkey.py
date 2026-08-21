from __future__ import annotations

from collections.abc import Callable
import ctypes
import logging
import sys
import threading
import time

try:
    from pynput import keyboard, mouse
except Exception:
    keyboard = None  # type: ignore
    mouse = None  # type: ignore

_LOGGER = logging.getLogger("vitai.hotkey")


def _normalize_modifier(mod: str) -> str:
    m = mod.strip().lower()
    if m in ("cmd", "command", "super", "win", "meta"):
        return "cmd"
    if m in ("alt", "opt", "option"):
        return "alt"
    if m in ("ctrl", "control"):
        return "ctrl"
    if m in ("shift",):
        return "shift"
    if m in ("none", ""):
        return ""
    return m


def _canonical_mouse_button(button) -> str:
    if mouse is not None:
        if button == mouse.Button.right:
            return "mouse_right"
        if button == mouse.Button.middle:
            return "mouse_middle"
        if button == mouse.Button.left:
            return "mouse_left"
        if button == getattr(mouse.Button, "x1", None):
            return "mouse_x1"
        if button == getattr(mouse.Button, "x2", None):
            return "mouse_x2"
    btn_str = str(button).lower()
    if "right" in btn_str:
        return "mouse_right"
    if "middle" in btn_str:
        return "mouse_middle"
    if "left" in btn_str:
        return "mouse_left"
    if "x1" in btn_str or "back" in btn_str or "button8" in btn_str:
        return "mouse_x1"
    if "x2" in btn_str or "forward" in btn_str or "button9" in btn_str:
        return "mouse_x2"
    return "mouse_extra"


def format_key_display(key_str: str) -> str:
    k = key_str.strip().lower()
    if k == "mouse_right":
        return "Chuột Phải"
    if k == "mouse_middle":
        return "Chuột Giữa"
    if k == "mouse_left":
        return "Chuột Trái"
    if k in ("mouse_x1", "mouse_side"):
        return "Nút Chuột Phụ 1 (Back)"
    if k in ("mouse_x2", "mouse_extra"):
        return "Nút Chuột Phụ 2 (Forward)"
    return k.upper()


class _PynputHotkeyBackend:
    def __init__(self, modifier: str, key: str, callback: Callable[[], None]):
        self._modifier_str = modifier.lower()
        self._target_key_str = key.lower()
        self._callback = callback
        self._pressed_keys: set[str] = set()
        self._last_trigger_time = 0.0
        self._kb_listener: keyboard.Listener | None = None
        self._mouse_listener: mouse.Listener | None = None

    def start(self) -> None:
        _LOGGER.info(f"[HOTKEY] Pynput listener khởi động: lắng nghe {self._modifier_str}+{self._target_key_str}")
        self._kb_listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._kb_listener.start()

        # Nếu target_key là phím chuột, kích hoạt thêm mouse listener để bắt trigger
        if self._is_mouse_trigger():
            self._mouse_listener = mouse.Listener(
                on_click=self._on_mouse_click,
            )
            self._mouse_listener.start()

    def stop(self) -> None:
        if self._kb_listener is not None:
            self._kb_listener.stop()
            self._kb_listener = None
        if self._mouse_listener is not None:
            self._mouse_listener.stop()
            self._mouse_listener = None

    def _is_mouse_trigger(self) -> bool:
        return self._target_key_str.startswith("mouse_") or self._target_key_str in (
            "right", "middle", "left", "x1", "x2", "side", "extra"
        )

    def _canonical(self, key) -> str:
        if keyboard is not None:
            if isinstance(key, keyboard.KeyCode):
                if key.char:
                    return key.char.lower()
                if hasattr(key, 'vk') and key.vk:
                    if 65 <= key.vk <= 90:
                        return chr(key.vk).lower()
                return str(key).lower()
            if key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr):
                return "alt"
            if key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
                return "ctrl"
            if key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
                return "shift"
            if hasattr(keyboard.Key, 'cmd') and key in (
                getattr(keyboard.Key, 'cmd', None),
                getattr(keyboard.Key, 'cmd_l', None),
                getattr(keyboard.Key, 'cmd_r', None),
            ):
                return "cmd"
        k_str = str(key).lower()
        if "alt" in k_str:
            return "alt"
        if "ctrl" in k_str:
            return "ctrl"
        if "shift" in k_str:
            return "shift"
        if "cmd" in k_str:
            return "cmd"
        return k_str

    def _on_press(self, key) -> None:
        name = self._canonical(key)
        self._pressed_keys.add(name)

        if not self._is_mouse_trigger() and self._check_match():
            now = time.time()
            if now - self._last_trigger_time > 0.4:
                self._last_trigger_time = now
                _LOGGER.info(f"[HOTKEY] ✅ Phát hiện phím tắt bàn phím: {self._modifier_str}+{self._target_key_str} → Kích hoạt!")
                self._callback()

    def _on_release(self, key) -> None:
        name = self._canonical(key)
        self._pressed_keys.discard(name)

    def _on_mouse_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        if not pressed:
            return
        btn_name = _canonical_mouse_button(button)
        matches_btn = (
            btn_name == self._target_key_str
            or (btn_name == "mouse_x1" and self._target_key_str in ("mouse_x1", "mouse_side", "x1"))
            or (btn_name == "mouse_x2" and self._target_key_str in ("mouse_x2", "mouse_extra", "x2"))
            or (btn_name == "mouse_right" and self._target_key_str == "right")
            or (btn_name == "mouse_middle" and self._target_key_str == "middle")
            or (btn_name == "mouse_left" and self._target_key_str == "left")
        )

        if matches_btn and self._check_modifiers_only():
            now = time.time()
            if now - self._last_trigger_time > 0.4:
                self._last_trigger_time = now
                _LOGGER.info(f"[HOTKEY] 🖱️ Phát hiện phím chuột kích hoạt: {self._modifier_str}+{self._target_key_str} → Kích hoạt!")
                self._callback()

    def _check_modifiers_only(self) -> bool:
        if not self._modifier_str or self._modifier_str in ("none", ""):
            return True
        mods = [_normalize_modifier(m) for m in self._modifier_str.split("+") if m.strip()]
        for m in mods:
            if m and m not in self._pressed_keys:
                return False
        return True

    def _check_match(self) -> bool:
        mods = [_normalize_modifier(m) for m in self._modifier_str.split("+") if m.strip()]
        for m in mods:
            if m and m not in self._pressed_keys:
                return False
        return self._target_key_str in self._pressed_keys


class _Win32HotkeyBackend:
    MODIFIERS = {
        "alt": 0x0001,
        "ctrl": 0x0002,
        "shift": 0x0004,
        "win": 0x0008,
    }
    WM_HOTKEY = 0x0312

    def __init__(self, modifier: str, key: str, callback: Callable[[], None]):
        if sys.platform != "win32":
            raise RuntimeError("Win32 hotkey backend is only available on Windows")
        self._callback = callback
        self._hotkey_id = 1
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        combo = f"{modifier}+{key}"
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
        self._backend = self._create_backend()
        try:
            self._backend.start()
        except Exception as exc:
            if isinstance(self._backend, _Win32HotkeyBackend):
                _LOGGER.warning("Win32 hotkey backend failed on start, falling back to pynput: %s", exc)
                self._backend = _PynputHotkeyBackend(self._modifier, self._key, self._callback)
                self._backend.start()
            else:
                raise

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
        parts = self._modifier.split("+") if self._modifier and self._modifier != "none" else []
        formatted = []
        for p in parts:
            p_norm = _normalize_modifier(p)
            if p_norm == "cmd":
                formatted.append("Cmd" if sys.platform == "darwin" else "Win")
            elif p_norm == "alt":
                formatted.append("Opt" if sys.platform == "darwin" else "Alt")
            elif p_norm == "ctrl":
                formatted.append("Ctrl")
            elif p_norm == "shift":
                formatted.append("Shift")
            elif p.strip():
                formatted.append(p.strip().capitalize())

        key_disp = format_key_display(self._key)
        if formatted:
            return "+".join(formatted) + f"+{key_disp}"
        return key_disp

    def _create_backend(self):
        # Nếu target_key là phím chuột, bắt buộc dùng pynput
        if self._key.startswith("mouse_") or self._backend_id == "pynput":
            return _PynputHotkeyBackend(self._modifier, self._key, self._callback)

        if self._backend_id in {"auto", "win32"}:
            try:
                return _Win32HotkeyBackend(self._modifier, self._key, self._callback)
            except Exception as exc:
                _LOGGER.warning("Win32 hotkey backend failed, falling back to pynput: %s", exc)
                return _PynputHotkeyBackend(self._modifier, self._key, self._callback)
        return _PynputHotkeyBackend(self._modifier, self._key, self._callback)
