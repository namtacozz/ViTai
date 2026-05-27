from types import SimpleNamespace

from vitai.llm import build_prompt, extract_text, system_prompt_for


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
