from typing import Annotated, Any

from app.exceptions.authentication_and_authorization import AuthenticationError
from app.helpers.custom_types import DataBaseSession
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()


async def get_bearer_credential(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail={
                "message": "Authentication credential is required",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


BearerCredentials = Annotated[str, Depends(get_bearer_credential)]


async def get_authenticated_service(
    request: Request, session: DataBaseSession, credentials: BearerCredentials
):
    try:
        authenticated = await request.app.state.authentication.authenticate(
            session=session, credential=credentials
        )

        return authenticated
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


AuthenticatedServiceDependency = Annotated[dict[str, Any], Depends(get_authenticated_service)]
