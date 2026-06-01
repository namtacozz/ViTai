from vitai import translate
from vitai.transtyle import get_profile


class CountingProvider:
    id = "counting"
    display_name = "Counting"

    def __init__(self):
        self.calls = 0

    def translate_batch(self, texts, target_language, source_language, api_key=""):
        self.calls += 1
        return [f"vi:{text}" for text in texts]


def test_translate_texts_uses_memory_for_repeated_text(monkeypatch):
    provider = CountingProvider()
    monkeypatch.setitem(translate._PROVIDERS, "counting", provider)
    translate.clear_translation_cache()

    first = translate.translate_texts(["Hello"], provider_id="counting", profile=get_profile("standard", {}))
    second = translate.translate_texts(["Hello"], provider_id="counting", profile=get_profile("standard", {}))

    assert first == ["vi:Hello"]
    assert second == ["vi:Hello"]
    assert provider.calls == 1


def test_translation_memory_is_bounded(monkeypatch):
    provider = CountingProvider()
    monkeypatch.setitem(translate._PROVIDERS, "counting", provider)
    translate.clear_translation_cache(max_size=2)

    translate.translate_texts(["one"], provider_id="counting")
    translate.translate_texts(["two"], provider_id="counting")
    translate.translate_texts(["three"], provider_id="counting")

    assert len(translate._TRANSLATION_CACHE) == 2
    assert all(key[-1] != "one" for key in translate._TRANSLATION_CACHE)
