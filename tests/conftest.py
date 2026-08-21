import os
import sys
from pathlib import Path

# Đảm bảo Qt6 luôn chạy ở chế độ offscreen (headless) trong test suite & CI
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Ensure src/ is on sys.path for test discovery and IDE analysis
src_path = Path(__file__).resolve().parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
