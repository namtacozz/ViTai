<div align="center">
  <img src="assets/icon.ico" width="100" alt="ViTai Logo" />
  
  # ViTai
  ### The Ultimate Screen Translation & AI Academic Assistant
  
  ![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
  ![Windows](https://img.shields.io/badge/Windows-Supported-0078D6?style=for-the-badge&logo=windows)
  ![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
</div>

---

**ViTai** (formerly merging ViTai & ViTrans) is a minimalist, powerful System Tray application for Windows. It provides **two core functionalities**:
1. **Screen Translation:** Instantly translate any text on your screen (even unselectable text in games/videos) using OCR and advanced translation models (Google, DeepL, AI).
2. **Ghost FAA (Floating Academic Assistant):** Select any text and let AI answer your questions or solve multiple-choice questions instantly via a sleek, transparent overlay.

## 🚀 Key Features

### 🌐 Screen Translation
- 🔠 **OCR Built-in:** Uses EasyOCR or PaddleOCR to read text directly from a designated area on your screen.
- ⚡ **Multi-Engine Translation:** Supports Google Translate, DeepL, and advanced AI LLMs for context-aware translations.
- 🎨 **Visual Overlays:** Translations appear directly on top of the original text with customizable bounding boxes, backgrounds, and text colors.

### 👻 Ghost FAA (AI Assistant)
- 🎯 **Zero-UI Experience:** Answers appear as a floating text overlay precisely where you release your mouse, acting like a smart tooltip.
- 🧠 **Multi-Provider AI:** Extremely lightweight via direct REST API calls. Supported providers: Gemini (Google), OpenAI (ChatGPT), DeepSeek, Anthropic, etc.
- ✨ **MCQ Optimization:** The smart algorithm automatically detects Multiple Choice Questions (MCQ) and decisively returns only the exact answer letter.
- 📋 **Copy to Clipboard:** Double-click the answer overlay to copy the AI's response directly to your clipboard.

### ⚙️ Global Features
- **Centralized Settings UI:** Easily configure the application by right-clicking the icon in the System Tray. Organize everything neatly with tabs for General, Translation, and AI Assistant settings.
- **Independent Hotkeys:** Set unique hotkeys for Screen Translation (e.g., `Alt+T`) and Ghost FAA (e.g., `Alt+Q`).
- **Memory Caching:** Remembers previous translations and AI answers to respond instantly (`0ms`) if you highlight the same text again.

## 📥 Quick Install & Setup

1. Go to the [Releases](https://github.com/namtacozz/ViTai/releases) page and download the latest `ViTai_Release.zip`.
2. Extract the ZIP folder.
3. Open the application. Right-click the system tray icon, select **Settings**.
4. In the **AI Assistant** tab, input your API Key for your preferred LLM provider.
5. In the **Translation** tab, select your preferred OCR and translation engines.

## 🖱 How to Use

- **Translation Mode:**
  - Press the Translation Hotkey (Default: `Alt+T`).
  - Use your mouse to draw a box around the text on your screen.
  - The translated text will overlay the original text area.

- **Ghost FAA Mode:**
  - Highlight a text block or question in any application (Browser, PDF, Word).
  - Press the FAA Hotkey (Default: `Alt+Q`), OR enable "Ghost FAA" auto-mode in settings to trigger automatically on selection.
  - The answer will float directly below your mouse cursor. Click anywhere or press `Esc` to close it.

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

3. Package it into an `.exe`:
```bash
python scripts/build_windows.py
```
*Note: If you encounter a Permission denied error, ensure that `ViTai.exe` is completely closed (Right-click tray icon > Quit) before building.*

The fully compiled application will be available in the `dist/ViTai/` directory.
