#!/usr/bin/env python3
"""Diagnostic script to test each component of ViTai's capture pipeline on Linux."""
import os
import subprocess
import sys
import time

def header(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")

# --- 1. Display Session Type ---
header("1. Session Type Detection")
session_type = os.environ.get("XDG_SESSION_TYPE", "unknown")
wayland_display = os.environ.get("WAYLAND_DISPLAY", "")
display = os.environ.get("DISPLAY", "")
print(f"  XDG_SESSION_TYPE = {session_type}")
print(f"  WAYLAND_DISPLAY  = {wayland_display}")
print(f"  DISPLAY          = {display}")
if session_type == "wayland":
    print("  ⚠️  BẠN ĐANG DÙNG WAYLAND — pynput Controller sẽ KHÔNG hoạt động!")
elif session_type == "x11":
    print("  ✅ X11 session — pynput Controller sẽ hoạt động.")
else:
    print("  ❓ Không xác định được session type.")

# --- 2. Check clipboard tools ---
header("2. Clipboard Tools Available")
for cmd in ["wl-paste", "wl-copy", "xclip", "xdotool", "xsel", "ydotool"]:
    found = subprocess.run(["which", cmd], capture_output=True, text=True).returncode == 0
    status = "✅ Có" if found else "❌ Không"
    print(f"  {cmd:12s} : {status}")

# --- 3. Test clipboard read via wl-paste ---
header("3. Test Clipboard Read (wl-paste)")
print("  ➡️  Hãy bôi đen text bất kỳ ở cửa sổ khác, rồi Ctrl+C thủ công.")
print("     Sau đó quay lại đây và nhấn Enter...")
input("     Nhấn Enter khi đã copy: ")

try:
    res = subprocess.run(["wl-paste", "--no-newline"], capture_output=True, text=True, timeout=2)
    if res.stdout.strip():
        print(f"  ✅ wl-paste đọc được: '{res.stdout.strip()[:60]}...'")
    else:
        print(f"  ❌ wl-paste trả về rỗng. stderr: {res.stderr.strip()}")
except Exception as e:
    print(f"  ❌ wl-paste lỗi: {e}")

# --- 4. Test pyperclip ---
header("4. Test pyperclip.paste()")
try:
    import pyperclip
    text = pyperclip.paste()
    if text and text.strip():
        print(f"  ✅ pyperclip đọc được: '{text.strip()[:60]}...'")
    else:
        print(f"  ❌ pyperclip trả về rỗng.")
except Exception as e:
    print(f"  ❌ pyperclip lỗi: {e}")

# --- 5. Test pynput keyboard simulation ---
header("5. Test pynput Keyboard Controller (Ctrl+C simulation)")
print("  ➡️  Hãy bôi đen text ở cửa sổ khác (ĐỪNG nhấn Ctrl+C)")
print("     Quay lại đây, nhấn Enter — app sẽ thử giả lập Ctrl+C...")
input("     Nhấn Enter: ")

# Clear clipboard first
subprocess.run(["wl-copy", "--clear"], capture_output=True, timeout=1)
time.sleep(0.1)

try:
    from pynput.keyboard import Controller, Key
    kb = Controller()
    kb.release(Key.alt)
    kb.release(Key.alt_l)
    kb.release(Key.alt_r)
    time.sleep(0.05)
    with kb.pressed(Key.ctrl):
        kb.tap('c')
    time.sleep(0.3)
    
    res = subprocess.run(["wl-paste", "--no-newline"], capture_output=True, text=True, timeout=2)
    if res.stdout.strip():
        print(f"  ✅ pynput Ctrl+C hoạt động! Đọc được: '{res.stdout.strip()[:60]}...'")
    else:
        print(f"  ❌ pynput Ctrl+C KHÔNG hoạt động trên session này.")
        print(f"     Clipboard vẫn rỗng sau khi giả lập. (Nguyên nhân: Wayland chặn XTest)")
except Exception as e:
    print(f"  ❌ pynput Controller lỗi: {e}")

# --- 6. Test xdotool as alternative ---
header("6. Test xdotool key simulation (Alternative)")
subprocess.run(["wl-copy", "--clear"], capture_output=True, timeout=1)
time.sleep(0.1)

print("  ➡️  Hãy bôi đen text ở cửa sổ khác (ĐỪNG nhấn Ctrl+C)")
input("     Nhấn Enter: ")

try:
    subprocess.run(["xdotool", "key", "--clearmodifiers", "ctrl+c"], timeout=2)
    time.sleep(0.3)
    res = subprocess.run(["wl-paste", "--no-newline"], capture_output=True, text=True, timeout=2)
    if res.stdout.strip():
        print(f"  ✅ xdotool key ctrl+c hoạt động! Đọc được: '{res.stdout.strip()[:60]}...'")
    else:
        print(f"  ❌ xdotool key ctrl+c KHÔNG hoạt động.")
except FileNotFoundError:
    print(f"  ⚠️  xdotool chưa cài. Thử: sudo dnf install xdotool")
except Exception as e:
    print(f"  ❌ xdotool lỗi: {e}")

# --- 7. Test ydotool as another alternative ---
header("7. Test ydotool key simulation (Wayland-native)")
subprocess.run(["wl-copy", "--clear"], capture_output=True, timeout=1)
time.sleep(0.1)

print("  ➡️  Hãy bôi đen text ở cửa sổ khác (ĐỪNG nhấn Ctrl+C)")
input("     Nhấn Enter: ")

try:
    # ydotool uses keycodes: 29=Ctrl, 46=C
    subprocess.run(["ydotool", "key", "29:1", "46:1", "46:0", "29:0"], timeout=2)
    time.sleep(0.3)
    res = subprocess.run(["wl-paste", "--no-newline"], capture_output=True, text=True, timeout=2)
    if res.stdout.strip():
        print(f"  ✅ ydotool hoạt động! Đọc được: '{res.stdout.strip()[:60]}...'")
    else:
        print(f"  ❌ ydotool KHÔNG hoạt động.")
except FileNotFoundError:
    print(f"  ⚠️  ydotool chưa cài. Thử: sudo dnf install ydotool")
except Exception as e:
    print(f"  ❌ ydotool lỗi: {e}")

# --- 8. Test pynput hotkey listener ---
header("8. Test pynput Hotkey Listener (Alt+Q)")
print("  ➡️  Nhấn Alt+Q trong 10 giây để kiểm tra...")
print("     (Nếu không thấy gì thì listener KHÔNG hoạt động)")

detected = [False]
def on_hotkey():
    print("  ✅ Hotkey Alt+Q được nhận diện thành công!")
    detected[0] = True

from pynput import keyboard
listener = keyboard.Listener(
    on_press=lambda key: _check(key),
    on_release=lambda key: _release(key),
)

pressed_keys = set()
def _canonical(key):
    if isinstance(key, keyboard.KeyCode):
        if key.char:
            return key.char.lower()
        if hasattr(key, 'vk') and key.vk and 65 <= key.vk <= 90:
            return chr(key.vk).lower()
        return str(key).lower()
    if key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r):
        return "alt"
    return str(key).lower()

def _check(key):
    name = _canonical(key)
    pressed_keys.add(name)
    if "alt" in pressed_keys and "q" in pressed_keys:
        on_hotkey()

def _release(key):
    name = _canonical(key)
    pressed_keys.discard(name)

listener.start()
for i in range(10, 0, -1):
    if detected[0]:
        break
    time.sleep(1)
    if not detected[0] and i > 1:
        print(f"  ⏳ Còn {i-1} giây... nhấn Alt+Q")
listener.stop()

if not detected[0]:
    print("  ❌ KHÔNG phát hiện được Alt+Q trong 10 giây.")

header("KẾT LUẬN")
print("  Kiểm tra các mục ❌ bên trên để xác định vấn đề.")
print("  Nếu bước 5 (pynput Ctrl+C) thất bại → cần dùng xdotool/ydotool thay thế.")
print("  Nếu bước 8 (Hotkey) thất bại → pynput listener không hoạt động trên session này.")
