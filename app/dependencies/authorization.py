from typing import Annotated, cast

from app.dependencies.authentication import AuthenticatedServiceDependency
from app.exceptions.authentication_and_authorization import AuthorizationError
from app.helpers.custom_types import DataBaseSession
from app.services.authentication import AuthenticateResponse
from app.services.authorization import AuthorizationService
from fastapi import Depends, Request


async def get_authorization_service(
    session: DataBaseSession,
    request: Request,
    authenticated: AuthenticatedServiceDependency,
) -> AuthenticateResponse:
    service = cast(AuthorizationService, request.app.state.authorization)
    authorised = await service.has_permission(
        service_identity_id=authenticated.service_id, session=session
    )

    if not authorised:
        raise AuthorizationError("You are not authorised to access this resource")

    return authenticated


AuthorizationServiceDependency = Annotated[AuthenticateResponse, Depends(get_authorization_service)]
