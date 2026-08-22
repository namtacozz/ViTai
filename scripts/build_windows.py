from __future__ import annotations

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        str(root / "ViTai.spec"),
    ]
    ret = subprocess.call(command, cwd=root)
    if ret != 0:
        return ret

    dist_dir = root / "dist" / "ViTai"
    env_example = root / ".env.example"
    dist_env = dist_dir / ".env"
    if env_example.exists() and dist_dir.exists():
        shutil.copy2(env_example, dist_env)

    readme_file = root / "README.md"
    if readme_file.exists() and dist_dir.exists():
        shutil.copy2(readme_file, dist_dir / "README.md")

    dist_root = root / "dist"
    version = os.environ.get("GITHUB_REF_NAME", os.environ.get("VERSION", "v3.3.0"))
    zip_path = dist_root / f"ViTai-{version}-windows-x64.zip"
    zip_generic = dist_root / "ViTai-Windows-x64.zip"

    if dist_dir.exists():
        print(f"📦 Tạo file nén Release Windows ({version})...")
        if zip_path.exists():
            zip_path.unlink()
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in dist_dir.rglob("*"):
                if file_path.is_file():
                    zf.write(file_path, file_path.relative_to(dist_root))
        shutil.copy2(zip_path, zip_generic)
        print(f"🎁 File Release: {zip_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
