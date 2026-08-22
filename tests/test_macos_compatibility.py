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


def test_ensure_darwin_compat():
    from vitai.darwin_compat import ensure_darwin_compat

    ensure_darwin_compat(force=True)
    assert "ApplicationServices" in sys.modules
    assert hasattr(sys.modules["ApplicationServices"], "AXIsProcessTrusted")
    assert sys.modules["ApplicationServices"].AXIsProcessTrusted() in (True, False, 1, 0)


def test_macos_virtual_keycodes():
    from vitai.darwin_compat import VK_MAP_DARWIN

    assert VK_MAP_DARWIN[55] == "cmd"
    assert VK_MAP_DARWIN[54] == "cmd"
    assert VK_MAP_DARWIN[58] == "alt"
    assert VK_MAP_DARWIN[61] == "alt"
    assert VK_MAP_DARWIN[59] == "ctrl"
    assert VK_MAP_DARWIN[62] == "ctrl"
    assert VK_MAP_DARWIN[56] == "shift"
    assert VK_MAP_DARWIN[60] == "shift"
    assert VK_MAP_DARWIN[12] == "q"
    assert VK_MAP_DARWIN[9] == "v"
    assert VK_MAP_DARWIN[8] == "c"


def test_hotkey_canonical_with_vk_darwin():
    backend = _PynputHotkeyBackend("ctrl+alt", "v", lambda: None)

    class MockVKKey:
        def __init__(self, vk, char=None):
            self.vk = vk
            self.char = char

    with patch("sys.platform", "darwin"):
        assert backend._canonical(MockVKKey(55)) == "cmd"
        assert backend._canonical(MockVKKey(58)) == "alt"
        assert backend._canonical(MockVKKey(59)) == "ctrl"
        assert backend._canonical(MockVKKey(9)) == "v"
        assert backend._canonical(MockVKKey(12)) == "q"
        # Test Option characters
        assert backend._canonical(MockVKKey(None, char="œ")) == "q"
        assert backend._canonical(MockVKKey(None, char="√")) == "v"


def test_menu_hotkey_match_macos_combos():
    backend = _PynputHotkeyBackend("ctrl+alt", "v", lambda: None)

    # 1. Option + Command + V
    with patch("sys.platform", "darwin"):
        backend._pressed_keys = {"alt", "cmd", "v"}
        assert backend._check_match() is True

        # 2. Option + Control + V
        backend._pressed_keys = {"alt", "ctrl", "v"}
        assert backend._check_match() is True

        # 3. Chỉ có Option + V -> False (yêu cầu ctrl/cmd + alt)
        backend._pressed_keys = {"alt", "v"}
        assert backend._check_match() is False


def test_answer_hotkey_match_option_q():
    backend = _PynputHotkeyBackend("alt", "q", lambda: None)

    with patch("sys.platform", "darwin"):
        backend._pressed_keys = {"alt", "q"}
        assert backend._check_match() is True

        # Option alias
        backend_opt = _PynputHotkeyBackend("option", "q", lambda: None)
        backend_opt._pressed_keys = {"alt", "q"}
        assert backend_opt._check_match() is True


def test_darwin_ghost_window_and_front_helpers():
    from vitai.darwin_compat import (
        bring_window_to_front,
        order_front_regardless,
        send_cmd_c_macos,
        set_darwin_activation_policy,
        setup_macos_dock_reopen_handler,
        setup_macos_ghost_window,
    )

    mock_widget = MagicMock()
    mock_widget.winId.return_value = 123456

    # Non-darwin should be safe no-op
    with patch("sys.platform", "linux"):
        setup_macos_ghost_window(mock_widget)
        order_front_regardless(mock_widget)
        set_darwin_activation_policy(True)
        setup_macos_dock_reopen_handler(lambda: None)
        assert send_cmd_c_macos() is False

    # Darwin calls
    with patch("sys.platform", "darwin"):
        set_darwin_activation_policy(True)
        set_darwin_activation_policy(False)
        bring_window_to_front(mock_widget)
        assert mock_widget.show.called
        assert mock_widget.raise_.called
        assert mock_widget.activateWindow.called


def test_check_and_request_macos_accessibility():
    from vitai.darwin_compat import check_and_request_macos_accessibility

    # On linux should return True
    with patch("sys.platform", "linux"):
        assert check_and_request_macos_accessibility() is True

    # On darwin should be safe
    with patch("sys.platform", "darwin"):
        result = check_and_request_macos_accessibility()
        assert isinstance(result, bool)


def test_darwin_hybrid_and_native_backend_instantiation():
    from vitai.hotkey import (
        HotkeyManager,
        _DarwinCGEventTapHotkeyBackend,
        _DarwinHybridHotkeyBackend,
    )

    cb = MagicMock()
    with patch("sys.platform", "darwin"):
        mgr = HotkeyManager("alt", "q", cb)
        backend = mgr._create_backend()
        assert isinstance(backend, _DarwinHybridHotkeyBackend)
        assert backend._pynput is not None
        assert backend._native is not None

        native_backend = _DarwinCGEventTapHotkeyBackend("alt", "q", cb)
        assert native_backend._target_key_str == "q"
        assert native_backend._modifier_str == "alt"
        native_backend.stop()

