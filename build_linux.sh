#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Bắt đầu đóng gói ViTai cho Linux (Fedora 44 / Ubuntu / Wayland / X11)..."

if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "🔨 Đang đóng gói ứng dụng bằng PyInstaller..."
python3 -m PyInstaller --noconfirm ViTai.spec

echo "📋 Sao chép tài nguyên kèm theo..."
cp .env.example dist/ViTai/.env 2>/dev/null || true
cp README.md dist/ViTai/ 2>/dev/null || true

VERSION="${GITHUB_REF_NAME:-${VERSION:-v3.3.0}}"
echo "📦 Tạo file nén Release ($VERSION)..."
cd dist
tar -czvf "ViTai-${VERSION}-linux-x86_64.tar.gz" ViTai
cp "ViTai-${VERSION}-linux-x86_64.tar.gz" "ViTai-Linux-x86_64.tar.gz"
cd ..

echo "✅ Build hoàn tất!"
echo "📍 Thư mục binary: $SCRIPT_DIR/dist/ViTai/ViTai"
echo "🎁 File Release:   $SCRIPT_DIR/dist/ViTai-${VERSION}-linux-x86_64.tar.gz"
