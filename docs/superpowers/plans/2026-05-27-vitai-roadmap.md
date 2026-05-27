# ViTai Roadmap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build ViTai MVP: Windows system tray app using Alt+Q to capture selected text, call Gemini, detect MCQ, and show answer overlay.

**Architecture:** Small PyQt6 desktop app. Main thread owns QApplication, tray, overlay; hotkey callback emits Qt signal; background worker captures selected text, calls Gemini, then emits answer back to UI.

**Tech Stack:** Python 3.12, PyQt6, pynput + Win32 hotkey backend, pyperclip + ctypes SendInput, google-genai, python-dotenv, PyInstaller.

---

## File Structure

- `src/vitai/__init__.py` — package marker.
- `src/vitai/hotkey.py` — copy from `D:\ViTrans\src\vitrans\hotkey.py`; global Alt+Q backend.
- `src/vitai/resources.py` — copy from `D:\ViTrans\src\vitrans\resources.py`; PyInstaller resource path.
- `src/vitai/encoding.py` — copy from `D:\ViTrans\src\vitrans\encoding.py`; UTF-8 stdio setup.
- `src/vitai/logging_config.py` — copy/adapt from ViTrans; log to `~/.vitai/vitai.log`.
- `src/vitai/startup.py` — copy/adapt from ViTrans only if needed for future; not required by MVP runtime.
- `src/vitai/config.py` — small dataclass config: Gemini key, model, hotkey, startup flag.
- `src/vitai/capture.py` — clipboard backup, Ctrl+C simulation, restore clipboard.
- `src/vitai/mcq.py` — detect MCQ options and normalize LLM output for MCQ.
- `src/vitai/llm.py` — prompt building and Gemini call.
- `src/vitai/overlay.py` — topmost answer popup with copy button and auto-close.
- `src/vitai/main.py` — QApplication, tray, hotkey, config, worker threads, UI bridge.
- `tests/test_config.py` — config load/save tests.
- `tests/test_mcq.py` — MCQ detector tests.
- `tests/test_llm.py` — prompt routing tests without API call.
- `requirements.txt` — runtime + dev test deps.
- `.env.example` — Gemini key template.
- `.gitignore` — copy from ViTrans or create equivalent.
- `assets/icon.ico` — copy from `D:\ViTrans\assets\logo.ico`.
- `assets/logo.png` — copy from `D:\ViTrans\assets\logo.png` if exists.
- `scripts/build_windows.py` — PyInstaller build script.
- `README.md` — usage and build instructions.

---

## Task 1: Project Scaffold + Reused Utilities

**Files:**
- Create: `src/vitai/__init__.py`
- Create: `src/vitai/hotkey.py`
- Create: `src/vitai/resources.py`
- Create: `src/vitai/encoding.py`
- Create: `src/vitai/logging_config.py`
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create/copy: `assets/icon.ico`
- Optional copy: `assets/logo.png`

**Prompt for another session:**

```text
Implement Task 1 from d:\ViTai\docs\superpowers\plans\2026-05-27-vitai-roadmap.md. Create ViTai scaffold and copy/adapt reusable ViTrans utilities. Do not implement config/capture/LLM/main yet. Run import smoke check at end.
```

- [ ] **Step 1: Create folders**

Run:

```bash
mkdir -p src/vitai assets scripts tests
```

Expected: folders exist.

- [ ] **Step 2: Copy production-tested ViTrans files**

Run:

```bash
cp D:/ViTrans/src/vitrans/hotkey.py src/vitai/hotkey.py
cp D:/ViTrans/src/vitrans/resources.py src/vitai/resources.py
cp D:/ViTrans/src/vitrans/encoding.py src/vitai/encoding.py
cp D:/ViTrans/assets/logo.ico assets/icon.ico
if [ -f D:/ViTrans/assets/logo.png ]; then cp D:/ViTrans/assets/logo.png assets/logo.png; fi
```

Expected: files copied.

- [ ] **Step 3: Create package marker**

Write `src/vitai/__init__.py`:

```python
__version__ = "0.1.0"
```

- [ ] **Step 4: Create logging config**

Write `src/vitai/logging_config.py`:

