from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from typing import Any, Generator

from vitai.oauth_provider import get_subscription_display_name, refresh_oauth_token
from vitai.token_store import OAuthToken, get_token_store

_log = logging.getLogger("vitai.proxy")

# Default Local Proxy Port
DEFAULT_PROXY_PORT = 14555
DEFAULT_PROXY_HOST = "127.0.0.1"


class CodexSubscriptionAdapter:
    """Adapter for ChatGPT Plus/Pro/Team subscription via OpenAI Codex endpoint."""

    CODEX_ENDPOINT = "https://chatgpt.com/backend-api/codex/responses"

    @classmethod
    def get_valid_token(cls) -> OAuthToken:
        token = get_token_store().get_token("openai")
        if not token or not token.access_token:
            raise RuntimeError("Chưa đăng nhập OpenAI Codex (OAuth). Vui lòng đăng nhập trong Cài đặt.")

        if token.is_expired():
            _log.info("OpenAI OAuth token expired, refreshing...")
            token = refresh_oauth_token(token)
            get_token_store().save_token(token)

        return token

    @classmethod
    def execute(
        cls,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        stream: bool = False,
    ) -> str:
        """Call ChatGPT Codex backend with proper masquerading headers and format."""
        token = cls.get_valid_token()

        # Separate system instruction and conversation messages
        system_instructions: list[str] = []
        conversation_inputs: list[dict[str, Any]] = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                system_instructions.append(content)
            else:
                conversation_inputs.append({
                    "type": "message",
                    "role": "user" if role == "user" else "assistant",
                    "content": [{"type": "input_text", "text": content}],
                })

        if not conversation_inputs:
            conversation_inputs.append({
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": "Hello"}],
            })

        # Standardize model for Codex backend
        codex_model = model.strip() or "gpt-5.3-codex"
        if codex_model.startswith("cx/"):
            codex_model = codex_model[3:]

        payload = {
            "model": codex_model,
            "input": conversation_inputs,
            "instructions": "\n\n".join(system_instructions) if system_instructions else "You are ViTai AI Assistant.",
            "stream": True,  # Codex backend is always SSE stream
            "store": False,
            "reasoning": {
                "effort": "low",
                "summary": "auto",
            },
        }

        data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {token.access_token}",
            "originator": "codex_cli_rs",
            "User-Agent": "codex_cli_rs/0.136.0 (Linux; x86_64)",
            "OpenAI-Beta": "responses=v1",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }

        if token.account_id:
            headers["ChatGPT-Account-ID"] = token.account_id

        req = urllib.request.Request(
            cls.CODEX_ENDPOINT,
            data=data_bytes,
            headers=headers,
            method="POST",
        )

        _log.info(f"[CODEX] Gửi request Codex Subscription (model={codex_model}, account={token.account_id or 'N/A'})...")

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return cls._parse_sse_response(resp)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            _log.error(f"[CODEX] HTTP Error {e.code}: {err_body}")
            if e.code == 401:
                # Try refreshing once on 401
                _log.info("[CODEX] 401 Unauthorized, refreshing token and retrying...")
                token = refresh_oauth_token(token)
                get_token_store().save_token(token)
                headers["Authorization"] = f"Bearer {token.access_token}"
                req = urllib.request.Request(
                    cls.CODEX_ENDPOINT,
                    data=data_bytes,
                    headers=headers,
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=30) as retry_resp:
                    return cls._parse_sse_response(retry_resp)
            raise RuntimeError(f"OpenAI Codex Error ({e.code}): {err_body[:200]}")
        except Exception as e:
            _log.error(f"[CODEX] Connection failed: {e}")
            raise RuntimeError(f"Lỗi kết nối OpenAI Codex: {e}")

    @classmethod
    def _parse_sse_response(cls, resp: Any) -> str:
        """Parse text/event-stream chunks from OpenAI Codex endpoint."""
        full_text_chunks: list[str] = []

        for line in resp:
            line_str = line.decode("utf-8", errors="ignore").strip()
            if not line_str or line_str.startswith(":"):
                continue

            if line_str.startswith("data: "):
                data_content = line_str[6:].strip()
                if data_content == "[DONE]":
                    break
                try:
                    event = json.loads(data_content)
                    event_type = event.get("type", "")

                    if event_type == "response.output_text.delta":
                        delta = event.get("delta", "")
                        if delta:
                            full_text_chunks.append(delta)
                    elif event_type == "response.completed":
                        # Full response completion
                        resp_obj = event.get("response", {})
                        for out in resp_obj.get("output", []):
                            for item in out.get("content", []):
                                if item.get("type") == "output_text":
                                    # Fallback if chunks weren't captured
                                    if not full_text_chunks:
                                        full_text_chunks.append(item.get("text", ""))
                    elif "delta" in event and isinstance(event["delta"], str):
                        full_text_chunks.append(event["delta"])
                except json.JSONDecodeError:
                    continue

        result = "".join(full_text_chunks).strip()
        return result


