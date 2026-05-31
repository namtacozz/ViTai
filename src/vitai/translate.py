from __future__ import annotations

import os
import time
from typing import Protocol

from deep_translator import GoogleTranslator

from vitai.transtyle import TranstyleProfile, apply_postprocess, apply_preprocess, find_exact_correction, get_profile


class TranslationError(RuntimeError):
    pass


class TranslatorProvider(Protocol):
    id: str
    display_name: str

    def translate_batch(
        self,
        texts: list[str],
        target_language: str,
        source_language: str,
        api_key: str = "",
    ) -> list[str]:
        ...


class GoogleTranslatorProvider:
    id = "google"
    display_name = "Google Translate"

    def translate_batch(
        self,
        texts: list[str],
        target_language: str,
        source_language: str,
        api_key: str = "",
    ) -> list[str]:
        translator = GoogleTranslator(source=source_language, target=target_language)
        return translator.translate_batch(texts)


class DeepLTranslatorProvider:
    id = "deepl"
    display_name = "DeepL"

    def translate_batch(
        self,
        texts: list[str],
        target_language: str,
        source_language: str,
        api_key: str = "",
    ) -> list[str]:
        key = api_key or os.environ.get("VITRANS_DEEPL_API_KEY", "")
        if not key:
            raise TranslationError("DeepL API key is missing")
        try:
            from deep_translator import DeeplTranslator
        except ImportError as exc:
            raise TranslationError("DeepL translator is unavailable") from exc
        translator = DeeplTranslator(api_key=key, source=source_language, target=target_language)
        return translator.translate_batch(texts)


_PROVIDERS: dict[str, TranslatorProvider] = {
    "google": GoogleTranslatorProvider(),
    "deepl": DeepLTranslatorProvider(),
}

_TRANSLATION_CACHE: dict[tuple[str, str, str, str, int, str], str] = {}


def clear_translation_cache() -> None:
    _TRANSLATION_CACHE.clear()


def translate_texts(
    texts: list[str],
    target_language: str = "vi",
    source_language: str = "auto",
    attempts: int = 3,
    profile: TranstyleProfile | None = None,
    provider_id: str = "google",
    deepl_api_key: str = "",
    failover_enabled: bool = True,
) -> list[str]:
    if not texts:
        return []

    active_profile = profile or get_profile("standard", {})
    results: dict[str, str] = {}
    missing_texts: list[str] = []
    preprocessed_by_original: dict[str, str] = {}

    for text in dict.fromkeys(texts):
        corrected = find_exact_correction(active_profile, source_language, target_language, text)
        if corrected is not None:
            results[text] = corrected
            continue
        cache_key = _cache_key(provider_id, target_language, source_language, active_profile, text)
        if cache_key in _TRANSLATION_CACHE:
            results[text] = _TRANSLATION_CACHE[cache_key]
            continue
        preprocessed = apply_preprocess(active_profile, text)
        preprocessed_by_original[text] = preprocessed
        missing_texts.append(text)

    if missing_texts:
        translated = _translate_missing_texts(
            [preprocessed_by_original[text] for text in missing_texts],
            target_language,
            source_language,
            attempts,
            active_profile,
            provider_id,
            deepl_api_key,
            failover_enabled,
        )
        for original in missing_texts:
            translated_text = translated[preprocessed_by_original[original]]
            processed = apply_postprocess(active_profile, translated_text)
            _TRANSLATION_CACHE[_cache_key(provider_id, target_language, source_language, active_profile, original)] = processed
            results[original] = processed

    return [results[text] for text in texts]


def _cache_key(
    provider_id: str,
    target_language: str,
    source_language: str,
    profile: TranstyleProfile,
    text: str,
) -> tuple[str, str, str, str, int, str]:
    return (provider_id, target_language, source_language, profile.id, profile.version, text)


def _translate_missing_texts(
    texts: list[str],
    target_language: str,
    source_language: str,
    attempts: int,
    profile: TranstyleProfile,
    provider_id: str = "google",
    deepl_api_key: str = "",
    failover_enabled: bool = True,
) -> dict[str, str]:
    provider = _provider_for_id(provider_id)
    try:
        return _translate_with_provider(provider, texts, target_language, source_language, attempts, deepl_api_key)
    except Exception as exc:
        if provider_id != "google" and failover_enabled:
            google_provider = _provider_for_id("google")
            return _translate_with_provider(google_provider, texts, target_language, source_language, attempts, "")
        if isinstance(exc, TranslationError):
            raise
        raise TranslationError(f"{provider.display_name} failed: {exc}") from exc


def _provider_for_id(provider_id: str) -> TranslatorProvider:
    provider = _PROVIDERS.get(provider_id)
    if provider is None:
        raise TranslationError(f"Unknown translator provider: {provider_id}")
    return provider


def _translate_with_provider(
    provider: TranslatorProvider,
    texts: list[str],
    target_language: str,
    source_language: str,
    attempts: int,
    api_key: str,
) -> dict[str, str]:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            translations = provider.translate_batch(texts, target_language, source_language, api_key)
            if len(translations) != len(texts):
                raise TranslationError(
                    f"Translation batch returned {len(translations)} items for {len(texts)} inputs"
                )
            return dict(zip(texts, translations, strict=True))
        except TranslationError:
            raise
        except Exception as exc:
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(0.25 * (2 ** attempt))

    raise TranslationError(f"{provider.display_name} failed: {last_error}")