```python
from __future__ import annotations

import logging
from pathlib import Path


def configure_logging() -> None:
    log_dir = Path.home() / ".vitai"
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "vitai.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
```

- [ ] **Step 5: Create dependencies**

Write `requirements.txt`:

```text
PyQt6==6.7.1
pynput==1.7.7
pyperclip>=1.8
google-genai>=1.0
python-dotenv>=1.0
pytest>=8.0
```

- [ ] **Step 6: Create env template**

Write `.env.example`:

```text
GEMINI_API_KEY=your_key_here
```

- [ ] **Step 7: Create gitignore**

Write `.gitignore`:

```gitignore
.venv/
__pycache__/
*.pyc
.pytest_cache/
.env
dist/
build/
*.spec
*.log
```

- [ ] **Step 8: Run import smoke check**

Run:

```bash
PYTHONPATH=src python - <<'PY'
import vitai
from vitai.hotkey import HotkeyManager
from vitai.resources import resource_path
from vitai.encoding import configure_utf8_stdio
from vitai.logging_config import configure_logging
print(vitai.__version__)
print(HotkeyManager)
print(resource_path("assets/icon.ico"))
print(configure_utf8_stdio, configure_logging)
PY
```

Expected: command exits 0 and prints `0.1.0`.

---

## Task 2: Config Persistence

**Files:**
- Create: `src/vitai/config.py`
- Create: `tests/test_config.py`

**Prompt for another session:**

```text
Implement Task 2 from d:\ViTai\docs\superpowers\plans\2026-05-27-vitai-roadmap.md. Add config dataclass and tests only. Keep fields minimal. Run pytest for config tests.
```

- [ ] **Step 1: Write failing config tests**

Write `tests/test_config.py`:

```python
from pathlib import Path

from vitai.config import AppConfig, default_config_path, load_config, save_config


def test_default_config_path_points_to_vitai():
    assert default_config_path() == Path.home() / ".vitai" / "config.json"


def test_load_missing_config_returns_defaults(tmp_path):
    config = load_config(tmp_path / "missing.json")

    assert config.gemini_api_key == ""
    assert config.model == "gemini-2.0-flash"
    assert config.hotkey_modifier == "alt"
    assert config.hotkey_key == "q"
    assert config.hotkey_backend == "auto"


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "config.json"
    original = AppConfig(gemini_api_key="abc", model="gemini-test", hotkey_key="x")

    save_config(path, original)
    loaded = load_config(path)

    assert loaded == original


def test_unknown_keys_are_ignored(tmp_path):
    path = tmp_path / "config.json"
    path.write_text('{"gemini_api_key":"abc","unknown":"ignored"}', encoding="utf-8")

    loaded = load_config(path)

    assert loaded.gemini_api_key == "abc"
    assert not hasattr(loaded, "unknown")
```

- [ ] **Step 2: Run tests to verify fail**

Run:

```bash
PYTHONPATH=src pytest tests/test_config.py -v
```

Expected: FAIL because `vitai.config` missing.

- [ ] **Step 3: Implement config**

Write `src/vitai/config.py`:

```python
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    gemini_api_key: str = ""
    model: str = "gemini-2.0-flash"
    hotkey_modifier: str = "alt"
    hotkey_key: str = "q"
    hotkey_backend: str = "auto"
    start_with_windows: bool = False


def default_config_path() -> Path:
    return Path.home() / ".vitai" / "config.json"


def load_config(path: Path | None = None) -> AppConfig:
    config_path = path or default_config_path()
    if not config_path.exists():
        return AppConfig()

    data = json.loads(config_path.read_text(encoding="utf-8"))
    defaults = asdict(AppConfig())
    defaults.update({key: value for key, value in data.items() if key in defaults})
    return AppConfig(**defaults)


def save_config(path: Path | None, config: AppConfig) -> None:
    config_path = path or default_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(asdict(config), indent=2, ensure_ascii=False), encoding="utf-8")
```

- [ ] **Step 4: Run config tests**

Run:

```bash
PYTHONPATH=src pytest tests/test_config.py -v
```

Expected: 4 passed.

---

