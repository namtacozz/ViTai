from __future__ import annotations

import http.server
import logging
import threading
import urllib.parse
import webbrowser
from typing import Callable

from vitai.oauth_provider import (
    build_auth_url,
    exchange_code_for_token,
    get_oauth_config,
)
from vitai.token_store import OAuthToken, get_token_store

_log = logging.getLogger("vitai.auth_server")

HTML_SUCCESS = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>ViTai — Đăng nhập thành công</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: #121214;
            color: #E1E1E6;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
        }
        .card {
            background-color: #18181B;
            border: 1px solid #27272A;
            border-radius: 12px;
            padding: 32px 40px;
            text-align: center;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            max-width: 420px;
        }
        h2 { color: #4ADE80; margin-bottom: 12px; font-size: 24px; }
        p { color: #A1A1AA; font-size: 14px; line-height: 1.6; }
        .badge {
            display: inline-block;
            margin-top: 16px;
            background-color: #27272A;
            color: #6366F1;
            padding: 6px 14px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 13px;
        }
    </style>
</head>
<body>
    <div class="card">
        <h2>🎉 Đăng nhập thành công!</h2>
        <p>ViTai đã kết nối thành công với tài khoản AI của bạn. Bạn có thể đóng tab trình duyệt này và quay lại ứng dụng.</p>
        <div class="badge">ViTai Assistant</div>
    </div>
</body>
</html>
"""

HTML_ERROR = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>ViTai — Lỗi xác thực</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: #121214;
            color: #E1E1E6;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
        }
        .card {
            background-color: #18181B;
            border: 1px solid #EF4444;
            border-radius: 12px;
            padding: 32px 40px;
            text-align: center;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            max-width: 420px;
        }
        h2 { color: #EF4444; margin-bottom: 12px; font-size: 24px; }
        p { color: #A1A1AA; font-size: 14px; line-height: 1.6; }
    </style>
</head>
<body>
    <div class="card">
        <h2>❌ Xác thực thất bại</h2>
        <p>{error_message}</p>
    </div>
</body>
</html>
"""


class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    server: OAuthServer

    def do_GET(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed_url.query)

        code = params.get("code", [None])[0]
        error = params.get("error", [None])[0]
        state = params.get("state", [None])[0]

        if error:
            _log.error(f"OAuth returned error: {error}")
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = HTML_ERROR.format(error_message=f"Nhà cung cấp trả về lỗi: {error}")
            self.wfile.write(html.encode("utf-8"))
            self.server.received_error = error
            self.server.done_event.set()
            return

        if code:
            _log.info(f"OAuth callback received code for provider '{self.server.provider}'")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_SUCCESS.encode("utf-8"))
            self.server.received_code = code
            self.server.received_state = state
            self.server.done_event.set()
            return

        # Fallback for unexpected routes
        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        # Silence default stderr logging from BaseHTTPRequestHandler
        pass


class OAuthServer(http.server.HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, provider: str):
        super().__init__(server_address, RequestHandlerClass)
        self.provider = provider
        self.received_code: str | None = None
        self.received_state: str | None = None
        self.received_error: str | None = None
        self.done_event = threading.Event()


def run_oauth_flow_sync(
    provider: str, timeout: int = 120
) -> OAuthToken:
    """Synchronously run the entire OAuth authorization & exchange flow."""
    cfg = get_oauth_config(provider)
    if not cfg:
        raise ValueError(f"Provider '{provider}' is not configured for OAuth.")

    auth_url, verifier, expected_state = build_auth_url(provider)

    server = OAuthServer(("127.0.0.1", cfg.port), OAuthCallbackHandler, provider=provider)
    
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    _log.info(f"OAuth server started on port {cfg.port}. Opening browser at: {auth_url}")
    webbrowser.open(auth_url)

    # Wait for callback or timeout
    finished = server.done_event.wait(timeout=timeout)
    server.shutdown()
    server.server_close()

    if not finished:
        raise TimeoutError("Quá thời gian chờ đăng nhập trình duyệt (120s).")

    if server.received_error:
        raise RuntimeError(f"Lỗi đăng nhập: {server.received_error}")

    if not server.received_code:
        raise RuntimeError("Không nhận được authorization code.")

    _log.info(f"Exchanging code for tokens for '{provider}'...")
    token = exchange_code_for_token(provider, server.received_code, verifier)
    get_token_store().save_token(token)
    return token


def start_oauth_flow_async(
    provider: str,
    on_success: Callable[[OAuthToken], None],
    on_error: Callable[[str], None],
    timeout: int = 120,
) -> threading.Thread:
    """Start the OAuth flow in a background thread and call callbacks on completion."""
    def _worker():
        try:
            token = run_oauth_flow_sync(provider, timeout=timeout)
            on_success(token)
        except Exception as e:
            _log.exception(f"OAuth flow error for {provider}: {e}")
            on_error(str(e))

    th = threading.Thread(target=_worker, daemon=True)
    th.start()
    return th
