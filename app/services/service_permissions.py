from uuid import UUID

from app.data_access.permissions_data_access import PermissionsRepository
from app.data_access.service_identity_data_access import (
    ServiceIdentityRepository,
)
from app.data_access.service_permissions_data_access import (
    ServicePermissionsRepository,
)
from app.db.postgres.models.service_permissions import ServicePermissions
from app.exceptions.base import ApplicationError
from app.exceptions.database import DatabaseIntegrityError
from app.schemas.service_permissions import ServicePermissionByServiceIdentity
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


class ServicePermissionNotFound(ApplicationError):
    def __init__(self, message: str):
        super().__init__(message, "SERVICE_PERMISSION_NOT_FOUND", 404)


class ServicePermissionAlreadyExists(ApplicationError):
    def __init__(self, message: str):
        super().__init__(message, "SERVICE_PERMISSION_ALREADY_EXISTS", 409)


class ServiceIdentityNotFoundError(ApplicationError):
    def __init__(self, message: str):
        super().__init__(message, "SERVICE_IDENTITY_NOT_FOUND", 404)


class PermissionNotFoundError(ApplicationError):
    def __init__(self, message: str):
        super().__init__(message, "PERMISSION_NOT_FOUND", 404)


class ServicePermissionAssignPayload(BaseModel):
    service_identity_id: UUID
    permission_id: UUID


class ServicePermissionsService:
    def __init__(
        self,
        service_permissions_data_access: ServicePermissionsRepository,
        service_identity_data_access: ServiceIdentityRepository,
        permissions_data_access: PermissionsRepository,
    ):
        self.service_permissions_data_access = service_permissions_data_access
        self.service_identity_data_access = service_identity_data_access
        self.permissions_data_access = permissions_data_access

    async def assign_permission(
        self,
        session: AsyncSession,
        payload: ServicePermissionAssignPayload,
    ) -> ServicePermissions:
        try:
            service_identity = await self.service_identity_data_access.get_by_id(
                session=session,
                service_id=payload.service_identity_id,
            )

            if service_identity is None:
                raise ServiceIdentityNotFoundError("Service identity not found")

            permission = await self.permissions_data_access.get_by_id(
                session=session,
                permission_id=payload.permission_id,
            )

            if permission is None:
                raise PermissionNotFoundError("Permission not found")

            existing = await self.service_permissions_data_access.get_by_service_and_permission(
                session=session,
                service_identity_id=payload.service_identity_id,
                permission_id=payload.permission_id,
            )

            if existing is not None:
                raise ServicePermissionAlreadyExists(
                    "Permission is already assigned to this service identity"
                )

            result = await self.service_permissions_data_access.assign_permission(
                session=session,
                service_identity_id=payload.service_identity_id,
                permission_id=payload.permission_id,
            )

            await session.commit()
            return result

        except (
            ServiceIdentityNotFoundError,
            PermissionNotFoundError,
            ServicePermissionAlreadyExists,
        ):
            await session.rollback()
            raise

        except IntegrityError as exc:
            await session.rollback()
            raise DatabaseIntegrityError(
                "Database constraint violation while assigning permission"
            ) from exc

    async def get_service_permissions(
        self,
        session: AsyncSession,
        service_identity_id: UUID,
    ) -> list[ServicePermissionByServiceIdentity]:
        db_result = await self.service_permissions_data_access.get_by_service_identity(
            session=session,
            service_identity_id=service_identity_id,
        )

        return [ServicePermissionByServiceIdentity.model_validate(res) for res in db_result]

    async def remove_permission(
        self,
        session: AsyncSession,
        service_identity_id: UUID,
        permission_id: UUID,
    ) -> None:
        try:
            removed = await self.service_permissions_data_access.remove_permission(
                session=session,
                service_identity_id=service_identity_id,
                permission_id=permission_id,
            )

            if not removed:
                raise ServicePermissionNotFound("Permission assignment not found")

            await session.commit()

        except ServicePermissionNotFound:
            await session.rollback()
            raise

        except IntegrityError as exc:
            await session.rollback()
            raise DatabaseIntegrityError("Database error while removing permission") from exc

    async def check_permission(
        self,
        session: AsyncSession,
        service_identity_id: UUID,
        permission_name: str,
    ) -> bool:
        return await self.service_permissions_data_access.has_permission(
            session=session,
            service_identity_id=service_identity_id,
            permission_name=permission_name,
        )