class GeminiOAuthAdapter:
    """Adapter for Google OAuth Gemini API."""

    @classmethod
    def get_valid_token(cls) -> OAuthToken:
        token = get_token_store().get_token("gemini")
        if not token or not token.access_token:
            raise RuntimeError("Chưa đăng nhập Google Gemini (OAuth). Vui lòng đăng nhập trong Cài đặt.")

        if token.is_expired():
            _log.info("Gemini OAuth token expired, refreshing...")
            token = refresh_oauth_token(token)
            get_token_store().save_token(token)

        return token

    @classmethod
    def execute(
        cls,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
    ) -> str:
        token = cls.get_valid_token()
        clean_model = model.replace("models/", "") if model else "gemini-2.5-flash"
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model}:generateContent"

        contents = []
        system_instruction = None

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                system_instruction = {"parts": [{"text": content}]}
            else:
                contents.append({
                    "role": "user" if role == "user" else "model",
                    "parts": [{"text": content}],
                })

        body: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {"temperature": temperature},
        }
        if system_instruction:
            body["systemInstruction"] = system_instruction

        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            endpoint,
            data=data,
            headers={
                "Authorization": f"Bearer {token.access_token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                candidates = res_data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    return "".join(p.get("text", "") for p in parts).strip()
                return ""
        except Exception as e:
            _log.error(f"[GEMINI OAUTH] Error: {e}")
            raise RuntimeError(f"Gemini OAuth Error: {e}")


class OpenAiCompatibleAdapter:
    """Adapter for standard OpenAI / OpenRouter / 9Router / Custom API keys."""

    @classmethod
    def execute(
        cls,
        base_url: str,
        api_key: str,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        extra_headers: dict[str, str] | None = None,
    ) -> str:
        url = base_url.rstrip("/")
        if not url.endswith("/chat/completions"):
            url = f"{url}/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}" if api_key else "",
            "User-Agent": "ViTai-Client/1.0",
        }
        if extra_headers:
            headers.update(extra_headers)

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }

        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                choices = res_data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "").strip()
                return ""
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", errors="ignore")
            _log.error(f"[OPENAI COMPATIBLE] HTTP Error {e.code}: {err}")
            raise RuntimeError(f"API Error ({e.code}): {err[:200]}")
        except Exception as e:
            _log.error(f"[OPENAI COMPATIBLE] Error: {e}")
            raise RuntimeError(f"Lỗi gọi API: {e}")


class AIProxyEngine:
    """Core router that routes completions to appropriate adapters."""

    @classmethod
    def route_chat(
        cls,
        provider: str,
        model: str,
        messages: list[dict[str, str]],
        api_key: str = "",
        base_url: str = "",
        temperature: float = 0.2,
    ) -> str:
        p = (provider or "").lower().strip()
        store = get_token_store()

        # 1. OpenAI: If OAuth logged in or provider explicitly codex -> Use Codex Subscription
        if p in ("openai", "codex", "chatgpt"):
            if store.is_authenticated("openai"):
                return CodexSubscriptionAdapter.execute(model, messages, temperature)
            # Fallback to standard OpenAI API Key
            return OpenAiCompatibleAdapter.execute(
                base_url or "https://api.openai.com/v1",
                api_key,
                model or "gpt-4o",
                messages,
                temperature,
            )

        # 2. Gemini OAuth
        if p == "gemini":
            if store.is_authenticated("gemini"):
                return GeminiOAuthAdapter.execute(model, messages, temperature)
            # Fallback to API Key
            if api_key:
                from vitai.llm import _ask_gemini
                # Combine messages into prompt
                prompt = "\n\n".join(m.get("content", "") for m in messages if m.get("role") == "user")
                return _ask_gemini(api_key, model or "gemini-2.5-flash", prompt, False)

        # 3. 9Router Local / Remote Proxy
        if p == "9router":
            target_url = base_url or "http://localhost:20128/v1"
            return OpenAiCompatibleAdapter.execute(
                target_url,
                api_key,
                model or "High",
                messages,
                temperature,
            )

        # 4. OpenRouter / Groq / DeepSeek / Custom
        target_url = base_url
        if not target_url:
            if p == "openrouter":
                target_url = "https://openrouter.ai/api/v1"
            elif p == "groq":
                target_url = "https://api.groq.com/openai/v1"
            elif p == "deepseek":
                target_url = "https://api.deepseek.com/v1"
            else:
                target_url = "https://api.openai.com/v1"

        return OpenAiCompatibleAdapter.execute(
            target_url,
            api_key,
            model,
            messages,
            temperature,
        )


class ViTaiProxyRequestHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler implementing standard OpenAI API endpoints."""

    def log_message(self, format: str, *args: Any) -> None:
        # Suppress noisy standard HTTP logs, use debug instead
        _log.debug(f"[PROXY SERVER] {self.address_string()} - " + (format % args))

    def _send_json(self, status: int, data: dict[str, Any]) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self) -> None:
        path = self.path.split("?")[0]

        if path in ("/health", "/status", "/v1/status", "/v1/quota", "/quota"):
            store = get_token_store()
            openai_token = store.get_token("openai")
            gemini_token = store.get_token("gemini")
            proxy_instance = get_local_proxy()
            self._send_json(200, {
                "status": "healthy",
                "app": "ViTai Local AI Proxy",
                "stats": {
                    "total_requests": getattr(proxy_instance, "total_requests", 0),
                    "successful_requests": getattr(proxy_instance, "successful_requests", 0),
                },
                "subscriptions": {
                    "openai": {
                        "authenticated": store.is_authenticated("openai"),
                        "email": openai_token.email if openai_token else "",
                        "plan": get_subscription_display_name(openai_token),
                        "quota_status": "Không giới hạn (Plus/Pro)" if (openai_token and openai_token.plan_type in ("plus", "pro", "team")) else "Gói Tiêu chuẩn (Free/Standard)",
                    },
                    "gemini": {
                        "authenticated": store.is_authenticated("gemini"),
                        "email": gemini_token.email if gemini_token else "",
                        "plan": "Google Workspace / Gemini Free Tier" if store.is_authenticated("gemini") else "Chưa kết nối",
                        "quota_status": "15 RPM / 1M TPM (Free Tier)" if store.is_authenticated("gemini") else "Chưa đăng nhập",
                    },
                },
            })
            return

        if path in ("/v1/models", "/models"):
            from vitai.model_registry import get_model_registry
            models = get_model_registry().get_models("openai")
            models_list = []
            for m in models:
                models_list.append({
                    "id": m,
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "vitai-proxy",
                })
            self._send_json(200, {"object": "list", "data": models_list})
            return

        self._send_json(404, {"error": {"message": "Not Found", "type": "invalid_request_error"}})

    def do_POST(self) -> None:
        path = self.path.split("?")[0]

        if path in ("/v1/chat/completions", "/chat/completions"):
            try:
                content_len = int(self.headers.get("Content-Length", 0))
                raw_body = self.rfile.read(content_len).decode("utf-8")
                req_json = json.loads(raw_body)

                model = req_json.get("model", "gpt-5.3-codex")
                messages = req_json.get("messages", [])
                temperature = float(req_json.get("temperature", 0.2))

                # Extract provider hint if any
                provider = "openai"
                if "gemini" in model.lower():
                    provider = "gemini"

                content = AIProxyEngine.route_chat(
                    provider=provider,
                    model=model,
                    messages=messages,
                    temperature=temperature,
                )

                resp_obj = {
                    "id": f"chatcmpl-vitai-{int(time.time())}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": model,
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": content,
                            },
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": len(str(messages)) // 4,
                        "completion_tokens": len(content) // 4,
                        "total_tokens": (len(str(messages)) + len(content)) // 4,
                    },
                }
                self._send_json(200, resp_obj)
            except Exception as e:
                _log.error(f"[PROXY SERVER] Request failed: {e}")
                self._send_json(500, {
                    "error": {
                        "message": str(e),
                        "type": "api_error",
                    }
                })
            return

        self._send_json(404, {"error": {"message": "Not Found", "type": "invalid_request_error"}})


class ViTaiLocalProxy:
    """Manages the lifecycle of the local ViTai HTTP Proxy server."""

    def __init__(self, host: str = DEFAULT_PROXY_HOST, port: int = DEFAULT_PROXY_PORT):
        self.host = host
        self.port = port
        self._server: ThreadingHTTPServer | None = None
        self._thread: Thread | None = None
        self._is_running = False

    def start(self) -> bool:
        if self._is_running:
            return True
        try:
            self._server = ThreadingHTTPServer((self.host, self.port), ViTaiProxyRequestHandler)
            self._thread = Thread(target=self._server.serve_forever, daemon=True, name="ViTai-Proxy-Server")
            self._thread.start()
            self._is_running = True
            _log.info(f"[PROXY] ✅ Local AI Proxy Server đã khởi động tại http://{self.host}:{self.port}")
            return True
        except Exception as e:
            _log.warning(f"[PROXY] Không thể khởi động Proxy Server tại cổng {self.port}: {e}")
            self._is_running = False
            return False

    def stop(self) -> None:
        if self._server and self._is_running:
            _log.info("[PROXY] Đang dừng Local AI Proxy Server...")
            self._server.shutdown()
            self._server.server_close()
            self._is_running = False
            _log.info("[PROXY] Local AI Proxy Server đã tắt.")

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def endpoint(self) -> str:
        return f"http://{self.host}:{self.port}/v1"


# Singleton instance
_local_proxy_instance: ViTaiLocalProxy | None = None


def get_local_proxy() -> ViTaiLocalProxy:
    global _local_proxy_instance
    if _local_proxy_instance is None:
        _local_proxy_instance = ViTaiLocalProxy()
    return _local_proxy_instance
