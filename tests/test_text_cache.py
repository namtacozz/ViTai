from PIL import Image

from vitai.text_cache import FrameChangeCache, TextResultCache, normalize_texts


def test_text_cache_remembers_multiple_recent_entries():
    cache = TextResultCache(lifetime_seconds=3.0, similarity_threshold=0.90, capacity=3)

    assert cache.is_duplicate(["Hello world"], now=1.0) is False
    assert cache.is_duplicate(["Another line"], now=1.1) is False
    assert cache.is_duplicate(["Hello world!"], now=1.2) is True


def test_text_cache_expires_old_entries():
    cache = TextResultCache(lifetime_seconds=1.0, similarity_threshold=0.90, capacity=3)

    assert cache.is_duplicate(["Hello world"], now=1.0) is False
    assert cache.is_duplicate(["Hello world"], now=3.0) is False


def test_normalize_texts_collapses_spaces():
    assert normalize_texts(["  Hello   world ", "", " Again  "]) == "Hello world\nAgain"


def test_frame_change_cache_skips_identical_frames():
    cache = FrameChangeCache(threshold=0.01)
    first = Image.new("RGB", (16, 16), "black")
    second = Image.new("RGB", (16, 16), "black")

    assert cache.has_changed(first) is True
    assert cache.has_changed(second) is False


def test_frame_change_cache_allows_changed_frames():
    cache = FrameChangeCache(threshold=0.01)
    first = Image.new("RGB", (16, 16), "black")
    second = Image.new("RGB", (16, 16), "white")

    assert cache.has_changed(first) is True
    assert cache.has_changed(second) is True
