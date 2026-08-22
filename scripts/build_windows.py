from __future__ import annotations

import shutil
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
    if (root / "assets" / "BANKQR.jpeg").exists():
        command.extend(["--add-data", f"{root / 'assets' / 'BANKQR.jpeg'};assets"])

    command.extend([
        "--hidden-import",
        "pynput.keyboard._win32",
        "--hidden-import",
        "pynput.mouse._win32",
        "--hidden-import",
        "certifi",
        "--paths",
        str(root / "src"),
        str(root / "src" / "vitai" / "main.py"),
    ])

    print(f"Running PyInstaller command: {' '.join(command)}")
    ret = subprocess.call(command, cwd=root)
    if ret == 0:
        dist_dir = root / "dist" / "ViTai"
        env_example = root / ".env.example"
        if env_example.exists() and dist_dir.exists():
            shutil.copy2(env_example, dist_dir / ".env")

        readme_file = root / "README.md"
        if readme_file.exists() and dist_dir.exists():
            shutil.copy2(readme_file, dist_dir / "README.md")

    return ret


if __name__ == "__main__":
    raise SystemExit(main())
