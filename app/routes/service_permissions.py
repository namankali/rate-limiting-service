from typing import cast
from uuid import UUID

from fastapi import APIRouter, Request, status

from app.helpers.custom_types import DataBaseSession
from app.services.service_permissions import (
    ServicePermissionAssignPayload,
    ServicePermissionsService,
)

router = APIRouter(
    prefix="/service-permissions",
    tags=["Service Permissions"],
)


@router.post(
    "/assign",
    status_code=status.HTTP_201_CREATED,
)
async def assign_permission(
    payload: ServicePermissionAssignPayload,
    session: DataBaseSession,
    request: Request,
):
    service = cast(ServicePermissionsService, request.app.state.service_permissions_service)
    return await service.assign_permission(
        session=session,
        payload=payload,
    )


@router.get("/{service_identity_id}")
async def get_service_permissions(
    service_identity_id: UUID,
    session: DataBaseSession,
    request: Request,
):
    service = cast(ServicePermissionsService, request.app.state.service_permissions_service)
    return await service.get_service_permissions(
        session=session,
        service_identity_id=service_identity_id,
    )


@router.delete(
    "/{service_identity_id}/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_permission(
    service_identity_id: UUID,
    permission_id: UUID,
    session: DataBaseSession,
    request: Request,
):
    service = cast(ServicePermissionsService, request.app.state.service_permissions_service)
    await service.remove_permission(
        session=session,
        service_identity_id=service_identity_id,
        permission_id=permission_id,
    )


@router.get("/{service_identity_id}/check/{permission_name}")
async def check_permission(
    service_identity_id: UUID,
    permission_name: str,
    session: DataBaseSession,
    request: Request,
) -> dict[str, bool]:
    service = cast(ServicePermissionsService, request.app.state.service_permissions_service)
    allowed = await service.check_permission(
        session=session,
        service_identity_id=service_identity_id,
        permission_name=permission_name,
    )

    return {"allowed": allowed}
