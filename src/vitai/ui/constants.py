from __future__ import annotations

import re

PROVIDER_PRESETS = [
    ("OpenAI Codex (ChatGPT Plus/Pro Subs)", "openai", "https://chatgpt.com/backend-api/codex", "cx/gpt-5.5"),
    ("Google Gemini (Google OAuth / Key)", "gemini", "https://generativelanguage.googleapis.com/v1beta", "gemini-2.5-flash"),
    ("Kiro AI (OAuth / AWS)", "kiro", "https://app.kiro.ai/v1", "kr/claude-sonnet-4.5"),
    ("9Router (Local Proxy :20128)", "9router", "http://localhost:20128/v1", "High"),
    ("OpenRouter (Miễn phí & Đa mô hình)", "openrouter", "https://openrouter.ai/api/v1", "google/gemini-2.0-flash-exp:free"),
    ("Groq (Siêu tốc 500 T/s)", "groq", "https://api.groq.com/openai/v1", "llama-3.3-70b-versatile"),
    ("DeepSeek", "deepseek", "https://api.deepseek.com/v1", "deepseek-chat"),
]

PROVIDER_GUIDES = {
    "9router": {
        "title": "Hướng dẫn sử dụng 9Router",
        "content": """
        <h3 style="color: #E09F5E;">9Router — Local Proxy</h3>
        <p><b>9Router</b> là proxy định tuyến AI chạy song song tại cổng <code>http://localhost:20128/v1</code>.</p>
        <p><b>Ưu điểm:</b> Tự động chọn model tối ưu và cân bằng tải.</p>
        """,
    },
    "openai": {
        "title": "Hướng dẫn OpenAI Codex (Subscription)",
        "content": """
        <h3 style="color: #E09F5E;">◈ OpenAI Codex (ChatGPT Plus / Pro / Free)</h3>
        <p><b>Cách 1 (Khuyên dùng):</b> Nhấn nút <b>Đăng nhập OpenAI Codex</b>. Đăng nhập tài khoản ChatGPT của bạn trên trình duyệt để sử dụng miễn phí gói Plus/Pro/Team mà không cần mua API Key!</p>
        <p><b>Cách 2:</b> Nhập API Key thủ công từ <a style="color: #E09F5E;" href="https://platform.openai.com/api-keys">platform.openai.com</a> vào ô API Key fallback.</p>
        """,
    },
    "gemini": {
        "title": "Hướng dẫn Xác thực Google Gemini",
        "content": """
        <h3 style="color: #E09F5E;">◈ Google Gemini AI</h3>
        <p><b>Cách 1:</b> Nhấn nút <b>Đăng nhập Google</b> để authorize tài khoản Google của bạn.</p>
        <p><b>Cách 2:</b> Lấy API Key miễn phí từ <a style="color: #E09F5E;" href="https://aistudio.google.com/">Google AI Studio (aistudio.google.com)</a> và dán vào ô API Key.</p>
        """,
    },
    "kiro": {
        "title": "Hướng dẫn Kiro AI",
        "content": """
        <h3 style="color: #E09F5E;">◈ Kiro AI Authentication</h3>
        <p>Hỗ trợ đăng nhập nhanh qua tài khoản Kiro / AWS Builder ID. Nhấn <b>Đăng nhập Kiro AI</b> để kích hoạt phiên làm việc.</p>
        """,
    },
    "openrouter": {
        "title": "Hướng dẫn OpenRouter",
        "content": """
        <h3 style="color: #E09F5E;">◈ OpenRouter (Hỗ trợ nhiều Model Free)</h3>
        <p>Truy cập <a style="color: #E09F5E;" href="https://openrouter.ai/keys">OpenRouter Keys</a> để tạo key miễn phí.</p>
        <p>Các model có đuôi <code>:free</code> (như <code>google/gemini-2.0-flash-exp:free</code>, <code>deepseek/deepseek-r1:free</code>) có thể sử dụng hoàn toàn miễn phí!</p>
        """,
    },
    "groq": {
        "title": "Hướng dẫn Groq Cloud",
        "content": """
        <h3 style="color: #E09F5E;">◈ Groq Cloud API (~500 tokens/s)</h3>
        <p>Lấy key tại: <a style="color: #E09F5E;" href="https://console.groq.com/keys">Groq Console API Keys</a></p>
        """,
    },
    "deepseek": {
        "title": "Hướng dẫn DeepSeek",
        "content": """
        <h3 style="color: #E09F5E;">◈ DeepSeek Platform</h3>
        <p>Lấy key tại: <a style="color: #E09F5E;" href="https://platform.deepseek.com/api_keys">DeepSeek API Keys</a></p>
        """,
    },
}

SIZE_CHOICES = [
    ("12 px", 12),
    ("14 px", 14),
    ("16 px", 16),
    ("18 px", 18),
    ("20 px", 20),
    ("22 px", 22),
    ("24 px", 24),
    ("28 px", 28),
]

COLOR_CHOICES = [
    ("Warm Amber (#E09F5E)", "#E09F5E"),
    ("Warm Tan (#D2B48C)", "#D2B48C"),
    ("Pure White (#FFFFFF)", "#FFFFFF"),
    ("Light Gray (#E0E0E0)", "#E0E0E0"),
    ("Emerald Green (#4ADE80)", "#4ADE80"),
    ("Sky Blue (#38BDF8)", "#38BDF8"),
    ("Soft Yellow (#FDE047)", "#FDE047"),
    ("Vibrant Pink (#F472B6)", "#F472B6"),
]


import re


def extract_hex_color(text: str | None, default: str = "#E09F5E") -> str:
    if not text:
        return default
    text = text.strip()
    match = re.search(r"#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})", text)
    if match:
        return match.group(0).upper()
    for disp, code in COLOR_CHOICES:
        if text == disp or text == code or code.lower() in text.lower():
            return code
    return default





