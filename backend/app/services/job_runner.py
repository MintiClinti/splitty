from concurrent.futures import ThreadPoolExecutor
from threading import Lock

from app.core.config import settings


class JobRunner:
    def __init__(self) -> None:
        self._executor = ThreadPoolExecutor(max_workers=settings.max_workers)
        self._lock = Lock()

    def submit(self, fn, *args, **kwargs) -> None:
        with self._lock:
            self._executor.submit(fn, *args, **kwargs)


job_runner = JobRunner()