## Task 3: MCQ Detection and Prompt Helpers

**Files:**
- Create: `src/vitai/mcq.py`
- Create: `tests/test_mcq.py`

**Prompt for another session:**

```text
Implement Task 3 from d:\ViTai\docs\superpowers\plans\2026-05-27-vitai-roadmap.md. Add MCQ detection and tests only. Run pytest for MCQ tests.
```

- [ ] **Step 1: Write failing MCQ tests**

Write `tests/test_mcq.py`:

```python
from vitai.mcq import is_mcq, normalize_mcq_answer


def test_detects_lettered_options_with_periods():
    text = "Capital of France?\nA. London\nB. Paris\nC. Rome\nD. Berlin"

    assert is_mcq(text) is True


def test_detects_lettered_options_with_parentheses():
    text = "2 + 2 = ?\nA) 3\nB) 4"

    assert is_mcq(text) is True


def test_requires_at_least_two_unique_options():
    text = "A. This is one bullet only"

    assert is_mcq(text) is False


def test_general_question_is_not_mcq():
    assert is_mcq("Explain database connection pooling.") is False


def test_normalize_mcq_answer_extracts_first_label():
    assert normalize_mcq_answer("Answer: b") == "B"


def test_normalize_mcq_answer_returns_stripped_text_when_no_label():
    assert normalize_mcq_answer("Không chắc chắn") == "Không chắc chắn"
```

- [ ] **Step 2: Run tests to verify fail**

Run:

```bash
PYTHONPATH=src pytest tests/test_mcq.py -v
```

Expected: FAIL because `vitai.mcq` missing.

- [ ] **Step 3: Implement MCQ module**

Write `src/vitai/mcq.py`:

```python
from __future__ import annotations

import re

MCQ_PATTERN = re.compile(r"(?mi)^\s*([A-Za-z])\s*[.)\]:\-]\s*.+")
ANSWER_PATTERN = re.compile(r"\b([A-Za-z])\b")


def is_mcq(text: str) -> bool:
    matches = MCQ_PATTERN.findall(text)
    unique_labels = {match.upper() for match in matches}
    return len(unique_labels) >= 2


def normalize_mcq_answer(answer: str) -> str:
    match = ANSWER_PATTERN.search(answer.strip())
    if match:
        return match.group(1).upper()
    return answer.strip()
```

- [ ] **Step 4: Run MCQ tests**

Run:

```bash
PYTHONPATH=src pytest tests/test_mcq.py -v
```

Expected: 6 passed.

---

## Task 4: LLM Prompt Routing and Gemini Client

**Files:**
- Create: `src/vitai/llm.py`
- Create: `tests/test_llm.py`

**Prompt for another session:**

```text
Implement Task 4 from d:\ViTai\docs\superpowers\plans\2026-05-27-vitai-roadmap.md. Add Gemini LLM wrapper with testable prompt routing. Do not perform real API calls in tests. Run pytest for LLM tests.
```

- [ ] **Step 1: Write failing LLM tests**

Write `tests/test_llm.py`:

```python
from vitai.llm import build_prompt


def test_general_prompt_limits_answer_length():
    prompt = build_prompt("Explain TCP.", is_mcq=False)

    assert "Trả lời rõ ràng, tối đa 2 câu" in prompt
    assert "Explain TCP." in prompt


def test_mcq_prompt_requires_single_answer_letter():
    prompt = build_prompt("A. One\nB. Two", is_mcq=True)

    assert "CHỈ trả về DUY NHẤT một ký tự đáp án" in prompt
    assert "A. One\nB. Two" in prompt
```

- [ ] **Step 2: Run tests to verify fail**

Run:

```bash
PYTHONPATH=src pytest tests/test_llm.py -v
```

Expected: FAIL because `vitai.llm` missing.

- [ ] **Step 3: Implement LLM module**

Write `src/vitai/llm.py`:

