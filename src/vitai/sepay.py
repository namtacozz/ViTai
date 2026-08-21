from __future__ import annotations

import json
import logging
import random
import re
import urllib.parse
import urllib.request
from typing import Any

_log = logging.getLogger("vitai.sepay")

DEFAULT_SEPAY_TOKEN = "OXH81WY1GJ23KVBZZJJRMZNESOBAPCL4BA4KU6FDWQLOD5HMDKIASAP8W3Y5U9NL"
DEFAULT_BANK_ID = "MB"
DEFAULT_BANK_ACC = "99924052005"
DEFAULT_BANK_NAME = "LE VO THANH NAM"
DEFAULT_REGISTRATION_PRICE = 50000


def generate_order_code() -> str:
    """Tạo mã nội dung chuyển khoản duy nhất dạng VITAI + 6 số ngẫu nhiên."""
    rand_num = random.randint(100000, 999999)
    return f"VITAI{rand_num}"


def get_vietqr_url(
    bank_id: str = DEFAULT_BANK_ID,
    account_no: str = DEFAULT_BANK_ACC,
    account_name: str = DEFAULT_BANK_NAME,
    amount: int = DEFAULT_REGISTRATION_PRICE,
    memo: str = "",
) -> str:
    """Tạo đường dẫn ảnh VietQR chuẩn tự động điền số tiền và nội dung chuyển khoản."""
    encoded_name = urllib.parse.quote(account_name)
    encoded_memo = urllib.parse.quote(memo)
    return (
        f"https://img.vietqr.io/image/{bank_id}-{account_no}-compact2.png"
        f"?amount={amount}&addInfo={encoded_memo}&accountName={encoded_name}"
    )


def check_sepay_payment(
    order_code: str,
    expected_amount: int = DEFAULT_REGISTRATION_PRICE,
    api_token: str = DEFAULT_SEPAY_TOKEN,
    timeout: int = 8,
) -> tuple[bool, str, dict[str, Any] | None]:
    """
    Kiểm tra xem mã giao dịch order_code đã có tiền vào tài khoản thông qua SePay API hay chưa.
    
    Returns:
        (is_paid, message, transaction_data)
    """
    if not api_token:
        return False, "Chưa cấu hình SePay API Token", None

    clean_code = re.sub(r"[^A-Za-z0-9]", "", order_code).upper()
    if not clean_code:
        return False, "Mã giao dịch không hợp lệ", None

    url = "https://my.sepay.vn/userapi/transactions/list?limit=20"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {api_token.strip()}",
            "Content-Type": "application/json",
            "User-Agent": "curl/8.0.0",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                return False, f"SePay API trả về mã lỗi HTTP {resp.status}", None
            
            body = resp.read().decode("utf-8")
            data = json.loads(body)
            transactions = data.get("transactions", [])

            for tx in transactions:
                # Kiểm tra số tiền vào (amount_in)
                try:
                    amount_in = float(tx.get("amount_in", 0))
                except Exception:
                    amount_in = 0.0

                if amount_in < expected_amount:
                    continue

                # Kiểm tra nội dung chuyển khoản
                content = str(tx.get("transaction_content", "")).upper()
                clean_content = re.sub(r"[^A-Za-z0-9]", "", content)

                if clean_code in clean_content:
                    _log.info(f"[SEPAY] Khớp thanh toán thành công cho mã {order_code}: {tx.get('reference_number')}")
                    return True, "Thanh toán thành công!", tx

            return False, "Chưa nhận được giao dịch chuyển khoản khớp nội dung", None

    except Exception as exc:
        _log.error(f"[SEPAY] Lỗi gọi API SePay: {exc}")
        return False, f"Lỗi kết nối SePay: {exc}", None
