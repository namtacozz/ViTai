from __future__ import annotations

import logging
import os
import sys
import threading
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QApplication

_log = logging.getLogger("vitai.mouse")

_global_pos: tuple[int, int] | None = None
_tracker_thread: threading.Thread | None = None
_running = False


def start_mouse_tracker() -> None:
    """Khởi động thread theo dõi tọa độ chuột qua evdev (nếu có quyền đọc /dev/input) trên Linux."""
    global _tracker_thread, _running
    if sys.platform != "linux" or _running:
        return

    try:
        import evdev
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        # Lọc các thiết bị chuột / touchpad
        mouse_devs = [
            d for d in devices
            if evdev.ecodes.EV_REL in d.capabilities() or evdev.ecodes.EV_ABS in d.capabilities()
        ]
        if not mouse_devs:
            _log.info("[MOUSE] Chưa có quyền đọc /dev/input (Cần: sudo usermod -aG input $USER)")
            return

        _running = True
        _tracker_thread = threading.Thread(target=_evdev_loop, args=(mouse_devs,), daemon=True)
        _tracker_thread.start()
        _log.info(f"[MOUSE] ✅ Đã kích hoạt Mouse Tracker cấp Kernel ({len(mouse_devs)} thiết bị)")
    except Exception as e:
        _log.debug(f"[MOUSE] Không thể khởi động evdev mouse tracker: {e}")


def _evdev_loop(devices: list) -> None:
    global _global_pos
    import evdev
    import select

    # Lấy kích thước màn hình
    screen_w, screen_h = 1920, 1080
    app = QApplication.instance()
    if app:
        primary = app.primaryScreen()
        if primary:
            geo = primary.geometry()
            screen_w, screen_h = geo.width(), geo.height()

    cur_x = screen_w // 2
    cur_y = screen_h // 2
    _global_pos = (cur_x, cur_y)

    dev_map = {dev.fd: dev for dev in devices}

    while _running:
        try:
            r, _, _ = select.select(dev_map.keys(), [], [], 1.0)
            for fd in r:
                dev = dev_map.get(fd)
                if not dev:
                    continue
                for event in dev.read():
                    if event.type == evdev.ecodes.EV_REL:
                        if event.code == evdev.ecodes.REL_X:
                            cur_x = max(0, min(screen_w, cur_x + event.value))
                        elif event.code == evdev.ecodes.REL_Y:
                            cur_y = max(0, min(screen_h, cur_y + event.value))
                        _global_pos = (cur_x, cur_y)
        except Exception:
            pass


def get_mouse_position() -> tuple[int, int]:
    """Lấy tọa độ chuột tốt nhất có thể."""
    global _global_pos
    if _global_pos is not None:
        return _global_pos

    try:
        from pynput import mouse
        pos = mouse.Controller().position
        if pos and pos != (0, 0):
            return int(pos[0]), int(pos[1])
    except Exception:
        pass

    try:
        qpos = QCursor.pos()
        if qpos.x() > 0 or qpos.y() > 0:
            return qpos.x(), qpos.y()
    except Exception:
        pass

    # Fallback vị trí thanh dock / góc trên phải
    app = QApplication.instance()
    if app:
        primary = app.primaryScreen()
        if primary:
            geo = primary.geometry()
            return geo.width() - 80, 50

    return 600, 300
