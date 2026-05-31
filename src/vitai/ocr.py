from functools import lru_cache
import importlib.util
import logging

from vitai.encoding import configure_utf8_stdio

configure_utf8_stdio()

import easyocr
import numpy as np
from PIL import Image

from vitai.models import OcrResult, Rect

_LOGGER = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_reader() -> easyocr.Reader:
    return easyocr.Reader(["en"], gpu=False)


def warm_up_reader() -> None:
    get_reader()


def ocr_provider_available(provider_id: str) -> bool:
    if provider_id == "easyocr":
        return True
    if provider_id == "paddleocr":
        return importlib.util.find_spec("paddleocr") is not None
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
    if provider_id == "paddleocr":
        try:
            return _read_paddleocr(image, min_confidence)
        except Exception as exc:
            _LOGGER.warning("PaddleOCR failed, falling back to EasyOCR: %s", exc)
    return _read_easyocr(image, min_confidence)


def _read_easyocr(image: Image.Image, min_confidence: float) -> list[OcrResult]:
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
