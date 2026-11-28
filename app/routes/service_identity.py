from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from app.dependencies.admin import require_admin
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
from app.services.service_credential_service import ServiceCredtialsService
from app.services.service_identity_service import ServiceIdentityService

router = APIRouter(dependencies=[Depends(require_admin)])


@router.post("/", response_model=ServiceIdentityResponse, status_code=status.HTTP_201_CREATED)
async def create_service_identity_(
    payload: ServiceIdentityPayload, session: DataBaseSession, request: Request
) -> ServiceIdentityResponse:
    service = cast(ServiceIdentityService, request.app.state.service_identity_service)

    service_identity = await service.create_service_identity(session=session, payload=payload)

    return ServiceIdentityResponse.model_validate(service_identity)


@router.get("/all", response_model=list[ServiceIdentityResponse])
async def get_service_identites(
    session: DataBaseSession, request: Request
) -> list[ServiceIdentityResponse]:
    service = cast(ServiceIdentityService, request.app.state.service_identity_service)

    service_identites = await service.get_service_identities(session=session)

    return [ServiceIdentityResponse.model_validate(si) for si in service_identites]


@router.get("/{service_identity}", response_model=ServiceIdentityResponse)
async def get_service_identity(
    session: DataBaseSession, service_identity: UUID, request: Request
) -> ServiceIdentityResponse:
    service = cast(ServiceIdentityService, request.app.state.service_identity_service)

    service_identity_record = await service.get_service_identity_by_id(
        service_id=service_identity, session=session
    )

    return ServiceIdentityResponse.model_validate(service_identity_record)


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
    service = cast(ServiceIdentityService, request.app.state.service_identity_service)

    updates = payload.model_dump(exclude_unset=True)

    service_identity = await service.update_service_identity(
        session=session, updates=updates, service_identity_id=service_identity_id
    )

    return ServiceIdentityResponse.model_validate(service_identity)


# service credentials APIs
@router.post("/{service_identity_id}/credentials")
async def create_credentials(
    request: Request,
    payload: ServiceCredentialPayload,
    service_identity_id: UUID,
    session: DataBaseSession,
) -> ServiceCredentialResponse:
    service = cast(ServiceCredtialsService, request.app.state.service_credentials_service)

    return await service.create_service_credetial(
        session=session, payload=payload, service_identity_id=service_identity_id
    )


@router.get("/credentials/{credential_id}", response_model=ServiceCredentialResponseById)
async def get_by_credential_id(
    session: DataBaseSession, credential_id: str, request: Request
) -> ServiceCredentialResponseById:
    service = cast(ServiceCredtialsService, request.app.state.service_credentials_service)

    service_credential = await service.get_by_credential_id(
        session=session, credential_id=credential_id
    )

    return ServiceCredentialResponseById.model_validate(service_credential)


@router.get(
    "/{service_identity_id}/credentials",
    response_model=list[ServiceCredtialResponseByServiceIdentityId],
)
async def get_credentials_service_id(
    session: DataBaseSession, service_identity_id: UUID, request: Request
) -> list[ServiceCredtialResponseByServiceIdentityId]:
    service = cast(ServiceCredtialsService, request.app.state.service_credentials_service)

    service_credentials = await service.get_service_credentials(
        session=session, service_identity_id=service_identity_id
    )

    return [
        ServiceCredtialResponseByServiceIdentityId.model_validate(service_credential)
        for service_credential in service_credentials
    ]


@router.patch(
    "/{credential_id}/revoke",
)
async def update_service_credential(
    session: DataBaseSession, credential_id: str, request: Request
) -> int:
    service = cast(ServiceCredtialsService, request.app.state.service_credentials_service)

    return await service.update_service_credential_by_id(
        session=session, credential_id=credential_id
    )


@router.patch("/{credential_id}/rotate", response_model=ServiceCredentialResponse)
async def rotate_service_credential(
    session: DataBaseSession, credential_id: str, request: Request
) -> ServiceCredentialResponse:
    service = cast(ServiceCredtialsService, request.app.state.service_credentials_service)

    service_cred = await service.rotate_credentials(session=session, credential_id=credential_id)

    return ServiceCredentialResponse.model_validate(service_cred)
