from __future__ import annotations

from collections.abc import Callable
import ctypes
import logging
import sys
import threading
import time

from vitai.darwin_compat import ensure_darwin_compat

ensure_darwin_compat()

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
        opt_map = {
            "œ": "q", "∑": "w", "´": "e", "®": "r", "†": "t", "¥": "y", "¨": "u", "ˆ": "i", "ø": "o", "π": "p",
            "å": "a", "ß": "s", "∂": "d", "ƒ": "f", "©": "g", "˙": "h", "∆": "j", "˚": "k", "¬": "l",
            "Ω": "z", "≈": "x", "ç": "c", "√": "v", "∫": "b", "˜": "n", "µ": "m",
        }
        self._modifier_str = modifier.lower().strip()
        raw_key = key.lower().strip()
        self._target_key_str = opt_map.get(raw_key, raw_key)
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
            # 1. Kiểm tra đối tượng phím bổ trợ enum trước (Key.alt, Key.ctrl, Key.cmd, Key.shift...)
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

            # 2. Ưu tiên tra cứu Hardware Virtual Keycode trên macOS từ VK_MAP_DARWIN
            if sys.platform == "darwin" and hasattr(key, 'vk') and key.vk is not None:
                from vitai.darwin_compat import VK_MAP_DARWIN
                if key.vk in VK_MAP_DARWIN:
                    return VK_MAP_DARWIN[key.vk]

            # 3. Tra cứu KeyCode & ký tự Unicode sinh ra bởi Option key
            char_val = getattr(key, "char", None)
            if char_val:
                opt_map = {
                    "œ": "q", "∑": "w", "´": "e", "®": "r", "†": "t", "¥": "y", "¨": "u", "ˆ": "i", "ø": "o", "π": "p",
                    "å": "a", "ß": "s", "∂": "d", "ƒ": "f", "©": "g", "˙": "h", "∆": "j", "˚": "k", "¬": "l",
                    "Ω": "z", "≈": "x", "ç": "c", "√": "v", "∫": "b", "˜": "n", "µ": "m",
                }
                if char_val in opt_map:
                    return opt_map[char_val]
                return char_val.lower()

            vk_val = getattr(key, "vk", None)
            if vk_val and isinstance(vk_val, int):
                if 65 <= vk_val <= 90:
                    return chr(vk_val).lower()
                return str(key).lower()

        k_str = str(key).lower()
        if "alt" in k_str or "opt" in k_str:
            return "alt"
        if "ctrl" in k_str or "control" in k_str:
            return "ctrl"
        if "shift" in k_str:
            return "shift"
        if "cmd" in k_str or "command" in k_str:
            return "cmd"
        return k_str

    def _on_press(self, key) -> None:
        name = self._canonical(key)
        self._pressed_keys.add(name)
        _LOGGER.info(f"[HOTKEY] 🎹 Nhận phím: '{name}' | Đang giữ: {list(self._pressed_keys)} | Chờ: '{self._modifier_str}+{self._target_key_str}'")

        if not self._is_mouse_trigger() and self._check_match():
            now = time.time()
            if now - self._last_trigger_time > 0.4:
                self._last_trigger_time = now
                _LOGGER.info(f"[HOTKEY] ✅ Khớp phím tắt bàn phím: {self._modifier_str}+{self._target_key_str} → Kích hoạt!")
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

    def _is_mod_pressed(self, mod: str) -> bool:
        if not mod:
            return True
        norm_mod = _normalize_modifier(mod)
        if norm_mod in self._pressed_keys or mod in self._pressed_keys:
            return True
        if sys.platform == "darwin":
            # Trên macOS, hỗ trợ tương thích chéo phím Command (⌘) và Control (⌃)
            if norm_mod in ("ctrl", "cmd"):
                if "ctrl" in self._pressed_keys or "cmd" in self._pressed_keys:
                    return True
        if norm_mod == "alt" and ("alt" in self._pressed_keys or "opt" in self._pressed_keys):
            return True
        return False

    def _check_modifiers_only(self) -> bool:
        if not self._modifier_str or self._modifier_str in ("none", ""):
            return True
        mods = [_normalize_modifier(m) for m in self._modifier_str.split("+") if m.strip()]
        for m in mods:
            if m and not self._is_mod_pressed(m):
                return False
        return True

    def _check_match(self) -> bool:
        mods = [_normalize_modifier(m) for m in self._modifier_str.split("+") if m.strip()]
        for m in mods:
            if m and not self._is_mod_pressed(m):
                return False
        return self._target_key_str in self._pressed_keys


