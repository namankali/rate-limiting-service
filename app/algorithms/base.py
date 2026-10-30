from abc import ABC, abstractmethod

from app.policies.policy import Policy


class RateLimitingAlgorithm(ABC):
    @abstractmethod
    def evaluate(self, key: str, policy: Policy) -> bool:
        """Evaluate a request against the selected policy"""
        raise NotImplementedError
