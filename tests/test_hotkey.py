from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

try:
    from pynput import keyboard
except Exception:
    class _DummyKey:
        alt = "alt"
        ctrl = "ctrl"
        shift = "shift"
        cmd = "cmd"
        cmd_l = "cmd_l"
        cmd_r = "cmd_r"
    class _DummyKeyboard:
        Key = _DummyKey()
        KeyCode = object
    keyboard = _DummyKeyboard()  # type: ignore

from vitai.hotkey import (
    HotkeyManager,
    _PynputHotkeyBackend,
    _normalize_modifier,
    _canonical_mouse_button,
    format_key_display,
)


def test_normalize_modifier():
    assert _normalize_modifier("win") == "win"
    assert _normalize_modifier("cmd") == "win"
    assert _normalize_modifier("command") == "win"
    assert _normalize_modifier("super") == "win"
    assert _normalize_modifier("meta") == "win"
    assert _normalize_modifier("opt") == "alt"
    assert _normalize_modifier("option") == "alt"
    assert _normalize_modifier("alt") == "alt"
    assert _normalize_modifier("ctrl") == "ctrl"
    assert _normalize_modifier("control") == "ctrl"
    assert _normalize_modifier("shift") == "shift"
    assert _normalize_modifier("") == ""


def test_canonical_mouse_button():
    assert _canonical_mouse_button("Button.right") == "mouse_right"
    assert _canonical_mouse_button("Button.middle") == "mouse_middle"
    assert _canonical_mouse_button("Button.left") == "mouse_left"
    assert _canonical_mouse_button("Button.x1") == "mouse_x1"
    assert _canonical_mouse_button("Button.x2") == "mouse_x2"


def test_format_key_display():
    assert format_key_display("mouse_right") == "Chuột Phải"
    assert format_key_display("mouse_middle") == "Chuột Giữa"
    assert format_key_display("mouse_left") == "Chuột Trái"
    assert format_key_display("mouse_x1") == "Nút Chuột Phụ 1 (Back)"
    assert format_key_display("mouse_x2") == "Nút Chuột Phụ 2 (Forward)"
    assert format_key_display("q") == "Q"


def test_hotkey_canonical():
    backend = _PynputHotkeyBackend("alt", "q", lambda: None)
    
    if hasattr(keyboard.Key, "alt"):
        assert backend._canonical(keyboard.Key.alt) == "alt"
    if hasattr(keyboard.Key, "ctrl"):
        assert backend._canonical(keyboard.Key.ctrl) == "ctrl"
    if hasattr(keyboard.Key, "shift"):
        assert backend._canonical(keyboard.Key.shift) == "shift"


def test_hotkey_check_match():
    backend = _PynputHotkeyBackend("alt", "q", lambda: None)
    backend._pressed_keys = {"alt", "q"}
    assert backend._check_match() is True

    # Test combo ctrl+alt
    backend2 = _PynputHotkeyBackend("ctrl+alt", "v", lambda: None)
    backend2._pressed_keys = {"ctrl", "alt", "v"}
    assert backend2._check_match() is True

    backend2._pressed_keys = {"alt", "v"}
    assert backend2._check_match() is False


def test_hotkey_display_text():
    manager = HotkeyManager("ctrl+alt", "v", lambda: None)
    assert manager.display_text == "Ctrl+Alt+V"

    manager2 = HotkeyManager("alt", "mouse_right", lambda: None)
    assert manager2.display_text == "Alt+Chuột Phải"

    manager3 = HotkeyManager("win", "q", lambda: None)
    assert manager3.display_text == "Win+Q"


def test_hotkey_manager_backend_creation():
    cb = MagicMock()
    with patch("sys.platform", "linux"):
        mgr = HotkeyManager("alt", "q", cb)
        backend = mgr._create_backend()
        assert isinstance(backend, _PynputHotkeyBackend)
