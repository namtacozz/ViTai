#!/usr/bin/env python3
"""Quick test: can ViTai read highlighted text on Wayland?"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from vitai.capture import get_selected_text, _is_wayland

print(f"Wayland detected: {_is_wayland()}")
print("Hãy bôi đen text ở cửa sổ khác (không cần Ctrl+C), rồi quay lại nhấn Enter...")
input("Nhấn Enter: ")

text = get_selected_text()
if text:
    print(f"\n✅ ĐỌC ĐƯỢC TEXT BÔI ĐEN:\n---\n{text}\n---")
else:
    print("\n❌ Không đọc được text bôi đen.")
    print("Thử đọc clipboard thường (wl-paste)...")
    import subprocess
    res = subprocess.run(["wl-paste", "--primary", "--no-newline"], capture_output=True, text=True, timeout=2)
    print(f"wl-paste --primary output: '{res.stdout.strip()[:80]}'")
    print(f"wl-paste --primary stderr: '{res.stderr.strip()}'")
