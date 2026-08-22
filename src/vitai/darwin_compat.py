from __future__ import annotations

import logging
import sys
from typing import Any, Callable

_LOGGER = logging.getLogger("vitai.darwin_compat")

# Bảng mã phím phần cứng tiêu chuẩn macOS (Apple Virtual Keycodes)
VK_MAP_DARWIN: dict[int, str] = {
    # Chữ cái
    0: "a", 1: "s", 2: "d", 3: "f", 4: "h", 5: "g", 6: "z", 7: "x",
    8: "c", 9: "v", 11: "b", 12: "q", 13: "w", 14: "e", 15: "r",
    16: "y", 17: "t", 31: "o", 32: "u", 34: "i", 35: "p", 37: "l",
    38: "j", 40: "k", 45: "n", 46: "m",
    # Số
    18: "1", 19: "2", 20: "3", 21: "4", 23: "5", 22: "6", 26: "7",
    28: "8", 25: "9", 29: "0",
    # Ký tự & Phím chức năng
    24: "=", 27: "-", 30: "]", 33: "[", 39: "'", 41: ";", 42: "\\",
    43: ",", 44: "/", 47: ".", 50: "`",
    36: "\n", 48: "\t", 49: " ", 51: "backspace", 53: "esc",
    # Phím bổ trợ phần cứng macOS (Modifier Virtual Keycodes)
    54: "cmd", 55: "cmd",       # Right Cmd (0x36), Left Cmd (0x37)
    56: "shift", 60: "shift",   # Left Shift (0x38), Right Shift (0x3C)
    58: "alt", 61: "alt",       # Left Option/Alt (0x3A), Right Option/Alt (0x3D)
    59: "ctrl", 62: "ctrl",     # Left Control (0x3B), Right Control (0x3E)
    57: "caps_lock", 63: "fn",  # Caps Lock (0x39), Fn (0x3F)
}


def ensure_darwin_compat(force: bool = False) -> None:
    """
    Xử lý các vấn đề tương thích sâu trên macOS (Apple Silicon / Intel, macOS 14/15/26+):
    1. Tránh crash KeyError: 'AXIsProcessTrusted' do thiếu ApplicationServices trong PyInstaller.
    2. Tránh crash SIGTRAP / dispatch_assert_queue trong HIToolbox TSMGetInputSourceProperty 
       khi pynput.keyboard.Listener chạy trên background thread.
    """
    if not (sys.platform == "darwin" or force):
        return

    # 1. Cung cấp fallback cho AXIsProcessTrusted nếu PyObjC ApplicationServices bị thiếu
    if "ApplicationServices" not in sys.modules:
        try:
            import ApplicationServices  # type: ignore
        except Exception:
            try:
                import ctypes
                import ctypes.util
                import types
                as_mod = types.ModuleType("ApplicationServices")
                lib_path = ctypes.util.find_library("ApplicationServices")
                if lib_path:
                    try:
                        lib = ctypes.cdll.LoadLibrary(lib_path)
                        as_mod.AXIsProcessTrusted = getattr(lib, "AXIsProcessTrusted", lambda: True)
                    except Exception:
                        as_mod.AXIsProcessTrusted = lambda: True
                else:
                    as_mod.AXIsProcessTrusted = lambda: True
                sys.modules["ApplicationServices"] = as_mod
            except Exception:
                pass
    else:
        as_mod = sys.modules["ApplicationServices"]
        if not hasattr(as_mod, "AXIsProcessTrusted"):
            as_mod.AXIsProcessTrusted = lambda: True

    # 2. Xử lý pynput.keyboard listener crash do gọi HIToolbox TSMGetInputSourceProperty trên background thread
    try:
        import contextlib
        import pynput._util.darwin as pynput_darwin

        # Nạp và cache layout trên Main Thread (nơi được phép gọi Carbon TIS APIs)
        _cached_context = (0, None)
        try:
            with pynput_darwin.keycode_context() as ctx:
                _cached_context = ctx
        except Exception:
            pass

        @contextlib.contextmanager
        def _safe_keycode_context():
            yield _cached_context

        # Thay thế hàm keycode_context để thread ngầm không gọi Carbon APIs gây crash
        pynput_darwin.keycode_context = _safe_keycode_context

        # Bổ sung bảng tra cứu ảo khi layout_data không có sẵn
        orig_keycode_to_string = getattr(pynput_darwin, "keycode_to_string", None)

        def _safe_keycode_to_string(context, keycode, modifier_state=0):
            try:
                if context and context[1] is not None and orig_keycode_to_string is not None:
                    return orig_keycode_to_string(context, keycode, modifier_state)
            except Exception:
                pass
            return VK_MAP_DARWIN.get(keycode, "")

        pynput_darwin.keycode_to_string = _safe_keycode_to_string
    except Exception:
        pass


