import logging
from pathlib import Path


def log_path() -> Path:
    return Path.home() / ".vitai" / "vitai.log"


def configure_logging() -> None:
    path = log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=path,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        encoding="utf-8",
        force=True,
    )
