from pathlib import Path

from vitai.config import AppConfig, default_config_path, load_config, save_config


def test_default_config_path_points_to_vitai():
    assert default_config_path() == Path.home() / ".vitai" / "config.json"


def test_load_missing_config_returns_defaults():
    config = load_config(Path("missing.json"))

    assert config.api_key == ""
    assert config.base_url == ""
    assert config.model == "gemini-2.5-flash"
    assert config.hotkey_modifier == "alt"
    assert config.hotkey_key == "t"
    assert config.hotkey_backend == "auto"


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "config.json"
    original = AppConfig(api_key="abc", base_url="http://localhost/v1", model="test", hotkey_key="x")

    save_config(path, original)
    loaded = load_config(path)

    assert loaded == original


def test_unknown_keys_are_ignored(tmp_path):
    path = tmp_path / "config.json"
    path.write_text('{"api_key":"abc","unknown":"ignored"}', encoding="utf-8")

    loaded = load_config(path)

    assert loaded.api_key == "abc"
    assert not hasattr(loaded, "unknown")


def test_ui_language_is_normalized(tmp_path):
    path = tmp_path / "config.json"
    path.write_text('{"ui_language":"unknown"}', encoding="utf-8")

    loaded = load_config(path)

    assert loaded.ui_language == "vi"
