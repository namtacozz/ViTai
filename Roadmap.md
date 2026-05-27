# 🚀 ViTai — Roadmap phát triển

> **Ứng dụng System Tray "Alt+Q" — Trợ lý học thuật tức thì**
>
> Phiên bản: 2.0 · Ngày: 2026-05-27 · Timeline: **2 ngày**

---

## 📋 Mục lục

0. [🔄 Tài nguyên tái sử dụng từ ViTrans](#0--tài-nguyên-tái-sử-dụng-từ-vitrans-dvitrans)
1. [Tổng quan dự án](#1-tổng-quan-dự-án)
2. [Tính năng lõi (MVP)](#2-tính-năng-lõi-mvp)
3. [Non-goals (KHÔNG làm trong 2 ngày)](#3-non-goals)
4. [Stack công nghệ & lý do chọn](#4-stack-công-nghệ--lý-do-chọn)
5. [Kiến trúc & luồng dữ liệu](#5-kiến-trúc--luồng-dữ-liệu)
6. [Lộ trình chi tiết — 2 ngày](#6-lộ-trình-chi-tiết--2-ngày)
7. [LLM Integration — Prompt templates](#7-llm-integration--prompt-templates)
8. [MCQ Detection & Parsing](#8-mcq-detection--parsing)
9. [Cấu trúc thư mục dự án](#9-cấu-trúc-thư-mục-dự-án)
10. [Agent Runbook — Hướng dẫn cho AI Agent](#10-agent-runbook)
11. [Kiểm thử nhanh (Smoke Test)](#11-kiểm-thử-nhanh)
12. [Đóng gói & phân phối](#12-đóng-gói--phân-phối)

---

## 0. 🔄 Tài nguyên tái sử dụng từ ViTrans (`D:\ViTrans`)

> Dự án ViTrans (translate overlay app) có kiến trúc tương tự — cùng Python, system tray, global hotkey, overlay UI.
> Tái sử dụng tối đa để rút ngắn thời gian phát triển.

### Bảng mapping — Copy & Adapt

| File ViTrans | Dùng cho ViTai | Mức độ | Ghi chú sửa đổi |
|---|---|---|---|
| `src/vitrans/hotkey.py` (128 dòng) | `src/vitai/hotkey.py` | ✅ **Copy nguyên** | Đổi default key `t` → `q`, giữ nguyên `HotkeyManager` + dual backend (Win32 + pynput fallback). Đã production-tested |
| `src/vitrans/config.py` (96 dòng) | `src/vitai/config.py` | 🔧 **Rút gọn** | Giữ pattern `@dataclass` + `load_config/save_config` JSON. Xoá fields translate/OCR/transtyle, thêm `gemini_api_key`, `model` |
| `src/vitrans/resources.py` (8 dòng) | `src/vitai/resources.py` | ✅ **Copy nguyên** | Hàm `resource_path()` xử lý PyInstaller `_MEIPASS` — giữ nguyên |
| `src/vitrans/encoding.py` (8 dòng) | `src/vitai/encoding.py` | ✅ **Copy nguyên** | `configure_utf8_stdio()` — cần cho Windows console encoding |
| `src/vitrans/logging_config.py` (19 dòng) | `src/vitai/logging_config.py` | ✅ **Copy, đổi path** | Đổi `.vitrans/vitrans.log` → `.vitai/vitai.log` |
| `src/vitrans/startup.py` (84 dòng) | `src/vitai/startup.py` | 🔧 **Copy, đổi tên** | Đổi `APP_NAME = "ViTrans"` → `"ViTai"`. Giữ `set_startup()`, `is_admin()` |
| `src/vitrans/main.py` (525 dòng) | `src/vitai/main.py` | 🔧 **Tham khảo cấu trúc** | Lấy pattern: `QApplication` + `QSystemTrayIcon` + `HotkeyManager` + signal bridge. Bỏ toàn bộ OCR/translate/overlay-drag logic, thay bằng capture-text → LLM → show-popup |
| `src/vitrans/overlay.py` (483 dòng) | `src/vitai/overlay.py` | 🔧 **Viết mới, tham khảo style** | ViTrans overlay quá phức tạp (drag, resize, OCR boxes). ViTai chỉ cần popup đơn giản. Tham khảo: `WindowFlags`, `WA_TranslucentBackground`, `paintEvent`, font/color scheme |
| `assets/logo.ico` + `logo.png` | `assets/icon.ico` | 🔧 **Tạm dùng, thay sau** | Dùng tạm logo ViTrans làm placeholder, tạo icon riêng cho ViTai sau |
| `.gitignore` (12 dòng) | `.gitignore` | ✅ **Copy nguyên** | Đã cover `.venv/`, `dist/`, `build/`, `__pycache__/`, `.env` |
| `scripts/build_windows.py` (38 dòng) | `scripts/build_windows.py` | 🔧 **Rút gọn** | Bỏ `--collect-data easyocr`, `torchvision`, `scipy`. Chỉ giữ core PyInstaller command + `--add-data assets` |
| `ViTrans.spec` | `ViTai.spec` | 🔧 **Rút gọn** | Bỏ easyocr/torch hidden imports. Đổi name, entry point |

### KHÔNG dùng từ ViTrans (không liên quan)

| File | Lý do bỏ |
|---|---|
| `ocr.py`, `capture.py` (screen capture) | ViTai capture text qua clipboard, không chụp màn hình |
| `translate.py`, `offline_translate.py` | ViTai dùng LLM API, không dùng Google Translate |
| `selection.py` | ViTrans dùng fullscreen selection drag — ViTai không cần |
| `settings.py` (28KB!) | Quá phức tạp, ViTai MVP không cần settings UI |
| `overlay.py` (drag/resize/OCR boxes) | Quá phức tạp — viết overlay đơn giản hơn |
| `i18n.py`, `transtyle*.py`, `tts.py`, `history.py`, `text_cache.py`, `models.py` | Không cần cho MVP |

### Quyết định stack thay đổi (nhờ ViTrans)

| Thành phần | Roadmap cũ | → Thay đổi | Lý do |
|---|---|---|---|
| **UI framework** | `tkinter` | → **`PyQt6`** | ViTrans đã dùng PyQt6, có sẵn pattern overlay + tray. PyQt6 mạnh hơn tkinter rất nhiều |
| **Global hotkey** | `keyboard` (pip) | → **`pynput` + Win32 API** | ViTrans đã có `hotkey.py` production-tested với dual backend |
| **System tray** | `pystray` + `Pillow` | → **`QSystemTrayIcon` (PyQt6)** | Tích hợp sẵn trong PyQt6, không cần thêm dependency |
| **Capture text** | `pyperclip` | → **`pyperclip`** (giữ nguyên) | Vẫn là cách đơn giản nhất |

---

## 1. Tổng quan dự án

**ViTai** là ứng dụng Windows chạy nền (system tray), giúp người dùng:

1. **Bôi đen** một đoạn văn bản (thường là câu hỏi) ở bất kỳ ứng dụng nào.
2. Nhấn **Alt + Q**.
3. Nhận ngay **đáp án** hiển thị trong overlay nhỏ bên cạnh — không cần chuyển tab, không cần mở trình duyệt.

**Mục đích:** Hỗ trợ nghiên cứu học thuật nhanh gọn, giảm context-switching khi học tập.

---

## 2. Tính năng lõi (MVP)

| # | Tính năng | Mô tả |
|---|-----------|-------|
| 1 | **Global Hotkey** | Đăng ký `Alt+Q` toàn cục, hoạt động trên mọi ứng dụng |
| 2 | **Capture text bôi đen** | Tự động lấy văn bản đang được bôi đen (select) |
| 3 | **Gọi LLM API** | Gửi đến Gemini API (miễn phí, nhanh) → nhận đáp án |
| 4 | **Hiển thị overlay** | Popup nhỏ hiện đáp án ngay gần vị trí chuột, topmost, không chiếm focus |
| 5 | **MCQ detection** | Nhận diện câu trắc nghiệm → trả về đúng 1 đáp án (A/B/C/D) |
| 6 | **System tray icon** | Chạy nền, icon tray với menu cơ bản (Show/Hide, Quit) |

---

## 3. Non-goals (KHÔNG làm trong 2 ngày)

- ❌ UI Settings phức tạp (cấu hình model, temperature, ...)
- ❌ Streaming response (trả về 1 lần cho nhanh)
- ❌ Multi-provider (chỉ dùng 1 provider: Gemini)
- ❌ Auto-update, installer MSIX
- ❌ CI/CD pipeline
- ❌ Telemetry, analytics
- ❌ OCR fallback
- ❌ Local LLM support
- ❌ Multi-platform (Mac/Linux)
- ❌ Cache/rate-limit phức tạp
- ❌ Bảo mật enterprise-grade (DPAPI, Credential Manager)

---

## 4. Stack công nghệ & lý do chọn

| Thành phần | Công nghệ | Lý do |
|------------|-----------|-------|
| **Ngôn ngữ** | Python 3.12 | Khớp với ViTrans (đã test ổn định), AI SDK sẵn có |
| **Global hotkey** | `pynput` + Win32 API (**copy từ ViTrans**) | `hotkey.py` đã production-tested, dual backend auto-fallback |
| **Capture text** | `pyperclip` + simulate `Ctrl+C` | Đơn giản nhất, hoạt động trên hầu hết app Windows |
| **LLM API** | Google Gemini API (`google-genai`) | Miễn phí tier cao (15 RPM / 1M tokens/ngày), nhanh, dễ setup |
| **Overlay UI** | `PyQt6` (**từ ViTrans**) | Mạnh hơn tkinter, có sẵn pattern overlay topmost + translucent từ ViTrans |
| **System tray** | `QSystemTrayIcon` (PyQt6 built-in) | Không cần thêm dependency, ViTrans đã có pattern sẵn |
| **Đóng gói** | `PyInstaller` (**script từ ViTrans**) | Tái sử dụng `scripts/build_windows.py`, chỉ cần rút gọn |

> **Tại sao Gemini API?**
> - Free tier: 15 requests/phút, 1 triệu tokens/ngày — đủ cho cá nhân.
> - Gemini 2.0 Flash rất nhanh (< 1s response cho câu hỏi ngắn).
> - SDK Python chính thức (`google-genai`) rất gọn.
> - Chỉ cần 1 API key miễn phí từ [Google AI Studio](https://aistudio.google.com/).

---

## 5. Kiến trúc & luồng dữ liệu

```
┌─────────────────────────────────────────────────────────────┐
│  User bôi đen text → Nhấn Alt+Q                            │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  1. Lưu clipboard hiện tại (backup)                         │
│  2. Simulate Ctrl+C → copy text vào clipboard               │
│  3. Đọc clipboard → lấy selected text                       │
│  4. Khôi phục clipboard cũ (restore)                        │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  MCQ Detector: Text có phải câu trắc nghiệm?               │
│  ├── CÓ  → Dùng prompt "force single label" (A/B/C/D)      │
│  └── KHÔNG → Dùng prompt "trả lời ngắn gọn"                │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  Gọi Gemini API (gemini-2.0-flash)                          │
│  → Nhận response text                                       │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  Hiển thị Overlay (PyQt6 topmost popup)                     │
│  → Vị trí: gần con trỏ chuột                               │
│  → Tự ẩn sau vài giây hoặc click ngoài / nhấn Escape        │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Lộ trình chi tiết — 2 ngày

### 📅 NGÀY 1 — Dựng core hoạt động end-to-end

> **Mục tiêu cuối ngày 1:** Nhấn Alt+Q trên text bôi đen → hiện popup có đáp án từ Gemini.

| Thứ tự | Task | Thời gian | Chi tiết |
|--------|------|-----------|----------|
| 1.1 | **Khởi tạo dự án + copy ViTrans** | 30 phút | Tạo `src/vitai/`. Copy nguyên từ ViTrans: `hotkey.py`, `resources.py`, `encoding.py`, `logging_config.py`, `.gitignore`, `assets/`. Tạo `requirements.txt` mới (PyQt6, pynput, pyperclip, google-genai, python-dotenv) |
| 1.2 | **Config + hotkey (Alt+Q)** | 30 phút | Rút gọn `config.py` từ ViTrans (giữ dataclass pattern, xoá OCR/translate fields, thêm `gemini_api_key`). Đổi default hotkey key thành `q`. Test: Alt+Q → print "triggered" |
| 1.3 | **Capture selected text** | 1 giờ | Viết `capture.py`: backup clipboard → simulate `Ctrl+C` (dùng `pyperclip` + `keyboard` module ctypes) → đọc clipboard → restore. Return None nếu không có text |
| 1.4 | **Gọi Gemini API** | 1 giờ | Viết `llm.py`: setup `google-genai` SDK. Hàm `ask(question, is_mcq) -> str`. Test: gọi API câu hỏi mẫu → nhận response |
| 1.5 | **Overlay popup (PyQt6)** | 1.5 giờ | Viết `overlay.py`: PyQt6 `QWidget` với `FramelessWindowHint + WindowStaysOnTopHint + Tool` (pattern từ ViTrans overlay). Translucent background, hiện response text, auto-hide 10s hoặc Escape |
| 1.6 | **Main + Tray (từ ViTrans)** | 1 giờ | Viết `main.py` theo pattern ViTrans: `QApplication` + `QSystemTrayIcon` + `HotkeyManager`. Callback: capture → LLM → overlay. Test E2E trên Notepad, Chrome |

**Checkpoint ngày 1:** ✅ Flow hoàn chỉnh Alt+Q → đáp án hiện lên.

---

### 📅 NGÀY 2 — MCQ detection, polish, đóng gói

> **Mục tiêu cuối ngày 2:** App hoàn chỉnh, chạy từ tray, phát hiện MCQ, đóng gói .exe.

| Thứ tự | Task | Thời gian | Chi tiết |
|--------|------|-----------|----------|
| 2.1 | **MCQ detector** | 1 giờ | Viết `mcq.py`: regex nhận diện pattern trắc nghiệm (A. B. C. D.). Phân loại: MCQ vs câu hỏi mở → chọn prompt template phù hợp |
| 2.2 | **Prompt templates** | 45 phút | Template MCQ: "Chỉ trả về 1 ký tự đáp án". Template general: "Trả lời ngắn gọn, tối đa 2 câu". Tích hợp vào pipeline |
| 2.3 | **Overlay UI polish** | 1.5 giờ | Tham khảo style ViTrans (`Segoe UI`, dark bg, white text, `WA_TranslucentBackground`). Loading state "⏳". Nút copy đáp án. Auto-close timer |
| 2.4 | **Error handling** | 1 giờ | Không có text → overlay hiện "⚠". API lỗi → overlay hiện "❌". API key chưa set → dialog nhập key (tham khảo `QInputDialog` từ ViTrans) |
| 2.5 | **Đóng gói .exe** | 1 giờ | Copy + rút gọn `scripts/build_windows.py` từ ViTrans (bỏ easyocr/torch). Test .exe |
| 2.6 | **README + cleanup** | 45 phút | Viết README.md (cách lấy API key, cách dùng). Cleanup code |

**Checkpoint ngày 2:** ✅ File `.exe` chạy độc lập, đầy đủ tính năng lõi.

---

## 7. LLM Integration — Prompt templates

### 7.1 Prompt cho câu hỏi mở (General)

```
System: Bạn là trợ lý học thuật ngắn gọn. Trả lời rõ ràng, tối đa 2 câu.
        Nếu không chắc chắn, trả lời "Không chắc chắn" kèm 1 câu lý do ngắn.

User: {selected_text}
```

### 7.2 Prompt cho câu trắc nghiệm (MCQ)

```
System: Bạn là trợ lý giải đề trắc nghiệm.
        CHỈ trả về DUY NHẤT một ký tự đáp án (A, B, C, D, ...).
        KHÔNG giải thích. KHÔNG thêm bất kỳ text nào khác.

User: {selected_text}
```

### 7.3 Gemini API call example (Python)

```python
from google import genai

client = genai.Client(api_key=API_KEY)

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=prompt,
    config={
        "temperature": 0.0,
        "max_output_tokens": 150,
    }
)
answer = response.text.strip()
```

---

## 8. MCQ Detection & Parsing

### Regex pattern nhận diện trắc nghiệm

```python
import re

MCQ_PATTERN = re.compile(
    r'(?mi)^\s*([A-Da-d])\s*[.)\]:\-]\s*.+',
)

def is_mcq(text: str) -> bool:
    """Trả về True nếu text chứa ít nhất 2 lựa chọn dạng A. B. C. D."""
    matches = MCQ_PATTERN.findall(text)
    unique_labels = set(m.upper() for m in matches)
    return len(unique_labels) >= 2
```

### Logic xử lý

```
Input text
    │
    ├── is_mcq(text) == True
    │   └── Gửi prompt MCQ → response = "B"
    │       └── Hiển thị overlay: "Đáp án: B"
    │
    └── is_mcq(text) == False
        └── Gửi prompt General → response = "..."
            └── Hiển thị overlay: "{response}"
```

---

## 9. Cấu trúc thư mục dự án

```
ViTai/
├── src/
│   └── vitai/
│       ├── __init__.py        # Package marker
│       ├── main.py            # Entry point — QApplication + tray + hotkey
│       ├── capture.py         # Capture selected text (clipboard method)
│       ├── llm.py             # Gemini API integration
│       ├── mcq.py             # MCQ detection & prompt routing
│       ├── overlay.py         # PyQt6 overlay popup (answer display)
│       ├── config.py          # Config dataclass + JSON persistence (← ViTrans)
│       ├── hotkey.py          # Global hotkey manager (← ViTrans copy)
│       ├── resources.py       # PyInstaller resource path (← ViTrans copy)
│       ├── encoding.py        # UTF-8 stdio config (← ViTrans copy)
│       └── logging_config.py  # Logging setup (← ViTrans copy)
├── assets/
│   └── icon.ico             # Tray icon (tạm dùng từ ViTrans)
├── scripts/
│   └── build_windows.py     # PyInstaller build script (← ViTrans rút gọn)
├── requirements.txt         # Dependencies
├── .env.example             # Template: GEMINI_API_KEY=your_key_here
├── .gitignore               # ← ViTrans copy
├── README.md
└── Roadmap.md
```

---

## 10. Agent Runbook — Hướng dẫn cho AI Agent

> Hướng dẫn step-by-step để AI Agent triển khai dự án.

### Phase 1 — Ngày 1: Core pipeline

```
Bước 1: Tạo cấu trúc + copy từ ViTrans
  → Tạo thư mục: src/vitai/, assets/, scripts/
  → COPY NGUYÊN từ D:\ViTrans\src\vitrans\ sang src/vitai/:
      hotkey.py, resources.py, encoding.py, logging_config.py
  → COPY: D:\ViTrans\.gitignore → .gitignore
  → COPY: D:\ViTrans\assets\logo.ico → assets/icon.ico
  → Tạo src/vitai/__init__.py (rỗng)
  → Tạo requirements.txt:
      PyQt6==6.7.1
      pynput==1.7.7
      pyperclip>=1.8
      google-genai>=1.0
      python-dotenv>=1.0
  → Tạo .env.example: GEMINI_API_KEY=your_key_here

Bước 2: Adapt config.py (từ ViTrans config.py)
  → Copy D:\ViTrans\src\vitrans\config.py → src/vitai/config.py
  → XOÁ: imports i18n, transtyle
  → XOÁ fields: x, y, width, height, target_language, source_language,
      translator_*, deepl_*, transtyle_*, auto_translate_*,
      overlay_color, ui_language, capture_provider, ocr_provider,
      offline_*, update_check_*
  → THÊM fields: gemini_api_key: str = "", model: str = "gemini-2.0-flash",
      hotkey_modifier: str = "alt", hotkey_key: str = "q"
  → Đổi config path: .vitrans → .vitai
  → Đơn giản hoá load_config/save_config (bỏ transtyle logic)

Bước 3: Adapt logging_config.py
  → Đổi path: .vitrans/vitrans.log → .vitai/vitai.log

Bước 4: Implement capture.py (VIẾT MỚI)
  → Hàm get_selected_text() -> str | None
  → Backup clipboard → simulate Ctrl+C → sleep(0.15) → đọc clipboard → restore
  → Dùng pyperclip + ctypes SendInput cho Ctrl+C
  → Return None nếu clipboard không đổi

Bước 5: Implement llm.py (VIẾT MỚI)
  → from google import genai
  → Hàm ask(question: str, is_mcq: bool) -> str
  → Chọn system prompt dựa trên is_mcq
  → Gọi Gemini API → return response.text.strip()
  → try/except → return error message string nếu lỗi

Bước 6: Implement overlay.py (VIẾT MỚI, tham khảo ViTrans)
  → Class AnswerOverlay(QWidget)
  → WindowFlags: FramelessWindowHint | WindowStaysOnTopHint | Tool
      (copy pattern từ ViTrans overlay.py dòng 80-86)
  → WA_TranslucentBackground (như ViTrans)
  → paintEvent: dark bg, white text, Segoe UI font
      (tham khảo ViTrans overlay.py paintEvent dòng 448-482)
  → Vị trí: gần cursor (QCursor.pos())
  → Auto-destroy sau 10s (QTimer.singleShot)
  → Escape key → đóng

Bước 7: Implement main.py (tham khảo ViTrans main.py)
  → Pattern giống ViTrans: class ViTaiApp
  → configure_utf8_stdio() (như ViTrans)
  → QApplication + setQuitOnLastWindowClosed(False) (như ViTrans dòng 63)
  → QSystemTrayIcon với icon (như ViTrans dòng 100-105)
  → HotkeyManager(modifier, key, callback) (như ViTrans dòng 76-81)
  → Callback: get_selected_text() → ask() → show overlay
  → UiBridge(QObject) với pyqtSignal cho thread safety (như ViTrans dòng 43-46)
  → app.run() → hotkey_manager.start() + qt_app.exec()

Bước 8: Test end-to-end
  → Chạy: PYTHONPATH=src python -m vitai.main
  → Mở Notepad, gõ câu hỏi, bôi đen, nhấn Alt+Q
  → Verify: popup hiện đáp án → PASS
```

### Phase 2 — Ngày 2: MCQ + polish + đóng gói

```
Bước 9: Implement mcq.py (VIẾT MỚI)
  → Hàm is_mcq(text: str) -> bool
  → Regex detect A./B./C./D. pattern
  → Integrate vào main.py: if is_mcq(text) → ask(text, is_mcq=True)

Bước 10: Polish overlay
  → Tham khảo ViTrans overlay style:
      - Font: QFont("Segoe UI", 12) (ViTrans overlay.py dòng 461)
      - Colors: dark bg rgba(20,20,20,150), white text (ViTrans dòng 104-106)
  → Loading state: "⏳ Đang suy nghĩ..."
  → Nút nhỏ "📋" để copy đáp án (QPushButton)

Bước 11: Error handling
  → Không có text → overlay hiện "⚠ Không tìm thấy text bôi đen"
  → API lỗi → overlay hiện "❌ Lỗi kết nối API"
  → API key chưa set → QInputDialog.getText() nhập key
      (tham khảo ViTrans main.py dòng 384-390 cho QInputDialog pattern)

Bước 12: Đóng gói PyInstaller
  → Copy D:\ViTrans\scripts\build_windows.py → scripts/build_windows.py
  → SỬA: bỏ --collect-data easyocr, --collect-submodules easyocr,
      --collect-submodules torchvision, --hidden-import scipy
  → Đổi name ViTrans → ViTai, entry src/vitai/main.py
  → Đổi icon path → assets/icon.ico
  → Chạy: python scripts/build_windows.py
  → Test: dist/ViTai/ViTai.exe

Bước 13: Viết README.md
  → Mô tả ngắn gọn
  → Cách lấy API key Gemini (link Google AI Studio)
  → Cách chạy dev: PYTHONPATH=src python -m vitai.main
  → Cách chạy exe: dist/ViTai/ViTai.exe
```

---

## 11. Kiểm thử nhanh (Smoke Test)

Danh sách test tối thiểu để đảm bảo app hoạt động:

| # | Test case | Kỳ vọng | App test |
|---|-----------|---------|----------|
| 1 | Bôi đen câu hỏi mở, nhấn Alt+Q | Overlay hiện đáp án ngắn gọn | Notepad |
| 2 | Bôi đen câu trắc nghiệm (A/B/C/D), nhấn Alt+Q | Overlay hiện 1 ký tự đáp án (vd: "B") | Chrome |
| 3 | Không bôi đen gì, nhấn Alt+Q | Overlay hiện thông báo lỗi | Bất kỳ |
| 4 | API key sai | Overlay hiện lỗi API | Bất kỳ |
| 5 | Nhấn Escape khi overlay đang hiện | Overlay đóng ngay | Bất kỳ |
| 6 | Clipboard có nội dung trước khi Alt+Q | Clipboard được khôi phục sau khi capture | Bất kỳ |

---

## 12. Đóng gói & phân phối

### Build command (dùng script từ ViTrans)

```bash
# Dev mode
PYTHONPATH=src python -m vitai.main

# Build .exe (copy + adapt scripts/build_windows.py từ ViTrans)
python scripts/build_windows.py
```

### Output

```
dist/
└── ViTai/
    └── ViTai.exe    # Chạy độc lập, không cần Python
```

### Phân phối

- Upload thư mục `dist/ViTai/` lên GitHub Releases (zip).
- Người dùng tải về → chạy `ViTai.exe` → nhập API key → sử dụng.
- Không cần cài đặt, không cần Python.

---

> **📝 Ghi chú:** Roadmap này tập trung vào việc có sản phẩm chạy được trong 2 ngày.
> Các tính năng nâng cao (streaming, multi-provider, cache, auto-update, UI settings...)
> sẽ được bổ sung sau khi core ổn định.