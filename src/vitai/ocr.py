from functools import lru_cache
import importlib.util
import logging
import re
import sys

from vitai.encoding import configure_utf8_stdio

configure_utf8_stdio()

import numpy as np
from PIL import Image

from vitai.models import OcrResult, Rect

_LOGGER = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_reader() -> 'easyocr.Reader':
    import easyocr
    return easyocr.Reader(["en"], gpu=False)


def warm_up_reader() -> None:
    get_reader()


def ocr_provider_available(provider_id: str) -> bool:
    if provider_id == "easyocr":
        return True
    if provider_id == "paddleocr":
        return importlib.util.find_spec("paddleocr") is not None
    if provider_id == "windows":
        return sys.platform == "win32"
    return False


@lru_cache(maxsize=1)
def get_paddleocr_reader():
    from paddleocr import PaddleOCR

    return PaddleOCR(use_angle_cls=True, lang="en", show_log=False)


def _bbox_to_rect(points: list[list[float]]) -> Rect:
    xs = [int(point[0]) for point in points]
    ys = [int(point[1]) for point in points]
    min_x = min(xs)
    min_y = min(ys)
    return Rect(x=min_x, y=min_y, width=max(xs) - min_x, height=max(ys) - min_y)


def read_text(image: Image.Image, min_confidence: float = 0.35, provider_id: str = "easyocr") -> list[OcrResult]:
    if provider_id == "windows":
        try:
            return rank_ocr_results(_read_windows_ocr(image, min_confidence))
        except Exception as exc:
            _LOGGER.warning("Windows OCR failed, falling back to EasyOCR: %s", exc)
    if provider_id == "paddleocr":
        try:
            return rank_ocr_results(_read_paddleocr(image, min_confidence))
        except Exception as exc:
            _LOGGER.warning("PaddleOCR failed, falling back to EasyOCR: %s", exc)
    return rank_ocr_results(_read_easyocr(image, min_confidence))


def rank_ocr_results(results: list[OcrResult]) -> list[OcrResult]:
    scored = [(result, _ocr_quality_score(result)) for result in results]
    filtered = [result for result, score in scored if score >= 0.35]
    return sorted(filtered, key=lambda result: (result.bbox.y, result.bbox.x))


def _ocr_quality_score(result: OcrResult) -> float:
    text = result.text.strip()
    if not text:
        return 0.0
    useful_chars = sum(1 for char in text if char.isalnum())
    useful_ratio = useful_chars / max(len(text), 1)
    repeated_noise = bool(re.fullmatch(r"([^\w\s])\1+", text))
    length_bonus = min(len(text) / 12, 1.0) * 0.15
    if result.confidence < 0.25:
        return 0.0
    score = (result.confidence * 0.70) + (useful_ratio * 0.30) + length_bonus
    if repeated_noise:
        score -= 0.75
    if len(text) <= 2 and useful_ratio < 1.0:
        score -= 0.35
    return score


def _read_easyocr(image: Image.Image, min_confidence: float) -> list[OcrResult]:
    import easyocr
    reader = get_reader()
    raw_results = reader.readtext(np.array(image))
    results: list[OcrResult] = []
    for points, text, confidence in raw_results:
        clean_text = text.strip()
        if not clean_text or confidence < min_confidence:
            continue
        results.append(OcrResult(text=clean_text, confidence=float(confidence), bbox=_bbox_to_rect(points)))
    return results


def _read_paddleocr(image: Image.Image, min_confidence: float) -> list[OcrResult]:
    ocr = get_paddleocr_reader()
    raw = ocr.ocr(np.array(image), cls=True)
    results: list[OcrResult] = []
    for page in raw or []:
        for item in page or []:
            points, payload = item
            text, confidence = payload
            clean_text = str(text).strip()
            if not clean_text or float(confidence) < min_confidence:
                continue
            results.append(OcrResult(text=clean_text, confidence=float(confidence), bbox=_bbox_to_rect(points)))
    return results


def _read_windows_ocr(image: Image.Image, min_confidence: float) -> list[OcrResult]:
    raise RuntimeError("Windows OCR runtime bridge is not installed")
