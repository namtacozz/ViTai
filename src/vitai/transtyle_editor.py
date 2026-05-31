from __future__ import annotations

from PyQt6.QtWidgets import QComboBox, QDialog, QHBoxLayout, QLabel, QPushButton, QPlainTextEdit, QVBoxLayout, QWidget

from vitai.transtyle import TranstyleProfile, get_profile, profile_choices


def parse_mapping_lines(text: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key:
            parsed[key] = value
    return parsed


def serialize_mapping(mapping: dict[str, str]) -> str:
    return "\n".join(f"{key}={value}" for key, value in mapping.items())


def build_updated_profile(
    profile: TranstyleProfile,
    glossary_text: str,
    pronoun_text: str,
    term_text: str,
    corrections_text: str,
) -> TranstyleProfile:
    return TranstyleProfile(
        id=profile.id,
        display_name=profile.display_name,
        enabled_rules=list(profile.enabled_rules),
        glossary=parse_mapping_lines(glossary_text),
        pronoun_rules=parse_mapping_lines(pronoun_text),
        term_rules=parse_mapping_lines(term_text),
        regex_rules=list(profile.regex_rules),
        corrections=parse_mapping_lines(corrections_text),
        version=profile.version + 1,
    )


class TranstyleEditorDialog(QDialog):
    def __init__(self, profiles: dict[str, TranstyleProfile], default_profile_id: str, parent: QWidget | None = None):
        super().__init__(parent)
        self._profiles = profiles
        self._selected_profile: TranstyleProfile | None = None
        self.setWindowTitle("Transtyle Editor")
        self.setMinimumSize(560, 620)
        self.profile_combo = QComboBox()
        for label, profile_id in profile_choices():
            self.profile_combo.addItem(label, profile_id)
        self.glossary_edit = QPlainTextEdit()
        self.pronoun_edit = QPlainTextEdit()
        self.term_edit = QPlainTextEdit()
        self.corrections_edit = QPlainTextEdit()
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        self._build_ui()
        self._set_combo_by_data(default_profile_id)
        self.profile_combo.currentIndexChanged.connect(self._load_selected_profile)
        self.save_btn.clicked.connect(self._save)
        self.cancel_btn.clicked.connect(self.reject)
        self._load_selected_profile()

    @property
    def selected_profile(self) -> TranstyleProfile | None:
        return self._selected_profile

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        row = QHBoxLayout()
        row.addWidget(QLabel("Profile"))
        row.addWidget(self.profile_combo, 1)
        layout.addLayout(row)
        for label, editor in (
            ("Glossary: source=target", self.glossary_edit),
            ("Pronouns: source=target", self.pronoun_edit),
            ("Terms: source=target", self.term_edit),
            ("Corrections: key=translation", self.corrections_edit),
        ):
            layout.addWidget(QLabel(label))
            layout.addWidget(editor)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(self.save_btn)
        buttons.addWidget(self.cancel_btn)
        layout.addLayout(buttons)

    def _load_selected_profile(self) -> None:
        profile_id = str(self.profile_combo.currentData())
        profile = get_profile(profile_id, self._profiles)
        self.glossary_edit.setPlainText(serialize_mapping(profile.glossary))
        self.pronoun_edit.setPlainText(serialize_mapping(profile.pronoun_rules))
        self.term_edit.setPlainText(serialize_mapping(profile.term_rules))
        self.corrections_edit.setPlainText(serialize_mapping(profile.corrections))

    def _save(self) -> None:
        profile = get_profile(str(self.profile_combo.currentData()), self._profiles)
        self._selected_profile = build_updated_profile(
            profile,
            self.glossary_edit.toPlainText(),
            self.pronoun_edit.toPlainText(),
            self.term_edit.toPlainText(),
            self.corrections_edit.toPlainText(),
        )
        self.accept()

    def _set_combo_by_data(self, value: str) -> None:
        for index in range(self.profile_combo.count()):
            if self.profile_combo.itemData(index) == value:
                self.profile_combo.setCurrentIndex(index)
                return
