from uuid import UUID

from fastapi import APIRouter, Request, status

from app.helpers.custom_types import DataBaseSession
from app.schemas.service_credential import (
    ServiceCredentialPayload,
    ServiceCredentialResponse,
    ServiceCredentialResponseById,
    ServiceCredtialResponseByServiceIdentityId,
)
from app.schemas.service_identity import (
    ServiceIdentityPayload,
    ServiceIdentityResponse,
    ServiceIdentityUpdate,
)

router = APIRouter()


@router.post("/", response_model=ServiceIdentityResponse, status_code=status.HTTP_201_CREATED)
async def create_service_identity_(
    payload: ServiceIdentityPayload, session: DataBaseSession, request: Request
) -> ServiceIdentityResponse:
    return await request.app.state.service_identity_service.create_service_identity(
        session=session, payload=payload
    )


@router.get("/all", response_model=list[ServiceIdentityResponse])
async def get_service_identites(
    session: DataBaseSession, request: Request
) -> list[ServiceIdentityResponse]:
    return await request.app.state.service_identity_service.get_service_identities(session=session)


@router.get("/{service_identity}", response_model=ServiceIdentityResponse)
async def get_service_identity(
    session: DataBaseSession, service_identity: UUID, request: Request
) -> ServiceIdentityResponse:
    print("hi")
    return await request.app.state.service_identity_service.get_service_identity_by_id(
        service_id=service_identity, session=session
    )


@router.patch(
    "/update/{service_identity_id}",
    response_model=ServiceIdentityResponse,
)
async def update_service_identity(
    session: DataBaseSession,
    service_identity_id: UUID,
    payload: ServiceIdentityUpdate,
    request: Request,
) -> ServiceIdentityResponse:
    updates = payload.model_dump(exclude_unset=True)

    return await request.app.state.service_identity_service.update_service_identity(
        session=session, updates=updates, service_identity_id=service_identity_id
    )


# service credentials APIs
@router.post("/{service_identity_id}/credentials")
async def create_credentials(
    request: Request,
    payload: ServiceCredentialPayload,
    service_identity_id: UUID,
    session: DataBaseSession,
) -> ServiceCredentialResponse:
    return await request.app.state.service_credentials_service.create_service_credetial(
        session=session, payload=payload, service_identity_id=service_identity_id
    )


@router.get("/credentials/{credential_id}", response_model=ServiceCredentialResponseById)
async def get_by_credential_id(
    session: DataBaseSession, credential_id: str, request: Request
) -> ServiceCredentialResponseById:
    return await request.app.state.service_credentials_service.get_by_credential_id(
        session=session, credential_id=credential_id
    )


@router.get(
    "/{service_identity_id}/credentials",
    response_model=list[ServiceCredtialResponseByServiceIdentityId],
)
async def get_credentials_service_id(
    session: DataBaseSession, service_identity_id: UUID, request: Request
) -> list[ServiceCredtialResponseByServiceIdentityId]:
    return await request.app.state.service_credentials_service.get_service_credentials(
        session=session, service_identity_id=service_identity_id
    )


@router.patch(
    "/{credential_id}/revoke",
)
async def update_service_credential(session: DataBaseSession, credential_id: str, request: Request):
    return await request.app.state.service_credentials_service.update_service_credential_by_id(
        session=session, credential_id=credential_id
    )


@router.patch(
    "/{credential_id}/rotate",
)
async def rotate_service_credential(session: DataBaseSession, credential_id: str, request: Request):
    return await request.app.state.service_credentials_service.rotate_credentials(
        session=session, credential_id=credential_id
    )
