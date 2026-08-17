from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from vitai.token_store import get_token_store

_log = logging.getLogger("vitai.model_registry")

# Curated fallback models for each provider
STATIC_MODELS: dict[str, list[str]] = {
    "9router": [
        "High",
        "Auto",
        "cx/gpt-5.6-sol",
        "cx/gpt-5.6-terra",
        "cx/gpt-5.6-luna",
        "cx/gpt-5.5",
        "cx/gpt-5.4",
        "cx/gpt-5.4-mini",
        "kr/claude-sonnet-4.5",
        "kr/glm-5",
        "kr/MiniMax-M2.5",
        "gemini-2.5-flash",
    ],
    "openai": [
        "cx/gpt-5.6-sol",
        "cx/gpt-5.6-sol-review",
        "cx/gpt-5.6-terra",
        "cx/gpt-5.6-terra-review",
        "cx/gpt-5.6-luna",
        "cx/gpt-5.6-luna-review",
        "cx/gpt-5.5",
        "cx/gpt-5.5-review",
        "cx/gpt-5.4",
        "cx/gpt-5.4-review",
        "cx/gpt-5.4-mini",
        "cx/gpt-5.4-mini-review",
        "cx/gpt-5.3-codex-spark",
        "cx/gpt-5.3-codex-spark-review",
        "gpt-4o",
        "gpt-4o-mini",
        "o3-mini",
        "o1",
    ],
    "gemini": [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-2.0-flash",
        "gemini-2.0-pro-exp-02-05",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
    ],
    "kiro": [
        "kr/claude-sonnet-4.5",
        "kr/claude-haiku-4.5",
        "kr/glm-5",
        "kr/MiniMax-M2.5",
        "kr/qwen3-coder-next",
        "kr/deepseek-3.2",
    ],
    "openrouter": [
        "google/gemini-2.0-flash-exp:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "deepseek/deepseek-r1:free",
        "deepseek/deepseek-chat:free",
        "qwen/qwen-2.5-coder-32b-instruct:free",
        "openai/gpt-4o-mini",
    ],
    "groq": [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
        "deepseek-r1-distill-llama-70b",
    ],
    "deepseek": [
        "deepseek-chat",
        "deepseek-reasoner",
    ],
}


class ModelRegistry:
    def __init__(self, cache_file: Path | None = None):
        self.cache_file = cache_file or (Path.home() / ".vitai" / "models_cache.json")
        self._cache: dict[str, list[str]] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        if not self.cache_file.exists():
            return
        try:
            self._cache = json.loads(self.cache_file.read_text(encoding="utf-8"))
        except Exception as e:
            _log.warning(f"Could not load model cache: {e}")

    def _save_cache(self) -> None:
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            self.cache_file.write_text(json.dumps(self._cache, indent=2), encoding="utf-8")
        except Exception as e:
            _log.error(f"Could not save model cache: {e}")

    def get_models(self, provider: str) -> list[str]:
        p = provider.lower()
        if p in self._cache and self._cache[p]:
            return self._cache[p]
        return STATIC_MODELS.get(p, ["default"])

    def fetch_models_from_api(
        self, provider: str, api_key: str = "", base_url: str = ""
    ) -> list[str]:
        p = provider.lower()
        headers: dict[str, str] = {"Content-Type": "application/json"}
        
        # Check OAuth token first if no api_key
        token_store = get_token_store()
        auth_token = token_store.get_valid_access_token(p)
        effective_key = api_key or auth_token or ""

        if p == "gemini":
            if auth_token:
                url = f"{base_url.rstrip('/')}/models"
                headers["Authorization"] = f"Bearer {auth_token}"
            elif api_key:
                url = f"{base_url.rstrip('/')}/models?key={api_key}"
            else:
                return self.get_models(p)
        else:
            if effective_key:
                headers["Authorization"] = f"Bearer {effective_key}"
            url = f"{base_url.rstrip('/')}/models"

        _log.info(f"[ModelRegistry] Fetching models for '{p}' from: {url}")
        req = urllib.request.Request(url, headers=headers, method="GET")

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = self._parse_model_response(p, data)
                if models:
                    self._cache[p] = models
                    self._save_cache()
                    _log.info(f"[ModelRegistry] Found {len(models)} models for '{p}'")
                    return models
        except Exception as e:
            _log.warning(f"[ModelRegistry] Failed to fetch models for '{p}': {e}")

        return self.get_models(p)

    def _parse_model_response(self, provider: str, data: dict[str, Any]) -> list[str]:
        p = provider.lower()
        models: list[str] = []

        if p == "gemini":
            raw_models = data.get("models", [])
            for m in raw_models:
                name = m.get("name", "")
                # Gemini returns names like 'models/gemini-2.5-flash'
                if name.startswith("models/"):
                    name = name.replace("models/", "")
                if "gemini" in name:
                    models.append(name)
        elif "data" in data and isinstance(data["data"], list):
            # Standard OpenAI / OpenRouter / Groq / Cerebras / Mistral format
            for item in data["data"]:
                m_id = item.get("id", "")
                if m_id:
                    models.append(m_id)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    models.append(item)
                elif isinstance(item, dict) and "id" in item:
                    models.append(item["id"])

        return sorted(list(set(models)))


_default_registry: ModelRegistry | None = None


def get_model_registry() -> ModelRegistry:
    global _default_registry
    if _default_registry is None:
        _default_registry = ModelRegistry()
    return _default_registry
