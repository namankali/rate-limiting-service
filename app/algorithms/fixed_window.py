import math
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from threading import Lock

from app.algorithms.base import RateLimitingAlgorithm
from app.policies.algorithm_config import FixedWindowConfig
from app.policies.policy import Policy


@dataclass
class WindowState:
    count: int
    window_start: float


@dataclass
class FixedWindowCounter(RateLimitingAlgorithm):
    _clients: dict[str, WindowState] = field(default_factory=dict, init=False)
    _clock: Callable[[], float] = time.monotonic
    _lock: Lock = field(default_factory=Lock, init=False, repr=False)

    def evaluate(self, key: str, policy: Policy) -> bool:
        if not isinstance(policy.algorithm_config, FixedWindowConfig):
            raise ValueError("FixedWindowCounter requires FixedWindowConfig")

        return self.allow(
            client_id=key,
            limit=policy.algorithm_config.limit,
            window_seconds=policy.algorithm_config.window_seconds,
        )

    def allow(self, client_id: str, limit: int, window_seconds: float) -> bool:
        if limit <= 0:
            raise ValueError("Limit must be positive")
        if not math.isfinite(window_seconds) or window_seconds <= 0:
            raise ValueError("Window duration must be finite and positive")

        with self._lock:
            current_time = self._clock()
            if client_id not in self._clients:
                state = WindowState(1, current_time)
                self._clients[client_id] = state
                return True
            else:
                state = self._clients[client_id]
                if current_time - state.window_start >= window_seconds:
                    self._clients[client_id] = WindowState(1, current_time)
                    return True
                else:
                    if state.count >= limit:
                        return False
                    else:
                        state.count += 1
                        return True
