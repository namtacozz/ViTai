from __future__ import annotations

from anthropic import Anthropic
from vitai.rag import get_rag_context

GENERAL_SYSTEM_PROMPT = """Chỉ đưa ra câu trả lời trực tiếp ngắn gọn nhất có thể, đi thẳng vào đáp án. KHÔNG giải thích, KHÔNG chào hỏi, KHÔNG dài dòng."""

MCQ_SYSTEM_PROMPT = """Bạn là trợ lý giải đề trắc nghiệm.
CHỈ trả về DUY NHẤT một ký tự đáp án (A, B, C, D, ...).
KHÔNG giải thích. KHÔNG thêm bất kỳ text nào khác."""


def system_prompt_for(is_mcq: bool, context: str = "") -> str:
    base = MCQ_SYSTEM_PROMPT if is_mcq else GENERAL_SYSTEM_PROMPT
    if context:
        base += f"\n\nDưới đây là tài liệu tham khảo có thể chứa thông tin liên quan tới câu hỏi. Hãy dựa vào tài liệu này để đưa ra đáp án chính xác nhất:\n\n{context}"
    return base


def build_prompt(question: str, is_mcq: bool, context: str = "") -> str:
    return f"System: {system_prompt_for(is_mcq, context)}\n\nUser: {question.strip()}"


def extract_text(response) -> str:
    content = getattr(response, "content", None)
    if content:
        parts: list[str] = []
        for block in content:
            if getattr(block, "type", None) == "text":
                parts.append(block.text)
        return "".join(parts).strip()

    choices = getattr(response, "choices", None)
    if choices:
        choice = choices[0]
        message = choice.get("message", {}) if isinstance(choice, dict) else choice.message
        text = message.get("content", "") if isinstance(message, dict) else getattr(message, "content", "")
        return text.strip()

    return ""


class AnthropicProxyClient:
    def __init__(self, auth_token: str, base_url: str, model: str = "High"):
        self._client = Anthropic(api_key=auth_token, base_url=base_url)
        self._model = model

    def ask(self, question: str, is_mcq: bool) -> str:
        context = get_rag_context(question)
        response = self._client.messages.create(
            model=self._model,
            max_tokens=150,
            system=system_prompt_for(is_mcq, context),
            messages=[{"role": "user", "content": question.strip()}],
        )
        return extract_text(response)
