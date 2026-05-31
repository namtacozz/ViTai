from collections.abc import Callable
import logging
import threading


class AutoTranslateWorker:
    def __init__(self, job: Callable[[], None], interval_seconds: float):
        self._job = job
        self._interval_seconds = interval_seconds
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._logger = logging.getLogger(__name__)

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.is_running:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        thread = self._thread
        if thread is None:
            return
        if threading.current_thread() is thread:
            self._thread = None
            return
        thread.join(timeout=1.0)
        if not thread.is_alive():
            self._thread = None

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._job()
            except Exception:
                self._logger.exception("Auto translate job failed")
            self._stop_event.wait(self._interval_seconds)
