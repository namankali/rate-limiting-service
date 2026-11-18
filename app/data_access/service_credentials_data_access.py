from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID

from app.db.postgres.models.client import Client
from app.db.postgres.models.service_credentials import ServiceCredentials
from app.db.postgres.models.service_identity import ServiceIdentity
from sqlalchemy import RowMapping, or_, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession


class ServiceCredentialsRepository:
    async def create(
        self,
        session: AsyncSession,
        service_identity_id: UUID,
        key_version: str,
        name: str,
        not_before: datetime,
        credential_id: str,
        credential_hash: bytes,
    ) -> ServiceCredentials:
        service_cred = ServiceCredentials(
            service_identity_id=service_identity_id,
            key_version=key_version,
            name=name,
            not_before=not_before,
            credential_hash=credential_hash,
            credential_id=credential_id,
        )

        session.add(service_cred)
        await session.flush()
        await session.refresh(service_cred)

        return service_cred

    async def get_by_credential_id(
        self, session: AsyncSession, credential_id: str, hash: bool = False
    ) -> RowMapping | None:
        columns = [
            ServiceCredentials.id,
            ServiceCredentials.name,
            ServiceCredentials.expires_at,
            ServiceCredentials.last_used_at,
            ServiceCredentials.key_version,
            ServiceCredentials.revoked_at,
            ServiceCredentials.is_active.label("service_credential_is_active"),
            ServiceIdentity.id.label("service_identity_id"),
            ServiceIdentity.name.label("service_identity_name"),
            ServiceIdentity.is_active.label("service_identity_is_active"),
        ]

        if hash:
            columns.append(ServiceCredentials.credential_hash)
            columns.append(ServiceCredentials.not_before)
            columns.append(ServiceIdentity.client_id)
            columns.append(Client.name.label("client_name"))

        query = (
            select(*columns)
            .outerjoin(
                ServiceIdentity,
                ServiceCredentials.service_identity_id == ServiceIdentity.id,
            )
            .outerjoin(Client, Client.id == ServiceIdentity.client_id)
            .where(ServiceCredentials.credential_id == credential_id)
        )

        result = await session.execute(query)
        return result.mappings().one_or_none()

    async def get_credetials_details_by_service_id(
        self, session: AsyncSession, service_identity_id: UUID
    ) -> Sequence[RowMapping]:
        query = select(
            ServiceCredentials.service_identity_id,
            ServiceCredentials.credential_id,
            ServiceCredentials.name,
            ServiceCredentials.expires_at,
            ServiceCredentials.last_used_at,
            ServiceIdentity.name.label("service_identity_name"),
            ServiceIdentity.description.label("service_identity_label"),
        ).where(ServiceCredentials.service_identity_id == service_identity_id)

        result = await session.execute(query)
        return result.mappings().all()

    async def get_valid_credential_by_credential_id(
        self, session: AsyncSession, credential_id: str
    ) -> ServiceCredentials | None:
        query = (
            select(ServiceCredentials)
            .where(ServiceCredentials.credential_id == credential_id)
            .where(ServiceCredentials.is_active.is_(True))
            .where(
                or_(
                    ServiceCredentials.expires_at.is_(None),
                    ServiceCredentials.expires_at > datetime.now(UTC),
                )
            )
        )

        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def revoke_by_credential_id(self, session: AsyncSession, credential_id: str) -> int:
        current_time = datetime.now(UTC)
        query = (
            update(ServiceCredentials)
            .where(ServiceCredentials.credential_id == credential_id)
            .where(ServiceCredentials.revoked_at.is_(None))
        ).values(
            {
                ServiceCredentials.revoked_at: current_time,
                ServiceCredentials.is_active: False,
                ServiceCredentials.updated_at: current_time,
            }
        )

        result = await session.execute(query)
        cursor_result = cast(CursorResult[Any], result)

        return cursor_result.rowcount

    async def update_last_used(self, session: AsyncSession, credential_id: str) -> int:
        current_time = datetime.now(UTC)

        query = (
            update(ServiceCredentials)
            .where(ServiceCredentials.credential_id == credential_id)
            .values({ServiceCredentials.last_used_at: current_time})
        )

        result = await session.execute(query)
        cursor_result = cast(CursorResult[Any], result)
        return cursor_result.rowcount
