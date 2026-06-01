from collections import deque
from dataclasses import dataclass
from difflib import SequenceMatcher
import re
import time

from PIL import Image, ImageChops


@dataclass
class _CacheEntry:
    normalized_text: str
    timestamp: float


def normalize_texts(texts: list[str]) -> str:
    cleaned = []
    for text in texts:
        normalized = re.sub(r"\s+", " ", text.strip())
        if normalized:
            cleaned.append(normalized)
    return "\n".join(cleaned)


class TextResultCache:
    def __init__(
        self,
        lifetime_seconds: float = 3.0,
        similarity_threshold: float = 0.90,
        capacity: int = 20,
    ) -> None:
        self.lifetime_seconds = lifetime_seconds
        self.similarity_threshold = similarity_threshold
        self.capacity = capacity
        self._entries: deque[_CacheEntry] = deque(maxlen=capacity)

    def is_duplicate(self, texts: list[str], now: float | None = None) -> bool:
        current_time = time.monotonic() if now is None else now
        normalized_text = normalize_texts(texts)

        if not normalized_text:
            self.clear()
            return False

        self._expire(current_time)
        is_duplicate = any(self._is_similar(entry.normalized_text, normalized_text) for entry in self._entries)
        self._entries.append(_CacheEntry(normalized_text=normalized_text, timestamp=current_time))
        return is_duplicate

    def clear(self) -> None:
        self._entries.clear()

    def _expire(self, current_time: float) -> None:
        while self._entries and current_time - self._entries[0].timestamp > self.lifetime_seconds:
            self._entries.popleft()

    def _is_similar(self, previous: str, current: str) -> bool:
        if previous == current:
            return True
        return SequenceMatcher(None, previous, current).ratio() >= self.similarity_threshold


class FrameChangeCache:
    def __init__(self, threshold: float = 0.003, sample_size: tuple[int, int] = (64, 64)) -> None:
        self.threshold = threshold
        self.sample_size = sample_size
        self._last_frame: Image.Image | None = None

    def has_changed(self, image: Image.Image) -> bool:
        current = image.convert("L").resize(self.sample_size)
        if self._last_frame is None:
            self._last_frame = current
            return True

        diff = ImageChops.difference(self._last_frame, current)
        histogram = diff.histogram()
        pixels = current.width * current.height
        total_delta = sum(value * count for value, count in enumerate(histogram))
        change_ratio = total_delta / (pixels * 255)
        self._last_frame = current
        return change_ratio >= self.threshold

    def clear(self) -> None:
        self._last_frame = None
