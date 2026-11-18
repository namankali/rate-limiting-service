from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.data_access.client_data_access import ClientRepository
from app.data_access.policy_data_access import PolicyRepository
from app.helpers.custom_types import DataBaseSession
from app.schemas.policy import (
    PolicyCreate,
    PolicyResponse,
    PolicyUpdate,
)
from app.services.policy_service import PolicyService

router = APIRouter()

policy_service = PolicyService(
    policy=PolicyRepository(),
    client=ClientRepository(),
)


@router.post(
    "/",
    response_model=PolicyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_policy(
    payload: PolicyCreate,
    session: DataBaseSession,
) -> PolicyResponse:
    try:
        policy = await policy_service.create_policy(
            session=session,
            payload=payload,
        )

        return PolicyResponse.model_validate(policy)

    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get(
    "/",
    response_model=list[PolicyResponse],
)
async def get_all_policies(
    session: DataBaseSession,
) -> list[PolicyResponse]:
    policies = await policy_service.get_all_policies(
        session=session,
    )

    return [PolicyResponse.model_validate(policy) for policy in policies]


@router.get(
    "/client/{client_id}",
    response_model=list[PolicyResponse],
)
async def get_client_policies(
    client_id: UUID,
    session: DataBaseSession,
) -> list[PolicyResponse]:
    try:
        policies = await policy_service.get_client_policies(
            session=session,
            client_id=client_id,
        )

        return [PolicyResponse.model_validate(policy) for policy in policies]

    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/{policy_id}",
    response_model=PolicyResponse,
)
async def get_policy(policy_id: UUID, session: DataBaseSession) -> PolicyResponse:
    try:
        policy = await policy_service.get_policy(
            session=session,
            policy_id=policy_id,
        )
        return PolicyResponse.model_validate(policy)

    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{policy_id}",
    response_model=PolicyResponse,
)
async def update_policy(
    policy_id: UUID,
    payload: PolicyUpdate,
    session: DataBaseSession,
) -> PolicyResponse:
    try:
        updates = payload.model_dump(
            exclude_unset=True,
        )

        policy = await policy_service.update_policy(
            session=session,
            policy_id=policy_id,
            updates=updates,
        )

        return PolicyResponse.model_validate(policy)

    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{policy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_policy(
    policy_id: UUID,
    session: DataBaseSession,
) -> None:
    try:
        await policy_service.delete_policy(
            session=session,
            policy_id=policy_id,
        )

    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
