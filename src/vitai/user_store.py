from __future__ import annotations

import hashlib
import json
import os
import secrets
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


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


# ==========================================
# Cloud Database Configuration & REST Client
# ==========================================

DEFAULT_SUPABASE_URL = "https://yndwxcnedlilmsbbydvb.supabase.co"
DEFAULT_SUPABASE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InluZHd4Y25lZGxpbG1zYmJ5ZHZiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODczMDE3MjQsImV4cCI6MjEwMjg3NzcyNH0."
    "9uTO5Vfg-eQvCIkiUcXFgH9vYsjnglicr4KbYnnl-E8"
)


@dataclass
class CloudConfig:
    provider: str = "supabase"  # "supabase", "firebase", "local"
    supabase_url: str = DEFAULT_SUPABASE_URL
    supabase_key: str = DEFAULT_SUPABASE_KEY
    firebase_project_id: str = ""
    firebase_api_key: str = ""
    table_name: str = "vitai_users"
    is_enabled: bool = True

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> CloudConfig:
        return cls(
            provider=data.get("provider", "supabase"),
            supabase_url=data.get("supabase_url", DEFAULT_SUPABASE_URL),
            supabase_key=data.get("supabase_key", DEFAULT_SUPABASE_KEY),
            firebase_project_id=data.get("firebase_project_id", ""),
            firebase_api_key=data.get("firebase_api_key", ""),
            table_name=data.get("table_name", "vitai_users"),
            is_enabled=data.get("is_enabled", True),
        )


def get_cloud_config_path() -> Path:
    cfg_dir = Path.home() / ".vitai"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    return cfg_dir / "cloud_config.json"


def load_cloud_config(config_path: Optional[Path] = None) -> CloudConfig:
    path = config_path or get_cloud_config_path()
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return CloudConfig.from_dict(data)
        except Exception:
            pass
    return CloudConfig()


def save_cloud_config(cfg: CloudConfig, config_path: Optional[Path] = None) -> None:
    path = config_path or get_cloud_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cfg.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")


