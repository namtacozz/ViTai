from __future__ import annotations

import ctypes
import os
import sys
from pathlib import Path

REGISTRY_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "ViTai"


def _get_linux_autostart_path() -> Path:
    config_dir = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    return Path(config_dir) / "autostart" / "vitai.desktop"


def _get_macos_launchagent_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / "com.vitai.app.plist"


def is_admin() -> bool:
    """Return True if the current process has administrator privileges."""
    if sys.platform == "win32":
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False
    else:
        return os.geteuid() == 0 if hasattr(os, "geteuid") else False


def set_startup(enable: bool) -> None:
    """Add or remove ViTai from system autostart."""
    if sys.platform == "win32":
        import winreg

        exe_path = sys.executable
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                REGISTRY_KEY,
                0,
                winreg.KEY_SET_VALUE,
            )
            if enable:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{exe_path}"')
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except OSError:
            pass
    elif sys.platform == "darwin":
        plist_file = _get_macos_launchagent_path()
        if enable:
            plist_file.parent.mkdir(parents=True, exist_ok=True)
            if getattr(sys, "frozen", False):
                app_path = sys.executable
                args_xml = f"        <string>{app_path}</string>"
            else:
                py_exe = sys.executable
                script_path = os.path.abspath(sys.argv[0])
                args_xml = f"""        <string>{py_exe}</string>
        <string>{script_path}</string>"""

            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.vitai.app</string>
    <key>ProgramArguments</key>
    <array>
{args_xml}
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>ProcessType</key>
    <string>Interactive</string>
    <key>StandardErrorPath</key>
    <string>/tmp/vitai.err</string>
    <key>StandardOutPath</key>
    <string>/tmp/vitai.out</string>
</dict>
</plist>
"""
            try:
                plist_file.write_text(plist_content, encoding="utf-8")
            except OSError:
                pass
        else:
            try:
                plist_file.unlink(missing_ok=True)
            except OSError:
                pass
    elif sys.platform.startswith("linux"):
        desktop_file = _get_linux_autostart_path()
        if enable:
            desktop_file.parent.mkdir(parents=True, exist_ok=True)
            if getattr(sys, "frozen", False):
                exe_path = sys.executable
            else:
                exe_path = f"/usr/bin/env python3 {os.path.abspath(sys.argv[0])}"

            desktop_content = f"""[Desktop Entry]
Type=Application
Exec={exe_path}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=ViTai
Comment=ViTai AI Assistant
"""
            try:
                desktop_file.write_text(desktop_content, encoding="utf-8")
            except OSError:
                pass
        else:
            try:
                desktop_file.unlink(missing_ok=True)
            except OSError:
                pass


def get_startup_enabled() -> bool:
    """Check whether ViTai is registered in startup."""
    if sys.platform == "win32":
        import winreg

        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                REGISTRY_KEY,
                0,
                winreg.KEY_READ,
            )
            winreg.QueryValueEx(key, APP_NAME)
            winreg.CloseKey(key)
            return True
        except (FileNotFoundError, OSError):
            return False
    elif sys.platform == "darwin":
        plist_file = _get_macos_launchagent_path()
        return plist_file.exists()
    elif sys.platform.startswith("linux"):
        desktop_file = _get_linux_autostart_path()
        return desktop_file.exists()

    return False


def install_linux_desktop_file() -> None:
    """Register ViTai in ~/.local/share/applications/ so GNOME/Wayland recognizes it as a system app."""
    if not sys.platform.startswith("linux"):
        return

    apps_dir = Path(os.path.expanduser("~/.local/share/applications"))
    apps_dir.mkdir(parents=True, exist_ok=True)
    desktop_file = apps_dir / "vitai.desktop"

    if getattr(sys, "frozen", False):
        exe_path = sys.executable
    else:
        exe_path = f"/usr/bin/env python3 {os.path.abspath(sys.argv[0])}"

    content = f"""[Desktop Entry]
Type=Application
Name=ViTai
GenericName=AI Assistant
Comment=ViTai Ghost Fast Answer Assistant
Exec={exe_path}
Terminal=false
Categories=Utility;
StartupNotify=true
StartupWMClass=vitai
X-GNOME-UsesNotifications=true
"""
    try:
        desktop_file.write_text(content, encoding="utf-8")
    except OSError:
        pass
