from uuid import UUID

from app.algorithms.base import RateLimitingAlgorithm
from app.helpers.formatter import make_quota_key
from app.helpers.redis_key_builder import make_redis_key
from app.policies.policy import RateLimitAlgorithms, Resources
from app.schemas.rate_limit import RateLimitResponse
from app.services.policy_service import PolicyService
from sqlalchemy.ext.asyncio import AsyncSession


class RateLimitingService:
    def __init__(
        self,
        fixed_window_counter: RateLimitingAlgorithm,
        sliding_window_counter: RateLimitingAlgorithm,
        token_bucket: RateLimitingAlgorithm,
        leaky_bucket: RateLimitingAlgorithm,
        policy_service: PolicyService,
        environment: str,
    ):
        self.algorithms = {
            RateLimitAlgorithms.FIXED_WINDOW: fixed_window_counter,
            RateLimitAlgorithms.SLIDING_WINDOW_LOG: sliding_window_counter,
            RateLimitAlgorithms.TOKEN_BUCKET: token_bucket,
            RateLimitAlgorithms.LEAKY_BUCKET: leaky_bucket,
        }

        self.policy_service = policy_service
        self.environment = environment

    async def evaluate_request(
        self,
        resource: Resources,
        route: str,
        identity_type: str,
        identity_value: str,
        client_id: UUID,
        session: AsyncSession,
        method: str,
    ) -> RateLimitResponse:
        # policy = self.registry.policy_selection(
        #     resource=resource,
        #     route=route,
        #     identity_type=identity_type,
        #     identity_value=identity_value,
        # )
        policy = await self.policy_service.get_matching_policy(
            resource=resource,
            identity_type=identity_type,
            session=session,
            client_id=client_id,
            route=route,
            method=method,
        )

        if policy is None:
            return RateLimitResponse(allowed=False)

        quota_key = make_quota_key(
            identity_value=identity_value,
            identity_type=policy.identity_type,
            quota_scope=policy.quota_scope,
        )

        redis_key = make_redis_key(
            algorithm=policy.algorithm.value,
            quota_key=quota_key,
            policy_identifier=policy.identifier,
            resource=resource.value,
            environment=self.environment,
            client_id=client_id,
        )

        algorithm = self.algorithms.get(policy.algorithm)

        if algorithm is None:
            raise ValueError(f"Unsupported rate-limiting algorithm: {policy.algorithm}")

        result = await algorithm.evaluate(
            key=redis_key,
            policy=policy,
        )

        return RateLimitResponse(
            retry_after=result.state.retry_after,
            limit=result.state.limit,
            remaining=result.state.remaining,
            allowed=result.allowed,
            policy=policy.identifier,
        )
