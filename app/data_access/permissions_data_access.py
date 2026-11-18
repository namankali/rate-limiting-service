from uuid import UUID

from app.db.postgres.models.permissions import Permissions
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession


class PermissionsRepository:
    async def create(
        self,
        session: AsyncSession,
        name: str,
        description: str | None,
    ) -> Permissions:
        permission = Permissions(
            name=name,
            description=description,
        )

        session.add(permission)
        await session.flush()
        await session.refresh(permission)

        return permission

    async def get_by_id(
        self,
        session: AsyncSession,
        permission_id: UUID,
    ) -> Permissions | None:
        query = select(Permissions).where(Permissions.id == permission_id)

        result = await session.execute(query)

        return result.scalar_one_or_none()

    async def get_by_name(
        self,
        session: AsyncSession,
        name: str,
    ) -> Permissions | None:
        query = select(Permissions).where(Permissions.name == name)

        result = await session.execute(query)

        return result.scalar_one_or_none()

    async def get_all(
        self,
        session: AsyncSession,
    ) -> list[Permissions]:
        query = select(Permissions).order_by(Permissions.created_at.desc())

        result = await session.execute(query)

        return list(result.scalars().all())

    async def update(
        self,
        session: AsyncSession,
        permission_id: UUID,
        update_data: dict[str, str],
    ) -> Permissions | None:
        query = (
            update(Permissions)
            .where(Permissions.id == permission_id)
            .values(**update_data)
            .returning(Permissions)
        )

        result = await session.execute(query)

        return result.scalar_one_or_none()

    async def delete(
        self,
        session: AsyncSession,
        permission_id: UUID,
    ) -> bool:
        query = delete(Permissions).where(Permissions.id == permission_id).returning(Permissions.id)

        result = await session.execute(query)

        deleted_id = result.scalar_one_or_none()

        return deleted_id is not None
