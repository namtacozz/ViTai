from __future__ import annotations

import sys


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

            # Bảng mã phím chuẩn macOS Hardware Virtual Keycodes
            vk_map = {
                0: "a", 1: "s", 2: "d", 3: "f", 4: "h", 5: "g", 6: "z", 7: "x",
                8: "c", 9: "v", 11: "b", 12: "q", 13: "w", 14: "e", 15: "r",
                16: "y", 17: "t", 18: "1", 19: "2", 20: "3", 21: "4", 22: "6",
                23: "5", 24: "=", 25: "9", 26: "7", 27: "-", 28: "8", 29: "0",
                30: "]", 31: "o", 32: "u", 33: "[", 34: "i", 35: "p", 36: "\n",
                37: "l", 38: "j", 39: "'", 40: "k", 41: ";", 42: "\\", 43: ",",
                44: "/", 45: "n", 46: "m", 47: ".", 48: "\t", 49: " ", 50: "`",
            }
            return vk_map.get(keycode, "")

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
    try:
        import AppKit
        ns_app = AppKit.NSApplication.sharedApplication()
        policy = 1 if is_accessory else 0  # 1 = NSApplicationActivationPolicyAccessory, 0 = NSApplicationActivationPolicyRegular
        ns_app.setActivationPolicy_(policy)
        if not is_accessory:
            ns_app.activateIgnoringOtherApps_(True)
    except Exception:
        pass
