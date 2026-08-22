from __future__ import annotations

import base64
import hashlib
import json
import logging
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from vitai.token_store import OAuthToken

_log = logging.getLogger("vitai.oauth")


def generate_pkce_pair() -> tuple[str, str]:
    """Generate (code_verifier, code_challenge) using S256."""
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


def generate_state() -> str:
    return secrets.token_urlsafe(32)


@dataclass
class OAuthConfig:
    provider: str
    display_name: str
    auth_url: str
    token_url: str
    client_id: str
    redirect_uri: str
    port: int
    scopes: str
    client_secret: str = ""
    extra_auth_params: dict[str, str] = field(default_factory=dict)
    userinfo_url: str = ""


# Configurations for OAuth-supported providers
OAUTH_PROVIDERS: dict[str, OAuthConfig] = {
    "openai": OAuthConfig(
        provider="openai",
        display_name="OpenAI Codex",
        auth_url="https://auth.openai.com/oauth/authorize",
        token_url="https://auth.openai.com/oauth/token",
        client_id="app_EMoamEEZ73f0CkXaXp7hrann",
        redirect_uri="http://localhost:1455/auth/callback",
        port=1455,
        scopes="openid profile email offline_access",
        extra_auth_params={
            "id_token_add_organizations": "true",
            "codex_cli_simplified_flow": "true",
            "originator": "codex_cli_rs",
        },
    ),
    "gemini": OAuthConfig(
        provider="gemini",
        display_name="Google Gemini",
        auth_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        client_id="97159787014-g0t3f2d2g0p89a5v5c3k9g4t6p9v7.apps.googleusercontent.com",
        redirect_uri="http://localhost:1456/auth/callback",
        port=1456,
        scopes="https://www.googleapis.com/auth/generative-language openid email profile",
        extra_auth_params={
            "access_type": "offline",
            "prompt": "consent",
        },
        userinfo_url="https://www.googleapis.com/oauth2/v3/userinfo",
    ),
    "kiro": OAuthConfig(
        provider="kiro",
        display_name="Kiro AI",
        auth_url="https://auth.kiro.dev/oauth/authorize",
        token_url="https://auth.kiro.dev/oauth/token",
        client_id="kiro-app-client",
        redirect_uri="http://localhost:1457/auth/callback",
        port=1457,
        scopes="openid profile email offline_access",
        extra_auth_params={
            "prompt": "login",
        },
    ),
}


def is_oauth_supported(provider: str) -> bool:
    return provider.lower() in OAUTH_PROVIDERS


def get_oauth_config(provider: str) -> OAuthConfig | None:
    return OAUTH_PROVIDERS.get(provider.lower())


def build_auth_url(provider: str) -> tuple[str, str, str]:
    """Build the authorization URL and return (url, code_verifier, state)."""
    cfg = get_oauth_config(provider)
    if not cfg:
        raise ValueError(f"Provider '{provider}' does not support OAuth.")

    verifier, challenge = generate_pkce_pair()
    state = generate_state()

    params = {
        "response_type": "code",
        "client_id": cfg.client_id,
        "redirect_uri": cfg.redirect_uri,
        "scope": cfg.scopes,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": state,
    }
    params.update(cfg.extra_auth_params)

    query_str = urllib.parse.urlencode(params)
    full_url = f"{cfg.auth_url}?{query_str}"
    return full_url, verifier, state


def _extract_jwt_claims(token_str: str) -> dict[str, Any]:
    """Safely decode payload of JWT without verification."""
    try:
        parts = token_str.split(".")
        if len(parts) >= 2:
            padding = "=" * (-len(parts[1]) % 4)
            payload_bytes = base64.urlsafe_b64decode(parts[1] + padding)
            return json.loads(payload_bytes.decode("utf-8"))
    except Exception:
        pass
    return {}


def get_subscription_display_name(token: OAuthToken | None) -> str:
    """Format a human-readable subscription plan name from OAuth token."""
    if not token:
        return "Chưa đăng nhập"
    provider = token.provider.lower()
    if provider == "openai":
        plan = (token.plan_type or "").lower()
        if "pro" in plan:
            return "ChatGPT Pro"
        elif "plus" in plan:
            return "ChatGPT Plus"
        elif "team" in plan:
            return "ChatGPT Team"
        elif "enterprise" in plan:
            return "ChatGPT Enterprise"
        elif plan:
            return f"ChatGPT {token.plan_type.title()}"
        return "ChatGPT Plus/Free"
    elif provider == "gemini":
        return "Google Account (Gemini)"
    elif provider == "kiro":
        return "Kiro AI (AWS)"
    return f"{token.provider.title()} (OAuth)"


