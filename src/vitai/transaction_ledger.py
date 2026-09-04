from __future__ import annotations

import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

_log = logging.getLogger("vitai.ledger")


def get_ledger_path() -> Path:
    base = Path.home() / ".vitai"
    base.mkdir(parents=True, exist_ok=True)
    return base / "used_transactions.json"


class TransactionLedger:
    """
    Quản lý nhật ký các giao dịch chuyển khoản đã sử dụng (Anti-Replay Protection).
    Ngăn chặn việc tái sử dụng cùng một mã giao dịch ngân hàng để kích hoạt nhiều tài khoản.
    """

    def __init__(self, ledger_path: Optional[Path] = None):
        self.ledger_path = ledger_path or get_ledger_path()
        self._lock = threading.Lock()
        self._used: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if self.ledger_path.exists():
            try:
                data = json.loads(self.ledger_path.read_text(encoding="utf-8"))
                self._used = data.get("transactions", {})
            except Exception as e:
                _log.warning(f"[LEDGER] Không thể đọc file ledger: {e}")
                self._used = {}

    def _save(self) -> None:
        try:
            self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "version": "1.0",
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "transactions": self._used,
            }
            self.ledger_path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as e:
            _log.error(f"[LEDGER] Không thể lưu file ledger: {e}")

    def is_consumed(self, reference_number: str) -> bool:
        """Kiểm tra mã tham chiếu ngân hàng đã từng được dùng để kích hoạt tài khoản chưa."""
        if not reference_number:
            return False
        ref_key = str(reference_number).strip().upper()
        with self._lock:
            return ref_key in self._used

    def mark_consumed(
        self,
        reference_number: str,
        order_code: str,
        amount: int,
        username: str = "",
    ) -> bool:
        """
        Đánh dấu giao dịch đã được sử dụng. Trả về True nếu ghi nhận thành công,
        False nếu giao dịch này đã bị dùng từ trước (phát hiện replay).
        """
        if not reference_number:
            return False
        ref_key = str(reference_number).strip().upper()
        with self._lock:
            if ref_key in self._used:
                _log.warning(f"[LEDGER] ⚠️ PHÁT HIỆN GIAN LẬN: Giao dịch '{ref_key}' đã được sử dụng trước đó!")
                return False

            self._used[ref_key] = {
                "order_code": order_code,
                "amount": amount,
                "username": username,
                "consumed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            self._save()
            _log.info(f"[LEDGER] ✅ Đã ghi nhận giao dịch '{ref_key}' cho tài khoản '{username}'")
            return True


_global_ledger: Optional[TransactionLedger] = None


def get_transaction_ledger() -> TransactionLedger:
    global _global_ledger
    if _global_ledger is None:
        _global_ledger = TransactionLedger()
    return _global_ledger
