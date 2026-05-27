from __future__ import annotations

import json
import urllib.request
import urllib.error

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


class LlmClient:
    def __init__(self, provider: str, api_key: str, base_url: str, model: str):
        self.provider = provider.lower()
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    def ask(self, question: str, is_mcq: bool) -> str:
        context = get_rag_context(question)
        sys_prompt = system_prompt_for(is_mcq, context)
        
        if self.provider == "anthropic":
            return self._ask_anthropic(question, sys_prompt)
        elif self.provider == "gemini":
            return self._ask_gemini(question, sys_prompt)
        elif self.provider in ["openai", "deepseek"]:
            return self._ask_openai_compatible(question, sys_prompt)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def _ask_anthropic(self, question: str, sys_prompt: str) -> str:
        data = {
            "model": self.model,
            "max_tokens": 150,
            "system": sys_prompt,
            "messages": [{"role": "user", "content": question.strip()}],
        }
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        return self._make_request(f"{self.base_url}/messages", data, headers, self._extract_anthropic)

    def _ask_openai_compatible(self, question: str, sys_prompt: str) -> str:
        data = {
            "model": self.model,
            "max_tokens": 150,
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": question.strip()}
            ],
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "content-type": "application/json"
        }
        return self._make_request(f"{self.base_url}/chat/completions", data, headers, self._extract_openai)

    def _ask_gemini(self, question: str, sys_prompt: str) -> str:
        data = {
            "system_instruction": {
                "parts": {"text": sys_prompt}
            },
            "contents": [
                {"parts": [{"text": question.strip()}]}
            ],
            "generationConfig": {
                "maxOutputTokens": 150
            }
        }
        headers = {"content-type": "application/json"}
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        return self._make_request(url, data, headers, self._extract_gemini)

    def _make_request(self, url: str, data: dict, headers: dict, extractor) -> str:
        req = urllib.request.Request(
            url, 
            data=json.dumps(data).encode("utf-8"), 
            headers=headers, 
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                result = json.loads(response.read().decode("utf-8"))
                return extractor(result)
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8', errors='ignore')
            raise RuntimeError(f"HTTP {e.code}: {error_body}")
        except Exception as e:
            raise RuntimeError(f"Lỗi API: {str(e)}")

    def _extract_anthropic(self, response: dict) -> str:
        content = response.get("content", [])
        for block in content:
            if block.get("type") == "text":
                return block.get("text", "").strip()
        return ""

    def _extract_openai(self, response: dict) -> str:
        choices = response.get("choices", [])
        if choices:
            message = choices[0].get("message", {})
            return message.get("content", "").strip()
        return ""
        
    def _extract_gemini(self, response: dict) -> str:
        candidates = response.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                return parts[0].get("text", "").strip()
        return ""
