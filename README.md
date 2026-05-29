<div align="center">
  <img src="assets/icon.ico" width="100" alt="ViTai Logo" />
  
  # ViTai
  ### Floating Academic Assistant (Ghost Mode)
  
  ![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
  ![Windows](https://img.shields.io/badge/Windows-Supported-0078D6?style=for-the-badge&logo=windows)
  ![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
</div>

---

**ViTai** is a minimalist System Tray application for Windows, designed specifically to help you instantly solve academic and multiple-choice questions. Simply highlight text anywhere (Browsers, Word, PDF viewers), and the answer will appear as a sleek, floating tooltip right next to your cursor, without interrupting your workflow.

## 🚀 Key Features

- 👻 **Ghost Mode (Zero-UI):** Answers appear as a floating text overlay (no borders, no solid background) precisely where you release your mouse. It acts like a smart tooltip and never steals focus from your active application.
- ⚙️ **Settings UI:** Easily configure the application by right-clicking the icon in the System Tray. Features include:
  - Customizable Hotkeys (e.g., `Alt+Q`, `Ctrl+Shift+E`).
  - Custom Typography: Change font family, font size, and use custom Hex color codes (e.g., `#212529`, `#ff0000`).
  - **Start with Windows** integration.
  - Auto-syncing Light/Dark mode based on your Windows theme preferences.
- ⚡ **Auto-Translate & Smart Caching:** Enable auto-mode to fetch answers the moment you release the mouse button (no hotkey needed). Combined with built-in **Memory Caching**, ViTai remembers previous answers and responds instantly (`0ms`) if you highlight the same question again.
- 🧠 **Multi-Provider AI (Zero-Dependency):** Extremely lightweight via direct REST API calls (no bulky SDKs). Supported providers:
  - Gemini (Google)
  - OpenAI (ChatGPT)
  - DeepSeek
  - Anthropic / Internal Proxies (e.g., 9Router)
- 📚 **Automated RAG System:** Drop any PDF textbook or document into the `docs/` folder. ViTai will automatically read, index, and use that context to answer your questions accurately. (*Modern Operating Systems 4th Edition* is included by default).
- ✨ **MCQ Optimization:** The smart algorithm automatically detects Multiple Choice Questions (MCQ) and decisively returns only the exact answer letter (e.g., A, B, C, D).

## 📥 Quick Install & Setup

1. Go to the [Releases](https://github.com/namtacozz/ViTai/releases) page and download the latest `ViTai_Release.zip`.
2. Extract the ZIP folder.
3. Open the `.env` file with Notepad. Remove the `#` symbol for the AI provider you want to use and paste your **API Key**.
4. Run `ViTai.exe`. The application will quietly run in the background (System Tray).

## 🖱 How to Use

1. Ensure ViTai is running in your System Tray.
2. Highlight a text block or question in any application.
3. **Method 1 (Automatic):** If "Auto-translate" is enabled in Settings, the answer will pop up automatically 150ms after you release the mouse.
4. **Method 2 (Manual):** Press the default hotkey `Alt + Q` (or your custom hotkey).
5. The answer will float directly below your mouse cursor.
6. Click anywhere on the screen or press `Esc` to close the answer tooltip.

## 🛠 Build from Source (For Developers)

If you want to modify the source code and build it yourself:

1. Create and activate a Virtual Environment:
```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Add your context books (if any) to the `docs/` folder.

4. Package it into an `.exe`:
```bash
python scripts/build_windows.py
```
*Note: If you encounter a Permission denied error, ensure that `ViTai.exe` is completely closed (Right-click tray icon > Quit) before building.*

The fully compiled application will be available in the `dist/ViTai/` directory.