def set_darwin_activation_policy(is_accessory: bool = True) -> None:
    """
    Chuyển đổi trạng thái hiển thị trên macOS:
    - is_accessory=True (1): Ứng dụng chạy ngầm tàng hình, KHÔNG icon Dock, KHÔNG Alt+Tab, không cướp focus của Chrome.
    - is_accessory=False (0): Mở giao diện Cài đặt (Settings) tương tác bình thường.
    """
    if sys.platform != "darwin":
        return

    # 1. PyObjC
    try:
        import AppKit
        ns_app = AppKit.NSApplication.sharedApplication()
        policy = 1 if is_accessory else 0  # 1 = Accessory, 0 = Regular
        ns_app.setActivationPolicy_(policy)
        if not is_accessory:
            ns_app.activateIgnoringOtherApps_(True)
        return
    except Exception:
        pass

    # 2. Ctypes fallback
    try:
        import ctypes
        import ctypes.util
        objc_path = ctypes.util.find_library("objc")
        if not objc_path:
            return
        objc = ctypes.cdll.LoadLibrary(objc_path)
        if not hasattr(objc, "objc_getClass") or not hasattr(objc, "sel_registerName"):
            return
        objc.objc_getClass.restype = ctypes.c_void_p
        objc.objc_getClass.argtypes = [ctypes.c_char_p]
        objc.sel_registerName.restype = ctypes.c_void_p
        objc.sel_registerName.argtypes = [ctypes.c_char_p]

        cls_nsapp = objc.objc_getClass(b"NSApplication")
        if not cls_nsapp:
            return
        sel_shared = objc.sel_registerName(b"sharedApplication")
        if not sel_shared:
            return
        msg_send = objc.objc_msgSend
        msg_send.restype = ctypes.c_void_p
        msg_send.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        ns_app = msg_send(cls_nsapp, sel_shared)
        if not ns_app:
            return

        sel_policy = objc.sel_registerName(b"setActivationPolicy:")
        if sel_policy:
            msg_send_long = ctypes.cast(msg_send, ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_long))
            msg_send_long(ns_app, sel_policy, ctypes.c_long(1 if is_accessory else 0))

        if not is_accessory:
            sel_activate = objc.sel_registerName(b"activateIgnoringOtherApps:")
            if sel_activate:
                msg_send_bool = ctypes.cast(msg_send, ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_bool))
                msg_send_bool(ns_app, sel_activate, True)
    except Exception:
        pass


def check_and_request_macos_accessibility() -> bool:
    """
    Kiểm tra và tự động kích hoạt hộp thoại yêu cầu quyền Trợ năng (Accessibility) trên macOS.
    Nếu chưa được cấp quyền, macOS sẽ hiện hộp thoại thông báo yêu cầu cấp quyền cho ViTai.
    """
    if sys.platform != "darwin":
        return True
    try:
        import ctypes
        import ctypes.util
        as_path = ctypes.util.find_library("ApplicationServices") or "/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices"
        cf_path = ctypes.util.find_library("CoreFoundation") or "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation"
        as_lib = ctypes.cdll.LoadLibrary(as_path)
        cf_lib = ctypes.cdll.LoadLibrary(cf_path)

        if not hasattr(as_lib, "AXIsProcessTrusted"):
            return True

        as_lib.AXIsProcessTrusted.restype = ctypes.c_bool
        as_lib.AXIsProcessTrusted.argtypes = []
        is_trusted = as_lib.AXIsProcessTrusted()
        if is_trusted:
            return True

        # Yêu cầu quyền bằng AXIsProcessTrustedWithOptions({kAXTrustedCheckOptionPrompt: true})
        if hasattr(as_lib, "AXIsProcessTrustedWithOptions") and hasattr(cf_lib, "CFDictionaryCreate"):
            cf_str = ctypes.c_void_p.in_dll(as_lib, "kAXTrustedCheckOptionPrompt")
            cf_true = ctypes.c_void_p.in_dll(cf_lib, "kCFBooleanTrue")

            cf_lib.CFDictionaryCreate.restype = ctypes.c_void_p
            cf_lib.CFDictionaryCreate.argtypes = [
                ctypes.c_void_p,
                ctypes.POINTER(ctypes.c_void_p),
                ctypes.POINTER(ctypes.c_void_p),
                ctypes.c_long,
                ctypes.c_void_p,
                ctypes.c_void_p,
            ]
            keys = (ctypes.c_void_p * 1)(cf_str)
            values = (ctypes.c_void_p * 1)(cf_true)
            options = cf_lib.CFDictionaryCreate(None, keys, values, 1, None, None)

            as_lib.AXIsProcessTrustedWithOptions.restype = ctypes.c_bool
            as_lib.AXIsProcessTrustedWithOptions.argtypes = [ctypes.c_void_p]
            trusted = as_lib.AXIsProcessTrustedWithOptions(options)
            if options and hasattr(cf_lib, "CFRelease"):
                cf_lib.CFRelease(options)
            return bool(trusted)
        return False
    except Exception as e:
        _LOGGER.debug(f"check_and_request_macos_accessibility error: {e}")
        return True


