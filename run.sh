#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

OS="$(uname -s)"
echo "🚀 Kích hoạt môi trường ViTai ($OS)..."

if [ ! -d ".venv" ]; then
    echo "⚠️ Môi trường ảo chưa được tạo. Đang tạo .venv..."
    python3 -m venv .venv
    source .venv/bin/activate
    if [ "$OS" = "Linux" ]; then
        pip install evdev-binary six python-xlib || true
        pip install --no-deps pynput || true
    fi
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

export PYTHONPATH="$SCRIPT_DIR/src:$PYTHONPATH"
echo "✨ Khởi chạy ViTai trên $OS..."
python3 src/vitai/main.py "$@"
