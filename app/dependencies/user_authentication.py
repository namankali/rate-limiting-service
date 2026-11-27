from typing import Annotated, cast

from app.db.postgres.models.users import Users
from app.exceptions.user_sessions import (
    InactiveUserError,
    InvalidSessionError,
)
from app.helpers.custom_types import DataBaseSession
from app.services.user_session_service import UserSessionService
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer(auto_error=False)


async def get_user_bearer_token(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(security),
    ],
) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Administrator authentication is required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return credentials.credentials


UserBearerToken = Annotated[
    str,
    Depends(get_user_bearer_token),
]


async def get_authenticated_user(
    request: Request,
    session: DataBaseSession,
    token: UserBearerToken,
) -> Users:
    service = cast(
        UserSessionService,
        request.app.state.user_session_service,
    )

    try:
        return await service.authenticate_session(
            session=session,
            token=token,
        )

    except InvalidSessionError as exc:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    except InactiveUserError as exc:
        raise HTTPException(
            status_code=403,
            detail="User account is inactive",
        ) from exc


AuthenticatedUser = Annotated[
    Users,
    Depends(get_authenticated_user),
]
