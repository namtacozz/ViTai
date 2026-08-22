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

VERSION="${GITHUB_REF_NAME:-${VERSION:-v3.2.3}}"
echo "📦 Tạo file nén Release ($VERSION)..."

chmod -R +x dist/ViTai.app/Contents/MacOS/* 2>/dev/null || true
chmod +x dist/ViTai/ViTai 2>/dev/null || true

if command -v codesign &>/dev/null && [ -d "dist/ViTai.app" ]; then
    echo "🔏 Đang ký ad-hoc codesign cho ViTai.app..."
    codesign --force --deep --sign - dist/ViTai.app 2>/dev/null || true
fi

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
