from typing import cast

from fastapi import APIRouter, HTTPException, Request, status

from app.dependencies.user_authentication import (
    AuthenticatedUser,
    UserBearerToken,
)
from app.exceptions.user_sessions import (
    InactiveUserError,
    InvalidLoginError,
    InvalidSessionError,
)
from app.helpers.custom_types import DataBaseSession
from app.schemas.user_sessions import (
    LoginRequest,
    LoginResponse,
    SessionUserResponse,
)
from app.services.user_session_service import UserSessionService

router = APIRouter()


@router.post(
    "/v1/login",
    response_model=LoginResponse,
)
async def login(
    payload: LoginRequest,
    request: Request,
    session: DataBaseSession,
) -> LoginResponse:
    service = cast(
        UserSessionService,
        request.app.state.user_session_service,
    )

    client_ip = request.client.host if request.client is not None else None

    try:
        return await service.login(
            session=session,
            email=str(payload.email),
            password=payload.password,
            user_agent=request.headers.get("user-agent"),
            ip_address=client_ip,
        )

    except InvalidLoginError as exc:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    except InactiveUserError as exc:
        raise HTTPException(
            status_code=403,
            detail="User account is inactive",
        ) from exc


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def logout(
    request: Request,
    session: DataBaseSession,
    token: UserBearerToken,
) -> None:
    service = cast(
        UserSessionService,
        request.app.state.user_session_service,
    )

    try:
        await service.logout(
            session=session,
            token=token,
        )

    except InvalidSessionError as exc:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session",
        ) from exc


@router.get(
    "/me",
    response_model=SessionUserResponse,
)
async def get_current_user(
    user: AuthenticatedUser,
) -> SessionUserResponse:
    current_user = user

    return SessionUserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role.value,
    )
