from uuid import UUID

from app.data_access.client_data_access import ClientRepository
from app.helpers.api_key import generate_api_key, hash_api_key
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


class ClientService:
    def __init__(self, repository: ClientRepository):
        self.repository = repository

    async def create_client(
        self, session: AsyncSession, name: str
    ) -> tuple[object, str]:
        api_key = generate_api_key()
        api_key_hash = hash_api_key(api_key=api_key)

        try:
            client = await self.repository.create(
                session=session, api_key_hash=api_key_hash, name=name
            )

            await session.commit()

            return client, api_key
        except IntegrityError as exec:
            await session.rollback()
            raise ValueError("Client could not be created") from exec

    async def get_client(self, session: AsyncSession, client_id: UUID):
        client = await self.repository.get_by_id(session=session, client_id=client_id)

        if client is None:
            raise LookupError("Client not found")

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
        except IntegrityError as exec:
            await session.rollback()
            raise ValueError("client update failed") from exec

    async def delete_client(self, session: AsyncSession, client_id: UUID):
        client = await self.get_client(session, client_id)

        await self.repository.delete(session, client)
        await session.commit()
