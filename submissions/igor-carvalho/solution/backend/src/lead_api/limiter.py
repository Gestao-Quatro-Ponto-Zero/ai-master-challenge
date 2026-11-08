"""Limite simples por usuário (janela deslizante de 60 s, em memória) para what-if e rotas de escrita."""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from .errors import ApiError


class RateLimiter:
    def __init__(self, per_minute: int, clock=time.monotonic):
        self.per_minute, self.clock = per_minute, clock
        self._hits: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> None:
        now = self.clock()
        with self._lock:
            q = self._hits[key]
            while q and now - q[0] > 60:
                q.popleft()
            if len(q) >= self.per_minute:
                raise ApiError(429, "RATE_LIMITED", "Muitas requisições. Tente novamente em instantes.")
            q.append(now)
