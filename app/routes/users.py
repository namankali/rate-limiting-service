from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from app.dependencies.admin import require_admin
from app.helpers.custom_types import DataBaseSession
from app.schemas.users import (
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.services.user_service import UserService

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(require_admin)],
)


@router.post(
    "/v1/insert",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    payload: UserCreate,
    session: DataBaseSession,
    request: Request,
) -> UserResponse:
    service = cast(UserService, request.app.state.user_service)

    return await service.create_user(
        session=session,
        payload=payload,
    )


@router.get(
    "/v1/fetch",
    response_model=list[UserResponse],
)
async def get_all_users(
    session: DataBaseSession,
    request: Request,
) -> list[UserResponse]:
    service = cast(UserService, request.app.state.user_service)

    return await service.get_all_users(
        session=session,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
async def get_user(
    user_id: UUID,
    session: DataBaseSession,
    request: Request,
) -> UserResponse:
    service = cast(UserService, request.app.state.user_service)

    return await service.get_user(
        session=session,
        user_id=user_id,
    )


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
)
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    session: DataBaseSession,
    request: Request,
) -> UserResponse:
    service = cast(UserService, request.app.state.user_service)

    return await service.update_user(
        session=session,
        user_id=user_id,
        payload=payload,
    )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def deactivate_user(
    user_id: UUID,
    session: DataBaseSession,
    request: Request,
) -> None:
    service = cast(UserService, request.app.state.user_service)

    await service.deactivate_user(
        session=session,
        user_id=user_id,
    )
