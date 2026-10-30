import math
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from threading import Lock

from app.algorithms.base import RateLimitingAlgorithm
from app.policies.algorithm_config import TokenBucketConfig
from app.policies.policy import Policy


@dataclass
class TokenBucketState:
    current_tokens: int
    last_refill_time: float


@dataclass
class TokenBucket(RateLimitingAlgorithm):
    _buckets: dict[str, TokenBucketState] = field(default_factory=dict, init=False)
    _clock: Callable[[], float] = time.monotonic
    _lock: Lock = field(default_factory=Lock, init=False, repr=False)

    def evaluate(self, key: str, policy: Policy) -> bool:
        if not isinstance(policy.algorithm_config, TokenBucketConfig):
            raise ValueError("TokenBucket requires TokenBucketConfig")
        return self.allow_request(
            key=key,
            refill_rate=policy.algorithm_config.refill_rate,
            capacity=policy.algorithm_config.capacity,
        )

    def allow_request(self, key: str, capacity: int, refill_rate: float) -> bool:
        if capacity <= 0:
            raise ValueError("Capacity should be positive")
        if not math.isfinite(refill_rate) or refill_rate <= 0:
            raise ValueError("Refill rate should be positive")
        with self._lock:
            current_time = self._clock()
            if key not in self._buckets:
                self._buckets[key] = TokenBucketState(
                    current_tokens=capacity, last_refill_time=current_time
                )

            state = self._buckets[key]
            self.refilling(state, current_time, capacity, refill_rate)

            if state.current_tokens <= 0:
                return False
            state.current_tokens -= 1
            return True

    def refilling(
        self,
        state: TokenBucketState,
        current_time: float,
        capacity: int,
        refill_rate: float,
    ) -> None:
        elapsed_time = current_time - state.last_refill_time

        if elapsed_time <= 0:
            return

        if state.current_tokens == capacity:
            state.last_refill_time = state.last_refill_time + elapsed_time
            return

        new_tokens = int(elapsed_time * refill_rate)

        if new_tokens > 0:
            state.current_tokens = min(capacity, state.current_tokens + new_tokens)
            state.last_refill_time += new_tokens / refill_rate
