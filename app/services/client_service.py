from uuid import UUID

from app.data_access.client_data_access import ClientRepository
from app.exceptions.client import ClientNotFoundError
from app.exceptions.database import DatabaseIntegrityError
from app.helpers.api_key import generate_api_key, hash_api_key
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


class ClientService:
    def __init__(self, repository: ClientRepository):
        self.repository = repository

    async def create_client(self, session: AsyncSession, name: str) -> tuple[object, str]:
        api_key = generate_api_key()
        api_key_hash = hash_api_key(api_key=api_key)

        try:
            client = await self.repository.create(
                session=session, api_key_hash=api_key_hash, name=name
            )

            await session.commit()

            return client, api_key
        except IntegrityError as exc:
            await session.rollback()
            raise DatabaseIntegrityError("Client could not be created") from exc

    async def get_client(self, session: AsyncSession, client_id: UUID):
        client = await self.repository.get_by_id(session=session, client_id=client_id)

        if client is None:
            raise ClientNotFoundError("Client not found")

        return client

    async def get_all_client(self, session: AsyncSession):
        return await self.repository.get_all_client(session=session)

    async def update(self, session: AsyncSession, client_id: UUID, updates: dict):
        client = await self.get_client(client_id=client_id, session=session)

        try:
            update_client = await self.repository.update(
                session=session, client=client, updates=updates
            )

            await session.commit()
            return update_client
        except IntegrityError as exc:
            await session.rollback()
            raise DatabaseIntegrityError("client update failed") from exc

    async def delete_client(self, session: AsyncSession, client_id: UUID):
        client = await self.get_client(session, client_id)

        try:
            await self.repository.delete(session, client)
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            raise DatabaseIntegrityError("Client could not be deleted") from exc
