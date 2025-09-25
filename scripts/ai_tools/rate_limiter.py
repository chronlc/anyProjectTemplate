"""A tiny token-bucket rate limiter."""
from __future__ import annotations

import time
import threading
from typing import Optional


class RateLimiter:
    def __init__(self, rate: float = 1.0, capacity: Optional[float] = None):
        """rate: tokens per second. capacity: bucket size."""
        self.rate = rate
        self.capacity = capacity if capacity is not None else max(1.0, rate)
        self._tokens = self.capacity
        self._last = time.monotonic()
        self._lock = threading.Lock()

    def _add_tokens(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last
        self._last = now
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)

    def acquire(self, tokens: float = 1.0) -> None:
        with self._lock:
            self._add_tokens()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return
            # Need to wait
            needed = tokens - self._tokens
        # Sleep outside lock
        wait = needed / self.rate
        time.sleep(wait)
        with self._lock:
            self._add_tokens()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return
            raise RuntimeError("Rate limiter failed to acquire tokens")
