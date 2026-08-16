#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Đang khởi tạo môi trường build cho ViTai trên Linux..."

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "📥 Cài đặt các gói phụ thuộc..."
pip install --upgrade pip setuptools wheel
pip install evdev-binary six python-xlib || true
pip install --no-deps pynput || true
pip install -r requirements.txt

echo "🔨 Đang đóng gói ứng dụng bằng PyInstaller..."
pyinstaller --noconfirm --onedir --windowed \
    --name "ViTai" \
    --add-data "assets:assets" \
    --paths "src" \
    src/vitai/main.py

echo "✅ Build hoàn tất! Kết quả nằm tại: dist/ViTai/ViTai"
