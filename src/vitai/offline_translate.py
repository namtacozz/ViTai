_OFFLINE_UNAVAILABLE_MESSAGE = "Offline translation is not installed"


class OfflineTranslationError(RuntimeError):
    pass


def offline_translation_available() -> bool:
    return False


def offline_translation_unavailable_message() -> str:
    return _OFFLINE_UNAVAILABLE_MESSAGE


def translate_offline(texts: list[str], target_language: str, source_language: str = "auto") -> list[str]:
    raise OfflineTranslationError(_OFFLINE_UNAVAILABLE_MESSAGE)
