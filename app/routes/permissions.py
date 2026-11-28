from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from app.dependencies.admin import require_admin
from app.helpers.custom_types import DataBaseSession
from app.services.permissions_service import (
    PermissionCreate,
    PermissionResponse,
    PermissionsService,
    PermissionUpdate,
)

router = APIRouter(
    prefix="/permissions", tags=["Permissions"], dependencies=[Depends(require_admin)]
)


@router.post(
    "/",
    response_model=PermissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_permission(
    payload: PermissionCreate,
    session: DataBaseSession,
    request: Request,
) -> PermissionResponse:
    service = cast(PermissionsService, request.app.state.permissions_service)

    return await service.create_permission(
        session=session,
        payload=payload,
    )


@router.get(
    "/all",
    response_model=list[PermissionResponse],
)
async def get_all_permissions(
    session: DataBaseSession,
    request: Request,
) -> list[PermissionResponse]:
    service = cast(PermissionsService, request.app.state.permissions_service)

    return await service.get_all_permissions(
        session=session,
    )


@router.get(
    "/by-name/{name}",
    response_model=PermissionResponse,
)
async def get_permission_by_name(
    name: str,
    session: DataBaseSession,
    request: Request,
) -> PermissionResponse:
    service = cast(PermissionsService, request.app.state.permissions_service)

    return await service.get_permission_by_name(
        session=session,
        name=name,
    )


@router.get(
    "/{permission_id}",
    response_model=PermissionResponse,
)
async def get_permission_by_id(
    permission_id: UUID,
    session: DataBaseSession,
    request: Request,
) -> PermissionResponse:
    service = cast(PermissionsService, request.app.state.permissions_service)

    return await service.get_permission_by_id(
        session=session,
        permission_id=permission_id,
    )


@router.patch(
    "/{permission_id}",
    response_model=PermissionResponse,
)
async def update_permission(
    permission_id: UUID,
    payload: PermissionUpdate,
    session: DataBaseSession,
    request: Request,
) -> PermissionResponse:
    service = cast(PermissionsService, request.app.state.permissions_service)

    return await service.update_permission(
        session=session,
        permission_id=permission_id,
        payload=payload,
    )


@router.delete(
    "/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_permission(
    permission_id: UUID,
    session: DataBaseSession,
    request: Request,
) -> None:
    service = cast(PermissionsService, request.app.state.permissions_service)

    await service.delete_permission(
        session=session,
        permission_id=permission_id,
    )
