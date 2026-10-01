<div align="center">

<img src="assets/logo.png" alt="ViTai Logo" width="120" />

# ViTai v3.5.0

### Instant AI Answer Overlay & Screen Vision Assistant — Ghost-Mode Desktop Companion

[![Version](https://img.shields.io/badge/Version-v3.5.0-10B981?style=for-the-badge&logo=rocket&logoColor=white)](https://github.com/namtacozz/ViTai/releases)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-51A2DA?style=for-the-badge&logo=desktop&logoColor=white)](#installation)
[![License](https://img.shields.io/badge/License-Proprietary-red?style=for-the-badge&logo=shield&logoColor=white)](#license)

**Highlight text or drag-select any screen region. Receive instant, invisible AI answers.**

[Download](#installation) · [How It Works](#how-it-works) · [Features](#key-features) · [Pricing](#pricing) · [FAQ](#faq)

---

</div>

## What is ViTai?

**ViTai** is a lightweight, stealth desktop application designed as an invisible AI-powered companion for exams, tests, and study. It offers two lightning-fast modes:

1. **Text Mode (`Alt + Q`):** Highlight any multiple choice or analytical question on screen. The correct answer (e.g. `A`, `B`, `C`, `D`) appears instantly as a floating overlay right next to your cursor.
2. **Vision Mode (`Alt + S`):** Drag and select any region on your screen (graphs, math formulas, image-based questions, locked canvas exams). The image is captured and routed directly to a vision-capable multimodal LLM, rendering the answer without leaving any trace.

No browser tabs. No copy-paste. No alt-tabbing. Just answers.

---

## How It Works

```
1. Select    →  Highlight question text (Alt + Q) OR drag-select screen region (Alt + S)
2. Trigger   →  Press configured hotkey or dedicated mouse button
3. Answer    →  AI-generated answer appears as a floating ghost overlay at cursor position
4. Dismiss   →  Press Esc or click anywhere to vanish instantly. Zero trace left behind.
```

ViTai connects to the AI provider **you choose** — using **your own API keys or OAuth login** (OpenAI Codex subscription, Google Gemini, Anthropic Claude, DeepSeek). Your tokens, your quota, your privacy.

---

## What's New in v3.5.0

- 📸 **Screen Region Vision Mode (`Alt + S`):** Interactive semi-transparent screen overlay. Drag a bounding box over any question image or diagram to send directly to multimodal vision models.
- 🎨 **Redesigned Home Tab:** Brand-new connected 3-step visual cards with native vector graphics, stepper timeline badges, and instant navigation buttons.
- ⚡ **Streamlined AI Providers:** Core focus on top high-accuracy providers (OpenAI Codex OAuth & API, Google Gemini, Claude, DeepSeek).
- 💾 **Full Settings Persistence:** Model selections, providers, and custom hotkeys remain firmly saved across app restarts.

---

## Key Features

| Feature | Description |
|---|---|
| **Ghost Overlay** | Frameless, borderless, fully transparent answer display. Invisible to standard window enumeration (`Alt+Tab`, taskbar). |
| **Dual Mode** | Text Selection (`Alt + Q`) + Screen Region Vision (`Alt + S`). |
| **Multi-Provider AI** | Connect to OpenAI/ChatGPT (with Free/Plus OAuth Codex support), Google Gemini, Anthropic Claude, DeepSeek, or any OpenAI-compatible endpoint. |
| **Flexible Hotkeys** | Bind any keyboard shortcut or mouse button (Right, Middle, Side/X1, Extra/X2) as your trigger. |
| **360° Color Wheel** | Pick any overlay text color to ensure perfect contrast on any background (Photoshop-style HSV wheel). |
| **Smart Cache** | Previously answered questions return in 0ms — no repeated API calls. |
| **Fast Mode** | Auto-analysis: answers appear the instant you release the mouse after highlighting. |
| **Cross-Platform** | Native builds for Windows 10/11 and Linux (X11 + Wayland/Fedora/Ubuntu/Arch). |
| **Hardware-Bound Security** | Multi-layer device fingerprinting. Encrypted local token storage. Anti-tamper account protection. |

---

## Installation

### Windows (10 / 11)
1. Download **[`ViTai-Windows-x64.zip`](https://github.com/namtacozz/ViTai/releases/download/v3.5.0/ViTai-Windows-x64.zip)** (or from [Latest Releases](https://github.com/namtacozz/ViTai/releases)).
2. Extract the `.zip` archive to any directory.
3. Run **`ViTai.exe`** — no dependencies required.

### Linux (Fedora / Ubuntu / Debian / Arch)
1. Download **[`ViTai-Linux-x86_64.tar.gz`](https://github.com/namtacozz/ViTai/releases/download/v3.5.0/ViTai-Linux-x86_64.tar.gz)** from [Latest Releases](https://github.com/namtacozz/ViTai/releases).
2. Extract and run:
   ```bash
   tar -xvf ViTai-Linux-x86_64.tar.gz
   cd ViTai && ./ViTai
   ```

> **Linux tip (Wayland/Fedora):** For smooth mouse and global input tracking, grant input access once:
> ```bash
> sudo usermod -aG input $USER
> ```
> Then log out and log back in.

---

## Pricing

ViTai uses a one-time activation model — **no recurring subscriptions, no hidden fees**.

| Plan | Price | Duration | Devices |
|---|---|---|---|
| **Standard** | 50,000 VND (~$2 USD) | 90 days | 1 device |
| **Lifetime** | 300,000 VND (~$12 USD) | Forever | 1 device |

**No daily request limits.** You use your own AI provider credentials — your usage is only limited by your own LLM quota.

### How to Activate
1. Launch ViTai and click **"Đăng ký tài khoản" (Register)** on the lock screen.
2. Scan the VietQR code and transfer the exact amount displayed.
3. Your account is **automatically activated 24/7** via instant webhook integration — no waiting, no manual approval.

> Need to transfer your license to a new machine? Contact admin support for a device reset.

---

## Supported AI Providers

| Provider | Auth Method | Default Model | Multimodal Vision |
|---|---|---|---|
| **OpenAI / ChatGPT** | OAuth Codex / API Key | cx/gpt-5.6-terra, gpt-4o-mini | Yes |
| **Google Gemini** | API Key | gemini-2.5-flash | Yes |
| **Anthropic Claude** | API Key | claude-3-5-sonnet | Yes |
| **DeepSeek** | API Key | deepseek-chat | Text only |
| **Custom** | Any OpenAI-compatible endpoint | — | Configurable |

---

## FAQ

<details>
<summary><b>Is ViTai detectable by exam proctoring software?</b></summary>

ViTai's overlay is designed to be invisible to standard window enumeration (`Alt+Tab`, taskbar). It uses frameless, input-transparent Qt windows. However, advanced proctoring tools with screen capture may still detect pixel changes. Use responsibly.
</details>

<details>
<summary><b>Can I use ViTai on multiple computers?</b></summary>

Each license is bound to one physical device via hardware fingerprinting. To switch devices, contact support for a device transfer.
</details>

<details>
<summary><b>What happens when my 90-day plan expires?</b></summary>

The app will prompt you to renew. Your settings and cache are preserved. You can upgrade to Lifetime at any time.
</details>

<details>
<summary><b>Do you store my API keys or AI conversations?</b></summary>

No. All API keys are stored locally on your device with hardware-bound encryption. AI requests go directly from your machine to your chosen provider. We never see your keys or your queries.
</details>

<details>
<summary><b>Which languages are supported?</b></summary>

ViTai works with any language supported by your chosen AI provider. The UI is available in Vietnamese and English.
</details>

---

## Tech Stack

- **GUI Framework:** PyQt6 (cross-platform native)
- **AI Integration:** Zero-dependency HTTP client via Python standard library `urllib.request`
- **Packaging:** PyInstaller (portable standalone distribution)
- **Cloud Sync:** Supabase PostgREST (hybrid offline/online fallback)

---

## License

ViTai is **proprietary software**. Source code is maintained privately in `ViTai-Core`.
Binary releases are distributed under a commercial license.
Unauthorized redistribution, reverse engineering, or modification is prohibited.

Developed by **Vì Người Tài Team**.
