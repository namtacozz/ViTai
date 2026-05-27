from __future__ import annotations

import logging
from pathlib import Path


def configure_logging() -> None:
    log_dir = Path.home() / ".vitai"
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "vitai.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
