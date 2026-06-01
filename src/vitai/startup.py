"""Windows startup registry and admin elevation helpers."""

import ctypes
import subprocess
import sys

REGISTRY_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "ViTai"


def is_admin() -> bool:
    """Return True if the current process has administrator privileges."""
    if sys.platform != "win32":
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def set_startup(enable: bool) -> None:
    """Add or remove ViTai from the Windows startup registry (HKCU)."""
    if sys.platform != "win32":
        return

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


def get_startup_enabled() -> bool:
    """Check whether ViTai is registered in Windows startup."""
    if sys.platform != "win32":
        return False

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


def restart_as_admin() -> None:
    """Re-launch the application with elevated (admin) privileges via UAC.

    Exits the current process after requesting elevation.
    """
    if sys.platform != "win32" or is_admin():
        return
    ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        sys.executable,
        subprocess.list2cmdline(sys.argv[1:]),
        None,
        1,
    )
    sys.exit(0)
