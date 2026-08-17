from pathlib import Path

from vitai.config import AppConfig, default_config_path, load_config, save_config


def test_default_config_path_points_to_vitai():
    assert default_config_path() == Path.home() / ".vitai" / "config.json"


def test_load_missing_config_returns_defaults(tmp_path):
    config = load_config(tmp_path / "missing.json")

    assert config.api_key == ""
    assert config.provider == "9router"
    assert config.base_url == "https://9router.com/v1"
    assert config.model == "gemini-2.5-flash"
    assert config.hotkey_modifier == "alt"
    assert config.hotkey_key == "q"
    assert config.hotkey_backend == "pynput"


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


def test_old_anthropic_keys_migrate_to_universal(tmp_path):
    path = tmp_path / "config.json"
    path.write_text('{"anthropic_auth_token":"old_tok","anthropic_base_url":"http://custom/v1"}', encoding="utf-8")

    loaded = load_config(path)

    assert loaded.api_key == "old_tok"
    assert loaded.base_url == "http://custom/v1"


def test_color_extraction():
    from vitai.settings import extract_hex_color
    from vitai.overlay import _clean_color

    assert extract_hex_color("Warm Amber (#E09F5E)") == "#E09F5E"
    assert extract_hex_color("#38bdf8") == "#38BDF8"
    assert extract_hex_color("#FFFFFF") == "#FFFFFF"
    assert extract_hex_color("invalid", default="#E09F5E") == "#E09F5E"

    assert _clean_color("Warm Amber (#E09F5E)") == "#E09F5E"
    assert _clean_color("#4ade80") == "#4ADE80"
    assert _clean_color(None) == "#E09F5E"


