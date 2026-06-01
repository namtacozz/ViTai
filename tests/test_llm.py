from types import SimpleNamespace
from urllib.error import HTTPError
from io import BytesIO

import pytest

from vitai.llm import LlmClient, build_prompt, extract_text, system_prompt_for


def test_general_prompt_limits_answer_length():
    prompt = build_prompt("Explain TCP.", is_mcq=False)

    assert "Trả lời rõ ràng, tối đa 2 câu" in prompt
    assert "Explain TCP." in prompt


def test_mcq_prompt_requires_single_answer_letter():
    prompt = build_prompt("A. One\nB. Two", is_mcq=True)

    assert "CHỈ trả về DUY NHẤT một ký tự đáp án" in prompt
    assert "A. One\nB. Two" in prompt


def test_system_prompt_for_mcq():
    assert "DUY NHẤT một ký tự" in system_prompt_for(is_mcq=True)


def test_extract_text_joins_text_blocks_only():
    response = SimpleNamespace(
        content=[
            SimpleNamespace(type="text", text="Hello"),
            SimpleNamespace(type="thinking", text="ignore"),
            SimpleNamespace(type="text", text=" world"),
        ]
    )

    assert extract_text(response) == "Hello world"


def test_extract_text_supports_proxy_chat_completion_shape():
    response = SimpleNamespace(
        content=None,
        choices=[SimpleNamespace(message=SimpleNamespace(content="OK"))],
    )

    assert extract_text(response) == "OK"


def test_extract_text_supports_proxy_dict_chat_completion_shape():
    response = SimpleNamespace(
        content=None,
        choices=[{"message": {"content": "OK"}}],
    )

    assert extract_text(response) == "OK"


def test_http_error_masks_response_body(monkeypatch):
    def fail(_req, timeout):
        raise HTTPError(
            url="https://api.example.test",
            code=401,
            msg="Unauthorized",
            hdrs={},
            fp=BytesIO(b'{"error":"secret-token-value"}'),
        )

    monkeypatch.setattr("urllib.request.urlopen", fail)
    client = LlmClient("openai", "key", "https://api.example.test/v1", "model")

    with pytest.raises(RuntimeError) as exc_info:
        client._make_request("https://api.example.test/v1/chat/completions", {}, {}, lambda _: "")

    assert "HTTP 401" in str(exc_info.value)
    assert "secret-token-value" not in str(exc_info.value)


def test_gemini_key_not_sent_in_url(monkeypatch):
    captured = {}

    def fake_make_request(url, data, headers, extractor):
        captured["url"] = url
        captured["headers"] = headers
        return "OK"

    client = LlmClient("gemini", "gemini-secret", "https://generativelanguage.googleapis.com/v1beta", "gemini-2.5-flash")
    monkeypatch.setattr(client, "_make_request", fake_make_request)

    assert client._ask_gemini("Question", "System") == "OK"
    assert "gemini-secret" not in captured["url"]
    assert captured["headers"]["x-goog-api-key"] == "gemini-secret"
