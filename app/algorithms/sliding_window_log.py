from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from math import isfinite
from threading import Lock
from time import monotonic

from app.algorithms.base import RateLimitingAlgorithm
from app.policies.algorithm_config import SlidingWindowConfig
from app.policies.policy import Policy


@dataclass
class SlidingWindowLog(RateLimitingAlgorithm):
    _clients: dict[str, deque[float]] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock, init=False, repr=False)
    _clock: Callable[[], float] = monotonic

    def evaluate(self, key: str, policy: Policy) -> bool:
        if not isinstance(policy.algorithm_config, SlidingWindowConfig):
            raise ValueError("SlidingWindowLog requires SlidingWindowConfig")

        return self.add(
            client_id=key,
            limit=policy.algorithm_config.limit,
            window_duration=policy.algorithm_config.window_seconds,
        )

    def add(self, client_id: str, limit: int, window_duration: float) -> bool:
        if limit <= 0:
            raise ValueError("Limit must be positive or greater than zero")
        if not isfinite(window_duration) or window_duration <= 0:
            raise ValueError("window duration must be positive or greater than zero")

        with self._lock:
            current_time = self._clock()
            if client_id not in self._clients:
                self._clients[client_id] = deque([current_time])
                self.remove_old_durations(
                    self._clients[client_id],
                    duration=current_time,
                    window_duration=window_duration,
                )
                return True
            else:
                client_queue = self._clients[client_id]
                self.remove_old_durations(
                    client_queue, duration=current_time, window_duration=window_duration
                )
                if len(client_queue) < limit:
                    client_queue.append(current_time)
                    return True
                else:
                    return False

    def remove_old_durations(
        self, queue: deque[float], duration: float, window_duration: float
    ) -> None:
        if len(queue) == 0:
            return
        while True:
            if queue and duration - window_duration >= queue[0]:
                queue.popleft()
            else:
                break
