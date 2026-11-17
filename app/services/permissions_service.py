from datetime import UTC, datetime
from uuid import UUID

from app.data_access.permissions_data_access import PermissionsRepository
from app.exceptions.base import ApplicationError
from app.exceptions.database import DatabaseIntegrityError
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


# Pydantic Schemas
class PermissionCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = None


class PermissionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = None


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


# Custom Exceptions
class PermissionNotFound(ApplicationError):
    def __init__(self, message: str) -> None:
        super().__init__(
            message,
            "PERMISSION_NOT_FOUND",
            404,
        )


class PermissionAlreadyExists(ApplicationError):
    def __init__(self, message: str) -> None:
        super().__init__(
            message,
            "PERMISSION_ALREADY_EXISTS",
            409,
        )


class PermissionsService:
    def __init__(
        self,
        permission_data_access: PermissionsRepository,
    ):
        self.permission_data_access = permission_data_access

    async def create_permission(
        self,
        session: AsyncSession,
        payload: PermissionCreate,
    ) -> PermissionResponse:
        try:
            existing = await self.permission_data_access.get_by_name(
                session=session,
                name=payload.name,
            )

            if existing is not None:
                raise PermissionAlreadyExists(f"Permission already exists: {payload.name}")

            result = await self.permission_data_access.create(
                session=session,
                name=payload.name,
                description=payload.description,
            )

            print("db _result", result)

            await session.commit()

            return PermissionResponse.model_validate(result)

        except PermissionAlreadyExists:
            await session.rollback()
            raise

        except IntegrityError as exc:
            await session.rollback()
            raise PermissionAlreadyExists(f"Permission already exists: {payload.name}") from exc

    async def get_permission_by_id(
        self,
        session: AsyncSession,
        permission_id: UUID,
    ) -> PermissionResponse:
        result = await self.permission_data_access.get_by_id(
            session=session,
            permission_id=permission_id,
        )

        if result is None:
            raise PermissionNotFound(f"Permission not found: {permission_id}")

        return PermissionResponse.model_validate(result)

    async def get_permission_by_name(
        self,
        session: AsyncSession,
        name: str,
    ) -> PermissionResponse:
        result = await self.permission_data_access.get_by_name(
            session=session,
            name=name,
        )

        if result is None:
            raise PermissionNotFound(f"Permission not found: {name}")

        return PermissionResponse.model_validate(result)

    async def get_all_permissions(
        self,
        session: AsyncSession,
    ) -> list[PermissionResponse]:
        results = await self.permission_data_access.get_all(
            session=session,
        )

        return [PermissionResponse.model_validate(permission) for permission in results]

    async def update_permission(
        self,
        session: AsyncSession,
        permission_id: UUID,
        payload: PermissionUpdate,
    ) -> PermissionResponse:
        try:
            existing = await self.permission_data_access.get_by_id(
                session=session,
                permission_id=permission_id,
            )

            if existing is None:
                raise PermissionNotFound(f"Permission not found: {permission_id}")

            update_data = payload.model_dump(exclude_unset=True)

            if not update_data:
                return PermissionResponse.model_validate(existing)

            if "name" in update_data and update_data["name"] is not None:
                duplicate = await self.permission_data_access.get_by_name(
                    session=session,
                    name=update_data["name"],
                )

                if duplicate is not None and duplicate.id != permission_id:
                    raise PermissionAlreadyExists(
                        f"Permission already exists: {update_data['name']}"
                    )

            update_data["updated_at"] = datetime.now(UTC)

            result = await self.permission_data_access.update(
                session=session,
                permission_id=permission_id,
                update_data=update_data,
            )

            await session.commit()

            return PermissionResponse.model_validate(result)

        except PermissionNotFound, PermissionAlreadyExists:
            await session.rollback()
            raise

        except IntegrityError as exc:
            await session.rollback()
            raise DatabaseIntegrityError(
                "Database constraint violation while updating permission"
            ) from exc

    async def delete_permission(
        self,
        session: AsyncSession,
        permission_id: UUID,
    ) -> None:
        try:
            deleted = await self.permission_data_access.delete(
                session=session,
                permission_id=permission_id,
            )

            if not deleted:
                raise PermissionNotFound(f"Permission not found: {permission_id}")

            await session.commit()

        except PermissionNotFound:
            await session.rollback()
            raise

        except IntegrityError as exc:
            await session.rollback()
            raise DatabaseIntegrityError(
                "Cannot delete permission because it is associated with other records"
            ) from exc