def _get_cocoa_nswindow(view_ptr: int) -> Any:
    """Lấy con trỏ NSWindow từ con trỏ NSView của Qt thông qua ctypes libobjc."""
    if not view_ptr or sys.platform != "darwin":
        return None
    try:
        import ctypes
        import ctypes.util
        objc_path = ctypes.util.find_library("objc") or "/usr/lib/libobjc.A.dylib"
        objc = ctypes.cdll.LoadLibrary(objc_path)
        if not hasattr(objc, "objc_getClass") or not hasattr(objc, "sel_registerName"):
            return None
        objc.sel_registerName.restype = ctypes.c_void_p
        objc.sel_registerName.argtypes = [ctypes.c_char_p]
        objc.objc_msgSend.restype = ctypes.c_void_p
        objc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

        sel_window = objc.sel_registerName(b"window")
        ns_win = objc.objc_msgSend(ctypes.c_void_p(view_ptr), sel_window)
        return ns_win
    except Exception:
        return None


def setup_macos_ghost_window(widget: Any) -> None:
    """
    Cấu hình NSWindow của Ghost Overlay:
    - Mức hiển thị cao (Level 1000 = NSScreenSaverWindowLevel / Overlay) nổi xuyên suốt mọi ứng dụng & Fullscreen Google Chrome
    - Cấu hình Spaces (339): Xuất hiện ngay trên Space hiện tại của Chrome mà không cần tab chuyển Space
    - Xuyên thấu chuột (ignoresMouseEvents = True)
    - Không cướp focus, không che khuất Google Chrome
    """
    if sys.platform != "darwin" or widget is None:
        return

    configured = False
    try:
        import objc
        import AppKit
        view_ptr = int(widget.winId())
        ns_view = objc.objc_object(c_void_p=view_ptr)
        ns_win = ns_view.window()
        if ns_win:
            ns_win.setLevel_(1000)
            behavior = (
                AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces
                | AppKit.NSWindowCollectionBehaviorMoveToActiveSpace
                | AppKit.NSWindowCollectionBehaviorStationary
                | AppKit.NSWindowCollectionBehaviorIgnoresCycle
                | AppKit.NSWindowCollectionBehaviorFullScreenAuxiliary
            )
            ns_win.setCollectionBehavior_(behavior)
            ns_win.setIgnoresMouseEvents_(True)
            ns_win.setOpaque_(False)
            ns_win.setHasShadow_(False)
            ns_win.setHidesOnDeactivate_(False)
            configured = True
    except Exception:
        pass

    if not configured:
        try:
            import ctypes
            import ctypes.util
            view_ptr = int(widget.winId())
            ns_win = _get_cocoa_nswindow(view_ptr)
            if ns_win:
                objc_path = ctypes.util.find_library("objc") or "/usr/lib/libobjc.A.dylib"
                objc = ctypes.cdll.LoadLibrary(objc_path)
                objc.sel_registerName.restype = ctypes.c_void_p
                objc.sel_registerName.argtypes = [ctypes.c_char_p]
                msg_send = objc.objc_msgSend
                msg_send.restype = ctypes.c_void_p

                # setLevel: 1000
                sel_setLevel = objc.sel_registerName(b"setLevel:")
                msg_send_level = ctypes.cast(msg_send, ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_long))
                msg_send_level(ns_win, sel_setLevel, ctypes.c_long(1000))

                # setCollectionBehavior: 339
                sel_behavior = objc.sel_registerName(b"setCollectionBehavior:")
                msg_send_behavior = ctypes.cast(msg_send, ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong))
                msg_send_behavior(ns_win, sel_behavior, ctypes.c_ulong(339))

                # setIgnoresMouseEvents: True
                sel_mouse = objc.sel_registerName(b"setIgnoresMouseEvents:")
                msg_send_bool = ctypes.cast(msg_send, ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_bool))
                msg_send_bool(ns_win, sel_mouse, True)

                # setHidesOnDeactivate: False
                sel_hides = objc.sel_registerName(b"setHidesOnDeactivate:")
                msg_send_bool(ns_win, sel_hides, False)
        except Exception as e:
            _LOGGER.debug(f"setup_macos_ghost_window ctypes error: {e}")


