from __future__ import annotations

import logging
import re
from dataclasses import asdict, dataclass, field
from typing import Literal

_LOGGER = logging.getLogger(__name__)

RegexPhase = Literal["pre", "post"]


@dataclass(frozen=True)
class RegexRule:
    id: str
    pattern: str
    replacement: str
    phase: RegexPhase
    enabled: bool = True


@dataclass(frozen=True)
class TranstyleProfile:
    id: str
    display_name: str
    enabled_rules: list[str] = field(default_factory=list)
    glossary: dict[str, str] = field(default_factory=dict)
    pronoun_rules: dict[str, str] = field(default_factory=dict)
    term_rules: dict[str, str] = field(default_factory=dict)
    regex_rules: list[RegexRule] = field(default_factory=list)
    corrections: dict[str, str] = field(default_factory=dict)
    version: int = 0


BUILTIN_PROFILE_IDS = [
    "standard",
    "science_technology",
    "xianxia_chinese_novel",
    "anime_manga",
    "custom",
]

_BUILTIN_PROFILES = {
    "standard": TranstyleProfile(id="standard", display_name="Standard"),
    "science_technology": TranstyleProfile(
        id="science_technology",
        display_name="Science & Technology",
        enabled_rules=["preserve_technical_tokens"],
    ),
    "xianxia_chinese_novel": TranstyleProfile(
        id="xianxia_chinese_novel",
        display_name="Xianxia / Chinese Novel",
        enabled_rules=["xianxia_pronouns"],
        pronoun_rules={"tôi": "ta", "bạn": "ngươi"},
    ),
    "anime_manga": TranstyleProfile(
        id="anime_manga",
        display_name="Anime / Manga",
        enabled_rules=["anime_terms"],
    ),
    "custom": TranstyleProfile(id="custom", display_name="Custom"),
}


def profile_choices() -> list[tuple[str, str]]:
    return [(_BUILTIN_PROFILES[profile_id].display_name, profile_id) for profile_id in BUILTIN_PROFILE_IDS]


def get_profile(profile_id: str, overrides: dict[str, TranstyleProfile]) -> TranstyleProfile:
    if profile_id not in _BUILTIN_PROFILES:
        profile_id = "standard"
    base = _BUILTIN_PROFILES[profile_id]
    override = overrides.get(profile_id)
    if override is None:
        return base
    return merge_profile(base, override)


def merge_profile(base: TranstyleProfile, override: TranstyleProfile) -> TranstyleProfile:
    enabled_rules = list(override.enabled_rules)
    override_ids = {rule.id for rule in override.regex_rules}
    merged_regex_rules = [rule for rule in base.regex_rules if rule.id not in override_ids]
    merged_regex_rules.extend(override.regex_rules)
    base_pronoun_rules = base.pronoun_rules if "xianxia_pronouns" in enabled_rules else {}
    base_term_rules = base.term_rules if base.enabled_rules and enabled_rules else {}
    return TranstyleProfile(
        id=base.id,
        display_name=base.display_name,
        enabled_rules=enabled_rules,
        glossary={**base.glossary, **override.glossary},
        pronoun_rules={**base_pronoun_rules, **override.pronoun_rules},
        term_rules={**base_term_rules, **override.term_rules},
        regex_rules=merged_regex_rules,
        corrections={**base.corrections, **override.corrections},
        version=max(base.version, override.version),
    )


def profile_to_dict(profile: TranstyleProfile) -> dict:
    return asdict(profile)


def profile_from_dict(data: dict) -> TranstyleProfile:
    regex_rules = []
    for item in data.get("regex_rules", []):
        if not isinstance(item, dict):
            continue
        if not all(k in item for k in ("id", "pattern", "replacement", "phase")):
            continue
        if item.get("phase") not in ("pre", "post"):
            continue
        try:
            rule_data = {k: item[k] for k in ("id", "pattern", "replacement", "phase")}
            rule_data["enabled"] = item.get("enabled", True)
            regex_rules.append(RegexRule(**rule_data))
        except (TypeError, ValueError):
            continue
    return TranstyleProfile(
        id=str(data.get("id", "custom")),
        display_name=str(data.get("display_name", "Custom")),
        enabled_rules=[str(item) for item in data.get("enabled_rules", [])],
        glossary={str(key): str(value) for key, value in data.get("glossary", {}).items() if key},
        pronoun_rules={str(key): str(value) for key, value in data.get("pronoun_rules", {}).items() if key},
        term_rules={str(key): str(value) for key, value in data.get("term_rules", {}).items() if key},
        regex_rules=regex_rules,
        corrections={str(key): str(value) for key, value in data.get("corrections", {}).items() if key},
        version=int(data.get("version", 0)),
    )


def normalize_text(text: str) -> str:
    return " ".join(text.split())


def correction_key(style_id: str, source_language: str, target_language: str, original_text: str) -> str:
    return "|".join([style_id, source_language, target_language, normalize_text(original_text)])


def find_exact_correction(
    profile: TranstyleProfile,
    source_language: str,
    target_language: str,
    original_text: str,
) -> str | None:
    return profile.corrections.get(correction_key(profile.id, source_language, target_language, original_text))


def save_exact_correction(
    profile: TranstyleProfile,
    source_language: str,
    target_language: str,
    original_text: str,
    correct_translation: str,
) -> TranstyleProfile:
    key = correction_key(profile.id, source_language, target_language, original_text)
    corrections = dict(profile.corrections)
    corrections[key] = correct_translation
    return TranstyleProfile(
        id=profile.id,
        display_name=profile.display_name,
        enabled_rules=list(profile.enabled_rules),
        glossary=dict(profile.glossary),
        pronoun_rules=dict(profile.pronoun_rules),
        term_rules=dict(profile.term_rules),
        regex_rules=list(profile.regex_rules),
        corrections=corrections,
        version=profile.version + 1,
    )


def apply_preprocess(profile: TranstyleProfile, text: str) -> str:
    return _apply_regex_rules(profile, text, "pre")


def apply_postprocess(profile: TranstyleProfile, text: str) -> str:
    processed = _replace_all(text, profile.glossary)
    processed = _replace_all(processed, profile.pronoun_rules)
    processed = _replace_all(processed, profile.term_rules)
    processed = _apply_regex_rules(profile, processed, "post")
    return processed


def _replace_all(text: str, replacements: dict[str, str]) -> str:
    processed = text
    for source, target in replacements.items():
        if source:
            processed = processed.replace(source, target)
    return processed


def _apply_regex_rules(profile: TranstyleProfile, text: str, phase: RegexPhase) -> str:
    processed = text
    for rule in profile.regex_rules:
        if not rule.enabled or rule.phase != phase:
            continue
        try:
            processed = re.sub(rule.pattern, rule.replacement, processed)
        except re.error:
            _LOGGER.warning("Invalid Transtyle regex rule %s", rule.id)
    return processed

