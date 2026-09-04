from __future__ import annotations

import sys
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent, QMouseEvent
from PyQt6.QtWidgets import QPushButton

from vitai.hotkey import format_key_display

class HotkeyInputButton(QPushButton):
    hotkey_changed = pyqtSignal(str, str)

    def __init__(self, modifier: str = "alt", key: str = "q", parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("hotkeyButton")
        self.modifier = modifier
        self.key = key
        self.recording = False
        self._update_text()

    def set_hotkey(self, modifier: str, key: str) -> None:
        self.modifier = modifier
        self.key = key
        self._update_text()

    def _update_text(self) -> None:
        parts = self.modifier.split("+") if self.modifier and self.modifier != "none" else []
        formatted = []
        for p in parts:
            p_norm = p.strip().lower()
            if p_norm in ("win", "cmd", "super", "meta"):
                formatted.append("Win")
            elif p_norm in ("alt", "opt", "option"):
                formatted.append("Alt")
            elif p_norm in ("ctrl", "control"):
                formatted.append("Ctrl")
            elif p_norm in ("shift",):
                formatted.append("Shift")
            elif p.strip():
                formatted.append(p.strip().capitalize())

        key_disp = format_key_display(self.key)
        disp = "+".join(formatted) + f"+{key_disp}" if formatted else key_disp
        self.setText(f"{disp}  (Nhấn để đổi)")

    def _start_recording(self) -> None:
        self.recording = True
        self.setText("Nhấn phím hoặc click chuột...")
        self.grabKeyboard()
        self.grabMouse()

    def mousePressEvent(self, e: QMouseEvent | None) -> None:
        if not e:
            return

        if not self.recording:
            self._start_recording()
            return

        modifiers = []
        if e.modifiers() & Qt.KeyboardModifier.MetaModifier:
            modifiers.append("win")
        if e.modifiers() & Qt.KeyboardModifier.ControlModifier:
            modifiers.append("ctrl")
        if e.modifiers() & Qt.KeyboardModifier.AltModifier:
            modifiers.append("alt")
        if e.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            modifiers.append("shift")

        btn = e.button()
        key_name = ""
        if btn == Qt.MouseButton.RightButton:
            key_name = "mouse_right"
        elif btn == Qt.MouseButton.MiddleButton:
            key_name = "mouse_middle"
        elif btn == Qt.MouseButton.BackButton:
            key_name = "mouse_x1"
        elif btn == Qt.MouseButton.ForwardButton:
            key_name = "mouse_x2"
        elif btn == Qt.MouseButton.LeftButton and modifiers:
            key_name = "mouse_left"
        elif btn == Qt.MouseButton.LeftButton and not modifiers:
            self.recording = False
            self.releaseKeyboard()
            self.releaseMouse()
            self._show_quick_choice_menu()
            return

        if key_name:
            self.modifier = "+".join(modifiers) if modifiers else "none"
            self.key = key_name
            self.recording = False
            self.releaseKeyboard()
            self.releaseMouse()
            self._update_text()
            self.hotkey_changed.emit(self.modifier, self.key)

    def _show_quick_choice_menu(self) -> None:
        menu = QMenu(self)
        presets = [
            ("Chuột Phải", "none", "mouse_right"),
            ("Chuột Giữa", "none", "mouse_middle"),
            ("Nút Chuột Phụ 1 (Back)", "none", "mouse_x1"),
            ("Nút Chuột Phụ 2 (Forward)", "none", "mouse_x2"),
            ("Alt + Chuột Phải", "alt", "mouse_right"),
            ("Ctrl + Chuột Phải", "ctrl", "mouse_right"),
            ("Shift + Chuột Phải", "shift", "mouse_right"),
            ("Win + Chuột Phải", "win", "mouse_right"),
        ]
        for label, mod, k in presets:
            action = menu.addAction(label)
            if action is not None:
                action.triggered.connect(lambda _, m=mod, key_val=k: self._apply_hotkey_from_menu(m, key_val))
        menu.exec(self.mapToGlobal(self.rect().bottomLeft()))
        self._update_text()

    def _apply_hotkey_from_menu(self, modifier: str, key: str) -> None:
        self.modifier = modifier
        self.key = key
        self._update_text()
        self.hotkey_changed.emit(self.modifier, self.key)

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if not a0:
            return
        if not self.recording:
            super().keyPressEvent(a0)
            return

        key_code = a0.key()
        if key_code == Qt.Key.Key_Escape:
            self.recording = False
            self.releaseKeyboard()
            self.releaseMouse()
            self._update_text()
            return

        if key_code in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta):
            return

        modifiers = []
        if a0.modifiers() & Qt.KeyboardModifier.MetaModifier:
            modifiers.append("win")
        if a0.modifiers() & Qt.KeyboardModifier.ControlModifier:
            modifiers.append("ctrl")
        if a0.modifiers() & Qt.KeyboardModifier.AltModifier:
            modifiers.append("alt")
        if a0.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            modifiers.append("shift")

        if not modifiers:
            modifiers.append("alt")

        if 65 <= key_code <= 90:
            key_char = chr(key_code).lower()
        elif Qt.Key.Key_0 <= key_code <= Qt.Key.Key_9:
            key_char = chr(key_code)
        elif Qt.Key.Key_F1 <= key_code <= Qt.Key.Key_F12:
            key_char = f"f{key_code - Qt.Key.Key_F1 + 1}"
        elif key_code == Qt.Key.Key_Space:
            key_char = "space"
        else:
            text = a0.text().lower()
            if text and text.isalnum():
                key_char = text
            else:
                key_char = "q"

        self.modifier = "+".join(modifiers)
        self.key = key_char
        self.recording = False
        self.releaseKeyboard()
        self.releaseMouse()
        self._update_text()
        self.hotkey_changed.emit(self.modifier, self.key)


