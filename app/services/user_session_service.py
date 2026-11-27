import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.data_access.user_data_access import UserRepository
from app.data_access.user_session_data_access import UserSessionRepository
from app.db.postgres.models.users import Users
from app.exceptions.user_sessions import (
    InactiveUserError,
    InvalidLoginError,
    InvalidSessionError,
)
from app.schemas.user_sessions import (
    LoginResponse,
    SessionUserResponse,
)
from pwdlib import PasswordHash
from sqlalchemy.ext.asyncio import AsyncSession

password_hasher = PasswordHash.recommended()


class UserSessionService:
    def __init__(
        self,
        user_repository: UserRepository,
        session_repository: UserSessionRepository,
        session_duration_hours: int = 8,
    ):
        self.user_repository = user_repository
        self.session_repository = session_repository
        self.session_duration = timedelta(hours=session_duration_hours)

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    async def login(
        self,
        session: AsyncSession,
        email: str,
        password: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> LoginResponse:
        normalized_email = email.strip().lower()

        user = await self.user_repository.get_by_email(
            session=session,
            email=normalized_email,
        )

        if user is None:
            raise InvalidLoginError()

        if not password_hasher.verify(
            password,
            user.password_hash,
        ):
            raise InvalidLoginError()

        if not user.is_active:
            raise InactiveUserError()

        raw_token = secrets.token_urlsafe(32)

        token_hash = self._hash_token(raw_token)

        now = datetime.now(UTC)
        expires_at = now + self.session_duration

        try:
            user_session = await self.session_repository.create(
                session=session,
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at,
                user_agent=user_agent,
                ip_address=ip_address,
            )

            await session.commit()

        except Exception:
            await session.rollback()
            raise

        return LoginResponse(
            access_token=raw_token,
            expires_at=user_session.expires_at,
            user=SessionUserResponse(
                id=user.id,
                name=user.name,
                email=user.email,
                role=user.role.value,
            ),
        )

    async def authenticate_session(
        self,
        session: AsyncSession,
        token: str,
    ) -> Users:
        token_hash = self._hash_token(token)

        user_session = await self.session_repository.get_by_token_hash(
            session=session,
            token_hash=token_hash,
        )

        if user_session is None:
            raise InvalidSessionError()

        now = datetime.now(UTC)

        if user_session.revoked_at is not None or user_session.expires_at <= now:
            raise InvalidSessionError()

        user = await self.user_repository.get_by_id(
            session=session,
            user_id=user_session.user_id,
        )

        if user is None:
            raise InvalidSessionError()

        if not user.is_active:
            raise InactiveUserError()

        return user

    async def logout(
        self,
        session: AsyncSession,
        token: str,
    ) -> None:
        token_hash = self._hash_token(token)

        user_session = await self.session_repository.get_by_token_hash(
            session=session,
            token_hash=token_hash,
        )

        if user_session is None:
            raise InvalidSessionError()

        if user_session.revoked_at is not None:
            raise InvalidSessionError()

        now = datetime.now(UTC)

        if user_session.expires_at <= now:
            raise InvalidSessionError()

        try:
            await self.session_repository.revoke(
                session=session,
                user_session=user_session,
                revoked_at=now,
            )

            await session.commit()

        except Exception:
            await session.rollback()
            raise

    async def revoke_all_sessions(
        self,
        session: AsyncSession,
        user_id: UUID,
    ) -> int:
        try:
            count = await self.session_repository.revoke_all_for_user(
                session=session,
                user_id=user_id,
                revoked_at=datetime.now(UTC),
            )

            await session.commit()

            return count

        except Exception:
            await session.rollback()
            raise
