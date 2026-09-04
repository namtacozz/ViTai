from __future__ import annotations

import os
import threading
from datetime import datetime, timedelta
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame, QApplication
)
from vitai.ui.theme import get_stylesheet
from vitai.resources import resource_path
from vitai.sepay import (
    DEFAULT_BANK_ACC,
    DEFAULT_BANK_ID,
    DEFAULT_BANK_NAME,
    DEFAULT_REGISTRATION_PRICE,
    PRICE_90_DAYS,
    PRICE_LIFETIME,
    check_sepay_payment,
    generate_order_code,
    get_vietqr_url,
)
from vitai.transaction_ledger import get_transaction_ledger
from vitai.user_store import UserStore

class RegisterPaymentDialog(QDialog):
    """Hộp thoại đăng ký tài khoản tự động bằng cách quét mã VietQR (50.000đ) kết nối SePay."""

    qr_loaded_signal = pyqtSignal(bytes)
    payment_status_signal = pyqtSignal(bool, str)

    def __init__(self, user_store: UserStore, parent=None, theme: str = "dark"):
        super().__init__(parent)
        self.store = user_store
        self.theme = theme
        self.setWindowTitle("Đăng Ký Tài Khoản & Quét Mã VietQR (50.000đ)")
        self.resize(720, 520)
        self.setMinimumSize(680, 480)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.setStyleSheet(get_stylesheet(theme))

        self.order_code = generate_order_code()
        self.is_paid = False
        self.created_username = ""
        self.created_password = ""

        self.qr_loaded_signal.connect(self._on_qr_loaded)
        self.payment_status_signal.connect(self._on_payment_status)

        self._build_ui()
        self._start_qr_load()
        self._start_polling()

    def _build_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(16)

        # -----------------------------
        # CỘT TRÁI: VIETQR & NGÂN HÀNG
        # -----------------------------
        card_left = QFrame()
        card_left.setObjectName("cardFrame")
        layout_left = QVBoxLayout(card_left)
        layout_left.setContentsMargins(16, 16, 16, 16)
        layout_left.setSpacing(10)
        layout_left.setAlignment(Qt.AlignmentFlag.AlignTop)

        lbl_qr_title = QLabel("QUÉT MÃ VIETQR (50.000đ)")
        lbl_qr_title.setStyleSheet("font-size: 13px; font-weight: 800; color: #E09F5E;")
        lbl_qr_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_left.addWidget(lbl_qr_title)

        # QR Image Box
        self.qr_box = QLabel()
        self.qr_box.setFixedSize(180, 180)
        self.qr_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_box.setStyleSheet(
            "background-color: #FFFFFF; border: 2px solid rgba(224, 159, 94, 0.4); "
            "border-radius: 10px; color: #0C0D0E; font-size: 12px; font-weight: 600;"
        )
        self.qr_box.setText("Đang tạo mã QR...")
        layout_left.addWidget(self.qr_box, 0, Qt.AlignmentFlag.AlignCenter)

        # Bank Info Box
        info_box = QFrame()
        info_box.setStyleSheet(
            "background-color: rgba(224, 159, 94, 0.08); border: 1px solid rgba(224, 159, 94, 0.25); "
            "border-radius: 8px; padding: 6px;"
        )
        info_layout = QVBoxLayout(info_box)
        info_layout.setContentsMargins(6, 6, 6, 6)
        info_layout.setSpacing(4)

        lbl_bank = QLabel(f"Ngân hàng: <b>MBBank ({DEFAULT_BANK_ID})</b>")
        lbl_bank.setStyleSheet("font-size: 11px; color: " + ("#E2E8F0" if self.theme == "dark" else "#1E293B"))
        info_layout.addWidget(lbl_bank)

        lbl_owner = QLabel(f"Chủ TK: <b>{DEFAULT_BANK_NAME}</b>")
        lbl_owner.setStyleSheet("font-size: 11px; color: " + ("#E2E8F0" if self.theme == "dark" else "#1E293B"))
        info_layout.addWidget(lbl_owner)

        stk_row = QHBoxLayout()
        lbl_stk = QLabel(f"STK: <b>{DEFAULT_BANK_ACC}</b>")
        lbl_stk.setStyleSheet("font-size: 12px; font-weight: 700; color: #E09F5E;")
        stk_row.addWidget(lbl_stk)
        stk_row.addStretch()
        btn_copy_stk = QPushButton("Copy STK")
        btn_copy_stk.setFixedHeight(22)
        btn_copy_stk.setStyleSheet("font-size: 10px; padding: 2px 6px;")
        btn_copy_stk.clicked.connect(lambda: self._copy_text(DEFAULT_BANK_ACC, "Đã sao chép STK!"))
        stk_row.addWidget(btn_copy_stk)
        info_layout.addLayout(stk_row)

        lbl_amount = QLabel("Số tiền: <b>50.000 VNĐ</b>")
        lbl_amount.setStyleSheet("font-size: 12px; font-weight: 700; color: #4ADE80;")
        info_layout.addWidget(lbl_amount)

        memo_row = QHBoxLayout()
        lbl_memo = QLabel(f"Nội dung: <b>{self.order_code}</b>")
        lbl_memo.setStyleSheet("font-size: 12px; font-weight: 800; color: #38BDF8;")
        memo_row.addWidget(lbl_memo)
        memo_row.addStretch()
        btn_copy_memo = QPushButton("Copy ND")
        btn_copy_memo.setFixedHeight(22)
        btn_copy_memo.setStyleSheet("font-size: 10px; padding: 2px 6px;")
        btn_copy_memo.clicked.connect(lambda: self._copy_text(self.order_code, "Đã sao chép mã nội dung!"))
        memo_row.addWidget(btn_copy_memo)
        info_layout.addLayout(memo_row)

        layout_left.addWidget(info_box)

        lbl_note = QLabel("Lưu ý: Giữ đúng nội dung chuyển khoản để hệ thống tự động nhận diện trong 3 giây!")
        lbl_note.setStyleSheet("font-size: 10px; color: #94A3B8;")
        lbl_note.setWordWrap(True)
        layout_left.addWidget(lbl_note)

        layout_left.addStretch()
        main_layout.addWidget(card_left, 1)

        # -----------------------------
        # CỘT PHẢI: FORM ĐĂNG KÝ
        # -----------------------------
        card_right = QFrame()
        card_right.setObjectName("cardFrame")
        layout_right = QVBoxLayout(card_right)
        layout_right.setContentsMargins(18, 18, 18, 18)
        layout_right.setSpacing(10)

        lbl_form_title = QLabel("TẠO TÀI KHOẢN MỚI")
        lbl_form_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #E09F5E;")
        layout_right.addWidget(lbl_form_title)

        lbl_form_desc = QLabel(
            "Nhập tên đăng nhập & mật khẩu tùy ý của bạn (không giới hạn ký tự). "
            "Sau khi chuyển tiền, hệ thống SePay sẽ tự động kích hoạt tài khoản 24/7."
        )
        lbl_form_desc.setStyleSheet("font-size: 12px; color: #94A3B8;")
        lbl_form_desc.setWordWrap(True)
        layout_right.addWidget(lbl_form_desc)

        layout_right.addSpacing(4)

        lbl_u = QLabel("Tên đăng nhập:")
        lbl_u.setStyleSheet("font-size: 12px; font-weight: 600;")
        layout_right.addWidget(lbl_u)
        self.reg_user_input = QLineEdit()
        self.reg_user_input.setPlaceholderText("Nhập tên đăng nhập tùy ý...")
        layout_right.addWidget(self.reg_user_input)

        lbl_p = QLabel("Mật khẩu:")
        lbl_p.setStyleSheet("font-size: 12px; font-weight: 600;")
        layout_right.addWidget(lbl_p)
        self.reg_pass_input = QLineEdit()
        self.reg_pass_input.setPlaceholderText("Nhập mật khẩu...")
        self.reg_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout_right.addWidget(self.reg_pass_input)

        lbl_p2 = QLabel("Xác nhận mật khẩu:")
        lbl_p2.setStyleSheet("font-size: 12px; font-weight: 600;")
        layout_right.addWidget(lbl_p2)
        self.reg_pass2_input = QLineEdit()
        self.reg_pass2_input.setPlaceholderText("Nhập lại mật khẩu...")
        self.reg_pass2_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout_right.addWidget(self.reg_pass2_input)

        # Payment status message
        self.status_lbl = QLabel("Đang chờ bạn quét mã QR chuyển khoản...")
        self.status_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #E09F5E;")
        self.status_lbl.setWordWrap(True)
        layout_right.addWidget(self.status_lbl)

        layout_right.addStretch()

        # Action Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.btn_cancel = QPushButton("Hủy")
        self.btn_cancel.setObjectName("exitButton")
        self.btn_cancel.clicked.connect(self._on_cancel)
        btn_row.addWidget(self.btn_cancel)

        self.btn_submit = QPushButton("Kiểm Tra & Tạo Tài Khoản")
        self.btn_submit.setObjectName("saveButton")
        self.btn_submit.clicked.connect(self._on_submit)
        btn_row.addWidget(self.btn_submit)

        layout_right.addLayout(btn_row)
        main_layout.addWidget(card_right, 1)

    def _copy_text(self, text: str, toast: str) -> None:
        clip = QApplication.clipboard()
        if clip:
            clip.setText(text)
            self.status_lbl.setText(toast)
            self.status_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #38BDF8;")

    def _start_qr_load(self) -> None:
        def fetch_qr():
            raw_bytes: bytes | None = None
            try:
                import urllib.request
                url = get_vietqr_url(
                    bank_id=DEFAULT_BANK_ID,
                    account_no=DEFAULT_BANK_ACC,
                    account_name=DEFAULT_BANK_NAME,
                    amount=DEFAULT_REGISTRATION_PRICE,
                    memo=self.order_code,
                )
                req = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Accept": "image/png,image/*;q=0.8,*/*;q=0.5",
                    },
                )
                from vitai.http_util import safe_urlopen
                with safe_urlopen(req, timeout=8) as resp:
                    if resp.status == 200:
                        raw_bytes = resp.read()
            except Exception:
                pass

            if not raw_bytes:
                try:
                    fallback_p = resource_path("assets/BANKQR.jpeg")
                    if os.path.exists(fallback_p):
                        with open(fallback_p, "rb") as f:
                            raw_bytes = f.read()
                except Exception:
                    pass

            if raw_bytes:
                try:
                    self.qr_loaded_signal.emit(raw_bytes)
                except (RuntimeError, Exception):
                    pass

        t = threading.Thread(target=fetch_qr, daemon=True)
        t.start()

    def _on_qr_loaded(self, raw_bytes: bytes) -> None:
        try:
            pix = QPixmap()
            if pix.loadFromData(raw_bytes):
                self.qr_box.setPixmap(
                    pix.scaled(
                        180,
                        180,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
        except Exception:
            pass

    def _start_polling(self) -> None:
        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(3500)
        self.poll_timer.timeout.connect(self._poll_sepay)
        self.poll_timer.start()

    def _poll_sepay(self) -> None:
        if self.is_paid:
            return

        def check_bg():
            paid, msg, tx = check_sepay_payment(self.order_code, expected_amount=DEFAULT_REGISTRATION_PRICE)
            if paid:
                self.payment_status_signal.emit(True, "Đã nhận thành công 50.000đ! Sẵn sàng tạo tài khoản.")

        t = threading.Thread(target=check_bg, daemon=True)
        t.start()

    def _on_payment_status(self, paid: bool, msg: str) -> None:
        if paid:
            self.is_paid = True
            self.status_lbl.setText("✓ " + msg)
            self.status_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #4ADE80;")
            self.btn_submit.setText("Tạo Tài Khoản Ngay")

    def _on_submit(self) -> None:
        u_text = self.reg_user_input.text().strip()
        p_text = self.reg_pass_input.text()
        p2_text = self.reg_pass2_input.text()

        if not u_text:
            self.status_lbl.setText("Vui lòng nhập tên đăng nhập!")
            self.status_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #EF4444;")
            return

        if not p_text:
            self.status_lbl.setText("Vui lòng nhập mật khẩu!")
            self.status_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #EF4444;")
            return

        if p_text != p2_text:
            self.status_lbl.setText("Mật khẩu xác nhận không khớp!")
            self.status_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #EF4444;")
            return

        if not self.is_paid:
            self.status_lbl.setText("Đang kiểm tra SePay...")
            self.status_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #E09F5E;")
            self.btn_submit.setEnabled(False)
            QApplication.processEvents()

            paid, msg, tx = check_sepay_payment(self.order_code, expected_amount=DEFAULT_REGISTRATION_PRICE)
            self.btn_submit.setEnabled(True)
            if not paid:
                self.status_lbl.setText(f"Chưa nhận được chuyển khoản 50.000đ với nội dung '{self.order_code}'. Vui lòng quét mã QR trước khi bấm.")
                self.status_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #EF4444;")
                return
            self.is_paid = True

        # Tạo user mới với role 'user'
        ok, msg = self.store.create_user(u_text, p_text, role="user")
        if not ok:
            self.status_lbl.setText(msg)
            self.status_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #EF4444;")
            return

        self.created_username = u_text
        self.created_password = p_text
        if hasattr(self, "poll_timer") and self.poll_timer.isActive():
            self.poll_timer.stop()
        self.accept()

    def _on_cancel(self) -> None:
        if hasattr(self, "poll_timer") and self.poll_timer.isActive():
            self.poll_timer.stop()
        self.reject()

    def closeEvent(self, a0) -> None:
        if hasattr(self, "poll_timer") and self.poll_timer.isActive():
            self.poll_timer.stop()
        super().closeEvent(a0)


