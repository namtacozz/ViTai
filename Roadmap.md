# 🚀 ViTai v2.0 — Roadmap: Cross-Platform & UI Premium

> **ViTai (Very Important Treasure AI)**
>
> Mục tiêu v2.0: Đưa ViTai từ ứng dụng Windows-only thành ứng dụng **đa nền tảng (Linux Fedora 44 + Windows)** với giao diện được thiết kế lại từ đầu — chuyên nghiệp, hiện đại, đẳng cấp hơn.

---

## 📋 Tầm Nhìn

ViTai hiện tại đã có core hoạt động ổn định trên Windows:
- Bôi đen text → Nhấn `Alt+Q` → Hiện đáp án AI ngay lập tức.
- Hỗ trợ MCQ detection, multi-provider (Anthropic/OpenAI/Gemini/DeepSeek), cache thông minh.

**Phiên bản v2.0 tập trung vào 2 trụ cột:**

| Trụ cột | Mô tả |
|---------|-------|
| 🐧 **Cross-Platform** | Chạy mượt trên cả Linux (Fedora 44 — Wayland/X11) và Windows |
| 🎨 **UI Overhaul** | Giao diện Settings & Overlay được thiết kế lại hoàn toàn — dark mode mặc định, glassmorphism, micro-animation, typography chuyên nghiệp |

> **Lưu ý:** Chức năng lõi (text capture → LLM → overlay answer) giữ nguyên 100%. Không thêm, không bớt tính năng.

---

## 🏗️ Hiện trạng Codebase (commit `af0b8a4`)

### Modules hiện tại

| File | Chức năng | Tình trạng Linux |
|------|-----------|------------------|
| `main.py` | Entry point, tray, hotkey, mouse listener | ⚠️ Dùng `ctypes.windll` — Windows-only |
| `capture.py` | Giả lập Ctrl+C lấy text bôi đen | ❌ Hoàn toàn Windows-only (`ctypes.windll.user32.SendInput`) |
| `startup.py` | Đăng ký khởi động cùng Windows | ❌ Windows registry only |
| `hotkey.py` | Global hotkey (pynput + Win32 fallback) | ✅ pynput backend tương thích Linux |
| `settings.py` | Giao diện cài đặt (PyQt6) | ⚠️ `is_dark_mode()` dùng `winreg` — cần fallback |
| `overlay.py` | Popup hiển thị đáp án | ✅ PyQt6 — tương thích cross-platform |
| `config.py` | Dataclass config + JSON persistence | ✅ Cross-platform |
| `llm.py` | Multi-provider LLM client | ✅ Cross-platform |
| `mcq.py` | MCQ detection | ✅ Cross-platform |
| `rag.py` | RAG context từ PDF | ✅ Cross-platform |

### Dependencies hiện tại
```
PyQt6==6.7.1, pynput==1.7.7, pyperclip, python-dotenv, PyMuPDF, rank_bm25
```

---

## Phase 1 — Cross-Platform Linux Support 🐧

> **Mục tiêu:** ViTai chạy được trên Fedora 44 (GNOME/Wayland) mà không cần sửa đổi gì đặc biệt.

### 1.1 — `capture.py` → Cross-platform text capture

**Vấn đề:** File hiện tại dùng `ctypes.windll.user32.SendInput` (Windows-only) để giả lập Ctrl+C.

**Giải pháp:**
- Giữ nguyên logic Windows hiện tại cho `sys.platform == "win32"`
- Thêm fallback Linux dùng `pynput.keyboard.Controller` để giả lập `Ctrl+C`
- `pyperclip` đã hỗ trợ sẵn Linux (qua `xclip` / `xsel` / `wl-clipboard`)

#### [MODIFY] [capture.py](file:///home/arjunsharma/Tài liệu/GitHub/ViTai/src/vitai/capture.py)
- Tách `_send_ctrl_c()` thành `_send_ctrl_c_windows()` và `_send_ctrl_c_linux()`
- Trong `get_selected_text()`: kiểm tra `sys.platform` để chọn backend phù hợp

---

### 1.2 — `startup.py` → Linux autostart

**Vấn đề:** Chỉ dùng `winreg` (Windows Registry).

**Giải pháp:**
- Windows: giữ nguyên logic registry
- Linux: tạo file `.desktop` tại `~/.config/autostart/vitai.desktop`