def order_front_regardless(widget: Any) -> None:
    """
    Hiển thị cửa sổ Overlay lên phía trước mà KHÔNG kích hoạt app, giữ nguyên 100% focus của Google Chrome.
    """
    if sys.platform != "darwin" or widget is None:
        return
    ordered = False
    try:
        import objc
        import AppKit
        view_ptr = int(widget.winId())
        ns_view = objc.objc_object(c_void_p=view_ptr)
        ns_win = ns_view.window()
        if ns_win:
            ns_win.orderFrontRegardless()
            ordered = True
    except Exception:
        pass

    if not ordered:
        try:
            import ctypes
            import ctypes.util
            view_ptr = int(widget.winId())
            ns_win = _get_cocoa_nswindow(view_ptr)
            if ns_win:
                objc_path = ctypes.util.find_library("objc") or "/usr/lib/libobjc.A.dylib"
                objc = ctypes.cdll.LoadLibrary(objc_path)
                objc.sel_registerName.restype = ctypes.c_void_p
                objc.sel_registerName.argtypes = [ctypes.c_char_p]
                sel_order = objc.sel_registerName(b"orderFrontRegardless")
                objc.objc_msgSend.restype = ctypes.c_void_p
                objc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
                objc.objc_msgSend(ns_win, sel_order)
        except Exception as e:
            _LOGGER.debug(f"order_front_regardless ctypes error: {e}")


def bring_window_to_front(widget: Any) -> None:
    """
    Đưa cửa sổ Cài đặt lên trên cùng và nhận focus tương tác đầy đủ.
    """
    if widget is None:
        return

    set_darwin_activation_policy(False)
    widget.show()
    widget.raise_()
    widget.activateWindow()

    if sys.platform == "darwin":
        brought = False
        try:
            import AppKit
            ns_app = AppKit.NSApplication.sharedApplication()
            ns_app.activateIgnoringOtherApps_(True)

            import objc
            view_ptr = int(widget.winId())
            ns_view = objc.objc_object(c_void_p=view_ptr)
            ns_win = ns_view.window()
            if ns_win:
                ns_win.makeKeyAndOrderFront_(None)
                ns_win.orderFrontRegardless()
                brought = True
        except Exception:
            pass

        if not brought:
            try:
                import ctypes
                import ctypes.util
                objc_path = ctypes.util.find_library("objc") or "/usr/lib/libobjc.A.dylib"
                objc = ctypes.cdll.LoadLibrary(objc_path)
                if hasattr(objc, "objc_getClass") and hasattr(objc, "sel_registerName"):
                    objc.sel_registerName.restype = ctypes.c_void_p
                    objc.sel_registerName.argtypes = [ctypes.c_char_p]
                    objc.objc_getClass.restype = ctypes.c_void_p
                    objc.objc_getClass.argtypes = [ctypes.c_char_p]
                    objc.objc_msgSend.restype = ctypes.c_void_p
                    objc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

                    cls_nsapp = objc.objc_getClass(b"NSApplication")
                    sel_shared = objc.sel_registerName(b"sharedApplication")
                    if cls_nsapp and sel_shared:
                        ns_app = objc.objc_msgSend(cls_nsapp, sel_shared)
                        sel_activate = objc.sel_registerName(b"activateIgnoringOtherApps:")
                        if ns_app and sel_activate:
                            msg_send_bool = ctypes.cast(objc.objc_msgSend, ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_bool))
                            msg_send_bool(ns_app, sel_activate, True)

                    view_ptr = int(widget.winId())
                    ns_win = _get_cocoa_nswindow(view_ptr)
                    if ns_win:
                        sel_makeKey = objc.sel_registerName(b"makeKeyAndOrderFront:")
                        sel_order = objc.sel_registerName(b"orderFrontRegardless")
                        msg_send_ptr = ctypes.cast(objc.objc_msgSend, ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p))
                        msg_send_ptr(ns_win, sel_makeKey, None)
                        objc.objc_msgSend(ns_win, sel_order)
            except Exception as e:
                _LOGGER.debug(f"bring_window_to_front ctypes error: {e}")


