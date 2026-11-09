from dataclasses import dataclass


@dataclass(frozen=True)
class RateLimitState:
    limit: int
    remaining: int
    retry_after: float | None = None


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    state: RateLimitState