class _DarwinCGEventTapHotkeyBackend:
    """
    Backend bắt phím tắt & chuột Native Quartz CoreGraphics trên macOS:
    - Bắt sự kiện bàn phím/chuột toàn cục trực tiếp từ WindowServer
    - Nhận diện tức thì phím Option+Q, Option+Cmd+V, Option+Ctrl+V...
    - Tự động phục hồi nếu Event Tap bị hệ thống tạm ngắt (kCGEventTapDisabledByTimeout)
    """
    def __init__(self, modifier: str, key: str, callback: Callable[[], None]):
        self._modifier_str = modifier.lower().strip()
        raw_key = key.lower().strip()
        opt_map = {
            "œ": "q", "∑": "w", "´": "e", "®": "r", "†": "t", "¥": "y", "¨": "u", "ˆ": "i", "ø": "o", "π": "p",
            "å": "a", "ß": "s", "∂": "d", "ƒ": "f", "©": "g", "˙": "h", "∆": "j", "˚": "k", "¬": "l",
            "Ω": "z", "≈": "x", "ç": "c", "√": "v", "∫": "b", "˜": "n", "µ": "m",
        }
        self._target_key_str = opt_map.get(raw_key, raw_key)
        self._callback = callback
        self._last_trigger_time = 0.0
        self._thread: threading.Thread | None = None
        self._run_loop: Any = None
        self._mach_port: Any = None
        self._callback_ref: Any = None
        self._running = False

    def start(self) -> None:
        if sys.platform != "darwin" or self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop_thread, daemon=True, name="DarwinCGEventTap")
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._run_loop:
            try:
                import ctypes
                cf_path = ctypes.util.find_library("CoreFoundation") or "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation"
                cf = ctypes.cdll.LoadLibrary(cf_path)
                if hasattr(cf, "CFRunLoopStop"):
                    cf.CFRunLoopStop(self._run_loop)
            except Exception:
                pass
        self._run_loop = None
        self._mach_port = None

    def _run_loop_thread(self) -> None:
        try:
            import ctypes
            import ctypes.util
            cg_path = ctypes.util.find_library("CoreGraphics") or "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics"
            cf_path = ctypes.util.find_library("CoreFoundation") or "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation"
            cg = ctypes.cdll.LoadLibrary(cg_path)
            cf = ctypes.cdll.LoadLibrary(cf_path)

            if not hasattr(cg, "CGEventTapCreate") or not hasattr(cf, "CFRunLoopGetCurrent"):
                return

            CGEventTapCallback = ctypes.CFUNCTYPE(
                ctypes.c_void_p,
                ctypes.c_void_p,
                ctypes.c_uint32,
                ctypes.c_void_p,
                ctypes.c_void_p,
            )

            kCGSessionEventTap = 1
            kCGHeadInsertEventTap = 0
            kCGEventTapOptionListenOnly = 1

            # KeyDown=10, KeyUp=11, FlagsChanged=12, LeftDown=1, RightDown=3, OtherDown=25
            event_mask = (1 << 10) | (1 << 11) | (1 << 12) | (1 << 1) | (1 << 3) | (1 << 25)

            kCGEventFlagMaskAlternate = 0x00080000  # Option
            kCGEventFlagMaskCommand   = 0x00100000  # Command
            kCGEventFlagMaskControl   = 0x00040000  # Control
            kCGEventFlagMaskShift     = 0x00020000  # Shift

            kCGKeyboardEventKeycode = 9
            kCGMouseEventButtonNumber = 3

            char_to_vk = {
                "q": 12, "w": 13, "e": 14, "r": 15, "t": 17, "y": 16, "u": 32, "i": 34, "o": 31, "p": 35,
                "a": 0, "s": 1, "d": 2, "f": 3, "g": 5, "h": 4, "j": 38, "k": 40, "l": 37,
                "z": 6, "x": 7, "c": 8, "v": 9, "b": 11, "n": 45, "m": 46,
                "1": 18, "2": 19, "3": 20, "4": 21, "5": 23, "6": 22, "7": 26, "8": 28, "9": 25, "0": 29,
                "space": 49, "tab": 48, "return": 36, "enter": 36, "esc": 53,
            }
            target_vk = char_to_vk.get(self._target_key_str, None)

            cg.CGEventGetFlags.restype = ctypes.c_uint64
            cg.CGEventGetFlags.argtypes = [ctypes.c_void_p]
            cg.CGEventGetIntegerValueField.restype = ctypes.c_int64
            cg.CGEventGetIntegerValueField.argtypes = [ctypes.c_void_p, ctypes.c_uint32]

            def tap_callback(proxy, event_type, event, refcon):
                if event_type == 0xFFFFFFFE:  # kCGEventTapDisabledByTimeout
                    if self._mach_port and hasattr(cg, "CGEventTapEnable"):
                        cg.CGEventTapEnable(self._mach_port, True)
                    return event

                # Handle KeyDown (10)
                if event_type == 10:
                    flags = cg.CGEventGetFlags(event)
                    keycode = cg.CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)

                    is_alt = bool(flags & kCGEventFlagMaskAlternate)
                    is_cmd = bool(flags & kCGEventFlagMaskCommand)
                    is_ctrl = bool(flags & kCGEventFlagMaskControl)
                    is_shift = bool(flags & kCGEventFlagMaskShift)

                    mods_req = [_normalize_modifier(m) for m in self._modifier_str.split("+") if m.strip()]
                    mod_ok = True
                    for m in mods_req:
                        if m == "alt" and not is_alt:
                            mod_ok = False
                        elif m == "cmd" and not (is_cmd or is_ctrl):
                            mod_ok = False
                        elif m == "ctrl" and not (is_ctrl or is_cmd):
                            mod_ok = False
                        elif m == "shift" and not is_shift:
                            mod_ok = False

                    if mod_ok and target_vk is not None and keycode == target_vk:
                        now = time.time()
                        if now - self._last_trigger_time > 0.35:
                            self._last_trigger_time = now
                            _LOGGER.info(f"[NATIVE_DARWIN_TAP] 🎯 Phím tắt kích hoạt ({self._modifier_str}+{self._target_key_str})!")
                            self._callback()

                # Handle Mouse Clicks (1=Left, 3=Right, 25=Other)
                elif event_type in (1, 3, 25) and self._target_key_str.startswith("mouse_"):
                    flags = cg.CGEventGetFlags(event)
                    is_alt = bool(flags & kCGEventFlagMaskAlternate)
                    is_cmd = bool(flags & kCGEventFlagMaskCommand)
                    is_ctrl = bool(flags & kCGEventFlagMaskControl)
                    is_shift = bool(flags & kCGEventFlagMaskShift)

                    mods_req = [_normalize_modifier(m) for m in self._modifier_str.split("+") if m.strip()]
                    mod_ok = True
                    for m in mods_req:
                        if m == "alt" and not is_alt:
                            mod_ok = False
                        elif m == "cmd" and not (is_cmd or is_ctrl):
                            mod_ok = False
                        elif m == "ctrl" and not (is_ctrl or is_cmd):
                            mod_ok = False
                        elif m == "shift" and not is_shift:
                            mod_ok = False

                    matched_btn = False
                    if event_type == 3 and self._target_key_str in ("mouse_right", "right"):
                        matched_btn = True
                    elif event_type == 1 and self._target_key_str in ("mouse_left", "left"):
                        matched_btn = True
                    elif event_type == 25:
                        btn_num = cg.CGEventGetIntegerValueField(event, kCGMouseEventButtonNumber)
                        if btn_num == 2 and self._target_key_str in ("mouse_middle", "middle"):
                            matched_btn = True
                        elif btn_num == 3 and self._target_key_str in ("mouse_x1", "mouse_side", "x1"):
                            matched_btn = True
                        elif btn_num == 4 and self._target_key_str in ("mouse_x2", "mouse_extra", "x2"):
                            matched_btn = True

                    if mod_ok and matched_btn:
                        now = time.time()
                        if now - self._last_trigger_time > 0.35:
                            self._last_trigger_time = now
                            _LOGGER.info(f"[NATIVE_DARWIN_TAP] 🖱️ Chuột kích hoạt ({self._modifier_str}+{self._target_key_str})!")
                            self._callback()

                return event

            self._callback_ref = CGEventTapCallback(tap_callback)

            cg.CGEventTapCreate.restype = ctypes.c_void_p
            cg.CGEventTapCreate.argtypes = [
                ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint64,
                CGEventTapCallback, ctypes.c_void_p
            ]
            self._mach_port = cg.CGEventTapCreate(
                kCGSessionEventTap,
                kCGHeadInsertEventTap,
                kCGEventTapOptionListenOnly,
                event_mask,
                self._callback_ref,
                None,
            )

            if not self._mach_port:
                _LOGGER.warning("[NATIVE_DARWIN_TAP] Không thể tạo CGEventTap! Yêu cầu cấp quyền Trợ năng (Accessibility)...")
                from vitai.darwin_compat import check_and_request_macos_accessibility
                check_and_request_macos_accessibility()
                return

            cf.CFMachPortCreateRunLoopSource.restype = ctypes.c_void_p
            cf.CFMachPortCreateRunLoopSource.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_long]
            source = cf.CFMachPortCreateRunLoopSource(None, self._mach_port, 0)
            if not source:
                return

            self._run_loop = cf.CFRunLoopGetCurrent()
            cf.CFRunLoopAddSource.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
            cf.CFRunLoopAddSource(self._run_loop, source, getattr(cf, "kCFRunLoopCommonModes", None))

            cg.CGEventTapEnable(self._mach_port, True)
            _LOGGER.info(f"[NATIVE_DARWIN_TAP] ✅ Quartz Event Tap đang chạy: {self._modifier_str}+{self._target_key_str}")
            cf.CFRunLoopRun()
        except Exception as e:
            _LOGGER.error(f"[NATIVE_DARWIN_TAP] Lỗi khởi động event tap: {e}")


