from typing import Any
from uuid import UUID

from app.db.postgres.models.policy import Policy
from app.policies.policy import IdentityTypes, Resources
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession


class PolicyRepository:
    async def create(
        self,
        session: AsyncSession,
        identifier: str,
        client_id: UUID,
        resource: str,
        method: str,
        route: str,
        algorithm: str,
        algorithm_config: dict[str, Any],
        identity_type: str,
        quota_scope: str,
        name: str,
    ) -> Policy:
        policy = Policy(
            identifier=identifier,
            client_id=client_id,
            resource=resource,
            route=route,
            algorithm=algorithm,
            algorithm_config=algorithm_config,
            identity_type=identity_type,
            quota_scope=quota_scope,
            name=name,
            method=method,
        )

        session.add(policy)
        await session.flush()
        await session.refresh(policy)

        return policy

    async def get_by_id(self, session: AsyncSession, policy_id: UUID) -> Policy | None:
        result = await session.execute(
            select(Policy).where(Policy.id == policy_id).where(Policy.is_active.is_(True))
        )
        return result.scalar_one_or_none()

    async def get_by_identifier(self, session: AsyncSession, identifier: str) -> Policy | None:
        result = await session.execute(
            select(Policy).where(Policy.identifier == identifier).where(Policy.is_active.is_(True))
        )
        return result.scalar_one_or_none()

    async def get_client_specific_policies(
        self, session: AsyncSession, client_id: UUID
    ) -> list[Policy]:
        result = await session.execute(
            select(Policy).where(Policy.client_id == client_id).where(Policy.is_active.is_(True))
        )
        return list(result.scalars().all())

    async def get_all_policies(
        self,
        session: AsyncSession,
    ) -> list[Policy]:
        result = await session.execute(
            select(Policy).where(Policy.is_active.is_(True)).order_by(Policy.created_at.desc())
        )
        return list(result.scalars().all())

    async def update(
        self, session: AsyncSession, policy: Policy, updates: dict[str, Any]
    ) -> Policy:
        for field, value in updates.items():
            setattr(policy, field, value)

        await session.flush()
        await session.refresh(policy)

        return policy

    async def delete(self, session: AsyncSession, policy: Policy) -> None:
        await session.delete(policy)
        await session.flush()

    async def get_matching_policy_candidates(
        self,
        session: AsyncSession,
        resource: Resources,
        route: str,
        identity_type: IdentityTypes,
        client_id: UUID,
        method: str,
    ) -> list[Policy]:
        query = select(Policy).where(
            Policy.resource == resource.value,
            Policy.client_id == client_id,
            Policy.identity_type == identity_type.value,
            Policy.is_active.is_(True),
            Policy.method == method,
            or_(Policy.route == route, Policy.route == "*"),
        )

        result = await session.execute(query)

        return list(result.scalars().all())
