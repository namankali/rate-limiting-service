from dataclasses import dataclass

from redis.asyncio import Redis

from app.algorithms.base import RateLimitingAlgorithm
from app.algorithms.state import RateLimitResult, RateLimitState
from app.db.redis.queries import evaluate_leaky_bucket
from app.policies.algorithm_config import LeakyBucketConfig
from app.policies.policy import Policy


@dataclass
class LeakyBucket(RateLimitingAlgorithm):
    redis_client: Redis

    async def evaluate(
        self,
        key: str,
        policy: Policy,
    ) -> RateLimitResult:
        if not isinstance(policy.algorithm_config, LeakyBucketConfig):
            raise ValueError("LeakyBucket requires LeakyBucketConfig")

        allowed, water_level, remaining, retry_after_ms = await evaluate_leaky_bucket(
            redis_client=self.redis_client,
            key=key,
            capacity=policy.algorithm_config.capacity,
            leak_rate=policy.algorithm_config.leak_rate,
        )

        retry_after = retry_after_ms / 1000 if not allowed else None

        return RateLimitResult(
            allowed=allowed,
            state=RateLimitState(
                limit=policy.algorithm_config.capacity,
                remaining=remaining,
                retry_after=retry_after,
            ),
        )


# import math
# import time
# from collections.abc import Callable
# from dataclasses import dataclass, field
# from threading import Lock

# from app.algorithms.base import RateLimitingAlgorithm
# from app.algorithms.state import RateLimitResult, RateLimitState
# from app.policies.algorithm_config import LeakyBucketConfig
# from app.policies.policy import Policy


# @dataclass
# class LeakyBucketState:
#     water_level: float
#     last_leak_time: float


# @dataclass
# class LeakyBucket(RateLimitingAlgorithm):
#     _buckets: dict[str, LeakyBucketState] = field(default_factory=dict, init=False)
#     _clock: Callable[[], float] = time.monotonic
#     _lock: Lock = field(default_factory=Lock, init=False, repr=False)

#     def evaluate(self, key: str, policy: Policy) -> RateLimitResult:
#         if not isinstance(policy.algorithm_config, LeakyBucketConfig):
#             raise ValueError("LeakyBucket requires LeakyBucketConfig")

#         with self._lock:
#             current_time = self._clock()
#             is_allowed = self._allow(
#                 key=key,
#                 leak_rate=policy.algorithm_config.leak_rate,
#                 capacity=policy.algorithm_config.capacity,
#                 current_time=current_time,
#             )

#             retry_after = None
#             if not is_allowed:
#                 # formula ->> max(0, (water-level -(capacity -1))/leak_rate)
#                 retry_after = max(
#                     0.0,
#                     (
#                         self._buckets[key].water_level
#                         - (policy.algorithm_config.capacity - 1)
#                     )
#                     / policy.algorithm_config.leak_rate,
#                 )

#             return RateLimitResult(
#                 allowed=is_allowed,
#                 state=RateLimitState(
#                     limit=policy.algorithm_config.capacity,
#                     remaining=max(
#                         0,
#                         math.floor(
#                             policy.algorithm_config.capacity
#                             - self._buckets[key].water_level
#                         ),
#                     ),
#                     retry_after=retry_after,
#                 ),
#             )

#     def _allow(
#         self, key: str, leak_rate: float, capacity: int, current_time: float
#     ) -> bool:
#         if not isinstance(capacity, int) or capacity <= 0:
#             raise ValueError("Capacity should be positive")
#         if not math.isfinite(leak_rate) or leak_rate <= 0:
#             raise ValueError("Leak rate should be positive and finite")

#         if key not in self._buckets:
#             self._buckets[key] = LeakyBucketState(
#                 water_level=0.0, last_leak_time=current_time
#             )
#         state = self._buckets[key]
#         self._leak(current_time=current_time, leak_rate=leak_rate, state=state)
#         if state.water_level >= capacity:
#             return False
#         else:
#             state.water_level += 1.0
#             return True

#     def _leak(self, state: LeakyBucketState, current_time: float, leak_rate: float):
#         elapsed_time = current_time - state.last_leak_time
#         if elapsed_time <= 0:
#             return

#         water_leak = elapsed_time * leak_rate

#         current_water_level = max(0.0, state.water_level - water_leak)

#         state.last_leak_time = current_time
#         state.water_level = current_water_level
