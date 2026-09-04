import colorsys
import math
import re
from typing import Optional

from PyQt6.QtCore import QPoint, QPointF, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QConicalGradient,
    QImage,
    QMouseEvent,
    QPainter,
    QPen,
    QRadialGradient,
)
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


def hsv_to_rgb(h: float, s: float, v: float) -> tuple[int, int, int]:
    """Chuyển đổi HSV (h: 0-360, s: 0-1, v: 0-1) sang RGB (0-255)."""
    h_norm = (h % 360) / 360.0
    r, g, b = colorsys.hsv_to_rgb(h_norm, max(0.0, min(1.0, s)), max(0.0, min(1.0, v)))
    return round(r * 255), round(g * 255), round(b * 255)


def rgb_to_hsv(r: int, g: int, b: int) -> tuple[float, float, float]:
    """Chuyển đổi RGB (0-255) sang HSV (h: 0-360, s: 0-1, v: 0-1)."""
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    return h * 360.0, s, v


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Chuyển đổi RGB sang chuỗi HEX (#RRGGBB)."""
    return f"#{max(0, min(255, r)):02X}{max(0, min(255, g)):02X}{max(0, min(255, b)):02X}"


def extract_hex(text: str | None, default: str = "#E09F5E") -> str:
    """Trích xuất mã màu HEX hợp lệ từ chuỗi văn bản."""
    if not text:
        return default
    m = re.search(r"#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})", text.strip())
    if m:
        return m.group(0).upper()
    return default


class QColorWheelWidget(QWidget):
    """Widget đĩa màu tròn (Hue 360° x Saturation 0-100%) chuẩn Photoshop/Aseprite."""

    color_changed = pyqtSignal(QColor)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setMinimumSize(180, 180)
        self._hue = 30.0  # 0 - 360
        self._sat = 0.8   # 0.0 - 1.0
        self._val = 0.95  # 0.0 - 1.0
        self._wheel_image: Optional[QImage] = None
        self._is_dragging = False

    def set_hsv(self, h: float, s: float, v: float) -> None:
        self._hue = max(0.0, min(360.0, h))
        self._sat = max(0.0, min(1.0, s))
        self._val = max(0.0, min(1.0, v))
        self._wheel_image = None
        self.update()

    def set_value(self, v: float) -> None:
        self._val = max(0.0, min(1.0, v))
        self._wheel_image = None
        self.update()

    def get_color(self) -> QColor:
        color = QColor()
        h_int = int(self._hue) % 360
        s_int = int(self._sat * 255)
        v_int = int(self._val * 255)
        color.setHsv(h_int, s_int, v_int)
        return color

    def resizeEvent(self, a0) -> None:
        self._wheel_image = None
        super().resizeEvent(a0)

    def _generate_wheel_image(self, size: int) -> QImage:
        img = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
        img.fill(Qt.GlobalColor.transparent)

        radius = size / 2.0
        center = QPointF(radius, radius)

        p = QPainter(img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. Vẽ Hue bằng Conical Gradient siêu tốc native C++
        conical = QConicalGradient(center, 0.0)
        steps = 24
        for i in range(steps + 1):
            pos = i / steps
            hue_angle = i * (360.0 / steps)
            color = QColor.fromHsvF(hue_angle / 360.0, 1.0, self._val)
            conical.setColorAt(pos, color)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(conical))
        p.drawEllipse(center, radius, radius)

        # 2. Phủ Saturation bằng Radial Gradient (tâm hòa sắc bão hòa 0%)
        radial = QRadialGradient(center, radius)
        center_color = QColor.fromHsvF(0.0, 0.0, self._val, 1.0)
        edge_color = QColor.fromHsvF(0.0, 0.0, self._val, 0.0)
        radial.setColorAt(0.0, center_color)
        radial.setColorAt(1.0, edge_color)

        p.setBrush(QBrush(radial))
        p.drawEllipse(center, radius, radius)
        p.end()

        return img

    def paintEvent(self, a0) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        size = min(w, h) - 12
        if size < 20:
            return

        cx = w / 2.0
        cy = h / 2.0
        radius = size / 2.0

        if self._wheel_image is None or self._wheel_image.width() != size:
            self._wheel_image = self._generate_wheel_image(size)

        # Vẽ đĩa màu
        painter.drawImage(int(cx - radius), int(cy - radius), self._wheel_image)

        # Viền ngoài thanh thoát
        painter.setPen(QPen(QColor(255, 255, 255, 60), 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QRectF(cx - radius, cy - radius, size, size))

        # Tính vị trí con trỏ reticle (H, S)
        angle_rad = math.radians(self._hue)
        dist = self._sat * radius
        cursor_x = cx + dist * math.cos(angle_rad)
        cursor_y = cy + dist * math.sin(angle_rad)

        # Vẽ con trỏ tròn Reticle tương phản cao
        painter.setPen(QPen(QColor("#0C0D0E"), 2.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(cursor_x, cursor_y), 6, 6)

        painter.setPen(QPen(QColor("#FFFFFF"), 1.5))
        painter.drawEllipse(QPointF(cursor_x, cursor_y), 6, 6)

    def mousePressEvent(self, a0: QMouseEvent | None) -> None:
        if a0 and a0.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._update_from_pos(a0.position().x(), a0.position().y())

    def mouseMoveEvent(self, a0: QMouseEvent | None) -> None:
        if a0 and self._is_dragging:
            self._update_from_pos(a0.position().x(), a0.position().y())

    def mouseReleaseEvent(self, a0: QMouseEvent | None) -> None:
        if a0 and a0.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = False

    def _update_from_pos(self, x: float, y: float) -> None:
        w = self.width()
        h = self.height()
        size = min(w, h) - 12
        radius = size / 2.0
        cx = w / 2.0
        cy = h / 2.0

        dx = x - cx
        dy = y - cy
        dist = math.hypot(dx, dy)

        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        if angle_deg < 0:
            angle_deg += 360.0

        self._hue = angle_deg
        self._sat = min(1.0, max(0.0, dist / radius))
        self.update()
        self.color_changed.emit(self.get_color())


class CircularColorPickerDialog(QDialog):
    """Hộp thoại bảng màu phổ hình tròn cao cấp (Photoshop/Aseprite style)."""

    def __init__(self, initial_color: str = "#E09F5E", theme: str = "dark", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Bảng Chọn Màu Phổ Hình Tròn")
        self.setFixedSize(480, 420)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        qcolor = QColor(initial_color)
        if not qcolor.isValid():
            qcolor = QColor("#E09F5E")
        self.current_color = qcolor

        self._build_ui()
        self._set_color_internal(self.current_color)

    def _build_ui(self) -> None:
        self.setStyleSheet(
            """
            QDialog {
                background-color: #121316;
                color: #EDEDED;
                border-radius: 12px;
            }
            QLabel {
                color: #A1A1AA;
                font-size: 12px;
                font-weight: 500;
            }
            QLineEdit, QSpinBox {
                background-color: #1E1F24;
                color: #FFFFFF;
                border: 1px solid #2F3138;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 12px;
            }
            QLineEdit:focus, QSpinBox:focus {
                border: 1px solid #E09F5E;
            }
            QPushButton#btnPreset {
                border-radius: 5px;
                border: 1px solid #3F3F46;
            }
            QPushButton#btnPreset:hover {
                border: 2px solid #FFFFFF;
            }
            QPushButton#btnOk {
                background-color: #E09F5E;
                color: #0C0D0E;
                font-weight: 700;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                border: none;
            }
            QPushButton#btnOk:hover {
                background-color: #F0AF6E;
            }
            QPushButton#btnCancel {
                background-color: #27272A;
                color: #A1A1AA;
                font-weight: 600;
                border-radius: 6px;
                padding: 8px 14px;
                font-size: 13px;
                border: 1px solid #3F3F46;
            }
            QPushButton#btnCancel:hover {
                background-color: #3F3F46;
                color: #FFFFFF;
            }
            QSlider::groove:vertical {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFFFF, stop:1 #000000);
                width: 14px;
                border-radius: 7px;
            }
            QSlider::handle:vertical {
                background: #E09F5E;
                border: 2px solid #FFFFFF;
                height: 14px;
                margin: -2px -4px;
                border-radius: 7px;
            }
            """
        )

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(14)

        # Header Title
        title_label = QLabel("BẢNG PHỔ MÀU ĐÁP ÁN (360° WHEEL)")
        title_label.setStyleSheet("font-size: 13px; font-weight: 800; color: #E09F5E; letter-spacing: 0.5px;")
        main_layout.addWidget(title_label)

        # Body: Color Wheel (Left) + Value Slider (Mid) + Controls (Right)
        body_layout = QHBoxLayout()
        body_layout.setSpacing(14)

        # 1. Color Wheel
        self.wheel = QColorWheelWidget(self)
        self.wheel.color_changed.connect(self._on_wheel_changed)
        body_layout.addWidget(self.wheel, 1)

        # 2. Value/Brightness Slider
        val_layout = QVBoxLayout()
        val_layout.setSpacing(4)
        lbl_v = QLabel("Sáng")
        lbl_v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.val_slider = QSlider(Qt.Orientation.Vertical)
        self.val_slider.setRange(0, 100)
        self.val_slider.setValue(95)
        self.val_slider.valueChanged.connect(self._on_val_slider_changed)
        val_layout.addWidget(lbl_v)
        val_layout.addWidget(self.val_slider, 1)
        body_layout.addLayout(val_layout)

        # 3. Numeric inputs & Swatch
        ctrl_layout = QVBoxLayout()
        ctrl_layout.setSpacing(8)

        # Live Swatch
        self.swatch_preview = QLabel()
        self.swatch_preview.setFixedHeight(46)
        self.swatch_preview.setStyleSheet(
            "background-color: #E09F5E; border: 1px solid #3F3F46; border-radius: 8px;"
        )
        ctrl_layout.addWidget(self.swatch_preview)

        # HEX Code Input
        hex_row = QHBoxLayout()
        hex_row.setSpacing(6)
        hex_row.addWidget(QLabel("HEX:"))
        self.hex_edit = QLineEdit("#E09F5E")
        self.hex_edit.textEdited.connect(self._on_hex_edited)
        hex_row.addWidget(self.hex_edit)
        ctrl_layout.addLayout(hex_row)

        # RGB SpinBoxes
        rgb_grid = QGridLayout()
        rgb_grid.setSpacing(6)

        rgb_grid.addWidget(QLabel("R:"), 0, 0)
        self.spin_r = QSpinBox()
        self.spin_r.setRange(0, 255)
        self.spin_r.valueChanged.connect(self._on_rgb_spin_changed)
        rgb_grid.addWidget(self.spin_r, 0, 1)

        rgb_grid.addWidget(QLabel("G:"), 1, 0)
        self.spin_g = QSpinBox()
        self.spin_g.setRange(0, 255)
        self.spin_g.valueChanged.connect(self._on_rgb_spin_changed)
        rgb_grid.addWidget(self.spin_g, 1, 1)

        rgb_grid.addWidget(QLabel("B:"), 2, 0)
        self.spin_b = QSpinBox()
        self.spin_b.setRange(0, 255)
        self.spin_b.valueChanged.connect(self._on_rgb_spin_changed)
        rgb_grid.addWidget(self.spin_b, 2, 1)

        ctrl_layout.addLayout(rgb_grid)
        ctrl_layout.addStretch()
        body_layout.addLayout(ctrl_layout)

        main_layout.addLayout(body_layout, 1)

        # Quick Preset Swatches
        presets_layout = QHBoxLayout()
        presets_layout.setSpacing(6)
        presets_label = QLabel("Nhanh:")
        presets_layout.addWidget(presets_label)

        PRESETS = [
            ("#E09F5E", "Warm Amber"),
            ("#F59E0B", "Cyber Gold"),
            ("#00F0FF", "Neon Cyan"),
            ("#10B981", "Emerald Green"),
            ("#A855F7", "Purple Glow"),
            ("#EF4444", "Crimson Red"),
            ("#38BDF8", "Sky Blue"),
            ("#FFFFFF", "Pure White"),
        ]

        for hex_code, name in PRESETS:
            btn = QPushButton()
            btn.setObjectName("btnPreset")
            btn.setFixedSize(24, 24)
            btn.setToolTip(f"{name} ({hex_code})")
            btn.setStyleSheet(f"background-color: {hex_code};")
            btn.clicked.connect(lambda _, c=hex_code: self._set_color_internal(QColor(c)))
            presets_layout.addWidget(btn)

        presets_layout.addStretch()
        main_layout.addLayout(presets_layout)

        # Bottom Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        btn_cancel = QPushButton("Hủy")
        btn_cancel.setObjectName("btnCancel")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_ok = QPushButton("Áp Dụng Màu")
        btn_ok.setObjectName("btnOk")
        btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(btn_ok)

        main_layout.addLayout(btn_layout)

    def _set_color_internal(self, color: QColor) -> None:
        if not color.isValid():
            return
        self.current_color = color
        h = color.hueF()
        s = color.saturationF()
        v = color.valueF()
        if h < 0:
            h = 0.0

        self.wheel.blockSignals(True)
        self.val_slider.blockSignals(True)
        self.spin_r.blockSignals(True)
        self.spin_g.blockSignals(True)
        self.spin_b.blockSignals(True)

        self.wheel.set_hsv(h * 360.0, s, v)
        self.val_slider.setValue(int(v * 100))

        self.spin_r.setValue(color.red())
        self.spin_g.setValue(color.green())
        self.spin_b.setValue(color.blue())
        self.hex_edit.setText(color.name().upper())

        self.swatch_preview.setStyleSheet(
            f"background-color: {color.name()}; border: 1px solid #3F3F46; border-radius: 8px;"
        )

        self.wheel.blockSignals(False)
        self.val_slider.blockSignals(False)
        self.spin_r.blockSignals(False)
        self.spin_g.blockSignals(False)
        self.spin_b.blockSignals(False)

    def _on_wheel_changed(self, color: QColor) -> None:
        self.current_color = color
        self.spin_r.blockSignals(True)
        self.spin_g.blockSignals(True)
        self.spin_b.blockSignals(True)

        self.spin_r.setValue(color.red())
        self.spin_g.setValue(color.green())
        self.spin_b.setValue(color.blue())
        self.hex_edit.setText(color.name().upper())
        self.swatch_preview.setStyleSheet(
            f"background-color: {color.name()}; border: 1px solid #3F3F46; border-radius: 8px;"
        )

        self.spin_r.blockSignals(False)
        self.spin_g.blockSignals(False)
        self.spin_b.blockSignals(False)

    def _on_val_slider_changed(self, val: int) -> None:
        v_float = val / 100.0
        self.wheel.set_value(v_float)
        self._on_wheel_changed(self.wheel.get_color())

    def _on_rgb_spin_changed(self) -> None:
        r = self.spin_r.value()
        g = self.spin_g.value()
        b = self.spin_b.value()
        self._set_color_internal(QColor(r, g, b))

    def _on_hex_edited(self, text: str) -> None:
        text = text.strip()
        if not text.startswith("#"):
            text = "#" + text
        color = QColor(text)
        if color.isValid():
            self._set_color_internal(color)

    @classmethod
    def get_color_hex(cls, initial_color: str = "#E09F5E", theme: str = "dark", parent: Optional[QWidget] = None) -> Optional[str]:
        dlg = cls(initial_color=initial_color, theme=theme, parent=parent)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            return dlg.current_color.name().upper()
        return None
