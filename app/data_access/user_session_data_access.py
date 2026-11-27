from datetime import datetime
from uuid import UUID

from app.db.postgres.models.sessions import UserSession
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class UserSessionRepository:
    async def create(
        self,
        session: AsyncSession,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> UserSession:
        user_session = UserSession(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )

        session.add(user_session)
        await session.flush()
        await session.refresh(user_session)

        return user_session

    async def get_by_token_hash(
        self,
        session: AsyncSession,
        token_hash: str,
    ) -> UserSession | None:
        result = await session.execute(
            select(UserSession).where(UserSession.token_hash == token_hash)
        )

        return result.scalar_one_or_none()

    async def get_by_id(
        self,
        session: AsyncSession,
        session_id: UUID,
    ) -> UserSession | None:
        result = await session.execute(select(UserSession).where(UserSession.id == session_id))

        return result.scalar_one_or_none()

    async def get_active_sessions(
        self,
        session: AsyncSession,
        user_id: UUID,
        now: datetime,
    ) -> list[UserSession]:
        result = await session.execute(
            select(UserSession)
            .where(
                UserSession.user_id == user_id,
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > now,
            )
            .order_by(UserSession.created_at.desc())
        )

        return list(result.scalars().all())

    async def revoke(
        self,
        session: AsyncSession,
        user_session: UserSession,
        revoked_at: datetime,
    ) -> UserSession:
        user_session.revoked_at = revoked_at

        await session.flush()
        await session.refresh(user_session)

        return user_session

    async def revoke_all_for_user(
        self,
        session: AsyncSession,
        user_id: UUID,
        revoked_at: datetime,
    ) -> int:
        result = await session.execute(
            select(UserSession).where(
                UserSession.user_id == user_id,
                UserSession.revoked_at.is_(None),
            )
        )

        sessions = list(result.scalars().all())

        for user_session in sessions:
            user_session.revoked_at = revoked_at

        await session.flush()

        return len(sessions)
