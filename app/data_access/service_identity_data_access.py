from typing import Any
from uuid import UUID

from app.db.postgres.models.service_identity import ServiceIdentity
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class ServiceIdentityRepository:
    async def create(
        self,
        session: AsyncSession,
        client_id: UUID,
        name: str,
        description: str,
    ) -> ServiceIdentity:
        ser_identity = ServiceIdentity(client_id=client_id, name=name, description=description)

        session.add(ser_identity)
        await session.flush()
        await session.refresh(ser_identity)

        return ser_identity

    async def get_all(
        self,
        session: AsyncSession,
    ) -> list[ServiceIdentity]:
        query = select(ServiceIdentity).where(ServiceIdentity.is_active.is_(True))
        result = await session.execute(query)

        return list(result.scalars().all())

    async def get_by_id(self, session: AsyncSession, service_id: UUID) -> ServiceIdentity | None:
        query = (
            select(ServiceIdentity)
            .where(ServiceIdentity.id == service_id)
            .where(ServiceIdentity.is_active.is_(True))
        )
        result = await session.execute(query)

        return result.scalar_one_or_none()

    async def update(
        self,
        session: AsyncSession,
        service_identity: ServiceIdentity,
        updates: dict[str, Any],
    ) -> ServiceIdentity:
        for field, value in updates.items():
            setattr(service_identity, field, value)

        await session.flush()
        await session.refresh(service_identity)

        return service_identity
