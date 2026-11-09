from abc import ABC, abstractmethod

from app.algorithms.state import RateLimitResult
from app.policies.policy import Policy


class RateLimitingAlgorithm(ABC):
    @abstractmethod
    async def evaluate(self, key: str, policy: Policy) -> RateLimitResult:
        """Evaluate a request against the selected policy"""
        raise NotImplementedError
