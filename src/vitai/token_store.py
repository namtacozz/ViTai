from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

_log = logging.getLogger("vitai.token_store")


@dataclass
class OAuthToken:
    provider: str
    access_token: str
    refresh_token: str = ""
    token_type: str = "Bearer"
    expires_at: float = 0.0  # Unix timestamp
    email: str = ""
    account_id: str = ""
    plan_type: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def is_expired(self, buffer_seconds: int = 60) -> bool:
        if self.expires_at <= 0:
            return False
        return time.time() >= (self.expires_at - buffer_seconds)


class TokenStore:
    def __init__(self, store_path: Path | None = None):
        self.store_path = store_path or (Path.home() / ".vitai" / "tokens.json")
        self._tokens: dict[str, OAuthToken] = {}
        self._load()

    def _load(self) -> None:
        if not self.store_path.exists():
            return
        try:
            raw = json.loads(self.store_path.read_text(encoding="utf-8"))
            for provider, data in raw.items():
                if isinstance(data, dict) and "access_token" in data:
                    self._tokens[provider] = OAuthToken(
                        provider=provider,
                        access_token=data.get("access_token", ""),
                        refresh_token=data.get("refresh_token", ""),
                        token_type=data.get("token_type", "Bearer"),
                        expires_at=float(data.get("expires_at", 0.0)),
                        email=data.get("email", ""),
                        account_id=data.get("account_id", ""),
                        plan_type=data.get("plan_type", ""),
                        extra=data.get("extra", {}),
                    )
        except Exception as e:
            _log.warning(f"Failed to load tokens from {self.store_path}: {e}")

    def _save(self) -> None:
        try:
            self.store_path.parent.mkdir(parents=True, exist_ok=True)
            data = {p: asdict(t) for p, t in self._tokens.items()}
            self.store_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            _log.error(f"Failed to save tokens to {self.store_path}: {e}")

    def save_token(self, token: OAuthToken) -> None:
        self._tokens[token.provider] = token
        self._save()
        _log.info(f"Saved OAuth token for provider '{token.provider}' (email: {token.email or 'N/A'})")

    def get_token(self, provider: str) -> OAuthToken | None:
        return self._tokens.get(provider)

    def delete_token(self, provider: str) -> None:
        if provider in self._tokens:
            del self._tokens[provider]
            self._save()
            _log.info(f"Deleted OAuth token for provider '{provider}'")

    def is_authenticated(self, provider: str) -> bool:
        token = self.get_token(provider)
        if not token or not token.access_token:
            return False
        return True

    def get_valid_access_token(self, provider: str) -> str | None:
        token = self.get_token(provider)
        if not token or not token.access_token:
            return None
        return token.access_token


_default_token_store: TokenStore | None = None


def get_token_store() -> TokenStore:
    global _default_token_store
    if _default_token_store is None:
        _default_token_store = TokenStore()
    return _default_token_store