```python
from __future__ import annotations

from google import genai

GENERAL_SYSTEM_PROMPT = """Bạn là trợ lý học thuật ngắn gọn. Trả lời rõ ràng, tối đa 2 câu.
Nếu không chắc chắn, trả lời "Không chắc chắn" kèm 1 câu lý do ngắn."""

MCQ_SYSTEM_PROMPT = """Bạn là trợ lý giải đề trắc nghiệm.
CHỈ trả về DUY NHẤT một ký tự đáp án (A, B, C, D, ...).
KHÔNG giải thích. KHÔNG thêm bất kỳ text nào khác."""


def build_prompt(question: str, is_mcq: bool) -> str:
    system_prompt = MCQ_SYSTEM_PROMPT if is_mcq else GENERAL_SYSTEM_PROMPT
    return f"System: {system_prompt}\n\nUser: {question.strip()}"


class GeminiClient:
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def ask(self, question: str, is_mcq: bool) -> str:
        response = self._client.models.generate_content(
            model=self._model,
            contents=build_prompt(question, is_mcq),
            config={"temperature": 0.0, "max_output_tokens": 150},
        )
        return (response.text or "").strip()
```

- [ ] **Step 4: Run LLM tests**

Run:

```bash
PYTHONPATH=src pytest tests/test_llm.py -v
```

Expected: 2 passed.

---

## Task 5: Clipboard Selected Text Capture

**Files:**
- Create: `src/vitai/capture.py`

**Prompt for another session:**

```text
Implement Task 5 from d:\ViTai\docs\superpowers\plans\2026-05-27-vitai-roadmap.md. Add Windows clipboard selected-text capture using pyperclip and ctypes SendInput. Include manual smoke command. Do not alter main app.
```

- [ ] **Step 1: Implement capture module**

Write `src/vitai/capture.py`:

```python
from __future__ import annotations

import ctypes
import time

import pyperclip

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
VK_CONTROL = 0x11
VK_C = 0x43


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("union", INPUT_UNION)]


def _keyboard_input(key: int, flags: int = 0) -> INPUT:
    return INPUT(type=INPUT_KEYBOARD, union=INPUT_UNION(ki=KEYBDINPUT(key, 0, flags, 0, None)))


def _send_ctrl_c() -> None:
    inputs = (INPUT * 4)(
        _keyboard_input(VK_CONTROL),
        _keyboard_input(VK_C),
        _keyboard_input(VK_C, KEYEVENTF_KEYUP),
        _keyboard_input(VK_CONTROL, KEYEVENTF_KEYUP),
    )
    ctypes.windll.user32.SendInput(len(inputs), ctypes.byref(inputs), ctypes.sizeof(INPUT))


def get_selected_text(delay: float = 0.15) -> str | None:
    original = pyperclip.paste()
    try:
        pyperclip.copy("")
        _send_ctrl_c()
        time.sleep(delay)
        selected = pyperclip.paste()
    finally:
        pyperclip.copy(original)

    selected = selected.strip()
    if not selected or selected == original.strip():
        return None
    return selected
```

- [ ] **Step 2: Run import smoke check**

Run:

```bash
PYTHONPATH=src python - <<'PY'
from vitai.capture import get_selected_text
print(get_selected_text)
PY
```

Expected: exits 0 and prints function repr.

- [ ] **Step 3: Manual smoke test**

Run:

```bash
PYTHONPATH=src python - <<'PY'
from vitai.capture import get_selected_text
print("Select text in another app within 3 seconds...")
import time; time.sleep(3)
print(repr(get_selected_text()))
PY
```

Expected: with selected text in another app, prints selected string and restores previous clipboard.

---

## Task 6: Answer Overlay UI

**Files:**
- Create: `src/vitai/overlay.py`

**Prompt for another session:**

```text
Implement Task 6 from d:\ViTai\docs\superpowers\plans\2026-05-27-vitai-roadmap.md. Add PyQt6 topmost answer overlay with copy button, Escape close, cursor positioning, auto-close. Include manual smoke command.
```

- [ ] **Step 1: Implement overlay**

Write `src/vitai/overlay.py`:

