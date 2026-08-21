from __future__ import annotations

import ctypes
import logging
import os
import subprocess
import sys
import time

_log = logging.getLogger("vitai.capture")

# --- Windows Win32 API setup ---
if sys.platform == "win32":
    INPUT_KEYBOARD = 1
    KEYEVENTF_KEYUP = 0x0002
    VK_CONTROL = 0x11
    VK_MENU = 0x12
    VK_SHIFT = 0x10
    VK_LWIN = 0x5B
    VK_RWIN = 0x5C
    VK_C = 0x43
    ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort),
            ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong),
            ("dwExtraInfo", ULONG_PTR),
        ]
    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [
            ("dx", ctypes.c_long), ("dy", ctypes.c_long),
            ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong),
            ("time", ctypes.c_ulong), ("dwExtraInfo", ULONG_PTR),
        ]
    class HARDWAREINPUT(ctypes.Structure):
        _fields_ = [("uMsg", ctypes.c_ulong), ("wParamL", ctypes.c_ushort), ("wParamH", ctypes.c_ushort)]
    class INPUT_UNION(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]
    class INPUT(ctypes.Structure):
        _fields_ = [("type", ctypes.c_ulong), ("union", INPUT_UNION)]

    def _keyboard_input(key: int, flags: int = 0) -> INPUT:
        return INPUT(type=INPUT_KEYBOARD, union=INPUT_UNION(ki=KEYBDINPUT(key, 0, flags, 0, 0)))

    def _send_ctrl_c_windows() -> None:
        inputs = (INPUT * 8)(
            _keyboard_input(VK_MENU, KEYEVENTF_KEYUP), _keyboard_input(VK_SHIFT, KEYEVENTF_KEYUP),
            _keyboard_input(VK_LWIN, KEYEVENTF_KEYUP), _keyboard_input(VK_RWIN, KEYEVENTF_KEYUP),
            _keyboard_input(VK_CONTROL), _keyboard_input(VK_C),
            _keyboard_input(VK_C, KEYEVENTF_KEYUP), _keyboard_input(VK_CONTROL, KEYEVENTF_KEYUP),
        )
        ctypes.windll.user32.SendInput(len(inputs), ctypes.byref(inputs), ctypes.sizeof(INPUT))


def _is_wayland() -> bool:
    return os.environ.get("XDG_SESSION_TYPE") == "wayland" or bool(os.environ.get("WAYLAND_DISPLAY"))


def _read_primary_selection_wayland() -> str | None:
    """Đọc text bôi đen từ PRIMARY selection trên Wayland (không cần Ctrl+C)."""
    try:
        res = subprocess.run(
            ["wl-paste", "--primary", "--no-newline"],
            capture_output=True, text=True, timeout=2,
        )
        text = res.stdout.strip()
        if res.returncode == 0 and text:
            _log.info(f"[CAPTURE] wl-paste --primary OK, đọc được {len(text)} ký tự: '{text[:50]}...'")
            return text
        else:
            _log.warning(f"[CAPTURE] wl-paste --primary rỗng. rc={res.returncode}, stderr='{res.stderr.strip()}'")
    except Exception as e:
        _log.error(f"[CAPTURE] wl-paste --primary lỗi: {e}")
    return None


def _read_clipboard_wayland() -> str | None:
    """Đọc clipboard thường trên Wayland."""
    try:
        res = subprocess.run(
            ["wl-paste", "--no-newline"],
            capture_output=True, text=True, timeout=2,
        )
        text = res.stdout.strip()
        if res.returncode == 0 and text:
            _log.info(f"[CAPTURE] wl-paste clipboard OK: '{text[:50]}...'")
            return text
        else:
            _log.warning(f"[CAPTURE] wl-paste clipboard rỗng. stderr='{res.stderr.strip()}'")
    except Exception as e:
        _log.error(f"[CAPTURE] wl-paste clipboard lỗi: {e}")
    return None