#### [MODIFY] [startup.py](file:///home/arjunsharma/Tài liệu/GitHub/ViTai/src/vitai/startup.py)
- Thêm `_get_linux_autostart_path()` → `~/.config/autostart/vitai.desktop`
- `set_startup(True)` trên Linux → ghi file `.desktop`
- `set_startup(False)` trên Linux → xóa file `.desktop`
- `get_startup_enabled()` trên Linux → kiểm tra file tồn tại

---

### 1.3 — `main.py` → Platform-aware initialization

**Vấn đề:** `set_windows_app_id()` gọi `ctypes.windll` — crash trên Linux.

**Giải pháp:**
- Đã có guard `if sys.platform == "win32"` — OK
- Thêm `setDesktopFileName("vitai")` cho GNOME integration
- Thêm hàm `install_linux_desktop_file()` để đăng ký app với GNOME Portal (hiện trong panel "Ứng dụng nền" giống Discord)

#### [MODIFY] [main.py](file:///home/arjunsharma/Tài liệu/GitHub/ViTai/src/vitai/main.py)
- `_tray_activated()`: mở rộng từ chỉ `DoubleClick` → thêm `Trigger` (single click) cho Linux
- Import và gọi `install_linux_desktop_file()` khi khởi động trên Linux

---

### 1.4 — `settings.py` → Cross-platform dark mode detection

**Vấn đề:** `is_dark_mode()` dùng `winreg` — crash trên Linux.

**Giải pháp:**
- Windows: giữ nguyên logic registry
- Linux: mặc định `True` (dark mode) hoặc đọc `gsettings` nếu có GNOME

#### [MODIFY] [settings.py](file:///home/arjunsharma/Tài liệu/GitHub/ViTai/src/vitai/settings.py)
- Sửa `is_dark_mode()` thêm branch `sys.platform.startswith("linux")`
- Label "Khởi động cùng Windows" → "Khởi động cùng hệ thống"

---

### 1.5 — `requirements.txt` → Tương thích Fedora 44 / Python 3.14

**Vấn đề:** `PyQt6==6.7.1` quá chặt, `pynput` cần `evdev` (compile từ C source → thiếu kernel-headers trên Fedora).

**Giải pháp:**
- Nới lỏng version: `PyQt6>=6.5.0`, `pynput>=1.7.6`
- Thêm `evdev-binary` (prebuilt wheel) cho Linux trong build script
- Cài `pynput` với `--no-deps` để tránh pip cố build `evdev` từ source

#### [MODIFY] [requirements.txt](file:///home/arjunsharma/Tài liệu/GitHub/ViTai/requirements.txt)

---

### 1.6 — Build scripts cho Linux

#### [NEW] `build_linux.sh`
- Tạo venv, cài `evdev-binary` → `pynput --no-deps` → requirements
- Build bằng PyInstaller `--onedir`

#### [NEW] `run.sh`
- Quick-start script: tạo venv nếu chưa có → cài deps → chạy app

---

## Phase 2 — UI Overhaul: Premium Dark Theme 🎨

> **Mục tiêu:** Giao diện Settings và Overlay trông chuyên nghiệp như một ứng dụng thương mại — không còn cảm giác "student project".

### 2.1 — Settings Window: Thiết kế lại từ đầu

**Hiện trạng:** Giao diện đơn giản, 2 GroupBox ("Giao diện" + "Hệ thống & Tự động"), stylesheet cơ bản.

**Thiết kế mới:**

| Thành phần | Hiện tại | → Mới |
|-----------|----------|-------|
| **Layout** | 1 cột, 2 GroupBox | Sidebar navigation + content panel |
| **Theme** | Light/Dark tự detect | Dark-first, glassmorphism panels |
| **Typography** | System font 13px | Inter/Outfit từ Google Fonts, scale rõ ràng |
| **Tabs** | Không có | 3 tabs: ⚙️ Hệ thống · 🤖 Trí tuệ AI · 🚫 Ngoại lệ |
| **Animation** | Không | Fade-in khi mở, hover glow trên buttons |
| **Size** | 450×480 fixed | ~560×520, tỷ lệ đẹp hơn |