```python
from __future__ import annotations

import pyperclip
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QCursor, QFont, QKeyEvent
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class AnswerOverlay(QWidget):
    def __init__(self, text: str = "", timeout_ms: int = 10000):
        super().__init__()
        self._answer = text
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._build_ui()
        self.set_answer(text)
        self._move_near_cursor()
        if timeout_ms > 0:
            QTimer.singleShot(timeout_ms, self.close)

    def _build_ui(self) -> None:
        self.setStyleSheet(
            "QWidget#card { background: rgba(20, 20, 20, 230); border: 1px solid rgba(255, 255, 255, 120); border-radius: 10px; }"
            "QLabel { color: white; background: transparent; }"
            "QPushButton { background: rgba(255, 255, 255, 30); border: 1px solid rgba(255, 255, 255, 80); border-radius: 6px; color: white; padding: 4px 8px; }"
            "QPushButton:hover { background: rgba(255, 255, 255, 55); }"
        )
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        card = QWidget(self)
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        self.label = QLabel(card)
        self.label.setFont(QFont("Segoe UI", 12))
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.label)

        row = QHBoxLayout()
        row.addStretch(1)
        self.copy_button = QPushButton("Copy", card)
        self.copy_button.clicked.connect(self.copy_answer)
        row.addWidget(self.copy_button)
        layout.addLayout(row)
        root.addWidget(card)
        self.resize(420, 120)

    def set_answer(self, text: str) -> None:
        self._answer = text
        self.label.setText(text)
        self.adjustSize()
        self.resize(min(max(self.width(), 280), 520), min(max(self.height(), 90), 320))

    def copy_answer(self) -> None:
        pyperclip.copy(self._answer)

    def show_message(self, text: str) -> None:
        self.set_answer(text)
        self._move_near_cursor()
        self.show()
        self.raise_()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)

    def _move_near_cursor(self) -> None:
        pos = QCursor.pos()
        screen = QApplication.screenAt(pos) or QApplication.primaryScreen()
        if screen is None:
            self.move(pos.x() + 16, pos.y() + 16)
            return
        available = screen.availableGeometry()
        x = min(pos.x() + 16, available.right() - self.width())
        y = min(pos.y() + 16, available.bottom() - self.height())
        self.move(max(available.left(), x), max(available.top(), y))
```

- [ ] **Step 2: Run import smoke check**

Run:

```bash
PYTHONPATH=src python - <<'PY'
from vitai.overlay import AnswerOverlay
print(AnswerOverlay)
PY
```

Expected: exits 0.

- [ ] **Step 3: Manual UI smoke test**

Run:

```bash
PYTHONPATH=src python - <<'PY'
import sys
from PyQt6.QtWidgets import QApplication
from vitai.overlay import AnswerOverlay
app = QApplication(sys.argv)
overlay = AnswerOverlay("Đáp án: B", timeout_ms=5000)
overlay.show()
sys.exit(app.exec())
PY
```

Expected: popup appears near cursor, Copy button copies text, Escape closes, auto-closes after 5s.

---

## Task 7: Main App, Tray, Hotkey, Pipeline

**Files:**
- Create: `src/vitai/main.py`
- Modify: `src/vitai/llm.py` if needed for exception messages

**Prompt for another session:**

```text
Implement Task 7 from d:\ViTai\docs\superpowers\plans\2026-05-27-vitai-roadmap.md. Wire QApplication, tray icon, Alt+Q hotkey, clipboard capture, MCQ detection, Gemini call, and overlay. Keep UI updates on Qt thread. Run import smoke check and dev app smoke test.
```

- [ ] **Step 1: Implement main app**

Write `src/vitai/main.py`:

