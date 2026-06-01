from vitai.models import OcrResult, Rect
from vitai.ocr import rank_ocr_results


def result(text, confidence, y=0):
    return OcrResult(text=text, confidence=confidence, bbox=Rect(x=0, y=y, width=100, height=20))


def test_rank_ocr_results_filters_low_quality_garbage():
    ranked = rank_ocr_results([
        result("@@@", 0.99),
        result("Hello world", 0.70),
        result("tiny", 0.10),
    ])

    assert [item.text for item in ranked] == ["Hello world"]


def test_rank_ocr_results_keeps_reading_order_for_good_results():
    ranked = rank_ocr_results([
        result("second", 0.90, y=30),
        result("first", 0.80, y=5),
    ])

    assert [item.text for item in ranked] == ["first", "second"]