#### [MODIFY] [settings.py](file:///home/arjunsharma/Tài liệu/GitHub/ViTai/src/vitai/settings.py)

**Tab 1 — ⚙️ Hệ thống:**
- Phím tắt kích hoạt (Modifier + Key combos)
- Khởi động cùng hệ thống (checkbox)
- Tự động trả lời khi bôi đen (checkbox)
- Cache đáp án (checkbox)

**Tab 2 — 🤖 Trí tuệ AI:**
- Provider selector (dropdown với preset: Gemini, Groq, Mistral, Cerebras, OpenRouter, 9Router, OpenAI, Anthropic, DeepSeek)
- API Key input (password field với toggle visibility)
- Base URL (auto-fill theo provider, có thể custom)
- Model name
- Font / Cỡ chữ / Màu chữ cho overlay

**Tab 3 — 🚫 Ngoại lệ:**
- Danh sách app không kích hoạt ViTai (giống EVKey exclusion list)
- Nút Thêm / Xóa app

---

### 2.2 — Overlay Answer: Nâng cấp thị giác

**Hiện trạng:** Text trần trên nền transparent, không border, không shadow.

**Thiết kế mới:**

| Thành phần | Hiện tại | → Mới |
|-----------|----------|-------|
| **Background** | Transparent | Semi-transparent dark blur (glassmorphism) |
| **Border** | Không | 1px subtle gradient border |
| **Shadow** | Không | Soft drop shadow |
| **Typography** | Config font, raw text | Styled text, proper padding |
| **Loading** | "..." | Animated dots hoặc subtle pulse |
| **Interaction** | Click to refresh | Click to refresh + hover highlight |

#### [MODIFY] [overlay.py](file:///home/arjunsharma/Tài liệu/GitHub/ViTai/src/vitai/overlay.py)

---

### 2.3 — Tray Icon & Menu: Polish

#### [MODIFY] [main.py](file:///home/arjunsharma/Tài liệu/GitHub/ViTai/src/vitai/main.py)
- Menu icons (emoji → proper styled text)
- Tooltip hiện phím tắt hiện tại
- Single-click mở Settings (thay vì double-click)

---

## 📊 Tổng hợp files thay đổi

| Phase | File | Hành động | Mức độ |
|-------|------|-----------|--------|
| 1.1 | `capture.py` | MODIFY | 🔧 Thêm Linux backend |
| 1.2 | `startup.py` | MODIFY | 🔧 Thêm Linux autostart |
| 1.3 | `main.py` | MODIFY | 🔧 Platform-aware init + tray |
| 1.4 | `settings.py` | MODIFY | 🔧 Cross-platform dark mode |
| 1.5 | `requirements.txt` | MODIFY | 🔧 Nới lỏng version |
| 1.6 | `build_linux.sh` | NEW | ✨ Build script cho Fedora |
| 1.6 | `run.sh` | NEW | ✨ Quick-start script |
| 2.1 | `settings.py` | MODIFY | 🎨 Thiết kế lại hoàn toàn |
| 2.2 | `overlay.py` | MODIFY | 🎨 Glassmorphism + polish |
| 2.3 | `main.py` | MODIFY | 🎨 Tray menu polish |

---

## ✅ Verification Plan

### Automated
```bash
# Chạy trên Fedora 44
./run.sh
# Hoặc build binary
./build_linux.sh && ./dist/ViTai/ViTai

# Chạy trên Windows
python scripts/build_windows.py
dist\ViTai\ViTai.exe
```

### Manual Testing
1. **Linux:** Mở app → icon xuất hiện trong panel "Ứng dụng nền" (như Discord) → click mở Settings
2. **Linux:** Bôi đen text trong Firefox/terminal → nhấn Alt+Q → overlay hiện đáp án
3. **Windows:** Tất cả chức năng cũ vẫn hoạt động bình thường (regression test)
4. **UI:** Settings window mở ra với dark theme đẹp, 3 tabs hoạt động mượt
5. **UI:** Overlay answer có background blur, shadow, typography chuyên nghiệp

---

> **📝 Nguyên tắc:** Giữ nguyên 100% logic nghiệp vụ. Chỉ thay đổi lớp platform và lớp UI. Mọi flow `text capture → MCQ detect → LLM call → overlay display` không bị ảnh hưởng.