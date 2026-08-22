from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest

from vitai.capture import (
    _is_wayland,
    _read_clipboard_wayland,
    _read_primary_selection_wayland,
    _read_primary_selection_x11,
    get_selected_text,
)


def test_is_wayland(monkeypatch):
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    assert _is_wayland() is True

    monkeypatch.delenv("XDG_SESSION_TYPE", raising=False)
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    assert _is_wayland() is True

    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    assert _is_wayland() is False


def test_read_primary_selection_wayland():
    mock_run = MagicMock()
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "Test Wayland Text\n"

    with patch("subprocess.run", mock_run):
        assert _read_primary_selection_wayland() == "Test Wayland Text"


def test_read_clipboard_wayland():
    mock_run = MagicMock()
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "Test Clipboard\n"

    with patch("subprocess.run", mock_run):
        assert _read_clipboard_wayland() == "Test Clipboard"


def test_read_primary_selection_x11():
    mock_run = MagicMock()
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "Test X11 Text\n"

    with patch("subprocess.run", mock_run):
        assert _read_primary_selection_x11() == "Test X11 Text"


def test_get_selected_text_wayland():
    with patch("vitai.capture._is_wayland", return_value=True), \
         patch("vitai.capture._read_primary_selection_wayland", return_value="Selected question text"):
        assert get_selected_text() == "Selected question text"


def test_get_selected_text_windows():
    with patch("sys.platform", "win32"), \
         patch("vitai.capture._is_wayland", return_value=False), \
         patch("pyperclip.paste", side_effect=["old", "Windows Selected Question"]), \
         patch("pyperclip.copy"), \
         patch("vitai.capture._send_ctrl_c_windows"):
        assert get_selected_text() == "Windows Selected Question"
