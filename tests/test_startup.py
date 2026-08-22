from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

from vitai.startup import (
    _get_linux_autostart_path,
    get_startup_enabled,
    install_linux_desktop_file,
    set_startup,
)


def test_linux_autostart_path(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert _get_linux_autostart_path() == tmp_path / "autostart" / "vitai.desktop"


def test_linux_startup_toggle(tmp_path, monkeypatch):
    mock_desktop = tmp_path / "autostart" / "vitai.desktop"
    monkeypatch.setattr("vitai.startup._get_linux_autostart_path", lambda: mock_desktop)

    with patch("sys.platform", "linux"):
        assert get_startup_enabled() is False

        set_startup(True)
        assert mock_desktop.exists()
        content = mock_desktop.read_text(encoding="utf-8")
        assert "Name=ViTai" in content
        assert get_startup_enabled() is True

        set_startup(False)
        assert not mock_desktop.exists()
        assert get_startup_enabled() is False


def test_install_linux_desktop_file(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    with patch("sys.platform", "linux"):
        install_linux_desktop_file()
        desktop_file = tmp_path / ".local" / "share" / "applications" / "vitai.desktop"
        assert desktop_file.exists()
        content = desktop_file.read_text(encoding="utf-8")
        assert "Name=ViTai" in content
        assert "Categories=Utility;" in content
