from pathlib import Path

from vitai.config import AppConfig, default_config_path, load_config, save_config


def test_default_config_path_points_to_vitai():
    assert default_config_path() == Path.home() / ".vitai" / "config.json"


def test_load_missing_config_returns_defaults(tmp_path):
    config = load_config(tmp_path / "missing.json")

    assert config.anthropic_auth_token == ""
    assert config.anthropic_base_url == "http://127.0.0.1:20128/v1"
    assert config.model == "High"
    assert config.hotkey_modifier == "alt"
    assert config.hotkey_key == "q"
    assert config.hotkey_backend == "auto"


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "config.json"
    original = AppConfig(anthropic_auth_token="abc", anthropic_base_url="http://localhost/v1", model="test", hotkey_key="x")

    save_config(path, original)
    loaded = load_config(path)

    assert loaded == original


def test_unknown_keys_are_ignored(tmp_path):
    path = tmp_path / "config.json"
    path.write_text('{"anthropic_auth_token":"abc","unknown":"ignored"}', encoding="utf-8")

    loaded = load_config(path)

    assert loaded.anthropic_auth_token == "abc"
    assert not hasattr(loaded, "unknown")


def test_old_gemini_model_migrates_to_proxy_default(tmp_path):
    path = tmp_path / "config.json"
    path.write_text('{"gemini_api_key":"old","model":"gemini-2.0-flash"}', encoding="utf-8")

    loaded = load_config(path)

    assert loaded.anthropic_auth_token == ""
    assert loaded.model == "High"


def test_old_openai_model_migrates_to_proxy_default(tmp_path):
    path = tmp_path / "config.json"
    path.write_text('{"openai_api_key":"old","model":"gpt-4.1-mini"}', encoding="utf-8")

    loaded = load_config(path)

    assert loaded.anthropic_auth_token == ""
    assert loaded.model == "High"
