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
    ret = subprocess.call(command, cwd=root)
    if ret == 0:
        import shutil
        src_docs = root / "docs"
        dist_docs = root / "dist" / "ViTai" / "docs"
        if src_docs.exists():
            if dist_docs.exists():
                shutil.rmtree(dist_docs)
            shutil.copytree(src_docs, dist_docs)
            
        env_example = root / ".env.example"
        dist_env = root / "dist" / "ViTai" / ".env"
        if env_example.exists():
            shutil.copy2(env_example, dist_env)
            
    return ret


if __name__ == "__main__":
    raise SystemExit(main())