```python
from __future__ import annotations

import ctypes
import logging
import os
import sys
import threading
import traceback
from dataclasses import replace

from dotenv import load_dotenv
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QApplication, QInputDialog, QMenu, QSystemTrayIcon

from vitai.capture import get_selected_text
from vitai.config import AppConfig, default_config_path, load_config, save_config
from vitai.encoding import configure_utf8_stdio
from vitai.hotkey import HotkeyManager
from vitai.llm import GeminiClient
from vitai.logging_config import configure_logging
from vitai.mcq import is_mcq, normalize_mcq_answer
from vitai.overlay import AnswerOverlay
from vitai.resources import resource_path

configure_utf8_stdio()


def set_windows_app_id() -> None:
    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ViTai.App")


class UiBridge(QObject):
    hotkey_pressed = pyqtSignal()
    answer_ready = pyqtSignal(str)


class ViTaiApp:
    def __init__(self):
        load_dotenv()
        configure_logging()
        self.logger = logging.getLogger(__name__)
        self._install_exception_hooks()
        self.config_path = default_config_path()
        self.config = self._load_config_with_env()
        set_windows_app_id()

        self.qt_app = QApplication(sys.argv)
        self.qt_app.setApplicationName("ViTai")
        self.qt_app.setApplicationDisplayName("ViTai")
        self.qt_app.setWindowIcon(QIcon(str(resource_path("assets/icon.ico"))))
        self.qt_app.setQuitOnLastWindowClosed(False)

        self.bridge = UiBridge()
        self.bridge.hotkey_pressed.connect(self.handle_hotkey)
        self.bridge.answer_ready.connect(self.show_answer)
        self.overlay: AnswerOverlay | None = None
        self.worker_lock = threading.Lock()
        self.tray = self._create_tray()
        self.hotkey_manager = HotkeyManager(
            self.config.hotkey_modifier,
            self.config.hotkey_key,
            self._emit_hotkey,
            backend=self.config.hotkey_backend,
        )

    def _load_config_with_env(self) -> AppConfig:
        config = load_config(self.config_path)
        env_key = os.getenv("GEMINI_API_KEY", "").strip()
        if env_key and not config.gemini_api_key:
            config = replace(config, gemini_api_key=env_key)
        return config

    def _install_exception_hooks(self) -> None:
        def _excepthook(exc_type, exc_value, exc_tb):
            self.logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_tb))
            traceback.print_exception(exc_type, exc_value, exc_tb, file=sys.stderr)

        sys.excepthook = _excepthook

    def _create_tray(self) -> QSystemTrayIcon:
        tray = QSystemTrayIcon(QIcon(str(resource_path("assets/icon.ico"))), self.qt_app)
        tray.setToolTip("ViTai")
        menu = QMenu()
        show_action = QAction("Show", menu)
        show_action.triggered.connect(lambda: self.show_answer("ViTai đang chạy. Bôi đen text rồi nhấn Alt+Q."))
        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(self.quit)
        menu.addAction(show_action)
        menu.addAction(quit_action)
        tray.setContextMenu(menu)
        tray.activated.connect(self._tray_activated)
        tray.show()
        return tray

    def _tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_answer("ViTai đang chạy. Bôi đen text rồi nhấn Alt+Q.")

    def _emit_hotkey(self) -> None:
        self.bridge.hotkey_pressed.emit()

    def handle_hotkey(self) -> None:
        self.show_answer("Đang suy nghĩ...")
        threading.Thread(target=self._process_selection, daemon=True).start()

    def _process_selection(self) -> None:
        if not self.worker_lock.acquire(blocking=False):
            self.bridge.answer_ready.emit("Đang xử lý câu trước.")
            return
        try:
            selected_text = get_selected_text()
            if not selected_text:
                self.bridge.answer_ready.emit("Không tìm thấy text bôi đen")
                return

            if not self.config.gemini_api_key:
                self.bridge.answer_ready.emit("Chưa có Gemini API key")
                return

            question_is_mcq = is_mcq(selected_text)
            client = GeminiClient(self.config.gemini_api_key, self.config.model)
            answer = client.ask(selected_text, question_is_mcq)
            if question_is_mcq:
                answer = f"Đáp án: {normalize_mcq_answer(answer)}"
            self.bridge.answer_ready.emit(answer or "Không có phản hồi")
        except Exception as exc:
            self.logger.exception("Failed to answer selection")
            self.bridge.answer_ready.emit(f"Lỗi kết nối API: {exc}")
        finally:
            self.worker_lock.release()

    def show_answer(self, text: str) -> None:
        if text == "Chưa có Gemini API key":
            if not self._prompt_for_api_key():
                text = "Chưa có Gemini API key"
            else:
                self.handle_hotkey()
                return
        if self.overlay is None or not self.overlay.isVisible():
            self.overlay = AnswerOverlay(text)
        self.overlay.show_message(text)

    def _prompt_for_api_key(self) -> bool:
        api_key, ok = QInputDialog.getText(None, "ViTai", "Nhập Gemini API key:")
        api_key = api_key.strip()
        if not ok or not api_key:
            return False
        self.config = replace(self.config, gemini_api_key=api_key)
        save_config(self.config_path, self.config)
        return True

    def run(self) -> int:
        self.hotkey_manager.start()
        return self.qt_app.exec()

    def quit(self) -> None:
        self.hotkey_manager.stop()
        self.tray.hide()
        self.qt_app.quit()


def main() -> int:
    app = ViTaiApp()
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run import smoke check**

Run:

```bash
PYTHONPATH=src python - <<'PY'
from vitai.main import ViTaiApp, main
print(ViTaiApp, main)
PY
```

Expected: exits 0.

- [ ] **Step 3: Run unit tests**

Run:

```bash
PYTHONPATH=src pytest tests -v
```

Expected: all tests pass.

- [ ] **Step 4: Manual E2E smoke test**

Run:

```bash
PYTHONPATH=src python -m vitai.main
```

Expected:
- Tray icon visible.
- Select text in Notepad, press Alt+Q.
- If API key absent, dialog asks for key and saves config.
- General question shows short answer.
- MCQ selection shows `Đáp án: X`.
- No selected text shows `Không tìm thấy text bôi đen`.
- Escape closes overlay.
- Clipboard restores after capture.

---

## Task 8: Build Script and Packaging

**Files:**
- Create: `scripts/build_windows.py`

**Prompt for another session:**

```text
Implement Task 8 from d:\ViTai\docs\superpowers\plans\2026-05-27-vitai-roadmap.md. Add simplified PyInstaller build script for ViTai. Run build if dependencies are installed, then smoke test dist/ViTai/ViTai.exe if possible.
```

- [ ] **Step 1: Implement build script**

Write `scripts/build_windows.py`:

```python
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        "ViTai",
        "--icon",
        str(root / "assets" / "icon.ico"),
        "--add-data",
        f"{root / 'assets' / 'icon.ico'};assets",
        "--paths",
        str(root / "src"),
        str(root / "src" / "vitai" / "main.py"),
    ]
    if (root / "assets" / "logo.png").exists():
        command[command.index("--paths"):command.index("--paths")] = [
            "--add-data",
            f"{root / 'assets' / 'logo.png'};assets",
        ]
    return subprocess.call(command, cwd=root)


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run build script help smoke**