def _read_primary_selection_x11() -> str | None:
    """Đọc PRIMARY selection trên X11."""
    for cmd in [
        ["xclip", "-selection", "primary", "-o"],
        ["xsel", "--primary", "--output"],
    ]:
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
            if res.returncode == 0 and res.stdout.strip():
                _log.info(f"[CAPTURE] {cmd[0]} primary OK: '{res.stdout.strip()[:50]}...'")
                return res.stdout.strip()
        except FileNotFoundError:
            continue
        except Exception:
            continue
    return None


def _simulate_ctrl_c_ydotool() -> bool:
    """Giả lập Ctrl+C bằng ydotool (Wayland-native)."""
    try:
        _log.info("[CAPTURE] Thử ydotool key Ctrl+C...")
        result = subprocess.run(
            ["ydotool", "key", "29:1", "46:1", "46:0", "29:0"],
            capture_output=True, timeout=2,
        )
        ok = result.returncode == 0
        _log.info(f"[CAPTURE] ydotool rc={result.returncode}, stderr='{result.stderr.decode().strip()}'")
        return ok
    except Exception as e:
        _log.warning(f"[CAPTURE] ydotool lỗi: {e}")
        return False


def _simulate_ctrl_c_pynput() -> bool:
    """Giả lập Ctrl+C bằng pynput (chỉ hoạt động trên X11 / Windows / macOS)."""
    try:
        from pynput.keyboard import Controller, Key
        kb = Controller()
        kb.release(Key.alt)
        kb.release(Key.alt_l)
        kb.release(Key.alt_r)
        if sys.platform == "darwin":
            kb.release(Key.cmd)
            kb.release(Key.cmd_l)
            kb.release(Key.cmd_r)
        time.sleep(0.03)
        cmd_key = Key.cmd if sys.platform == "darwin" else Key.ctrl
        with kb.pressed(cmd_key):
            kb.tap('c')
        _log.info("[CAPTURE] pynput Ctrl+C/Cmd+C đã gửi.")
        return True
    except Exception as e:
        _log.warning(f"[CAPTURE] pynput Ctrl+C/Cmd+C lỗi: {e}")
        return False


def _simulate_cmd_c_macos_applescript() -> bool:
    """Giả lập Cmd+C trên macOS bằng AppleScript (System Events)."""
    try:
        res = subprocess.run(
            ["osascript", "-e", 'tell application "System Events" to keystroke "c" using command down'],
            capture_output=True,
            text=True,
            timeout=2,
        )
        ok = res.returncode == 0
        _log.info(f"[CAPTURE] macOS osascript Cmd+C: ok={ok}")
        return ok
    except Exception as e:
        _log.warning(f"[CAPTURE] macOS osascript Cmd+C lỗi: {e}")
        return False


def _read_clipboard_macos() -> str | None:
    """Đọc clipboard trên macOS (hỗ trợ pbpaste và pyperclip)."""
    try:
        import pyperclip
        text = pyperclip.paste()
        if text and text.strip():
            return text.strip()
    except Exception:
        pass

    try:
        res = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=2)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        pass
    return None


def _get_selected_text_macos() -> str | None:
    """Bắt text bôi đen trên macOS bằng Cmd+C (pynput + fallback osascript)."""
    _log.info("[CAPTURE] macOS: Bắt đầu lấy text bôi đen qua Cmd+C...")
    try:
        import pyperclip
        original_clip = ""
        try:
            original_clip = pyperclip.paste()
        except Exception:
            pass

        try:
            pyperclip.copy("")
        except Exception:
            pass

        # 1. Thử gửi Cmd+C qua pynput
        success = _simulate_ctrl_c_pynput()
        time.sleep(0.12)
        selected = _read_clipboard_macos()

        # 2. Nếu chưa đọc được, thử fallback qua osascript AppleScript
        if not selected:
            _log.info("[CAPTURE] pynput chưa bắt được text trên macOS, thử fallback AppleScript...")
            if _simulate_cmd_c_macos_applescript():
                time.sleep(0.12)
                selected = _read_clipboard_macos()

        if selected:
            _log.info(f"[CAPTURE] ✅ macOS thành công: '{selected[:80]}'")
            return selected

        # Khôi phục lại clipboard cũ nếu không lấy được text mới
        if original_clip:
            try:
                pyperclip.copy(original_clip)
            except Exception:
                pass
    except Exception as e:
        _log.error(f"[CAPTURE] macOS lỗi: {e}")

    _log.warning("[CAPTURE] ❌ Không thể đọc text bôi đen trên macOS.")
    return None


