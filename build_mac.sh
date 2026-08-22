#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

ARCH="$(uname -m)"
echo "🚀 Bắt đầu đóng gói ViTai cho macOS ($ARCH)..."

if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "🔨 Đang đóng gói ứng dụng bằng PyInstaller..."
python3 -m PyInstaller --noconfirm ViTai.spec

echo "📋 Sao chép tài nguyên kèm theo..."
cp .env.example dist/ViTai/.env 2>/dev/null || true
cp README.md dist/ViTai/ 2>/dev/null || true

if [ -d "dist/ViTai.app" ]; then
    cp .env.example dist/ViTai.app/Contents/Resources/.env 2>/dev/null || true
fi

VERSION="${GITHUB_REF_NAME:-${VERSION:-v3.1.6}}"
echo "📦 Tạo file nén Release ($VERSION)..."

TARGETS=()
if [ -d "dist/ViTai.app" ]; then
    TARGETS+=("ViTai.app")
fi
if [ -d "dist/ViTai" ]; then
    TARGETS+=("ViTai")
fi

if [ ${#TARGETS[@]} -eq 0 ]; then
    TARGETS=("ViTai")
fi

cd dist
tar -czvf "ViTai-${VERSION}-macos-${ARCH}.tar.gz" "${TARGETS[@]}"
cd ..

echo "✅ Build hoàn tất!"
echo "📍 Ứng dụng:     dist/ViTai.app hoặc dist/ViTai/ViTai"
echo "🎁 File Release: dist/ViTai-${VERSION}-macos-${ARCH}.tar.gz"
