from vitai.ocr import ocr_provider_available


def test_windows_ocr_provider_is_declared_on_windows(monkeypatch):
    monkeypatch.setattr("sys.platform", "win32")

    assert ocr_provider_available("windows") is True
