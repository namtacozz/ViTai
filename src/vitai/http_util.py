from __future__ import annotations

import ssl
import urllib.error
import urllib.request
from typing import Any


def get_safe_ssl_context() -> ssl.SSLContext:
    """Tạo SSL Context an toàn, tự động nạp certifi bundle nếu có."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        pass

    try:
        return ssl.create_default_context()
    except Exception:
        return ssl._create_unverified_context()


def safe_urlopen(req: urllib.request.Request | str, timeout: float = 10.0, **kwargs: Any) -> Any:
    """Mở URL an toàn, tự động thử lại với unverified context nếu gặp lỗi SSL CERTIFICATE_VERIFY_FAILED."""
    ctx = kwargs.pop("context", None) or get_safe_ssl_context()
    try:
        return urllib.request.urlopen(req, timeout=timeout, context=ctx, **kwargs)
    except (ssl.SSLError, urllib.error.URLError) as exc:
        err_str = str(exc)
        if "CERTIFICATE_VERIFY_FAILED" in err_str or isinstance(exc, ssl.SSLError):
            unverified_ctx = ssl._create_unverified_context()
            return urllib.request.urlopen(req, timeout=timeout, context=unverified_ctx, **kwargs)
        raise
