from vitai.models import Rect


def translate_capture_bbox_to_overlay(bbox: Rect, content_origin_x: int, content_origin_y: int) -> Rect:
    return Rect(
        x=bbox.x + content_origin_x,
        y=bbox.y + content_origin_y,
        width=bbox.width,
        height=bbox.height,
    )


def content_capture_rect(overlay_rect: Rect, top_bar_height: int) -> Rect:
    return Rect(
        x=overlay_rect.x,
        y=overlay_rect.y + top_bar_height,
        width=overlay_rect.width,
        height=max(1, overlay_rect.height - top_bar_height),
    )


def font_size_for_bbox(bbox: Rect) -> int:
    return max(10, min(32, int(bbox.height * 0.85)))
