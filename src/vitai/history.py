from dataclasses import dataclass
import time


@dataclass(frozen=True)
class TranslationHistoryEntry:
    original: str
    translated: str
    timestamp: float


def _join_lines(lines: list[str]) -> str:
    return "\n".join(line.strip() for line in lines if line.strip())


class TranslationHistory:
    def __init__(self, capacity: int = 5) -> None:
        if capacity < 0:
            raise ValueError("capacity must be non-negative")
        self.capacity = capacity
        self._entries: list[TranslationHistoryEntry] = []

    @property
    def entries(self) -> list[TranslationHistoryEntry]:
        return list(self._entries)

    def add(
        self,
        originals: list[str],
        translations: list[str],
        now: float | None = None,
    ) -> TranslationHistoryEntry | None:
        original = _join_lines(originals)
        translated = _join_lines(translations)
        if not original or not translated:
            return None

        entry = TranslationHistoryEntry(
            original=original,
            translated=translated,
            timestamp=time.time() if now is None else now,
        )
        self._entries.insert(0, entry)
        del self._entries[self.capacity:]
        return entry

    def clear(self) -> None:
        self._entries.clear()
