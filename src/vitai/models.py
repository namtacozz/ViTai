from dataclasses import dataclass


@dataclass(frozen=True)
class Rect:
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class OcrResult:
    text: str
    confidence: float
    bbox: Rect


@dataclass(frozen=True)
class TranslatedBox:
    original: str
    translated: str
    bbox: Rect
    font_size: int
    source_language: str = "auto"
    target_language: str = "vi"
    transtyle_id: str = "standard"
