from datetime import UTC, datetime
from uuid import UUID

from app.data_access.user_data_access import UserRepository
from app.db.postgres.models.users import UserRole
from app.exceptions.database import DatabaseIntegrityError
from app.exceptions.user import (
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.schemas.users import UserCreate, UserResponse, UserUpdate
from pwdlib import PasswordHash
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

password_hash = PasswordHash.recommended()


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def create_user(
        self,
        session: AsyncSession,
        payload: UserCreate,
    ) -> UserResponse:
        email = str(payload.email).strip().lower()

        existing = await self.repository.get_by_email(
            session=session,
            email=email,
        )

        if existing is not None:
            raise UserAlreadyExistsError(f"User already exists: {email}")

        hashed_password = password_hash.hash(payload.password)

        user_data = {
            "name": payload.name,
            "email": email,
            "password_hash": hashed_password,
            "role": payload.role,
        }

        try:
            user = await self.repository.create(
                session=session,
                user_data=user_data,
            )

            await session.commit()

            return UserResponse.model_validate(user)

        except IntegrityError as exc:
            await session.rollback()
            raise UserAlreadyExistsError("A user with this email already exists") from exc

    async def get_user(
        self,
        session: AsyncSession,
        user_id: UUID,
    ) -> UserResponse:
        user = await self.repository.get_by_id(
            session=session,
            user_id=user_id,
        )

        if user is None:
            raise UserNotFoundError()

        return UserResponse.model_validate(user)

    async def get_all_users(
        self,
        session: AsyncSession,
    ) -> list[UserResponse]:
        users = await self.repository.get_all(session=session)

        return [UserResponse.model_validate(user) for user in users]

    async def update_user(
        self,
        session: AsyncSession,
        user_id: UUID,
        payload: UserUpdate,
    ) -> UserResponse:
        user = await self.repository.get_by_id(
            session=session,
            user_id=user_id,
        )

        if user is None:
            raise UserNotFoundError()

        updates = payload.model_dump(
            exclude_unset=True,
        )

        if "email" in updates and updates["email"] is not None:
            email = str(updates["email"]).strip().lower()

            existing = await self.repository.get_by_email(
                session=session,
                email=email,
            )

            if existing is not None and existing.id != user_id:
                raise UserAlreadyExistsError(f"User already exists: {email}")

            updates["email"] = email

        if not updates:
            return UserResponse.model_validate(user)

        updates["updated_at"] = datetime.now(UTC)

        try:
            updated_user = await self.repository.update(
                session=session,
                user=user,
                updates=updates,
            )

            await session.commit()

            return UserResponse.model_validate(updated_user)

        except IntegrityError as exc:
            await session.rollback()
            raise UserAlreadyExistsError(
                "User update failed because the email already exists"
            ) from exc

    async def deactivate_user(
        self,
        session: AsyncSession,
        user_id: UUID,
    ) -> None:
        user = await self.repository.get_by_id(
            session=session,
            user_id=user_id,
        )

        if user is None:
            raise UserNotFoundError()

        if user.role == UserRole.ADMIN:
            # Prevent accidentally disabling the last administrator.
            users = await self.repository.get_all(session=session)

            active_admins = [
                item for item in users if item.role == UserRole.ADMIN and item.is_active
            ]

            if len(active_admins) <= 1:
                raise ValueError("Cannot deactivate the last active administrator")

        try:
            await self.repository.update(
                session=session,
                user=user,
                updates={
                    "is_active": False,
                    "updated_at": datetime.now(UTC),
                },
            )

            await session.commit()

        except IntegrityError as exc:
            await session.rollback()
            raise DatabaseIntegrityError("User could not be deactivated") from exc
