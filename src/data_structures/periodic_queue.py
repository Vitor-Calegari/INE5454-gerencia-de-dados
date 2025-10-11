import time
import queue
import threading


class PeriodicQueue(queue.Queue):
    def __init__(self, min_interval: float, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._min_interval = min_interval
        self._last_dequeue_time = 0.0
        self._lock = threading.Lock()

    def get(self, block=True, timeout=None):
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_dequeue_time
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
            self._last_dequeue_time = time.monotonic()

        item = super().get(block=block, timeout=timeout)

        return item
