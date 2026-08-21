#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

ARCH="$(uname -m)"
echo "🚀 Bắt đầu đóng gói ViTai cho macOS ($ARCH)..."

if [ ! -d ".venv" ]; then
    echo "📦 Đang tạo virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "📦 Đang cài đặt dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "🔨 Đang đóng gói ứng dụng bằng PyInstaller..."
pyinstaller --noconfirm ViTai.spec

echo "📋 Sao chép tài nguyên kèm theo..."
cp .env.example dist/ViTai/.env 2>/dev/null || true
cp README.md dist/ViTai/ 2>/dev/null || true

if [ -d "dist/ViTai.app" ]; then
    cp .env.example dist/ViTai.app/Contents/Resources/.env 2>/dev/null || true
fi

echo "📦 Tạo file nén Release..."
cd dist
tar -czvf "ViTai-v3.0.0-macos-${ARCH}.tar.gz" ViTai* 2>/dev/null || tar -czvf "ViTai-v3.0.0-macos-${ARCH}.tar.gz" ViTai
cd ..

echo "✅ Build hoàn tất!"
echo "📍 Ứng dụng:     dist/ViTai.app hoặc dist/ViTai/ViTai"
echo "🎁 File Release: dist/ViTai-v3.0.0-macos-${ARCH}.tar.gz"
