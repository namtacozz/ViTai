from __future__ import annotations

import os
import sys
from pathlib import Path
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

import pytest

from vitai.hotkey import HotkeyManager, _PynputHotkeyBackend, _normalize_modifier
from vitai.startup import (
    _get_macos_launchagent_path,
    get_startup_enabled,
    set_startup,
)
from vitai.capture import (
    _read_clipboard_macos,
    _get_selected_text_macos,
    get_selected_text,
)


def test_normalize_modifier():
    assert _normalize_modifier("cmd") == "cmd"
    assert _normalize_modifier("command") == "cmd"
    assert _normalize_modifier("super") == "cmd"
    assert _normalize_modifier("win") == "cmd"
    assert _normalize_modifier("meta") == "cmd"
    assert _normalize_modifier("opt") == "alt"
    assert _normalize_modifier("option") == "alt"
    assert _normalize_modifier("alt") == "alt"
    assert _normalize_modifier("ctrl") == "ctrl"
    assert _normalize_modifier("control") == "ctrl"
    assert _normalize_modifier("shift") == "shift"


def test_hotkey_canonical_cmd():
    backend = _PynputHotkeyBackend("cmd", "q", lambda: None)
    
    if hasattr(keyboard.Key, "cmd"):
        assert backend._canonical(keyboard.Key.cmd) == "cmd"
    if hasattr(keyboard.Key, "cmd_l"):
        assert backend._canonical(keyboard.Key.cmd_l) == "cmd"
    if hasattr(keyboard.Key, "cmd_r"):
        assert backend._canonical(keyboard.Key.cmd_r) == "cmd"
    assert backend._canonical(keyboard.Key.alt) == "alt"
    assert backend._canonical(keyboard.Key.ctrl) == "ctrl"
    assert backend._canonical(keyboard.Key.shift) == "shift"


def test_hotkey_check_match_with_cmd():
    backend = _PynputHotkeyBackend("cmd+q", "", lambda: None)
    backend._modifier_str = "cmd"
    backend._target_key_str = "q"
    
    backend._pressed_keys = {"cmd", "q"}
    assert backend._check_match() is True

    # Test alias "command"
    backend2 = _PynputHotkeyBackend("command", "q", lambda: None)
    backend2._pressed_keys = {"cmd", "q"}
    assert backend2._check_match() is True

    # Test alias "opt" + "q"
    backend3 = _PynputHotkeyBackend("opt", "q", lambda: None)
    backend3._pressed_keys = {"alt", "q"}
    assert backend3._check_match() is True


def test_hotkey_display_text_darwin():
    manager = HotkeyManager("cmd+alt", "v", lambda: None)
    with patch("sys.platform", "darwin"):
        assert manager.display_text == "Cmd+Opt+V"

    manager2 = HotkeyManager("ctrl+shift", "q", lambda: None)
    with patch("sys.platform", "darwin"):
        assert manager2.display_text == "Ctrl+Shift+Q"


def test_macos_startup_plist(tmp_path, monkeypatch):
    mock_plist = tmp_path / "com.vitai.app.plist"
    monkeypatch.setattr("vitai.startup._get_macos_launchagent_path", lambda: mock_plist)

    with patch("sys.platform", "darwin"):
        assert get_startup_enabled() is False

        set_startup(True)
        assert mock_plist.exists()
        content = mock_plist.read_text(encoding="utf-8")
        assert "<string>com.vitai.app</string>" in content
        assert "<key>RunAtLoad</key>" in content
        assert "<true/>" in content
        assert get_startup_enabled() is True

        set_startup(False)
        assert not mock_plist.exists()
        assert get_startup_enabled() is False


def test_read_clipboard_macos():
    with patch("pyperclip.paste", return_value="Test macOS text"):
        assert _read_clipboard_macos() == "Test macOS text"


def test_get_selected_text_macos():
    with patch("vitai.capture._simulate_ctrl_c_pynput", return_value=True), \
         patch("vitai.capture._read_clipboard_macos", return_value="Selected question text"), \
         patch("pyperclip.paste", return_value=""), \
         patch("pyperclip.copy", return_value=None):
        
        captured = _get_selected_text_macos()
        assert captured == "Selected question text"


def test_get_selected_text_dispatches_darwin():
    with patch("sys.platform", "darwin"), \
         patch("vitai.capture._is_wayland", return_value=False), \
         patch("vitai.capture._get_selected_text_macos", return_value="Apple Silicon Captured Text"):
        
        result = get_selected_text()
        assert result == "Apple Silicon Captured Text"


def test_safe_urlopen_ssl_fallback():
    import ssl
    import urllib.error
    from vitai.http_util import safe_urlopen, get_safe_ssl_context

    ctx = get_safe_ssl_context()
    assert ctx is not None

    # Test fallback khi gặp lỗi SSL CERTIFICATE_VERIFY_FAILED
    mock_resp = MagicMock()
    mock_resp.status = 200

    def fake_urlopen(req, timeout=10, context=None):
        if context and not getattr(context, "check_hostname", True) is False:
            raise urllib.error.URLError("[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed")
        return mock_resp

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        resp = safe_urlopen("https://example.com", timeout=5)
        assert resp == mock_resp
