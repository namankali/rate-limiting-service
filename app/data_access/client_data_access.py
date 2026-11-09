from uuid import UUID

from app.db.postgres.models.client import Client
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class ClientRepository:
    async def create(
        self, session: AsyncSession, name: str, api_key_hash: str
    ) -> Client:
        client = Client(name=name, api_key_hash=api_key_hash)

        session.add(client)
        await session.flush()
        await session.refresh(client)

        return client

    async def get_by_id(self, session: AsyncSession, client_id: UUID) -> Client | None:
        result = await session.execute(select(Client).where(Client.id == client_id))
        return result.scalar_one_or_none()

    async def get_by_api_key_hash(
        self, session: AsyncSession, api_key_hash: str
    ) -> Client | None:
        result = await session.execute(
            select(Client).where(Client.api_key_hash == api_key_hash)
        )
        return result.scalar_one_or_none()

    async def get_all_client(self, session: AsyncSession) -> list[Client]:
        result = await session.execute(
            select(Client).order_by(Client.created_at.desc())
        )
        return list(result.scalars().all())

    async def update(
        self, session: AsyncSession, client: Client, updates: dict
    ) -> Client:
        for field, value in updates.items():
            setattr(client, field, value)

        await session.flush()
        await session.refresh(client)

        return client

    async def delete(
        self,
        session: AsyncSession,
        client: Client,
    ) -> None:
        await session.delete(client)
        await session.flush()
