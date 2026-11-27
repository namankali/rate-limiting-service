from typing import Any
from uuid import UUID

from app.db.postgres.models.users import Users
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class UserRepository:
    async def create(
        self,
        session: AsyncSession,
        user_data: dict[str, Any],
    ) -> Users:
        user = Users(**user_data)

        session.add(user)
        await session.flush()
        await session.refresh(user)

        return user

    async def get_by_id(
        self,
        session: AsyncSession,
        user_id: UUID,
    ) -> Users | None:
        result = await session.execute(select(Users).where(Users.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(
        self,
        session: AsyncSession,
        email: str,
    ) -> Users | None:
        result = await session.execute(select(Users).where(Users.email == email))
        return result.scalar_one_or_none()

    async def get_all(
        self,
        session: AsyncSession,
    ) -> list[Users]:
        result = await session.execute(select(Users).order_by(Users.created_at.desc()))
        return list(result.scalars().all())

    async def update(
        self,
        session: AsyncSession,
        user: Users,
        updates: dict[str, Any],
    ) -> Users:
        for field, value in updates.items():
            setattr(user, field, value)

        await session.flush()
        await session.refresh(user)

        return user
