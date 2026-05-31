# 🚀 ViTai — Roadmap v3.1+

> **Bộ công cụ siêu cấp Overlay — Dịch thuật · AI Assistant · Browser · Media**
>
> Cập nhật: 2026-05-31 · Phiên bản hiện tại: v3.0.0

---

## 📋 Mục lục

0. [Tình trạng hiện tại sau gộp](#0-tình-trạng-hiện-tại-sau-gộp-vitai--vitrans)
1. [Phase 0 — Sửa lỗi khẩn cấp](#1-phase-0--sửa-lỗi-khẩn-cấp-v31)
2. [Phase 1 — Nâng cấp FAA & Settings](#2-phase-1--nâng-cấp-faa--settings-v32)
3. [Phase 2 — Cải thiện dịch thuật (học từ Translumo)](#3-phase-2--cải-thiện-dịch-thuật-học-từ-translumo-v33)
4. [Phase 3 — Super Overlay Toolkit](#4-phase-3--super-overlay-toolkit-tầm-nhìn-dài-hạn-v40)
5. [Bảng tổng hợp file cần sửa](#5-bảng-tổng-hợp-file-cần-sửa)
6. [Kiến trúc mục tiêu](#6-kiến-trúc-mục-tiêu)

---

## 0. Tình trạng hiện tại sau gộp (ViTai + ViTrans)

### ✅ Hoạt động tốt
- Ghost FAA (bôi đen text → AI trả lời) — **OK**
- System tray icon, khởi động nền — **OK**
- LLM multi-provider (Gemini/OpenAI/Anthropic/DeepSeek) — **OK**
- MCQ detection & normalize — **OK**
- Answer overlay hiển thị đúng vị trí chuột — **OK**
- RAG context từ tài liệu local — **OK**
- PyInstaller build & GitHub Release — **OK** (đã fix thiếu module)

### ❌ Lỗi cần sửa ngay

| # | Vấn đề | Chi tiết |
|---|--------|----------|
| B1 | **Hotkey trùng** | Cả dịch thuật lẫn FAA đều gọi cùng `toggle_overlay`. Config mặc định `hotkey_key = "t"`, chỉ có 1 `HotkeyManager`. FAA chỉ trigger qua mouse listener, không có hotkey riêng |
| B2 | **Settings UI tab sai tên** | Tab "Basic" chứa overlay color + hotkey (nên là "General"). Tab "Advanced" chứa translator provider + OCR engine (nên là "Translation Engine"). Tab "AI Assistant" thiếu API Key input |
| B3 | **Dịch thuật không hoạt động** | Pipeline OCR → translate có flow đúng nhưng cần test end-to-end sau khi fix lazy import |
| B4 | **API Key chỉ qua .env** | Không có UI để nhập API Key trong Settings. Chỉ có prompt khi FAA phát hiện thiếu key |
| B5 | **Không có AI translator** | Dịch thuật chỉ dùng Google/DeepL. Chưa tích hợp LLM làm translation provider |

---

## 1. Phase 0 — Sửa lỗi khẩn cấp (v3.1)

> **Mục tiêu:** App hoạt động đúng cả 2 chức năng chính sau khi gộp.
> **Timeline:** 1 ngày

### Task 0.1 — Tách hotkey cho Translation và FAA

**Vấn đề:** Chỉ có 1 `HotkeyManager` bind vào `config.hotkey_key` (mặc định `"t"`). Ghost FAA trigger qua mouse listener, không có hotkey riêng.

**Giải pháp:**
- Thêm field `faa_hotkey_modifier` và `faa_hotkey_key` vào `AppConfig` (mặc định `"alt"` + `"q"`)
- Tạo `HotkeyManager` thứ 2 trong `ViTaiApp.__init__` cho FAA
- `Alt+T` → `toggle_overlay` (mở selection → OCR → translate)
- `Alt+Q` → `trigger_faa` (capture text bôi đen → LLM → answer overlay)
- Cập nhật Settings UI để cho phép đổi hotkey riêng cho từng chức năng

**Files cần sửa:**
- `config.py` — thêm `faa_hotkey_modifier`, `faa_hotkey_key`
- `main.py` — tạo `faa_hotkey_manager`, tách callback
- `settings.py` — thêm row hotkey cho FAA trong tab tương ứng

### Task 0.2 — Sửa Settings UI tab names & tổ chức

**Cấu trúc tab hiện tại → đề xuất:**

| Tab hiện tại | → Tab mới | Nội dung mới |
|---|---|---|
| Basic + System + Advanced (partial) | **⚙️ Chung** | UI language, Translation hotkey, FAA hotkey, Hotkey backend, Start with Windows, Run as Admin |
| Translate group + Advanced (partial) + Transtyle | **🌐 Dịch thuật** | Source/Target language, Translator provider (Google/DeepL/AI), API Key, OCR engine, Capture engine, Auto-translate, Transtyle, Overlay color |
| AI Assistant | **🤖 AI Assistant** | Ghost FAA toggle, LLM Provider, **API Key input**, Base URL, Model, Cache toggle, Font/Size/Color |

**Files cần sửa:**
- `settings.py` — refactor `_build_ui()`, đổi tên tab, di chuyển widget

### Task 0.3 — Thêm API Key input vào Settings

**Giải pháp:**
- Trong tab "AI Assistant", thêm `QLineEdit` cho API Key (với `setEchoMode(Password)`)
- Thêm `QLineEdit` cho Base URL và Model name
- `_build_config_from_ui()` phải đọc giá trị từ các field mới
- Ưu tiên: UI input > `.env` file > empty string

**Files cần sửa:**
- `settings.py` — thêm QLineEdit widgets
- `main.py` — sửa logic `LlmClient` init để ưu tiên config > env
- `llm.py` — thêm fallback `os.environ.get("GEMINI_API_KEY")` nếu `api_key` rỗng

### Task 0.4 — Fix translation pipeline end-to-end

**Kiểm tra:**
- Smoke test: chạy app → Alt+T → chọn vùng → verify kết quả dịch
- Đảm bảo error message hiện rõ ràng trong overlay thay vì crash

---

## 2. Phase 1 — Nâng cấp FAA & Settings (v3.2)

> **Mục tiêu:** FAA hoàn chỉnh, dịch thuật có thêm option dùng AI.
> **Timeline:** 1-2 ngày

### Task 1.1 — AI Translation Provider

Thêm LLM làm translator provider bên cạnh Google/DeepL. Khi user chọn "AI Translate" trong settings, gọi `LlmClient` với prompt dịch thuật chuyên dụng.

```
TRANSLATOR_PROVIDERS = [
    ("Google Translate", "google"),
    ("DeepL", "deepl"),
    ("AI Translate (LLM)", "ai"),       # ← MỚI
]
```

**Files cần sửa:**
- `translate.py` — thêm `AiTranslatorProvider` class
- `settings.py` — thêm "AI Translate" vào provider list

### Task 1.2 — Cải thiện FAA UX

- **Double-click** answer overlay → copy đáp án vào clipboard
- **Scroll** trong answer overlay nếu đáp án dài
- **Resize** answer overlay theo nội dung
- Loading animation thay vì text "..."

**Files cần sửa:** `overlay_vitai.py`

---

## 3. Phase 2 — Cải thiện dịch thuật, học từ Translumo (v3.3)

> **Mục tiêu:** Nâng chất lượng dịch thuật ngang tầm Translumo.
> **Timeline:** 3-5 ngày
>
> **Reference:** `F:\Dowload\Translumo-master`

### 3.1 — Windows OCR (Ưu tiên cao)

**Translumo dùng:** Windows OCR qua WinRT — miễn phí, nhanh, không cần GPU.

**ViTai nên làm:**
- Thêm Windows OCR provider qua `winrt` Python package
- Dùng làm primary OCR thay EasyOCR (nhanh hơn nhiều)

**Files mới:** `windows_ocr.py`
**Files sửa:** `ocr.py` — thêm provider

### 3.2 — Multi-OCR Consensus (Ưu tiên cao)

**Translumo dùng:** Chạy nhiều OCR engine song song, dùng scoring để chọn kết quả tốt nhất (`GetBestDetectionResult` trong `TranslationProcessingService.cs`).

**ViTai nên làm:** Chạy 2 engine (Windows OCR + EasyOCR), chọn kết quả confidence cao hơn.

**Files sửa:** `ocr.py` — consensus logic

### 3.3 — Similarity Cache (Ưu tiên cao)

**Translumo dùng:** `TextResultCacheService` với Jaro-Winkler + Dice similarity, tránh dịch lại text gần giống (OCR noise).

**ViTai hiện tại:** `TextResultCache` chỉ exact match.

**Cải thiện:**
- Implement Jaro-Winkler similarity
- Nếu text mới giống ≥90% text đã cache → skip
- Cache có TTL

**Files sửa:** `text_cache.py`

### 3.4 — Adaptive Auto-Translate (Ưu tiên trung bình)

Nếu không có text mới → tăng interval (giảm CPU). Thêm Pause/Resume trên overlay.

### 3.5 — Exclude Overlay from Capture (Ưu tiên trung bình)

Dùng `SetWindowDisplayAffinity` Win32 API để overlay không bị screen capture chụp lại.

**Files sửa:** `overlay.py`

### 3.6 — Proxy (Ưu tiên thấp)

Cho phép cấu hình HTTP proxy trong Settings cho translation requests.

---

## 4. Phase 3 — Super Overlay Toolkit / Tầm nhìn dài hạn (v4.0+)

> **Tầm nhìn:** ViTai = bộ công cụ overlay đa năng. Nhấn hotkey + bôi vùng → Action Picker hiện lên.

### Kiến trúc Action Picker

```
User nhấn Alt+T → Bôi vùng → Action Picker hiện lên:

  🌐 Dịch thuật      → Translation Overlay (OCR → Translate)
  🤖 Hỏi AI (FAA)    → Answer Overlay (LLM → Answer)
  🌍 Mini Browser     → QWebEngineView Overlay
  🎵 Music Player     → QMediaPlayer Overlay
  🎬 Video Player     → QVideoWidget Overlay
  📝 Sticky Note      → QTextEdit Overlay
```

### 4.1 — Action Picker Overlay
- Radial/popup menu với icon chức năng
- Click icon → tạo overlay tại vùng đã chọn

### 4.2 — Mini Browser Overlay
- `QWebEngineView` nhúng trong overlay
- Nút Back/Forward/Refresh/Close
- **Dependencies mới:** `PyQt6-WebEngine`

### 4.3 — Music Player Overlay
- Play/Pause/Next/Prev/Volume
- `QMediaPlayer` cho playback
- Local playlist hoặc URL stream

### 4.4 — Video Player Overlay
- `QVideoWidget` trong overlay
- Kéo thả file video

### 4.5 — Sticky Note Overlay
- `QTextEdit` tự động save vào `~/.vitai/notes/`

### Lộ trình Phase 3

| Giai đoạn | Tính năng | Ước tính |
|---|---|---|
| 4.0-alpha | Action Picker (radial menu) | 2 ngày |
| 4.0-beta | Mini Browser overlay | 3 ngày |
| 4.1 | Music Player overlay | 2 ngày |
| 4.2 | Video Player overlay | 2 ngày |
| 4.3 | Sticky Note overlay | 1 ngày |

---

## 5. Bảng tổng hợp file cần sửa

### Phase 0 (Khẩn cấp)

| File | Thay đổi |
|---|---|
| `config.py` | Thêm `faa_hotkey_modifier`, `faa_hotkey_key` |
| `main.py` | Tạo `faa_hotkey_manager` thứ 2, tách callback |
| `settings.py` | Refactor tabs, thêm API Key QLineEdit, FAA hotkey row |
| `llm.py` | Fallback đọc env nếu `api_key` rỗng |

### Phase 1

| File | Thay đổi |
|---|---|
| `translate.py` | Thêm `AiTranslatorProvider` class |
| `settings.py` | Thêm "AI Translate" vào provider list |
| `overlay_vitai.py` | Scroll, resize, copy, loading animation |

### Phase 2

| File | Thay đổi |
|---|---|
| `windows_ocr.py` | **MỚI** — Windows OCR provider |
| `ocr.py` | Thêm Windows OCR, consensus logic |
| `text_cache.py` | Jaro-Winkler similarity, TTL |
| `overlay.py` | Exclude from capture |

### Phase 3

| File | Thay đổi |
|---|---|
| `action_picker.py` | **MỚI** — Popup menu sau selection |
| `browser_overlay.py` | **MỚI** — QWebEngineView overlay |
| `music_overlay.py` | **MỚI** — QMediaPlayer overlay |
| `video_overlay.py` | **MỚI** — QVideoWidget overlay |
| `note_overlay.py` | **MỚI** — QTextEdit sticky note |
| `main.py` | Tích hợp action picker vào selection flow |

---

## 6. Kiến trúc mục tiêu

```
┌──────────────────────────────────────────────────────┐
│                   ViTai Application                   │
│                                                       │
│  ┌────────┐  ┌──────┐  ┌──────────────────────────┐  │
│  │Settings│  │ Tray │  │    Hotkey Managers        │  │
│  │ Window │  │ Icon │  │  ├─ Alt+T (Translate)     │  │
│  └────────┘  └──────┘  │  └─ Alt+Q (FAA)          │  │
│                         └──────────────────────────┘  │
│                      │                                │
│                      ▼                                │
│  ┌──────────────────────────────────────────────┐     │
│  │           Selection Window                    │     │
│  │      (bôi vùng trên màn hình)                │     │
│  └─────────────────┬────────────────────────────┘     │
│                    ▼                                  │
│  ┌──────────────────────────────────────────────┐     │
│  │         Action Picker (Phase 3)               │     │
│  │  🌐 Translate │ 🤖 AI │ 🌍 Browser │ 🎵 Music│     │
│  └──────┬────────┴──┬────┴─────┬──────┴──┬─────┘     │
│         ▼           ▼          ▼         ▼           │
│   ┌──────────┐ ┌────────┐ ┌───────┐ ┌───────┐       │
│   │Translate │ │ Answer │ │Browser│ │ Music │       │
│   │ Overlay  │ │Overlay │ │Overlay│ │Overlay│       │
│   │OCR→Trans │ │LLM→Ans │ │WebView│ │Player │       │
│   └──────────┘ └────────┘ └───────┘ └───────┘       │
│                                                       │
│  ┌──────────────────────────────────────────────┐     │
│  │             Core Services                     │     │
│  │  LlmClient · OCR · Translator · TTS · Cache  │     │
│  └──────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────┘
```

---

## 📝 Ghi chú cho session tiếp theo

**Ưu tiên tuyệt đối:** Phase 0 phải hoàn thành trước khi làm tính năng mới.

**Thứ tự:** Task 0.1 (hotkey) → 0.2 (tabs) → 0.3 (API Key UI) → 0.4 (test translate) → Phase 1 → Phase 2 → Phase 3.

**Translumo reference:** Source code tại `F:\Dowload\Translumo-master`. File quan trọng:
- `TranslationProcessingService.cs` — pipeline xử lý (multi-OCR, scoring, cache)
- `TextResultCacheService.cs` — similarity caching (Jaro-Winkler + Dice)
- `TranslatorFactory.cs` — factory pattern cho translator
- `ChatWindowConfiguration.cs` — overlay config (font, color, opacity)

**Không đụng code** trong session viết roadmap này. Mỗi Phase nên thực hiện trong 1 session riêng, commit & test trước khi bắt đầu Phase kế.