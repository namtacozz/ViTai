from __future__ import annotations

import logging
import os
import sys
import threading
from typing import Callable
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QApplication

_log = logging.getLogger("vitai.mouse")

_global_pos: tuple[int, int] | None = None
_last_selection_end_pos: tuple[int, int] | None = None
_mouse_press_pos: tuple[int, int] | None = None
_tracker_thread: threading.Thread | None = None
_running = False
_click_callbacks: list[Callable[[int, int, bool], None]] = []


def register_click_callback(callback: Callable[[int, int, bool], None]) -> None:
    """Đăng ký callback nhận sự kiện click chuột từ Kernel/evdev."""
    if callback not in _click_callbacks:
        _click_callbacks.append(callback)


def unregister_click_callback(callback: Callable[[int, int, bool], None]) -> None:
    if callback in _click_callbacks:
        _click_callbacks.remove(callback)


def get_last_selection_end_pos() -> tuple[int, int] | None:
    return _last_selection_end_pos


def start_mouse_tracker() -> None:
    """Khởi động thread theo dõi tọa độ chuột và sự kiện click qua evdev trên Linux."""
    global _tracker_thread, _running
    if sys.platform != "linux" or _running:
        return

    try:
        import evdev
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        # Lọc các thiết bị chuột / touchpad
        mouse_devs = [
            d for d in devices
            if evdev.ecodes.EV_REL in d.capabilities()
            or evdev.ecodes.EV_ABS in d.capabilities()
            or evdev.ecodes.EV_KEY in d.capabilities()
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


def _notify_clicks(x: int, y: int, pressed: bool) -> None:
    for cb in list(_click_callbacks):
        try:
            cb(x, y, pressed)
        except Exception:
            pass


def _evdev_loop(devices: list) -> None:
    global _global_pos, _last_selection_end_pos, _mouse_press_pos
    import evdev
    import select

    # Lấy kích thước màn hình
    screen_w, screen_h = 1920, 1080
    primary = QApplication.primaryScreen()
    if primary:
        geo = primary.geometry()
        screen_w, screen_h = geo.width(), geo.height()

    cur_x, cur_y = get_mouse_position()
    _global_pos = (cur_x, cur_y)

    dev_map = {dev.fd: dev for dev in devices}

    MOUSE_BUTTON_CODES = {
        evdev.ecodes.BTN_LEFT,
        evdev.ecodes.BTN_RIGHT,
        evdev.ecodes.BTN_MIDDLE,
        evdev.ecodes.BTN_SIDE,
        evdev.ecodes.BTN_EXTRA,
        evdev.ecodes.BTN_TOUCH,
    }

    while _running:
        try:
            r, _, _ = select.select(dev_map.keys(), [], [], 0.5)
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

                    elif event.type == evdev.ecodes.EV_KEY:
                        if event.code in MOUSE_BUTTON_CODES or (272 <= event.code <= 287):
                            # Sync vị trí thực tế chính xác từ hệ điều hành
                            real_x, real_y = get_mouse_position()
                            pressed = (event.value == 1)
                            
                            if pressed:
                                _mouse_press_pos = (real_x, real_y)
                            else:
                                if _mouse_press_pos is not None:
                                    _last_selection_end_pos = (real_x, real_y)
                                    _mouse_press_pos = None

                            _notify_clicks(real_x, real_y, pressed)
        except Exception:
            pass


def get_mouse_position() -> tuple[int, int]:
    """Lấy tọa độ con trỏ chuột thực tế chính xác nhất trên màn hình."""
    try:
        qpos = QCursor.pos()
        if qpos is not None and (qpos.x() > 0 or qpos.y() > 0):
            return qpos.x(), qpos.y()
    except Exception:
        pass

    try:
        from pynput import mouse
        pos = mouse.Controller().position
        if pos and pos != (0, 0):
            return pos[0], pos[1]
    except Exception:
        pass

    global _global_pos
    if _global_pos is not None:
        return _global_pos

    # Fallback vị trí mặc định giữa màn hình
    primary = QApplication.primaryScreen()
    if primary:
        geo = primary.geometry()
        return geo.width() // 2, geo.height() // 2

    return 600, 300
