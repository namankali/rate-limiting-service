from dataclasses import dataclass

from redis.asyncio import Redis

from app.algorithms.base import RateLimitingAlgorithm
from app.algorithms.state import RateLimitResult, RateLimitState
from app.db.redis.queries import evaluate_token_bucket
from app.policies.algorithm_config import TokenBucketConfig
from app.policies.policy import Policy


@dataclass
class TokenBucket(RateLimitingAlgorithm):
    redis_client: Redis

    async def evaluate(
        self,
        key: str,
        policy: Policy,
    ) -> RateLimitResult:
        if not isinstance(policy.algorithm_config, TokenBucketConfig):
            raise ValueError("TokenBucket requires TokenBucketConfig")

        allowed, tokens, remaining, retry_after_ms = await evaluate_token_bucket(
            redis_client=self.redis_client,
            key=key,
            capacity=policy.algorithm_config.capacity,
            refill_rate=policy.algorithm_config.refill_rate,
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
# from app.policies.algorithm_config import TokenBucketConfig
# from app.policies.policy import Policy


# @dataclass
# class TokenBucketState:
#     current_tokens: float
#     last_refill_time: float


# @dataclass
# class TokenBucket(RateLimitingAlgorithm):
#     _buckets: dict[str, TokenBucketState] = field(default_factory=dict, init=False)
#     _clock: Callable[[], float] = time.monotonic
#     _lock: Lock = field(default_factory=Lock, init=False, repr=False)

#     def evaluate(self, key: str, policy: Policy) -> RateLimitResult:
#         if not isinstance(policy.algorithm_config, TokenBucketConfig):
#             raise ValueError("TokenBucket requires TokenBucketConfig")

#         with self._lock:
#             current_time = self._clock()
#             is_allowed = self.allow_request(
#                 key=key,
#                 refill_rate=policy.algorithm_config.refill_rate,
#                 capacity=policy.algorithm_config.capacity,
#                 current_time=current_time,
#             )

#             retry_after = None
#             if not is_allowed:
#                 # formula ->> (1 - current_tokens)
#                 retry_after = max(
#                     0.0,
#                     (1.0 - self._buckets[key].current_tokens)
#                     / policy.algorithm_config.refill_rate,
#                 )

#             return RateLimitResult(
#                 allowed=is_allowed,
#                 state=RateLimitState(
#                     retry_after=retry_after,
#                     limit=policy.algorithm_config.capacity,
#                     remaining=max(
#                         0,
#                         math.floor(self._buckets[key].current_tokens),
#                     ),
#                 ),
#             )

#     def allow_request(
#         self, key: str, capacity: int, refill_rate: float, current_time: float
#     ) -> bool:
#         if capacity <= 0:
#             raise ValueError("Capacity should be positive")
#         if not math.isfinite(refill_rate) or refill_rate <= 0:
#             raise ValueError("Refill rate should be positive")

#         if key not in self._buckets:
#             self._buckets[key] = TokenBucketState(
#                 current_tokens=capacity, last_refill_time=current_time
#             )

#         state = self._buckets[key]
#         self.refilling(state, current_time, capacity, refill_rate)

#         if state.current_tokens <= 0.0:
#             return False
#         state.current_tokens -= 1
#         return True

#     def refilling(
#         self,
#         state: TokenBucketState,
#         current_time: float,
#         capacity: int,
#         refill_rate: float,
#     ) -> None:
#         elapsed_time = current_time - state.last_refill_time

#         if elapsed_time <= 0:
#             return

#         if state.current_tokens == capacity:
#             state.last_refill_time = current_time
#             return

#         new_tokens = elapsed_time * refill_rate

#         if new_tokens > 0:
#             state.current_tokens = min(capacity, state.current_tokens + new_tokens)
#             state.last_refill_time += new_tokens / refill_rate
