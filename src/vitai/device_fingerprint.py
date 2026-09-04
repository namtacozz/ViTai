from __future__ import annotations

import hashlib
import os
import platform
import sys
import uuid


def get_mac_address() -> str:
    """Lấy địa chỉ MAC card mạng thực tế của máy tính (định dạng XX:XX:XX:XX:XX:XX)."""
    try:
        mac_num = uuid.getnode()
        mac_hex = f"{mac_num:012x}"
        return ":".join(mac_hex[i:i + 2] for i in range(0, 12, 2)).upper()
    except Exception:
        return "00:00:00:00:00:00"


def get_machine_id() -> str:
    """Lấy định danh phần cứng máy tính duy nhất (OS Machine ID)."""
    if sys.platform.startswith("linux"):
        for path in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
            try:
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        val = f.read().strip()
                        if val:
                            return val
            except Exception:
                pass
    elif sys.platform == "win32":
        try:
            import winreg  # type: ignore
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Cryptography",
                0,
                winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
            )
            val, _ = winreg.QueryValueEx(key, "MachineGuid")
            winreg.CloseKey(key)
            if val:
                return str(val).strip()
        except Exception:
            pass

    # Fallback to node + system info
    return f"{platform.node()}-{platform.machine()}"


def get_cpu_signature() -> str:
    """Lấy thông số nhận diện CPU."""
    try:
        if sys.platform.startswith("linux"):
            try:
                with open("/proc/cpuinfo", "r", encoding="utf-8") as f:
                    for line in f:
                        if "model name" in line:
                            return line.split(":", 1)[1].strip()
            except Exception:
                pass
        return f"{platform.processor()}-{os.cpu_count()}"
    except Exception:
        return "UNKNOWN_CPU"


def get_device_fingerprint() -> str:
    """
    Tạo mã vân tay thiết bị (Hardware Fingerprint) kết hợp đa lớp:
    - MAC Address
    - OS Machine ID (Linux machine-id / Windows MachineGuid)
    - CPU Signature
    - Hostname & Architecture
    
    Đầu ra là chuỗi băm SHA-256 32 ký tự, chống triệt để việc đổi MAC giả mạo để lách bản quyền.
    """
    mac = get_mac_address()
    mid = get_machine_id()
    cpu = get_cpu_signature()
    arch = f"{platform.system()}-{platform.machine()}"

    composite = f"{mac}|{mid}|{cpu}|{arch}"
    return hashlib.sha256(composite.encode("utf-8")).hexdigest()[:32].upper()
