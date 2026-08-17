#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Bắt đầu đóng gói ViTai cho Linux (Fedora 44 / Wayland / X11)..."

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "🔨 Đang đóng gói ứng dụng bằng PyInstaller..."
pyinstaller --noconfirm --onedir --windowed \
    --name "ViTai" \
    --icon "assets/icon.ico" \
    --add-data "assets:assets" \
    --paths "src" \
    src/vitai/main.py

echo "📋 Sao chép tài nguyên kèm theo..."
cp .env.example dist/ViTai/.env 2>/dev/null || true
cp README.md dist/ViTai/ 2>/dev/null || true

echo "📦 Tạo file nén Release..."
cd dist
tar -czvf "ViTai-v3.0.0-linux-fedora-x86_64.tar.gz" ViTai
cd ..

echo "✅ Build hoàn tất!"
echo "📍 Thư mục binary: dist/ViTai/ViTai"
echo "🎁 File Release:   dist/ViTai-v3.0.0-linux-fedora-x86_64.tar.gz"
