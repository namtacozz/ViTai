from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request

from vitai.rag import get_rag_context
from vitai.token_store import get_token_store

_log = logging.getLogger("vitai.llm")

GENERAL_SYSTEM_PROMPT = """Chỉ đưa ra câu trả lời trực tiếp ngắn gọn nhất có thể, đi thẳng vào đáp án. Trả lời rõ ràng, tối đa 2 câu. KHÔNG giải thích, KHÔNG chào hỏi, KHÔNG dài dòng."""

MCQ_SYSTEM_PROMPT = """Bạn là trợ lý giải đề trắc nghiệm.
CHỈ trả về DUY NHẤT một ký tự đáp án (A, B, C, D, ...).
KHÔNG giải thích. KHÔNG thêm bất kỳ text nào khác."""


def system_prompt_for(is_mcq: bool, context: str = "") -> str:
    base = MCQ_SYSTEM_PROMPT if is_mcq else GENERAL_SYSTEM_PROMPT
    if context:
        base += f"\n\nDưới đây là tài liệu tham khảo có thể chứa thông tin liên quan tới câu hỏi. Hãy dựa vào tài liệu này để đưa ra đáp án chính xác nhất:\n\n{context}"
    return base


def build_prompt(question: str, is_mcq: bool, context: str = "") -> str:
    prompt = system_prompt_for(is_mcq, context)
    return f"{prompt}\n\nCâu hỏi:\n{question}"


def extract_text(response: Any) -> str:
    if response is None:
        return ""
    if isinstance(response, str):
        return response
    if hasattr(response, "content") and response.content:
        if isinstance(response.content, list):
            parts = []
            for block in response.content:
                if hasattr(block, "type") and block.type == "text" and hasattr(block, "text"):
                    parts.append(block.text)
                elif isinstance(block, dict) and block.get("type") == "text":
                    parts.append(block.get("text", ""))
            return "".join(parts).strip()
        return str(response.content).strip()
    if hasattr(response, "choices") and response.choices:
        choice = response.choices[0]
        if hasattr(choice, "message"):
            msg = choice.message
            if hasattr(msg, "content"):
                return str(msg.content or "").strip()
            if isinstance(msg, dict):
                return str(msg.get("content", "")).strip()
        elif isinstance(choice, dict):
            msg = choice.get("message", {})
            if isinstance(msg, dict):
                return str(msg.get("content", "")).strip()
    return str(response).strip()


class LlmClient:
    def __init__(
        self,
        provider: str,
        api_key: str = "",
        base_url: str = "",
        model: str = "",
        auth_method: str = "api_key",
    ):
        self.provider = (provider or "openai").lower()
        self.auth_method = auth_method
        self.base_url = base_url.rstrip("/") if base_url else ""
        self.model = model
        self.api_key = api_key

        token_store = get_token_store()
        self.is_oauth = token_store.is_authenticated(self.provider) if self.auth_method == "oauth" or not api_key else False

    def ask(self, question: str, is_mcq: bool) -> str:
        _log.info(
            f"[LLM] Bắt đầu gọi AI (provider='{self.provider}', model='{self.model}', oauth={self.is_oauth}, mcq={is_mcq})"
        )
        _log.info(f"[LLM] Câu hỏi ({len(question)} chars): '{question[:70]}...'")

        context = get_rag_context(question)
        if context:
            _log.info(f"[LLM] Đã nạp context RAG ({len(context)} chars)")

        sys_prompt = system_prompt_for(is_mcq, context)

        # Use AIProxyEngine to route request
        from vitai.proxy import AIProxyEngine

        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": question.strip()},
        ]

        try:
            if self.provider == "anthropic":
                return self._ask_anthropic(question, sys_prompt)

            answer = AIProxyEngine.route_chat(
                provider=self.provider,
                model=self.model,
                messages=messages,
                api_key=self.api_key,
                base_url=self.base_url,
            )
            _log.info(f"[LLM] ✅ AI phản hồi thành công: '{answer[:60]}...'")
            return answer
        except Exception as e:
            _log.error(f"[LLM] ❌ Lỗi gọi AI: {e}")
            raise e

    def _ask_anthropic(self, question: str, sys_prompt: str) -> str:
        data = {
            "model": self.model or "claude-3-5-sonnet-20241022",
            "max_tokens": 150,
            "system": sys_prompt,
            "messages": [{"role": "user", "content": question.strip()}],
        }
        headers = {
            "x-api-key": self.api_key or "dummy_key",
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        url = f"{self.base_url or 'https://api.anthropic.com/v1'}/messages"
        _log.info(f"[LLM] Gửi request Anthropic tới: {url}")
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        from vitai.http_util import safe_urlopen
        with safe_urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result["content"][0]["text"].strip()
