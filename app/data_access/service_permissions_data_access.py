from collections.abc import Sequence
from uuid import UUID

from app.db.postgres.models.permissions import Permissions
from app.db.postgres.models.service_permissions import ServicePermissions
from sqlalchemy import delete, select
from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession


class ServicePermissionsRepository:
    async def assign_permission(
        self,
        session: AsyncSession,
        service_identity_id: UUID,
        permission_id: UUID,
    ) -> ServicePermissions:
        service_permission = ServicePermissions(
            service_identity_id=service_identity_id,
            permission_id=permission_id,
        )

        session.add(service_permission)
        await session.flush()
        await session.refresh(service_permission)

        return service_permission

    async def get_by_service_identity(
        self,
        session: AsyncSession,
        service_identity_id: UUID,
    ) -> Sequence[RowMapping]:
        query = (
            select(
                ServicePermissions.id,
                ServicePermissions.service_identity_id,
                ServicePermissions.permission_id,
                Permissions.name.label("permission_name"),
                Permissions.description.label("permission_description"),
                ServicePermissions.created_at,
            )
            .join(
                Permissions,
                ServicePermissions.permission_id == Permissions.id,
            )
            .where(ServicePermissions.service_identity_id == service_identity_id)
        )

        result = await session.execute(query)
        return result.mappings().all()

    async def get_by_service_and_permission(
        self,
        session: AsyncSession,
        service_identity_id: UUID,
        permission_id: UUID,
    ) -> ServicePermissions | None:
        query = select(ServicePermissions).where(
            ServicePermissions.service_identity_id == service_identity_id,
            ServicePermissions.permission_id == permission_id,
        )

        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def remove_permission(
        self,
        session: AsyncSession,
        service_identity_id: UUID,
        permission_id: UUID,
    ) -> bool:
        query = delete(ServicePermissions).where(
            ServicePermissions.service_identity_id == service_identity_id,
            ServicePermissions.permission_id == permission_id,
        )

        result = await session.execute(query)
        deleted_id = result.scalar_one_or_none()
        return deleted_id is not None

    async def has_permission(
        self,
        session: AsyncSession,
        service_identity_id: UUID,
        permission_name: str,
    ) -> bool:
        query = (
            select(ServicePermissions.id)
            .join(
                Permissions,
                ServicePermissions.permission_id == Permissions.id,
            )
            .where(
                ServicePermissions.service_identity_id == service_identity_id,
                Permissions.name == permission_name,
            )
        )

        result = await session.execute(query)
        return result.scalar_one_or_none() is not None
