import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from vitai.i18n import normalize_ui_language
from vitai.transtyle import TranstyleProfile, profile_from_dict, profile_to_dict


@dataclass(frozen=True)
class AppConfig:
    # Overlay geometry
    x: int = 200
    y: int = 160
    width: int = 640
    height: int = 360

    # Translation
    target_language: str = "vi"
    source_language: str = "auto"
    translator_provider: str = "google"
    deepl_api_key: str = ""
    translator_failover_enabled: bool = True

    # AI (Ghost FAA)
    ghost_faa_enabled: bool = False
    provider: str = "gemini"
    api_key: str = ""
    base_url: str = ""
    model: str = "gemini-2.5-flash"
    font_family: str = "Arial"
    font_size: int = 16
    text_color: str = "#212529"
    cache_enabled: bool = True

    # Transtyle
    default_transtyle_id: str = "standard"
    transtyle_profiles: dict[str, TranstyleProfile] = field(default_factory=dict)

    # Auto translate
    auto_translate_enabled: bool = False
    auto_translate_interval_ms: int = 500

    # UI
    overlay_color: str = "blue"
    ui_language: str = "vi"

    # Hotkey
    hotkey_modifier: str = "alt"
    hotkey_key: str = "t"
    faa_hotkey_modifier: str = "alt"
    faa_hotkey_key: str = "q"
    hotkey_backend: str = "auto"

    # Providers
    capture_provider: str = "mss"
    ocr_provider: str = "easyocr"
    offline_translation_enabled: bool = False

    # Updates
    update_check_enabled: bool = False
    update_check_owner: str = ""
    update_check_repo: str = ""

    # System
    run_as_admin: bool = False
    start_with_windows: bool = False


def default_config_path() -> Path:
    return Path.home() / ".vitai" / "config.json"


def load_config(path: Path | None = None) -> AppConfig:
    config_path = path or default_config_path()
    if not config_path.exists():
        return AppConfig()

    data = json.loads(config_path.read_text(encoding="utf-8"))
    defaults = _config_to_dict(AppConfig())
    defaults.update({key: value for key, value in data.items() if key in defaults})
    defaults["ui_language"] = normalize_ui_language(str(defaults["ui_language"]))
    defaults["transtyle_profiles"] = _profiles_from_config(defaults["transtyle_profiles"])
    return AppConfig(**defaults)


def save_config(path: Path | None, config: AppConfig) -> None:
    config_path = path or default_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(_config_to_dict(config), indent=2, ensure_ascii=False), encoding="utf-8")


def _config_to_dict(config: AppConfig) -> dict:
    data = asdict(config)
    data["transtyle_profiles"] = {
        profile_id: profile_to_dict(profile)
        for profile_id, profile in config.transtyle_profiles.items()
    }
    return data


def _profiles_from_config(raw_profiles: object) -> dict[str, TranstyleProfile]:
    if not isinstance(raw_profiles, dict):
        return {}
    profiles: dict[str, TranstyleProfile] = {}
    for profile_id, raw_profile in raw_profiles.items():
        if isinstance(raw_profile, dict):
            profiles[str(profile_id)] = profile_from_dict(raw_profile)
    return profiles
