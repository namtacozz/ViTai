from __future__ import annotations

import ctypes
import time

import pyperclip

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
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ULONG_PTR),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", ctypes.c_ulong),
        ("wParamL", ctypes.c_ushort),
        ("wParamH", ctypes.c_ushort),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("union", INPUT_UNION)]


def _keyboard_input(key: int, flags: int = 0) -> INPUT:
    return INPUT(type=INPUT_KEYBOARD, union=INPUT_UNION(ki=KEYBDINPUT(key, 0, flags, 0, 0)))


def _send_ctrl_c() -> None:
    inputs = (INPUT * 8)(
        _keyboard_input(VK_MENU, KEYEVENTF_KEYUP),
        _keyboard_input(VK_SHIFT, KEYEVENTF_KEYUP),
        _keyboard_input(VK_LWIN, KEYEVENTF_KEYUP),
        _keyboard_input(VK_RWIN, KEYEVENTF_KEYUP),
        _keyboard_input(VK_CONTROL),
        _keyboard_input(VK_C),
        _keyboard_input(VK_C, KEYEVENTF_KEYUP),
        _keyboard_input(VK_CONTROL, KEYEVENTF_KEYUP),
    )
    sent = ctypes.windll.user32.SendInput(len(inputs), ctypes.byref(inputs), ctypes.sizeof(INPUT))
    if sent != len(inputs):
        raise ctypes.WinError()


def get_selected_text(delay: float = 0.15) -> str | None:
    original = pyperclip.paste()
    try:
        pyperclip.copy("")
        _send_ctrl_c()
        time.sleep(delay)
        selected = pyperclip.paste()
    finally:
        pyperclip.copy(original)

    selected = selected.strip()
    if not selected or selected == original.strip():
        return None
    return selected
