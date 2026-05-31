from dataclasses import dataclass
from difflib import SequenceMatcher
import time


@dataclass
class _CacheEntry:
    normalized_text: str
    timestamp: float


def normalize_texts(texts: list[str]) -> str:
    return "\n".join(text.strip() for text in texts if text.strip())


class TextResultCache:
    def __init__(self, lifetime_seconds: float = 3.0, similarity_threshold: float = 0.90) -> None:
        self.lifetime_seconds = lifetime_seconds
        self.similarity_threshold = similarity_threshold
        self._entry: _CacheEntry | None = None

    def is_duplicate(self, texts: list[str], now: float | None = None) -> bool:
        current_time = time.monotonic() if now is None else now
        normalized_text = normalize_texts(texts)

        if not normalized_text:
            self._entry = None
            return False

        is_duplicate = False
        if self._entry is not None:
            age = current_time - self._entry.timestamp
            if age <= self.lifetime_seconds:
                if normalized_text == self._entry.normalized_text:
                    is_duplicate = True
                else:
                    ratio = SequenceMatcher(None, self._entry.normalized_text, normalized_text).ratio()
                    is_duplicate = ratio >= self.similarity_threshold

        self._entry = _CacheEntry(normalized_text=normalized_text, timestamp=current_time)
        return is_duplicate

    def clear(self) -> None:
        self._entry = None
