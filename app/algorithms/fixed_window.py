from dataclasses import dataclass

from redis.asyncio import Redis

from app.algorithms.base import RateLimitingAlgorithm
from app.algorithms.state import RateLimitResult, RateLimitState
from app.db.redis.queries import evaluate_fixed_window
from app.policies.algorithm_config import FixedWindowConfig
from app.policies.policy import Policy

# @dataclass
# class WindowState:
#     count: int
#     window_start: float


@dataclass
class FixedWindowCounter(RateLimitingAlgorithm):
    # _clients: dict[str, WindowState] = field(default_factory=dict, init=False)
    # _clock: Callable[[], float] = time.monotonic
    # _lock: Lock = field(default_factory=Lock, init=False, repr=False)
    redis_client: Redis

    async def evaluate(
        self,
        key: str,
        policy: Policy,
    ) -> RateLimitResult:
        if not isinstance(policy.algorithm_config, FixedWindowConfig):
            raise ValueError("FixedWindowCounter requires FixedWindowConfig")

        allowed, count, remaining, retry_after_ms = await evaluate_fixed_window(
            redis_client=self.redis_client,
            key=key,
            limit=policy.algorithm_config.limit,
            window_seconds=policy.algorithm_config.window_seconds,
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

    # def evaluate(self, key: str, policy: Policy) -> RateLimitResult:
    #     if not isinstance(policy.algorithm_config, FixedWindowConfig):
    #         raise ValueError("FixedWindowCounter requires FixedWindowConfig")
    #     with self._lock:
    #         current_time = self._clock()
    #         is_allowed = self._allow(
    #             client_id=key,
    #             limit=policy.algorithm_config.limit,
    #             window_seconds=policy.algorithm_config.window_seconds,
    #             current_time=current_time,
    #         )
    #         duration = current_time - self._clients[key].window_start
    #         retry_after = None
    #         if not is_allowed:
    #             retry_after = max(
    #                 0.0, policy.algorithm_config.window_seconds - duration
    #             )

    #         return RateLimitResult(
    #             state=RateLimitState(
    #                 limit=policy.algorithm_config.limit,
    #                 retry_after=retry_after,
    #                 remaining=max(
    #                     0, policy.algorithm_config.limit - self._clients[key].count
    #                 ),
    #             ),
    #             allowed=is_allowed,
    #         )

    # def _allow(
    #     self, client_id: str, limit: int, window_seconds: float, current_time: float
    # ) -> bool:
    #     if limit <= 0:
    #         raise ValueError("Limit must be positive")
    #     if not math.isfinite(window_seconds) or window_seconds <= 0:
    #         raise ValueError("Window duration must be finite and positive")

    #     if client_id not in self._clients:
    #         state = WindowState(1, current_time)
    #         self._clients[client_id] = state
    #         return True
    #     else:
    #         state = self._clients[client_id]
    #         if current_time - state.window_start >= window_seconds:
    #             self._clients[client_id] = WindowState(1, current_time)
    #             return True
    #         else:
    #             if state.count >= limit:
    #                 return False
    #             else:
    #                 state.count += 1
    #                 return True
