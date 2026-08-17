from __future__ import annotations

import ast
import logging
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

_log = logging.getLogger("vitai.gnome_shortcuts")

VITAI_BINDING_PATH = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/vitai/"
VITAI_MENU_BINDING_PATH = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/vitai-menu/"
VITAI_SCHEMA = "org.gnome.settings-daemon.plugins.media-keys.custom-keybinding"
PARENT_SCHEMA = "org.gnome.settings-daemon.plugins.media-keys"


def _is_gnome() -> bool:
    if sys.platform != "linux":
        return False
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    return "gnome" in desktop or "ubuntu" in desktop or shutil.which("gsettings") is not None


def _format_gnome_binding(modifier: str, key: str) -> str:
    """Chuyển đổi modifier và key sang định dạng của GNOME (ví dụ: <Alt>q, <Control><Alt>q)."""
    parts = []
    for mod in modifier.lower().split("+"):
        mod = mod.strip()
        if mod == "alt":
            parts.append("<Alt>")
        elif mod in ("ctrl", "control"):
            parts.append("<Control>")
        elif mod in ("shift", "shift"):
            parts.append("<Shift>")
        elif mod in ("win", "super", "meta"):
            parts.append("<Super>")
    parts.append(key.lower().strip())
    return "".join(parts)


def _ensure_trigger_script() -> str:
    """Tạo một script trigger siêu nhẹ trong ~/.vitai/trigger.sh để tránh lỗi đường dẫn có khoảng trắng/dấu."""
    vitai_dir = Path.home() / ".vitai"
    vitai_dir.mkdir(parents=True, exist_ok=True)
    script_path = vitai_dir / "trigger.sh"

    script_content = """#!/bin/sh
python3 -c "
import socket, os, sys
sock_path = os.environ.get('XDG_RUNTIME_DIR', '') + '/vitai.sock'
if not os.path.exists(sock_path):
    sock_path = os.path.expanduser('~/.vitai/vitai.sock')
try:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(1.0)
    s.connect(sock_path)
    cmd = (sys.argv[1] if len(sys.argv) > 1 else 'TRIGGER') + '\\n'
    s.sendall(cmd.encode('utf-8'))
    s.close()
except Exception:
    pass
" "$@"
"""
    script_path.write_text(script_content, encoding="utf-8")
    script_path.chmod(script_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return str(script_path)


def register_gnome_hotkey(modifier: str, key: str) -> bool:
    """Đăng ký hoặc cập nhật phím tắt toàn cục trong GNOME Shell qua gsettings."""
    if not _is_gnome():
        return False

    binding_str = _format_gnome_binding(modifier, key)
    cmd = _ensure_trigger_script()

    try:
        # 1. Đặt thông tin cho binding ViTai
        path_schema = f"{VITAI_SCHEMA}:{VITAI_BINDING_PATH}"
        subprocess.run(["gsettings", "set", path_schema, "name", "ViTai Trigger"], check=True, capture_output=True)
        subprocess.run(["gsettings", "set", path_schema, "command", cmd], check=True, capture_output=True)
        subprocess.run(["gsettings", "set", path_schema, "binding", binding_str], check=True, capture_output=True)

        # 2. Thêm vào danh sách custom-keybindings của GNOME nếu chưa có
        res = subprocess.run(["gsettings", "get", PARENT_SCHEMA, "custom-keybindings"], capture_output=True, text=True, check=True)
        out = res.stdout.strip()
        
        bindings_list = []
        if out and out != "@as []":
            try:
                bindings_list = ast.literal_eval(out)
            except Exception:
                bindings_list = []

        if VITAI_BINDING_PATH not in bindings_list:
            bindings_list.append(VITAI_BINDING_PATH)
            formatted_list = str(bindings_list)
            subprocess.run(["gsettings", "set", PARENT_SCHEMA, "custom-keybindings", formatted_list], check=True, capture_output=True)

        _log.info(f"[GNOME] ✅ Đã đăng ký phím tắt GNOME Trigger: '{binding_str}' -> '{cmd}'")
        return True
    except Exception as e:
        _log.warning(f"[GNOME] Không thể đăng ký phím tắt GNOME: {e}")
        return False


def register_gnome_menu_hotkey(modifier: str = "ctrl+alt", key: str = "v") -> bool:
    """Đăng ký phím tắt toàn cục mở Menu/Settings trong GNOME Shell."""
    if not _is_gnome():
        return False

    binding_str = _format_gnome_binding(modifier, key)
    script_path = _ensure_trigger_script()
    cmd = f"{script_path} MENU"

    try:
        path_schema = f"{VITAI_SCHEMA}:{VITAI_MENU_BINDING_PATH}"
        subprocess.run(["gsettings", "set", path_schema, "name", "ViTai Menu"], check=True, capture_output=True)
        subprocess.run(["gsettings", "set", path_schema, "command", cmd], check=True, capture_output=True)
        subprocess.run(["gsettings", "set", path_schema, "binding", binding_str], check=True, capture_output=True)

        res = subprocess.run(["gsettings", "get", PARENT_SCHEMA, "custom-keybindings"], capture_output=True, text=True, check=True)
        out = res.stdout.strip()
        
        bindings_list = []
        if out and out != "@as []":
            try:
                bindings_list = ast.literal_eval(out)
            except Exception:
                bindings_list = []

        if VITAI_MENU_BINDING_PATH not in bindings_list:
            bindings_list.append(VITAI_MENU_BINDING_PATH)
            formatted_list = str(bindings_list)
            subprocess.run(["gsettings", "set", PARENT_SCHEMA, "custom-keybindings", formatted_list], check=True, capture_output=True)

        _log.info(f"[GNOME] ✅ Đã đăng ký phím tắt GNOME Menu: '{binding_str}' -> '{cmd}'")
        return True
    except Exception as e:
        _log.warning(f"[GNOME] Không thể đăng ký phím tắt GNOME Menu: {e}")
        return False


def unregister_gnome_hotkey() -> None:
    """Hủy đăng ký phím tắt trong GNOME."""
    if not _is_gnome():
        return

    try:
        res = subprocess.run(["gsettings", "get", PARENT_SCHEMA, "custom-keybindings"], capture_output=True, text=True)
        out = res.stdout.strip()
        if out and out != "@as []":
            try:
                bindings_list = ast.literal_eval(out)
                changed = False
                for bp in (VITAI_BINDING_PATH, VITAI_MENU_BINDING_PATH):
                    if bp in bindings_list:
                        bindings_list.remove(bp)
                        changed = True
                if changed:
                    formatted_list = str(bindings_list) if bindings_list else "@as []"
                    subprocess.run(["gsettings", "set", PARENT_SCHEMA, "custom-keybindings", formatted_list], check=True, capture_output=True)
                    _log.info("[GNOME] Đã hủy phím tắt GNOME của ViTai")
            except Exception:
                pass
    except Exception:
        pass