class _DarwinHybridHotkeyBackend:
    """
    Backend kết hợp đồng thời Quartz Native Event Tap và Pynput trên macOS
    để đảm bảo không bao giờ trượt phím tắt.
    """
    def __init__(self, modifier: str, key: str, callback: Callable[[], None]):
        self._shared_last_time = [0.0]

        def _debounced_callback():
            now = time.time()
            if now - self._shared_last_time[0] > 0.35:
                self._shared_last_time[0] = now
                callback()

        self._pynput = _PynputHotkeyBackend(modifier, key, _debounced_callback)
        self._native = _DarwinCGEventTapHotkeyBackend(modifier, key, _debounced_callback)

    def start(self) -> None:
        try:
            self._native.start()
        except Exception as e:
            _LOGGER.warning(f"Native Darwin tap start error: {e}")
        try:
            self._pynput.start()
        except Exception as e:
            _LOGGER.warning(f"Pynput start error: {e}")

    def stop(self) -> None:
        self._native.stop()
        self._pynput.stop()


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
        self._backend: _PynputHotkeyBackend | _Win32HotkeyBackend | _DarwinHybridHotkeyBackend | None = None

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
        if sys.platform == "darwin":
            return _DarwinHybridHotkeyBackend(self._modifier, self._key, self._callback)

        if self._key.startswith("mouse_") or self._backend_id == "pynput":
            return _PynputHotkeyBackend(self._modifier, self._key, self._callback)

        if self._backend_id in {"auto", "win32"}:
            try:
                return _Win32HotkeyBackend(self._modifier, self._key, self._callback)
            except Exception as exc:
                _LOGGER.warning("Win32 hotkey backend failed, falling back to pynput: %s", exc)
                return _PynputHotkeyBackend(self._modifier, self._key, self._callback)
        return _PynputHotkeyBackend(self._modifier, self._key, self._callback)


def create_hotkey_manager(modifier: str, key: str, callback: Callable[[], None]) -> HotkeyManager:
    return HotkeyManager(modifier, key, callback)
