import math
from dataclasses import dataclass


@dataclass(frozen=True)
class FixedWindowConfig:
    limit: int
    window_seconds: float

    def __post_init__(self) -> None:
        if self.limit <= 0:
            raise ValueError("Limit must be positive")
        if not math.isfinite(self.window_seconds) or self.window_seconds <= 0:
            raise ValueError("Window duration must be finite and positive")


@dataclass(frozen=True)
class SlidingWindowConfig:
    limit: int
    window_seconds: float

    def __post_init__(self) -> None:
        if self.limit <= 0:
            raise ValueError("Limit must be positive")
        if not math.isfinite(self.window_seconds) or self.window_seconds <= 0:
            raise ValueError("Window duration must be finite and positive")


@dataclass(frozen=True)
class TokenBucketConfig:
    capacity: int
    refill_rate: float

    def __post_init__(self) -> None:
        if self.capacity <= 0:
            raise ValueError("capacity should be positive")
        if not math.isfinite(self.refill_rate) or self.refill_rate <= 0:
            raise ValueError("Refill rate must be positive and finite")
