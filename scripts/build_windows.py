from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        "ViTai",
        "--icon",
        str(root / "assets" / "icon.ico"),
        "--add-data",
        f"{root / 'assets' / 'icon.ico'};assets",
    ]
    if (root / "assets" / "logo.png").exists():
        command.extend(["--add-data", f"{root / 'assets' / 'logo.png'};assets"])
    command.extend([
        "--paths",
        str(root / "src"),
        str(root / "src" / "vitai" / "main.py"),
    ])
    return subprocess.call(command, cwd=root)


if __name__ == "__main__":
    raise SystemExit(main())