class CloudAuthClient:
    """REST Client kết nối trực tiếp đến Supabase hoặc Firebase Firestore."""

    def __init__(self, config: CloudConfig):
        self.config = config

    def _http_request(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[dict[str, str]] = None,
        data: Optional[dict | list] = None,
        timeout: float = 6.0,
    ) -> tuple[bool, Any, str]:
        req_headers = headers or {}
        body_bytes = None
        if data is not None:
            body_bytes = json.dumps(data).encode("utf-8")
            req_headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=body_bytes, headers=req_headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status = resp.status
                resp_text = resp.read().decode("utf-8")
                parsed = json.loads(resp_text) if resp_text else None
                return True, parsed, f"HTTP {status}"
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8", errors="ignore")
            return False, None, f"HTTP Error {e.code}: {err_msg}"
        except Exception as e:
            return False, None, f"Network Error: {str(e)}"

    def test_connection(self) -> tuple[bool, str]:
        if not self.config.is_enabled:
            return False, "Cloud Sync hiện đang tắt."

        if self.config.provider == "supabase":
            if not self.config.supabase_url or not self.config.supabase_key:
                return False, "Chưa điền Supabase URL hoặc API Key."
            base_url = self.config.supabase_url.rstrip("/")
            endpoint = f"{base_url}/rest/v1/{self.config.table_name}?select=count&limit=1"
            headers = {
                "apikey": self.config.supabase_key,
                "Authorization": f"Bearer {self.config.supabase_key}",
            }
            ok, _, msg = self._http_request(endpoint, method="GET", headers=headers)
            if ok:
                return True, "Kết nối Supabase thành công! Bảng dữ liệu hoạt động bình thường."
            return False, f"Không thể kết nối Supabase: {msg}"

        elif self.config.provider == "firebase":
            if not self.config.firebase_project_id:
                return False, "Chưa điền Firebase Project ID."
            endpoint = (
                f"https://firestore.googleapis.com/v1/projects/{self.config.firebase_project_id}/databases/(default)/documents"
            )
            if self.config.firebase_api_key:
                endpoint += f"?key={self.config.firebase_api_key}"
            ok, _, msg = self._http_request(endpoint, method="GET")
            if ok:
                return True, "Kết nối Firebase Firestore thành công!"
            return False, f"Không thể kết nối Firebase: {msg}"

        return False, "Nhà cung cấp Cloud không hợp lệ."

    def get_user(self, username: str) -> tuple[bool, Optional[User], str]:
        u_key = username.strip().lower()
        if self.config.provider == "supabase":
            base_url = self.config.supabase_url.rstrip("/")
            encoded_user = urllib.parse.quote(u_key)
            endpoint = f"{base_url}/rest/v1/{self.config.table_name}?username=eq.{encoded_user}&select=*"
            headers = {
                "apikey": self.config.supabase_key,
                "Authorization": f"Bearer {self.config.supabase_key}",
            }
            ok, data, msg = self._http_request(endpoint, method="GET", headers=headers)
            if ok and isinstance(data, list):
                if data:
                    return True, User.from_dict(data[0]), "Tìm thấy tài khoản."
                return True, None, "Tài khoản không tồn tại trên Cloud."
            return False, None, msg

        return False, None, "Provider không được hỗ trợ."

    def list_users(self) -> tuple[bool, list[User], str]:
        if self.config.provider == "supabase":
            base_url = self.config.supabase_url.rstrip("/")
            endpoint = f"{base_url}/rest/v1/{self.config.table_name}?select=*&order=created_at.desc"
            headers = {
                "apikey": self.config.supabase_key,
                "Authorization": f"Bearer {self.config.supabase_key}",
            }
            ok, data, msg = self._http_request(endpoint, method="GET", headers=headers)
            if ok and isinstance(data, list):
                users = [User.from_dict(row) for row in data]
                return True, users, "Lấy danh sách thành công."
            return False, [], msg

        return False, [], "Provider không được hỗ trợ."

    def create_user(self, user: User) -> tuple[bool, str]:
        if self.config.provider == "supabase":
            base_url = self.config.supabase_url.rstrip("/")
            endpoint = f"{base_url}/rest/v1/{self.config.table_name}"
            headers = {
                "apikey": self.config.supabase_key,
                "Authorization": f"Bearer {self.config.supabase_key}",
                "Prefer": "resolution=ignore-duplicates",
            }
            ok, _, msg = self._http_request(endpoint, method="POST", headers=headers, data=user.to_dict())
            if ok:
                return True, "Tạo tài khoản trên Cloud thành công."
            return False, f"Lỗi tạo tài khoản trên Cloud: {msg}"

        return False, "Provider không được hỗ trợ."

    def update_fields(self, username: str, fields: dict) -> tuple[bool, str]:
        u_key = username.strip().lower()
        if self.config.provider == "supabase":
            base_url = self.config.supabase_url.rstrip("/")
            encoded_user = urllib.parse.quote(u_key)
            endpoint = f"{base_url}/rest/v1/{self.config.table_name}?username=eq.{encoded_user}"
            headers = {
                "apikey": self.config.supabase_key,
                "Authorization": f"Bearer {self.config.supabase_key}",
            }
            ok, _, msg = self._http_request(endpoint, method="PATCH", headers=headers, data=fields)
            if ok:
                return True, "Cập nhật dữ liệu Cloud thành công."
            return False, f"Lỗi cập nhật Cloud: {msg}"

        return False, "Provider không được hỗ trợ."

    def delete_user(self, username: str) -> tuple[bool, str]:
        u_key = username.strip().lower()
        if self.config.provider == "supabase":
            base_url = self.config.supabase_url.rstrip("/")
            encoded_user = urllib.parse.quote(u_key)
            endpoint = f"{base_url}/rest/v1/{self.config.table_name}?username=eq.{encoded_user}"
            headers = {
                "apikey": self.config.supabase_key,
                "Authorization": f"Bearer {self.config.supabase_key}",
            }
            ok, _, msg = self._http_request(endpoint, method="DELETE", headers=headers)
            if ok:
                return True, "Xóa tài khoản trên Cloud thành công."
            return False, f"Lỗi xóa trên Cloud: {msg}"

        return False, "Provider không được hỗ trợ."


# ==========================================
# User Store (Hybrid Local & Cloud Sync)
# ==========================================