Run:

```bash
python scripts/build_windows.py
```

Expected: creates `dist/ViTai/ViTai.exe` if PyInstaller installed; if missing, install `pyinstaller` or add it to dev requirements before retrying.

- [ ] **Step 3: Manual packaged app test**

Run:

```bash
dist/ViTai/ViTai.exe
```

Expected: same E2E behavior as Task 7.

---

## Task 9: README and Final Smoke Checklist

**Files:**
- Create: `README.md`

**Prompt for another session:**

```text
Implement Task 9 from d:\ViTai\docs\superpowers\plans\2026-05-27-vitai-roadmap.md. Add README with setup, API key, dev run, build, and smoke test checklist. Run full test suite and report remaining blockers.
```

- [ ] **Step 1: Write README**

Write `README.md`:

```markdown
# ViTai

Windows system tray assistant. Select text anywhere, press `Alt+Q`, get short academic answer in a small overlay near cursor.

## Features

- Global `Alt+Q` hotkey
- Selected text capture through clipboard
- Gemini API answer generation
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

3. Put Gemini key in `.env`:

```text
GEMINI_API_KEY=your_key_here
```

Get a Gemini API key from Google AI Studio.

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

Install PyInstaller if needed:

```bash
.venv/Scripts/python -m pip install pyinstaller
```

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
- Use bad API key: overlay shows API error.
- Press `Escape`: overlay closes.
- Clipboard content before `Alt+Q` remains restored after capture.
```

- [ ] **Step 2: Run full tests**

Run:

```bash
PYTHONPATH=src pytest tests -v
```

Expected: all tests pass.

- [ ] **Step 3: Run dev smoke**

Run:

```bash
PYTHONPATH=src python -m vitai.main
```

Expected: manual checklist in README passes.

---

## Final Self-Review Checklist

- [ ] Roadmap Section 0 reusable ViTrans resources covered by Tasks 1, 7, 8.
- [ ] Roadmap Section 2 MVP features covered by Tasks 3, 4, 5, 6, 7.
- [ ] Roadmap Section 4 stack covered by requirements and modules.
- [ ] Roadmap Section 5 flow covered by Task 7.
- [ ] Roadmap Section 7 prompts covered by Task 4.
- [ ] Roadmap Section 8 MCQ detection covered by Task 3.
- [ ] Roadmap Section 9 folder structure covered across tasks.
- [ ] Roadmap Section 11 smoke tests covered by Tasks 7 and 9.
- [ ] Roadmap Section 12 packaging covered by Task 8.
- [ ] Non-goals avoided: no settings UI, no streaming, no multi-provider, no OCR, no telemetry, no updater.

---

## Parallel Execution Assignment

| Wave | Can run in parallel | Depends on | Output |
|---|---|---|---|
| 1 | Task 1 | None | Base package, utilities, dependencies, assets |
| 2 | Task 2, Task 3, Task 4 | Task 1 | Config, MCQ, LLM modules + tests |
| 3 | Task 5, Task 6 | Task 1 | Capture and overlay modules |
| 4 | Task 7 | Tasks 2, 3, 4, 5, 6 | Runnable app |
| 5 | Task 8, Task 9 | Task 7 | Build script, packaged exe, README |

## Session Prompts Summary

| Task | Session prompt | Parallel group |
|---|---|---|
| 1 | `Implement Task 1 from d:\ViTai\docs\superpowers\plans\2026-05-27-vitai-roadmap.md. Create ViTai scaffold and copy/adapt reusable ViTrans utilities. Do not implement config/capture/LLM/main yet. Run import smoke check at end.` | Wave 1 |
| 2 | `Implement Task 2 from d:\ViTai\docs\superpowers\plans\2026-05-27-vitai-roadmap.md. Add config dataclass and tests only. Keep fields minimal. Run pytest for config tests.` | Wave 2 |
| 3 | `Implement Task 3 from d:\ViTai\docs\superpowers\plans\2026-05-27-vitai-roadmap.md. Add MCQ detection and tests only. Run pytest for MCQ tests.` | Wave 2 |
| 4 | `Implement Task 4 from d:\ViTai\docs\superpowers\plans\2026-05-27-vitai-roadmap.md. Add Gemini LLM wrapper with testable prompt routing. Do not perform real API calls in tests. Run pytest for LLM tests.` | Wave 2 |
| 5 | `Implement Task 5 from d:\ViTai\docs\superpowers\plans\2026-05-27-vitai-roadmap.md. Add Windows clipboard selected-text capture using pyperclip and ctypes SendInput. Include manual smoke command. Do not alter main app.` | Wave 3 |
| 6 | `Implement Task 6 from d:\ViTai\docs\superpowers\plans\2026-05-27-vitai-roadmap.md. Add PyQt6 topmost answer overlay with copy button, Escape close, cursor positioning, auto-close. Include manual smoke command.` | Wave 3 |
| 7 | `Implement Task 7 from d:\ViTai\docs\superpowers\plans\2026-05-27-vitai-roadmap.md. Wire QApplication, tray icon, Alt+Q hotkey, clipboard capture, MCQ detection, Gemini call, and overlay. Keep UI updates on Qt thread. Run import smoke check and dev app smoke test.` | Wave 4 |
| 8 | `Implement Task 8 from d:\ViTai\docs\superpowers\plans\2026-05-27-vitai-roadmap.md. Add simplified PyInstaller build script for ViTai. Run build if dependencies are installed, then smoke test dist/ViTai/ViTai.exe if possible.` | Wave 5 |
| 9 | `Implement Task 9 from d:\ViTai\docs\superpowers\plans\2026-05-27-vitai-roadmap.md. Add README with setup, API key, dev run, build, and smoke test checklist. Run full test suite and report remaining blockers.` | Wave 5 |
