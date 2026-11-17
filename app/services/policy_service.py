from dataclasses import asdict
from typing import Any
from uuid import UUID, uuid4

from app.data_access.client_data_access import ClientRepository
from app.data_access.policy_data_access import PolicyRepository
from app.db.postgres.models.policy import Policy as PolicyModel
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
from app.schemas.policy import PolicyCreate
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


class PolicyService:
    def __init__(
        self,
        policy: PolicyRepository,
        client: ClientRepository,
    ):
        self.policy = policy
        self.client = client

    def build_algorithm_config(
        self,
        algorithm: RateLimitAlgorithms | str,
        config: dict[str, Any],
    ) -> FixedWindowConfig | SlidingWindowConfig | TokenBucketConfig | LeakyBucketConfig:
        if isinstance(algorithm, str):
            algorithm = RateLimitAlgorithms(algorithm)

        config_mapping = {
            RateLimitAlgorithms.FIXED_WINDOW: FixedWindowConfig,
            RateLimitAlgorithms.SLIDING_WINDOW_LOG: SlidingWindowConfig,
            RateLimitAlgorithms.TOKEN_BUCKET: TokenBucketConfig,
            RateLimitAlgorithms.LEAKY_BUCKET: LeakyBucketConfig,
        }

        config_class = config_mapping.get(algorithm)

        if config_class is None:
            raise ValueError("Unsupported rate-limiting algorithm")

        return config_class(**config)

    def generate_policy_identifier(self, resource: str) -> str:
        return f"{resource}-{uuid4()}"

    async def create_policy(
        self,
        session: AsyncSession,
        payload: PolicyCreate,
    ) -> PolicyModel:
        # 1. Verify that the client exists.
        client = await self.client.get_by_id(
            session=session,
            client_id=payload.client_id,
        )

        if client is None or not client.is_active:
            raise LookupError("Active client not found")

        # 2. Validate/build algorithm configuration.
        algorithm_config = self.build_algorithm_config(
            algorithm=payload.algorithm,
            config=payload.algorithm_config,
        )

        # 3. Generate a unique policy identifier.
        identifier = self.generate_policy_identifier(payload.resource.value)

        try:
            # 4. Insert policy.
            policy = await self.policy.create(
                session=session,
                identifier=identifier,
                client_id=payload.client_id,
                resource=payload.resource.value,
                route=payload.route,
                algorithm=payload.algorithm.value,
                algorithm_config=asdict(algorithm_config),
                identity_type=payload.identity_type.value,
                quota_scope=payload.quota_scope.value,
                name=payload.name,
                method=payload.method,
            )

            # 5. Commit transaction.
            await session.commit()

            return policy

        except IntegrityError as exc:
            await session.rollback()
            raise ValueError("Policy could not be created due to a database constraint") from exc

        except Exception:
            await session.rollback()
            raise

    async def get_policy(
        self,
        session: AsyncSession,
        policy_id: UUID,
    ) -> PolicyModel:
        policy = await self.policy.get_by_id(
            session=session,
            policy_id=policy_id,
        )

        if policy is None:
            raise LookupError("Policy not found")

        return policy

    async def get_policy_by_identifier(
        self,
        session: AsyncSession,
        identifier: str,
    ) -> PolicyModel:
        policy = await self.policy.get_by_identifier(
            session=session,
            identifier=identifier,
        )

        if policy is None:
            raise LookupError("Policy not found")

        return policy

    async def get_client_policies(
        self,
        session: AsyncSession,
        client_id: UUID,
    ) -> list[PolicyModel]:
        client = await self.client.get_by_id(
            session=session,
            client_id=client_id,
        )

        if client is None:
            raise LookupError("Client not found")

        return await self.policy.get_client_specific_policies(
            session=session,
            client_id=client_id,
        )

    async def get_all_policies(
        self,
        session: AsyncSession,
    ) -> list[PolicyModel]:
        return await self.policy.get_all_policies(
            session=session,
        )

    async def update_policy(
        self,
        session: AsyncSession,
        policy_id: UUID,
        updates: dict[str, Any],
    ) -> PolicyModel:
        policy = await self.get_policy(
            session=session,
            policy_id=policy_id,
        )

        allowed_fields = {
            "name",
            "resource",
            "route",
            "algorithm",
            "algorithm_config",
            "identity_type",
            "quota_scope",
            "is_active",
        }

        invalid_fields = set(updates) - allowed_fields

        if invalid_fields:
            raise ValueError(f"Unsupported policy fields: {', '.join(sorted(invalid_fields))}")

        if not updates:
            raise ValueError("At least one field must be provided")

        # Prepare the final algorithm/configuration combination.
        algorithm = updates.get("algorithm", policy.algorithm)
        config = updates.get(
            "algorithm_config",
            policy.algorithm_config,
        )

        if hasattr(algorithm, "value"):
            algorithm = algorithm.value

        # Validate configuration against the final algorithm.
        algorithm_config = self.build_algorithm_config(
            algorithm=algorithm,
            config=config,
        )

        # Convert Enum values into strings for database storage.
        normalized_updates = {}

        for field, value in updates.items():
            if hasattr(value, "value"):
                value = value.value

            normalized_updates[field] = value

        normalized_updates["algorithm"] = algorithm
        normalized_updates["algorithm_config"] = asdict(algorithm_config)

        try:
            updated_policy = await self.policy.update(
                session=session,
                policy=policy,
                updates=normalized_updates,
            )

            await session.commit()

            return updated_policy

        except IntegrityError as exc:
            await session.rollback()
            raise ValueError("Policy could not be updated due to a database constraint") from exc

        except Exception:
            await session.rollback()
            raise

    async def delete_policy(
        self,
        session: AsyncSession,
        policy_id: UUID,
    ) -> None:
        policy = await self.get_policy(
            session=session,
            policy_id=policy_id,
        )

        try:
            await self.policy.delete(
                session=session,
                policy=policy,
            )

            await session.commit()

        except Exception:
            await session.rollback()
            raise

    async def get_matching_policy(
        self,
        session: AsyncSession,
        resource: str,
        route: str,
        identity_type: str,
        client_id: UUID,
        method: str,
    ) -> Policy | None:
        policy_result = await self.policy.get_matching_policy_candidates(
            session=session,
            identity_type=identity_type,
            route=route,
            resource=resource,
            client_id=client_id,
            method=method,
        )

        if not policy_result:
            return None

        exact_match = [policy for policy in policy_result if policy.route == route]

        wildcard_match = [policy for policy in policy_result if policy.route == "*"]

        if len(exact_match) > 1:
            raise ValueError("Multiple exact policies match the request")

        if len(exact_match) == 1:
            selected_policy = exact_match[0]

        else:
            if len(wildcard_match) > 1:
                raise ValueError("Multiple wildcard policies match the request")

            if len(wildcard_match) == 1:
                selected_policy = wildcard_match[0]
            else:
                return None

        return self._convert_to_domain_policy(selected_policy)

    @staticmethod
    def _convert_to_domain_policy(policy_record) -> Policy:
        algorithm = RateLimitAlgorithms(policy_record.algorithm)
        identity_type = IdentityTypes(policy_record.identity_type)
        resource = Resources(policy_record.resource)
        quota_scope = QuotaScope(policy_record.quota_scope)

        config_models = {
            RateLimitAlgorithms.FIXED_WINDOW: FixedWindowConfig,
            RateLimitAlgorithms.SLIDING_WINDOW_LOG: SlidingWindowConfig,
            RateLimitAlgorithms.TOKEN_BUCKET: TokenBucketConfig,
            RateLimitAlgorithms.LEAKY_BUCKET: LeakyBucketConfig,
        }

        config_model = config_models[algorithm]

        algorithm_config = config_model(**policy_record.algorithm_config)

        return Policy(
            algorithm=algorithm,
            identity_type=identity_type,
            identifier=policy_record.identifier,
            route=policy_record.route,
            resource=resource,
            quota_scope=quota_scope,
            algorithm_config=algorithm_config,
            name=policy_record.name,
            method=policy_record.method,
        )
