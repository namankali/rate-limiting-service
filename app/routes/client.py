from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.data_access.client_data_access import ClientRepository
from app.helpers.custom_types import DataBaseSession
from app.schemas.client import (
    ClientCreate,
    ClientCreatedResponse,
    ClientResponse,
    ClientUpdate,
)
from app.services.client_service import ClientService

router = APIRouter()


client_service = ClientService(repository=ClientRepository())


@router.post(
    "/", response_model=ClientCreatedResponse, status_code=status.HTTP_201_CREATED
)
async def create_client(payload: ClientCreate, session: DataBaseSession):
    try:
        client, api_key = await client_service.create_client(
            session=session,
            name=payload.name,
        )

        return ClientCreatedResponse(
            id=client.id,
            name=client.name,
            is_active=client.is_active,
            created_at=client.created_at,
            updated_at=client.updated_at,
            api_key=api_key,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, details=str(e)) from e


@router.get("/all", response_model=list[ClientResponse])
async def get_clients(session: DataBaseSession):
    try:
        return await client_service.get_all_client(session=session)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(client_id: UUID, session: DataBaseSession):
    try:
        return await client_service.get_client(session=session, client_id=client_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: UUID, payload: ClientUpdate, session: DataBaseSession
):
    try:
        print("paylod ->>>>> ", payload)
        client_data = await client_service.get_client(
            session=session, client_id=client_id
        )

        if client_data is None:
            raise LookupError(f"Client_id {client_id} is not found!")

        updates = payload.model_dump(exclude_unset=True)
        updates["is_active"] = client_data.is_active

        return await client_service.update(
            client_id=client_id, session=session, updates=updates
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_count(client_id: UUID, session: DataBaseSession):
    try:
        await client_service.delete_client(client_id=client_id, session=session)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