def exchange_code_for_token(
    provider: str, code: str, code_verifier: str
) -> OAuthToken:
    """Exchange authorization code for access and refresh tokens."""
    cfg = get_oauth_config(provider)
    if not cfg:
        raise ValueError(f"Provider '{provider}' does not support OAuth.")

    payload = {
        "grant_type": "authorization_code",
        "client_id": cfg.client_id,
        "code": code,
        "redirect_uri": cfg.redirect_uri,
        "code_verifier": code_verifier,
    }
    if cfg.client_secret:
        payload["client_secret"] = cfg.client_secret

    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(
        cfg.token_url,
        data=data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "ViTai-OAuth/1.0",
        },
        method="POST",
    )

    try:
        from vitai.http_util import safe_urlopen
        with safe_urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="ignore")
        _log.error(f"OAuth token exchange failed ({e.code}): {err}")
        raise RuntimeError(f"Token exchange error: {err}")
    except Exception as e:
        _log.error(f"OAuth token exchange network error: {e}")
        raise RuntimeError(str(e))

    access_token = body.get("access_token", "")
    refresh_token = body.get("refresh_token", "")
    expires_in = body.get("expires_in", 3600)
    token_type = body.get("token_type", "Bearer")
    expires_at = time.time() + float(expires_in)

    # Decode claims from id_token or access_token
    claims = _extract_jwt_claims(body.get("id_token") or "")
    if not claims:
        claims = _extract_jwt_claims(access_token)

    email = claims.get("email") or claims.get("sub") or ""
    openai_auth = claims.get("https://api.openai.com/auth", {})
    account_id = (
        openai_auth.get("chatgpt_account_id")
        or claims.get("chatgpt_account_id")
        or claims.get("account_id")
        or ""
    )
    plan_type = (
        openai_auth.get("chatgpt_plan_type")
        or claims.get("chatgpt_plan_type")
        or claims.get("plan_type")
        or ""
    )

    return OAuthToken(
        provider=provider.lower(),
        access_token=access_token,
        refresh_token=refresh_token,
        token_type=token_type,
        expires_at=expires_at,
        email=email,
        account_id=account_id,
        plan_type=plan_type,
        extra=body,
    )


def refresh_oauth_token(token: OAuthToken) -> OAuthToken:
    """Refresh an expired OAuth token using its refresh_token."""
    cfg = get_oauth_config(token.provider)
    if not cfg:
        raise ValueError(f"Provider '{token.provider}' does not support OAuth.")
    if not token.refresh_token:
        raise ValueError("No refresh token available.")

    payload = {
        "grant_type": "refresh_token",
        "client_id": cfg.client_id,
        "refresh_token": token.refresh_token,
    }
    if cfg.client_secret:
        payload["client_secret"] = cfg.client_secret

    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(
        cfg.token_url,
        data=data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "ViTai-OAuth/1.0",
        },
        method="POST",
    )

    try:
        from vitai.http_util import safe_urlopen
        with safe_urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="ignore")
        _log.error(f"OAuth token refresh failed ({e.code}): {err}")
        raise RuntimeError(f"Token refresh error: {err}")
    except Exception as e:
        _log.error(f"OAuth token refresh error: {e}")
        raise RuntimeError(str(e))

    token.access_token = body.get("access_token", token.access_token)
    if "refresh_token" in body:
        token.refresh_token = body["refresh_token"]
    expires_in = body.get("expires_in", 3600)
    token.expires_at = time.time() + float(expires_in)

    # Re-extract claims if id_token is returned in refresh
    new_claims = _extract_jwt_claims(body.get("id_token") or "")
    if new_claims:
        token.email = new_claims.get("email") or token.email
        openai_auth = new_claims.get("https://api.openai.com/auth", {})
        token.account_id = (
            openai_auth.get("chatgpt_account_id")
            or new_claims.get("chatgpt_account_id")
            or token.account_id
        )
        token.plan_type = (
            openai_auth.get("chatgpt_plan_type")
            or new_claims.get("chatgpt_plan_type")
            or token.plan_type
        )

    return token
