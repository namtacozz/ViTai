<div align="center">

<img src="assets/logo.png" alt="ViTai Logo" width="120" />

# ViTai v3.4.0

### Instant AI Answer Overlay — Ghost-Mode Desktop Assistant

[![Version](https://img.shields.io/badge/Version-v3.4.0-E09F5E?style=for-the-badge&logo=rocket&logoColor=white)](https://github.com/namtacozz/ViTai/releases)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-51A2DA?style=for-the-badge&logo=desktop&logoColor=white)](#installation)
[![License](https://img.shields.io/badge/License-Proprietary-red?style=for-the-badge&logo=shield&logoColor=white)](#license)

**Highlight any question on your screen. Get the answer instantly.**

[Download](#installation) · [How It Works](#how-it-works) · [Features](#key-features) · [Pricing](#pricing) · [FAQ](#faq)

---

</div>

## What is ViTai?

**ViTai** is a lightweight desktop application that acts as an invisible AI-powered study companion. Simply highlight any question — multiple choice, short answer, or analytical — on your screen and press a hotkey. The correct answer appears as a subtle overlay right next to your cursor, then vanishes with a single click.

No browser tabs. No copy-paste. No alt-tabbing. Just answers.

---

## How It Works

```
1. Highlight  →  Select any question text on screen (browser, PDF, document, exam platform)
2. Hotkey     →  Press your configured hotkey (default: Alt + Q) or mouse button
3. Answer     →  AI-generated answer appears as a floating overlay at cursor position
4. Dismiss    →  Click anywhere to hide. Zero trace left behind.
```

ViTai connects to the AI provider **you choose** — using **your own API keys or OAuth login**. The app simply routes your selected text to the LLM and displays the response. Your tokens, your quota, your control.

---

## Key Features

| Feature | Description |
|---|---|
| **Ghost Overlay** | Frameless, borderless, fully transparent answer display. Invisible to screen recording tools and `Alt+Tab`. |
| **Multi-Provider AI** | Connect to Google Gemini, OpenAI/ChatGPT, Anthropic Claude, DeepSeek, Kiro AI, or any OpenAI-compatible endpoint. |
| **Flexible Hotkeys** | Bind any keyboard shortcut or mouse button (Right, Middle, Side/X1, Extra/X2) as your trigger. |
| **360° Color Wheel** | Pick any overlay text color to ensure perfect contrast on any background. Photoshop-style HSV wheel. |
| **Smart Cache** | Previously answered questions return in 0ms — no repeated API calls. |
| **Fast Mode** | Enable auto-analysis: answers appear the instant you release the mouse after highlighting. No hotkey needed. |
| **Cross-Platform** | Native support for Windows 10/11 and Linux (X11 + Wayland/Fedora/Ubuntu/Arch). |
| **Hardware-Bound Security** | Multi-layer device fingerprinting. Encrypted local token storage. Anti-tamper account protection. |
| **Dark Mode UI** | Clean, minimal carbon-dark interface with warm amber accents. |

---

## Installation

### Windows (10 / 11)
1. Download **`ViTai-v3.4.0-windows-x64.zip`** from [Releases](https://github.com/namtacozz/ViTai/releases).
2. Extract to any folder.
3. Run **`ViTai.exe`** — no dependencies required.

### Linux (Fedora / Ubuntu / Debian / Arch)
1. Download **`ViTai-v3.4.0-linux-x86_64.tar.gz`** from [Releases](https://github.com/namtacozz/ViTai/releases).
2. Extract and run:
   ```bash
   tar -xvf ViTai-v3.4.0-linux-x86_64.tar.gz
   cd ViTai && ./ViTai
   ```

> **Linux tip (Wayland/Fedora):** For smooth mouse tracking, grant input access once:
> ```bash
> sudo usermod -aG input $USER
> ```
> Then log out and back in.

---

## Pricing

ViTai uses a one-time activation model — **no subscriptions that drain your wallet, no hidden fees**.

| Plan | Price | Duration | Devices |
|---|---|---|---|
| **Standard** | 50,000 VND (~$2 USD) | 90 days | 1 device |
| **Lifetime** | 300,000 VND (~$12 USD) | Forever | 1 device |

**No daily request limits.** You use your own AI provider API keys — your usage is only limited by your own LLM quota.

### How to Activate
1. Open ViTai and click **"Register Account"** on the lock screen.
2. Scan the VietQR code and transfer the exact amount to the displayed bank account.
3. Your account is **automatically activated 24/7** — no manual review, no waiting.

> Need to transfer your license to a new device? Contact support for a free device reset.

---

## Supported AI Providers

| Provider | Auth Method | Default Model |
|---|---|---|
| Google Gemini | API Key | gemini-2.5-flash |
| OpenAI / ChatGPT | API Key / OAuth | cx/gpt-5.5 |
| Anthropic Claude | API Key | claude-sonnet-4 |
| DeepSeek | API Key | deepseek-chat |
| Kiro AI | API Key / OAuth | kr/claude-sonnet-4.5 |
| 9Router (Local) | API Key | High |
| Custom | Any OpenAI-compatible endpoint | — |

---

## FAQ

<details>
<summary><b>Is ViTai detectable by exam proctoring software?</b></summary>

ViTai's overlay is designed to be invisible to standard window enumeration (`Alt+Tab`, taskbar). It uses frameless, input-transparent Qt windows. However, advanced proctoring tools with screen capture may still detect pixel changes. Use responsibly.
</details>

<details>
<summary><b>Can I use ViTai on multiple computers?</b></summary>

Each license is bound to one physical device via hardware fingerprinting. To switch devices, request a free device reset from support.
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

## Security

ViTai v3.4.0 includes enterprise-grade account protection:

- **Multi-layer device fingerprinting** — MAC address + OS Machine ID + CPU signature + architecture hash
- **PBKDF2-HMAC-SHA256** password hashing (100,000 iterations)
- **Anti-bruteforce lockout** — 5 failed attempts trigger a 5-minute temporary block
- **Transaction ledger** — prevents payment replay attacks (reusing bank transfer references)
- **Hardware-bound token encryption** — OAuth tokens are encrypted to your device; copying `tokens.json` to another machine renders it unreadable

---

## Tech Stack

- **Language:** Python 3.12+
- **GUI Framework:** PyQt6 (cross-platform native)
- **AI Integration:** Direct REST API calls via `urllib.request` (zero external HTTP dependencies)
- **Packaging:** PyInstaller (single-folder portable distribution)
- **Cloud Sync:** Supabase PostgREST (optional, hybrid offline/online)

---

## Support & Contact

- **GitHub Issues:** [Report a bug](https://github.com/namtacozz/ViTai/issues)
- **Facebook:** [ViTai Community](https://facebook.com)

---

## License

ViTai is **proprietary software**. The source code is not publicly available.
Binary releases are distributed under a commercial license.
Unauthorized redistribution, reverse engineering, or modification is prohibited.

Developed by **ViTai Team**.