def get_selected_text(delay: float = 0.05) -> str | None:
    """Lấy text đang bôi đen.
    
    Chiến lược:
    1. Linux Wayland: Đọc PRIMARY selection trực tiếp (không cần Ctrl+C)
    2. macOS: Giả lập Cmd+C bằng pynput / osascript và đọc clipboard (pbpaste / pyperclip)
    3. Windows: Giả lập Ctrl+C bằng Win32 API
    4. Linux X11: Đọc PRIMARY selection, hoặc giả lập Ctrl+C
    """
    _log.info(f"[CAPTURE] === Bắt đầu get_selected_text === (wayland={_is_wayland()}, platform={sys.platform})")

    # --- WAYLAND ---
    if _is_wayland():
        _log.info("[CAPTURE] Wayland: Đọc PRIMARY selection (wl-paste --primary)...")
        text = _read_primary_selection_wayland()
        if text:
            _log.info(f"[CAPTURE] ✅ Thành công! Text: '{text[:80]}'")
            return text

        _log.info("[CAPTURE] PRIMARY rỗng. Thử đọc clipboard thường...")
        text = _read_clipboard_wayland()
        if text:
            _log.info(f"[CAPTURE] ✅ Clipboard thường có text: '{text[:80]}'")
            return text

        _log.info("[CAPTURE] Clipboard cũng rỗng. Thử ydotool Ctrl+C...")
        if _simulate_ctrl_c_ydotool():
            time.sleep(0.2)
            text = _read_clipboard_wayland()
            if text:
                _log.info(f"[CAPTURE] ✅ ydotool + clipboard OK: '{text[:80]}'")
                return text

        _log.warning("[CAPTURE] ❌ Không thể đọc text bôi đen trên Wayland.")
        return None

    # --- MACOS ---
    if sys.platform == "darwin":
        return _get_selected_text_macos()

    # --- WINDOWS ---
    if sys.platform == "win32":
        _log.info("[CAPTURE] Windows: Giả lập Ctrl+C bằng Win32 API...")
        try:
            import pyperclip
            original = pyperclip.paste()
            pyperclip.copy("")
            _send_ctrl_c_windows()
            time.sleep(0.15)
            selected = pyperclip.paste()
            pyperclip.copy(original)
            selected = selected.strip()
            if selected and selected != original.strip():
                _log.info(f"[CAPTURE] ✅ Windows OK: '{selected[:80]}'")
                return selected
        except Exception as e:
            _log.error(f"[CAPTURE] Windows lỗi: {e}")
        return None

    # --- LINUX X11 ---
    _log.info("[CAPTURE] X11: Đọc PRIMARY selection...")
    text = _read_primary_selection_x11()
    if text:
        return text

    _log.info("[CAPTURE] PRIMARY rỗng. Thử pynput Ctrl+C...")
    if _simulate_ctrl_c_pynput():
        time.sleep(0.15)
        text = _read_primary_selection_x11()
        if text:
            return text
        try:
            import pyperclip
            text = pyperclip.paste()
            if text and text.strip():
                return text.strip()
        except Exception:
            pass

    _log.warning("[CAPTURE] ❌ Không thể đọc text trên X11.")
    return None

