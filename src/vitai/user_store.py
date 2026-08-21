from __future__ import annotations

import hashlib
import json
import os
import secrets
import sys
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


def get_mac_address() -> str:
    """Lấy địa chỉ MAC card mạng thực tế của máy tính."""
    try:
        mac_num = uuid.getnode()
        mac_hex = f"{mac_num:012x}"
        return ":".join(mac_hex[i:i+2] for i in range(0, 12, 2)).upper()
    except Exception:
        return "UNKNOWN_MAC"


def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Tạo salt và băm mật khẩu bằng SHA-256 kèm salt. Trả về (salt, hash)."""
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return salt, hashed


def verify_password(password: str, salt: str, password_hash: str) -> bool:
    """Xác thực mật khẩu người dùng."""
    hashed = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return secrets.compare_digest(hashed, password_hash)


@dataclass
class User:
    username: str
    password_hash: str
    salt: str
    role: str = "user"  # "admin" hoặc "user"
    bound_mac: Optional[str] = None  # Gán tự động ở lần đăng nhập đầu tiên
    created_at: str = ""
    is_active: bool = True

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> User:
        return cls(
            username=data.get("username", ""),
            password_hash=data.get("password_hash", ""),
            salt=data.get("salt", ""),
            role=data.get("role", "user"),
            bound_mac=data.get("bound_mac"),
            created_at=data.get("created_at", ""),
            is_active=data.get("is_active", True),
        )


class UserStore:
    """Quản lý kho dữ liệu tài khoản và khóa cứng thiết bị qua MAC address."""

    def __init__(self, db_path: Optional[Path] = None, store_path: Optional[Path] = None):
        target = db_path or store_path
        if target is None:
            db_dir = Path.home() / ".vitai"
            db_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = db_dir / "users.json"
        else:
            self.db_path = Path(target)
        self._users: dict[str, User] = {}
        self._load()

    def _load(self) -> None:
        if self.db_path.exists():
            try:
                data = json.loads(self.db_path.read_text(encoding="utf-8"))
                for u_dict in data.get("users", []):
                    u = User.from_dict(u_dict)
                    self._users[u.username.lower()] = u
            except Exception:
                self._users = {}

        # Khởi tạo tài khoản Admin mặc định nếu kho dữ liệu rỗng
        if not self._users:
            salt, pwd_hash = hash_password("admin")
            admin_user = User(
                username="admin",
                password_hash=pwd_hash,
                salt=salt,
                role="admin",
                bound_mac=None,
                created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                is_active=True,
            )
            self._users["admin"] = admin_user
            self._save()

    def _save(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": "1.0",
            "users": [u.to_dict() for u in self._users.values()],
        }
        self.db_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def authenticate(
        self, username: str, password: str, client_mac: Optional[str] = None
    ) -> tuple[bool, Optional[User], str]:
        """Xác thực đăng nhập và kiểm tra ràng buộc địa chỉ MAC."""
        u_key = username.strip().lower()
        if u_key not in self._users:
            return False, None, "Tài khoản không tồn tại trong hệ thống."

        user = self._users[u_key]
        if not user.is_active:
            return False, None, "Tài khoản này hiện đang bị tạm khóa. Vui lòng liên hệ Admin."

        if not verify_password(password, user.salt, user.password_hash):
            return False, None, "Mật khẩu không chính xác."

        current_mac = client_mac or get_mac_address()

        # Nếu là tài khoản chưa từng liên kết MAC (Lần đầu đăng nhập)
        if not user.bound_mac:
            user.bound_mac = current_mac
            self._save()
            return True, user, f"Đăng nhập thành công! Đã liên kết cố định thiết bị ({current_mac})."

        # Nếu đã có MAC liên kết trước đó
        if user.bound_mac != current_mac:
            # Nếu là Admin, cho phép đăng nhập quản trị từ mọi máy
            if user.role == "admin":
                return True, user, "Đăng nhập Quản Trị Viên thành công!"
            return (
                False,
                None,
                f"Tài khoản này đã bị khóa cứng với thiết bị khác (MAC: {user.bound_mac}). Không thể sử dụng trên máy tính này (MAC hiện tại: {current_mac}).",
            )

        return True, user, "Đăng nhập thành công!"

    def create_user(self, username: str, password: str, role: str = "user") -> tuple[bool, str]:
        u_key = username.strip().lower()
        if not u_key:
            return False, "Tên tài khoản không được để trống."
        if u_key in self._users:
            return False, f"Tài khoản '{username}' đã tồn tại."
        if len(password) < 4:
            return False, "Mật khẩu phải có ít nhất 4 ký tự."

        salt, pwd_hash = hash_password(password)
        new_user = User(
            username=username.strip(),
            password_hash=pwd_hash,
            salt=salt,
            role=role if role in ("admin", "user") else "user",
            bound_mac=None,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            is_active=True,
        )
        self._users[u_key] = new_user
        self._save()
        return True, f"Đã tạo thành công tài khoản '{username}'."

    def update_password(self, username: str, new_password: str) -> tuple[bool, str]:
        u_key = username.strip().lower()
        if u_key not in self._users:
            return False, "Tài khoản không tồn tại."
        if len(new_password) < 4:
            return False, "Mật khẩu mới phải có ít nhất 4 ký tự."

        salt, pwd_hash = hash_password(new_password)
        self._users[u_key].password_hash = pwd_hash
        self._users[u_key].salt = salt
        self._save()
        return True, "Đổi mật khẩu thành công!"

    def reset_mac(self, username: str) -> tuple[bool, str]:
        """Gỡ liên kết MAC cũ để user có thể đăng nhập trên máy tính mới."""
        u_key = username.strip().lower()
        if u_key not in self._users:
            return False, "Tài khoản không tồn tại."
        self._users[u_key].bound_mac = None
        self._save()
        return True, f"Đã xóa liên kết thiết bị của tài khoản '{username}'. User có thể kích hoạt trên máy mới."

    def toggle_active(self, username: str) -> tuple[bool, str]:
        u_key = username.strip().lower()
        if u_key not in self._users:
            return False, "Tài khoản không tồn tại."
        if u_key == "admin" and self._users[u_key].is_active:
            return False, "Không thể khóa tài khoản Admin chính."

        self._users[u_key].is_active = not self._users[u_key].is_active
        self._save()
        status_text = "kích hoạt" if self._users[u_key].is_active else "tạm khóa"
        return True, f"Tài khoản '{username}' đã được {status_text}."

    def delete_user(self, username: str) -> tuple[bool, str]:
        u_key = username.strip().lower()
        if u_key not in self._users:
            return False, "Tài khoản không tồn tại."
        if u_key == "admin":
            return False, "Không thể xóa tài khoản Admin mặc định."

        del self._users[u_key]
        self._save()
        return True, f"Đã xóa tài khoản '{username}'."

    def list_users(self) -> list[User]:
        return list(self._users.values())

    def get_user(self, username: str) -> Optional[User]:
        return self._users.get(username.strip().lower())


# ==========================================
# Session Management
# ==========================================

def get_session_path() -> Path:
    session_dir = Path.home() / ".vitai"
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir / "session.json"


def save_session(user: User, session_path: Optional[Path] = None) -> None:
    path = session_path or get_session_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "username": user.username,
        "role": user.role,
        "mac": get_mac_address(),
        "login_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def get_current_session(
    store: Optional[UserStore] = None, session_path: Optional[Path] = None
) -> Optional[User]:
    path = session_path or get_session_path()
    if not path.exists():
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        username = data.get("username", "")
        if not username:
            return None

        if store is None:
            store = get_user_store()

        user = store.get_user(username)
        if not user or not user.is_active:
            clear_session(session_path=path)
            return None

        current_mac = get_mac_address()
        # Kiểm tra MAC nếu không phải admin
        if user.role != "admin" and user.bound_mac and user.bound_mac != current_mac:
            clear_session(session_path=path)
            return None

        return user
    except Exception:
        return None


def clear_session(session_path: Optional[Path] = None) -> None:
    path = session_path or get_session_path()
    if path.exists():
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass


_global_user_store: Optional[UserStore] = None

def get_user_store() -> UserStore:
    global _global_user_store
    if _global_user_store is None:
        _global_user_store = UserStore()
    return _global_user_store