class UserStore:
    """Quản lý kho dữ liệu tài khoản và khóa cứng thiết bị qua MAC address (Local + Cloud)."""

    def __init__(
        self,
        db_path: Optional[Path] = None,
        store_path: Optional[Path] = None,
        cloud_config: Optional[CloudConfig] = None,
    ):
        target = db_path or store_path
        if target is None:
            db_dir = Path.home() / ".vitai"
            db_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = db_dir / "users.json"
        else:
            self.db_path = Path(target)

        self.cloud_config = cloud_config if cloud_config is not None else load_cloud_config()
        self.cloud_client = CloudAuthClient(self.cloud_config)
        self._users: dict[str, User] = {}
        self._load()

    def set_cloud_config(self, cfg: CloudConfig) -> None:
        self.cloud_config = cfg
        self.cloud_client = CloudAuthClient(cfg)
        save_cloud_config(cfg)

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
            salt, pwd_hash = hash_password("vit24052005")
            admin_user = User(
                username="vinguoitai",
                password_hash=pwd_hash,
                salt=salt,
                role="admin",
                bound_mac=None,
                created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                is_active=True,
            )
            self._users["vinguoitai"] = admin_user
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
        """Xác thực đăng nhập và kiểm tra ràng buộc địa chỉ MAC (Đồng bộ Cloud Online)."""
        u_key = username.strip().lower()

        # 1. Nếu có Cloud Sync bật, ưu tiên lấy dữ liệu mới nhất từ Cloud
        if self.cloud_config.is_enabled:
            ok, cloud_user, _ = self.cloud_client.get_user(u_key)
            if ok and cloud_user:
                self._users[u_key] = cloud_user
                self._save()

        if u_key not in self._users:
            return False, None, "Tài khoản không tồn tại trong hệ thống."

        user = self._users[u_key]
        if not user.is_active:
            return False, None, "Tài khoản này hiện đang bị tạm khóa. Vui lòng liên hệ Admin."

        if not verify_password(password, user.salt, user.password_hash):
            return False, None, "Mật khẩu không chính xác."

        current_mac = client_mac or get_mac_address()

        # 2. Nếu là Admin: Không bao giờ gán cố định MAC hay chặn MAC, cho phép đăng nhập tự do từ mọi máy
        if user.role == "admin":
            return True, user, "Đăng nhập Quản Trị Viên thành công! (Không giới hạn thiết bị)"

        # 3. Với User thường: Nếu là tài khoản chưa từng liên kết MAC (Lần đầu đăng nhập)
        if not user.bound_mac:
            user.bound_mac = current_mac
            self._save()
            # Cập nhật ngay lên Cloud Database
            if self.cloud_config.is_enabled:
                self.cloud_client.update_fields(u_key, {"bound_mac": current_mac})
            return True, user, f"Đăng nhập thành công! Đã liên kết cố định thiết bị ({current_mac})."

        # 4. Với User thường: Nếu đã có MAC liên kết trước đó
        if user.bound_mac != current_mac:
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

        # Đẩy lên Cloud nếu bật
        if self.cloud_config.is_enabled:
            ok_cloud, msg_cloud = self.cloud_client.create_user(new_user)
            if not ok_cloud:
                return True, f"Đã tạo tài khoản cục bộ (Lưu ý Cloud: {msg_cloud})"

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

        if self.cloud_config.is_enabled:
            self.cloud_client.update_fields(u_key, {"password_hash": pwd_hash, "salt": salt})

        return True, "Đổi mật khẩu thành công!"

    def reset_mac(self, username: str) -> tuple[bool, str]:
        """Gỡ liên kết MAC cũ để user có thể đăng nhập trên máy tính mới."""
        u_key = username.strip().lower()
        if u_key not in self._users:
            return False, "Tài khoản không tồn tại."
        self._users[u_key].bound_mac = None
        self._save()

        if self.cloud_config.is_enabled:
            self.cloud_client.update_fields(u_key, {"bound_mac": None})

        return True, f"Đã xóa liên kết thiết bị của tài khoản '{username}'. User có thể kích hoạt trên máy mới."

    def toggle_active(self, username: str) -> tuple[bool, str]:
        u_key = username.strip().lower()
        if u_key not in self._users:
            return False, "Tài khoản không tồn tại."
        if u_key == "admin" and self._users[u_key].is_active:
            return False, "Không thể khóa tài khoản Admin chính."

        self._users[u_key].is_active = not self._users[u_key].is_active
        self._save()

        if self.cloud_config.is_enabled:
            self.cloud_client.update_fields(u_key, {"is_active": self._users[u_key].is_active})

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

        if self.cloud_config.is_enabled:
            self.cloud_client.delete_user(u_key)

        return True, f"Đã xóa tài khoản '{username}'."

    def list_users(self) -> list[User]:
        # Nếu bật Cloud, tải danh sách mới nhất từ Cloud
        if self.cloud_config.is_enabled:
            ok, cloud_users, _ = self.cloud_client.list_users()
            if ok and cloud_users:
                for u in cloud_users:
                    self._users[u.username.lower()] = u
                self._save()

        return list(self._users.values())

    def get_user(self, username: str) -> Optional[User]:
        u_key = username.strip().lower()
        if self.cloud_config.is_enabled:
            ok, cloud_user, _ = self.cloud_client.get_user(u_key)
            if ok and cloud_user:
                self._users[u_key] = cloud_user
                self._save()
                return cloud_user

        return self._users.get(u_key)


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
