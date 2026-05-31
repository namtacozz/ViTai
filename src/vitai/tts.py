from collections.abc import Callable
import logging
import threading


class SpeechUnavailableError(RuntimeError):
    pass


class Pyttsx3Backend:
    def __init__(self) -> None:
        try:
            import pyttsx3
        except ImportError as exc:
            raise SpeechUnavailableError("TTS backend unavailable") from exc
        self._engine = pyttsx3.init()

    def say(self, text: str) -> None:
        self._engine.say(text)
        self._engine.runAndWait()

    def stop(self) -> None:
        self._engine.stop()


class SpeechRunner:
    def __init__(self, backend_factory: Callable[[], object] = Pyttsx3Backend) -> None:
        self._backend_factory = backend_factory
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._backend: object | None = None
        self._job_id = 0
        self.last_error: Exception | None = None
        self._logger = logging.getLogger(__name__)

    def speak(self, text: str) -> None:
        normalized = text.strip()
        if not normalized:
            raise SpeechUnavailableError("No translation yet")

        self.stop()
        self.last_error = None
        with self._lock:
            self._job_id += 1
            job_id = self._job_id
        thread = threading.Thread(target=self._run, args=(normalized, job_id), daemon=True)
        with self._lock:
            self._thread = thread
        thread.start()

    def _run(self, text: str, job_id: int) -> None:
        try:
            backend = self._backend_factory()
            with self._lock:
                if job_id == self._job_id:
                    self._backend = backend
            backend.say(text)
        except Exception as exc:
            self.last_error = exc
            self._logger.exception("TTS failed")
        finally:
            with self._lock:
                if job_id == self._job_id:
                    self._backend = None
                    if threading.current_thread() is self._thread:
                        self._thread = None

    def stop(self) -> None:
        with self._lock:
            backend = self._backend
            thread = self._thread
        if backend is not None:
            backend.stop()
        if thread is not None and threading.current_thread() is not thread:
            thread.join(timeout=1.0)

    def wait(self, timeout: float = 1.0) -> None:
        with self._lock:
            thread = self._thread
        if thread is not None:
            thread.join(timeout=timeout)
