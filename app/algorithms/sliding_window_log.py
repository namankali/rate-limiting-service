from dataclasses import dataclass
from uuid import uuid4

from redis.asyncio import Redis

from app.algorithms.base import RateLimitingAlgorithm
from app.algorithms.state import RateLimitResult, RateLimitState
from app.db.redis.queries import evaluate_sliding_window
from app.policies.algorithm_config import SlidingWindowConfig
from app.policies.policy import Policy


@dataclass
class SlidingWindowLog(RateLimitingAlgorithm):
    redis_client: Redis

    async def evaluate(
        self,
        key: str,
        policy: Policy,
    ) -> RateLimitResult:
        if not isinstance(policy.algorithm_config, SlidingWindowConfig):
            raise ValueError("SlidingWindowLog requires SlidingWindowConfig")

        request_id = str(uuid4())

        allowed, count, remaining, retry_after_ms = await evaluate_sliding_window(
            redis_client=self.redis_client,
            key=key,
            limit=policy.algorithm_config.limit,
            window_seconds=policy.algorithm_config.window_seconds,
            request_id=request_id,
        )

        retry_after = retry_after_ms / 1000 if not allowed else None

        return RateLimitResult(
            allowed=allowed,
            state=RateLimitState(
                limit=policy.algorithm_config.limit,
                remaining=remaining,
                retry_after=retry_after,
            ),
        )


# from collections import deque
# from collections.abc import Callable
# from dataclasses import dataclass, field
# from math import isfinite
# from threading import Lock
# from time import monotonic

# from app.algorithms.base import RateLimitingAlgorithm
# from app.algorithms.state import RateLimitResult, RateLimitState
# from app.policies.algorithm_config import SlidingWindowConfig
# from app.policies.policy import Policy


# @dataclass
# class SlidingWindowLog(RateLimitingAlgorithm):
#     _clients: dict[str, deque[float]] = field(default_factory=dict)
#     _lock: Lock = field(default_factory=Lock, init=False, repr=False)
#     _clock: Callable[[], float] = monotonic

#     def evaluate(self, key: str, policy: Policy) -> RateLimitResult:
#         if not isinstance(policy.algorithm_config, SlidingWindowConfig):
#             raise ValueError("SlidingWindowLog requires SlidingWindowConfig")

#         with self._lock:
#             current_time = self._clock()

#             is_allowed = self._allow(
#                 client_id=key,
#                 limit=policy.algorithm_config.limit,
#                 window_duration=policy.algorithm_config.window_seconds,
#                 current_time=current_time,
#             )

#             retry_after = None
#             if not is_allowed:
#                 queue = self._clients[key]
#                 oldest_timestamp = queue[0]
#                 retry_after = max(
#                     0.0,
#                     policy.algorithm_config.window_seconds
#                     - (current_time - oldest_timestamp),
#                 )

#             return RateLimitResult(
#                 allowed=is_allowed,
#                 state=RateLimitState(
#                     limit=policy.algorithm_config.limit,
#                     retry_after=retry_after,
#                     remaining=max(
#                         0, policy.algorithm_config.limit - len(self._clients[key])
#                     ),
#                 ),
#             )

#     def _allow(
#         self, client_id: str, limit: int, window_duration: float, current_time: float
#     ) -> bool:
#         if limit <= 0:
#             raise ValueError("Limit must be positive or greater than zero")
#         if not isfinite(window_duration) or window_duration <= 0:
#             raise ValueError("window duration must be positive or greater than zero")

#         if client_id not in self._clients:
#             self._clients[client_id] = deque([current_time])
#             return True
#         else:
#             client_queue = self._clients[client_id]
#             self._remove_expired_durations(
#                 client_queue, duration=current_time, window_duration=window_duration
#             )
#             if len(client_queue) < limit:
#                 client_queue.append(current_time)
#                 return True
#             else:
#                 return False

#     def _remove_expired_durations(
#         self, queue: deque[float], duration: float, window_duration: float
#     ) -> None:
#         if len(queue) == 0:
#             return
#         while True:
#             if queue and duration - window_duration >= queue[0]:
#                 queue.popleft()
#             else:
#                 break
