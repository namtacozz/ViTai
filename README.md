# ViTai

Windows system tray assistant. Select text anywhere, press `Alt+Q`, get short academic answer in a small overlay near cursor.

## Features

- Global `Alt+Q` hotkey
- Selected text capture through clipboard
- Anthropic SDK call through local proxy
- MCQ detection with single-letter answer display
- PyQt6 tray icon and topmost overlay
- PyInstaller build script

## Setup

1. Create virtual environment:

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
```

2. Create `.env`:

```bash
cp .env.example .env
```

3. Put Anthropic proxy settings in `.env`:

```text
ANTHROPIC_BASE_URL=http://127.0.0.1:20128/v1
ANTHROPIC_AUTH_TOKEN=your_token_here
ANTHROPIC_DEFAULT_OPUS_MODEL=High
ANTHROPIC_DEFAULT_SONNET_MODEL=High
ANTHROPIC_DEFAULT_HAIKU_MODEL=subagent
```

## Run in development

```bash
PYTHONPATH=src python -m vitai.main
```

## Use

1. Start app.
2. Select text in Notepad, Chrome, or another app.
3. Press `Alt+Q`.
4. Read answer overlay.
5. Press `Escape` to close overlay or wait for auto-close.

## Build Windows exe

Build:

```bash
python scripts/build_windows.py
```

Run packaged app:

```bash
dist/ViTai/ViTai.exe
```

## Smoke test

- Select general question, press `Alt+Q`: overlay shows short answer.
- Select MCQ with A/B/C/D options, press `Alt+Q`: overlay shows `Đáp án: X`.
- Press `Alt+Q` with no selected text: overlay shows `Không tìm thấy text bôi đen`.
- Stop local proxy or use bad token: overlay shows API error.
- Press `Escape`: overlay closes.
- Clipboard content before `Alt+Q` remains restored after capture.
