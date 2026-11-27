import hashlib
import json
from dataclasses import asdict
from uuid import UUID

from app.policies.algorithm_config import (
    FixedWindowConfig,
    LeakyBucketConfig,
    SlidingWindowConfig,
    TokenBucketConfig,
)
from app.policies.policy import (
    IdentityTypes,
    Policy,
    QuotaScope,
    RateLimitAlgorithms,
    Resources,
)
from redis.asyncio import Redis


class PolicyCache:
    def __init__(
        self,
        redis_client: Redis,
        ttl_seconds: int = 60,
    ) -> None:
        self.redis = redis_client
        self.ttl_seconds = ttl_seconds

    @staticmethod
    def build_key(
        client_id: UUID,
        resource: Resources,
        route: str,
        identity_type: IdentityTypes,
        method: str,
    ) -> str:
        cache_dimensions = {
            "client_id": str(client_id),
            "resource": resource.value,
            "route": route,
            "identity_type": identity_type.value,
            "method": method,
        }

        serialized = json.dumps(
            cache_dimensions,
            sort_keys=True,
            separators=(",", ":"),
        )

        digest = hashlib.sha256(serialized.encode()).hexdigest()

        return f"rate-limit:policy:v1:{digest}"

    def _build_algorithm_config(
        self,
        algorithm: RateLimitAlgorithms,
        config_data: dict[str, int],
    ) -> FixedWindowConfig | SlidingWindowConfig | TokenBucketConfig | LeakyBucketConfig:
        if algorithm == RateLimitAlgorithms.FIXED_WINDOW:
            return FixedWindowConfig(**config_data)

        elif algorithm == RateLimitAlgorithms.SLIDING_WINDOW_LOG:
            return SlidingWindowConfig(**config_data)

        elif algorithm == RateLimitAlgorithms.TOKEN_BUCKET:
            return TokenBucketConfig(**config_data)

        elif algorithm == RateLimitAlgorithms.LEAKY_BUCKET:
            return LeakyBucketConfig(**config_data)

        raise ValueError(f"Unsupported rate limiting algorithm: {algorithm}")

    async def get(self, key: str) -> Policy | None:
        cached_value = await self.redis.get(key)

        if cached_value is None:
            return None

        data = json.loads(cached_value)

        algorithm = RateLimitAlgorithms(data["algorithm"])

        algorithm_config = self._build_algorithm_config(
            algorithm=algorithm,
            config_data=data["algorithm_config"],
        )

        return Policy(
            identifier=data["identifier"],
            name=data["name"],
            algorithm=algorithm,
            algorithm_config=algorithm_config,
            identity_type=IdentityTypes(data["identity_type"]),
            resource=Resources(data["resource"]),
            route=data["route"],
            method=data["method"],
            quota_scope=QuotaScope(data["quota_scope"]),
        )

    async def set(self, key: str, policy: Policy) -> None:
        data = {
            "identifier": policy.identifier,
            "name": policy.name,
            "algorithm": policy.algorithm.value,
            "algorithm_config": asdict(policy.algorithm_config),
            "identity_type": policy.identity_type.value,
            "resource": policy.resource.value,
            "route": policy.route,
            "method": policy.method,
            "quota_scope": policy.quota_scope.value,
        }

        await self.redis.set(
            key,
            json.dumps(data),
            ex=self.ttl_seconds,
        )
