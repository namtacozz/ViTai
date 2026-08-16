from __future__ import annotations

import logging
from collections import deque

from PyQt6.QtCore import QObject, pyqtSignal


class LogBridge(QObject):
    new_log = pyqtSignal(str)


class UiLogHandler(logging.Handler):
    """Logging handler that stores log records and emits a signal for each new log."""
    
    MAX_LINES = 500
    
    def __init__(self):
        super().__init__(logging.DEBUG)
        self._bridge: LogBridge | None = None
        self._buffer: deque[str] = deque(maxlen=self.MAX_LINES)
        self.setFormatter(logging.Formatter("%(asctime)s  %(message)s", datefmt="%H:%M:%S"))
    
    def set_bridge(self, bridge: LogBridge) -> None:
        self._bridge = bridge
    
    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self._buffer.append(msg)
            if self._bridge is not None:
                self._bridge.new_log.emit(msg)
        except Exception:
            pass
    
    def get_all(self) -> str:
        return "\n".join(self._buffer)


# Singleton instances
_ui_handler: UiLogHandler | None = None
_log_bridge: LogBridge | None = None


def get_ui_log_handler() -> UiLogHandler:
    global _ui_handler
    if _ui_handler is None:
        _ui_handler = UiLogHandler()
    return _ui_handler


def get_log_bridge() -> LogBridge:
    global _log_bridge
    if _log_bridge is None:
        _log_bridge = LogBridge()
        get_ui_log_handler().set_bridge(_log_bridge)
    return _log_bridge


def install_ui_logging() -> None:
    """Install the UI log handler on the root vitai logger."""
    handler = get_ui_log_handler()
    root = logging.getLogger("vitai")
    if handler not in root.handlers:
        root.addHandler(handler)
        root.setLevel(logging.DEBUG)
