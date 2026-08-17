import json
import time
import urllib.request
from vitai.proxy import get_local_proxy, AIProxyEngine, CodexSubscriptionAdapter
from vitai.token_store import OAuthToken, get_token_store
from vitai.oauth_provider import get_subscription_display_name


def test_oauth_token_subscription_plan():
    token = OAuthToken(
        provider="openai",
        access_token="test_token",
        email="test@domain.com",
        account_id="acc_9999",
        plan_type="pro",
    )
    assert token.plan_type == "pro"
    assert token.account_id == "acc_9999"
    assert get_subscription_display_name(token) == "ChatGPT Pro"


def test_proxy_server_lifecycle_and_endpoints():
    from vitai.proxy import ViTaiLocalProxy
    proxy = ViTaiLocalProxy(port=14599)
    started = proxy.start()
    assert started
    assert proxy.is_running
    time.sleep(0.3)

    # 1. Health check endpoint
    req = urllib.request.Request("http://127.0.0.1:14599/health")
    with urllib.request.urlopen(req, timeout=5) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["status"] == "healthy"
        assert data["app"] == "ViTai Local AI Proxy"

    # 2. Models endpoint
    req_models = urllib.request.Request("http://127.0.0.1:14599/v1/models")
    with urllib.request.urlopen(req_models, timeout=5) as resp:
        assert resp.status == 200
        models_data = json.loads(resp.read().decode("utf-8"))
        assert "data" in models_data
        assert any(m["id"] == "cx/gpt-5.5" for m in models_data["data"])

    # 3. Stop proxy
    proxy.stop()
    assert not proxy.is_running

