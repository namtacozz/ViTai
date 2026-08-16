from __future__ import annotations

import logging
import os
import socket
import sys
import threading
from pathlib import Path

_log = logging.getLogger("vitai.ipc")


def get_socket_path() -> Path:
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if runtime_dir and os.path.isdir(runtime_dir):
        return Path(runtime_dir) / "vitai.sock"
    vitai_dir = Path.home() / ".vitai"
    vitai_dir.mkdir(parents=True, exist_ok=True)
    return vitai_dir / "vitai.sock"


def send_trigger() -> bool:
    """Gửi tín hiệu TRIGGER tới tiến trình ViTai đang chạy."""
    sock_path = get_socket_path()
    if not sock_path.exists():
        return False

    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        sock.connect(str(sock_path))
        sock.sendall(b"TRIGGER\n")
        sock.close()
        return True
    except Exception as e:
        _log.warning(f"[IPC] Gửi trigger thất bại: {e}")
        return False


class IpcServer:
    """Unix domain socket server để nhận lệnh trigger từ bên ngoài (như GNOME Shortcuts)."""

    def __init__(self, on_trigger_callback):
        self.on_trigger = on_trigger_callback
        self.sock_path = get_socket_path()
        self.server_sock: socket.socket | None = None
        self.running = False
        self.thread: threading.Thread | None = None

    def start(self) -> None:
        if sys.platform == "win32":
            return

        try:
            if self.sock_path.exists():
                self.sock_path.unlink()

            self.server_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.server_sock.bind(str(self.sock_path))
            self.server_sock.listen(5)
            self.running = True

            self.thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.thread.start()
            _log.info(f"[IPC] IPC Server đã khởi động tại: {self.sock_path}")
        except Exception as e:
            _log.error(f"[IPC] Lỗi khởi động IPC Server: {e}")

    def _listen_loop(self) -> None:
        while self.running and self.server_sock:
            try:
                conn, _ = self.server_sock.accept()
                data = conn.recv(128).decode("utf-8", errors="ignore").strip()
                conn.close()
                if data == "TRIGGER":
                    _log.info("[IPC] 🔔 Nhận tín hiệu TRIGGER từ Socket (Hệ thống/GNOME Phím tắt)")
                    self.on_trigger()
            except Exception:
                if not self.running:
                    break

    def stop(self) -> None:
        self.running = False
        if self.server_sock:
            try:
                self.server_sock.close()
            except Exception:
                pass
            self.server_sock = None
        if self.sock_path.exists():
            try:
                self.sock_path.unlink()
            except Exception:
                pass
