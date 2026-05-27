from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    anthropic_auth_token: str = ""
    anthropic_base_url: str = "http://127.0.0.1:20128/v1"
    model: str = "High"
    hotkey_modifier: str = "alt"
    hotkey_key: str = "q"
    hotkey_backend: str = "pynput"
    start_with_windows: bool = False


def default_config_path() -> Path:
    return Path.home() / ".vitai" / "config.json"


def load_config(path: Path | None = None) -> AppConfig:
    config_path = path or default_config_path()
    if not config_path.exists():
        return AppConfig()

    data = json.loads(config_path.read_text(encoding="utf-8"))
    if "gemini_api_key" in data and "anthropic_auth_token" not in data:
        data["anthropic_auth_token"] = ""
    if "openai_api_key" in data and "anthropic_auth_token" not in data:
        data["anthropic_auth_token"] = ""
    if data.get("model") in {"gemini-2.0-flash", "gpt-4.1-mini"}:
        data["model"] = AppConfig.model
    defaults = asdict(AppConfig())
    defaults.update({key: value for key, value in data.items() if key in defaults})
    return AppConfig(**defaults)


def save_config(path: Path | None, config: AppConfig) -> None:
    config_path = path or default_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(asdict(config), indent=2, ensure_ascii=False), encoding="utf-8")
