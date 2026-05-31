from __future__ import annotations

import importlib.util
import logging

from PIL import Image
from mss import mss

from vitai.models import Rect

_LOGGER = logging.getLogger(__name__)


def capture_provider_available(provider_id: str) -> bool:
    if provider_id == "mss":
        return True
    if provider_id == "dxcam":
        return importlib.util.find_spec("dxcam") is not None
    return False


def capture_rect(rect: Rect, provider_id: str = "mss") -> Image.Image:
    if provider_id == "dxcam":
        try:
            return _capture_dxcam(rect)
        except Exception as exc:
            _LOGGER.warning("DXCam capture failed, falling back to MSS: %s", exc)
    return _capture_mss(rect)


def _capture_mss(rect: Rect) -> Image.Image:
    monitor = {"left": rect.x, "top": rect.y, "width": rect.width, "height": rect.height}
    with mss() as screen_capture:
        screenshot = screen_capture.grab(monitor)
    return Image.frombytes("RGB", screenshot.size, screenshot.rgb)


def _capture_dxcam(rect: Rect) -> Image.Image:
    import dxcam

    camera = dxcam.create(output_color="RGB")
    region = (rect.x, rect.y, rect.x + rect.width, rect.y + rect.height)
    frame = camera.grab(region=region)
    if frame is None:
        raise RuntimeError("DXCam returned no frame")
    return Image.fromarray(frame, "RGB")
