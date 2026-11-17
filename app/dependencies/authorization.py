from typing import Annotated, Any

from app.dependencies.authentication import AuthenticatedServiceDependency
from app.exceptions.authentication_and_authorization import AuthorizationError
from app.helpers.custom_types import DataBaseSession
from fastapi import Depends, Request


async def get_authorization_service(
    session: DataBaseSession,
    request: Request,
    authenticated: AuthenticatedServiceDependency,
):
    authorised = await request.app.state.authorization.has_permission(
        service_identity_id=authenticated.get("service_id"), session=session
    )

    if not authorised:
        raise AuthorizationError("You are not authorised to access this resource")

    return authenticated


AuthorizationServiceDependency = Annotated[dict[str, Any], Depends(get_authorization_service)]