def send_cmd_c_macos() -> bool:
    """
    Bơm sự kiện Cmd+C bằng Quartz CoreGraphics (CGEvent):
    - Đảm bảo gửi cờ Command sạch, độc lập với phím Option đang giữ
    - Không chuyển app, không mở nhầm Chrome Developer Tools / Element Inspector
    """
    if sys.platform != "darwin":
        return False
    try:
        import ctypes
        import ctypes.util

        cg_path = ctypes.util.find_library("CoreGraphics") or "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics"
        cg = ctypes.cdll.LoadLibrary(cg_path)
        cf_path = ctypes.util.find_library("CoreFoundation") or "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation"
        cf = ctypes.cdll.LoadLibrary(cf_path)

        cg.CGEventCreateKeyboardEvent.argtypes = [ctypes.c_void_p, ctypes.c_ushort, ctypes.c_bool]
        cg.CGEventCreateKeyboardEvent.restype = ctypes.c_void_p
        cg.CGEventSetFlags.argtypes = [ctypes.c_void_p, ctypes.c_uint64]
        cg.CGEventSetFlags.restype = None
        cg.CGEventPost.argtypes = [ctypes.c_uint32, ctypes.c_void_p]
        cg.CGEventPost.restype = None
        cf.CFRelease.argtypes = [ctypes.c_void_p]
        cf.CFRelease.restype = None

        kCGHIDEventTap = 0
        kCGEventFlagMaskCommand = 0x00100000  # 1048576 (Command Key Flag)
        kVK_ANSI_C = 8

        # KeyDown 'C' kèm cờ Command
        ev_down = cg.CGEventCreateKeyboardEvent(None, kVK_ANSI_C, True)
        if ev_down:
            cg.CGEventSetFlags(ev_down, kCGEventFlagMaskCommand)
            cg.CGEventPost(kCGHIDEventTap, ev_down)
            cf.CFRelease(ev_down)

        # KeyUp 'C' kèm cờ Command
        ev_up = cg.CGEventCreateKeyboardEvent(None, kVK_ANSI_C, False)
        if ev_up:
            cg.CGEventSetFlags(ev_up, kCGEventFlagMaskCommand)
            cg.CGEventPost(kCGHIDEventTap, ev_up)
            cf.CFRelease(ev_up)

        return True
    except Exception as e:
        _LOGGER.warning(f"send_cmd_c_macos error: {e}")
        return False


_global_reopen_delegate = None

def setup_macos_dock_reopen_handler(callback: Callable[[], None]) -> None:
    """
    Hook sự kiện macOS Reopen (khi người dùng click icon Dock hoặc click đúp ViTai.app trong khi đang chạy ngầm).
    """
    if sys.platform != "darwin":
        return
    global _global_reopen_delegate
    try:
        import AppKit
        ns_app = AppKit.NSApplication.sharedApplication()

        class ReopenDelegate(AppKit.NSObject):
            def applicationShouldHandleReopen_hasVisibleWindows_(self, sender, flag):
                try:
                    callback()
                except Exception:
                    pass
                return True

            def applicationDidBecomeActive_(self, notification):
                try:
                    callback()
                except Exception:
                    pass

        _global_reopen_delegate = ReopenDelegate.alloc().init()
        ns_app.setDelegate_(_global_reopen_delegate)
    except Exception as e:
        _LOGGER.debug(f"setup_macos_dock_reopen_handler error: {e}")

