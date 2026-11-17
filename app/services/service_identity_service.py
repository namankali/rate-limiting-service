from typing import Any
from uuid import UUID

from app.data_access.client_data_access import ClientRepository
from app.data_access.service_identity_data_access import ServiceIdentityRepository
from app.db.postgres.models.service_identity import (
    ServiceIdentity as ServiceIdentityModel,
)
from app.exceptions.client import ClientNotFoundError
from app.exceptions.database import DatabaseIntegrityError
from app.exceptions.service_identity import (
    InvalidServiceIdentityError,
    ServiceIdentityNotFound,
)
from app.schemas.service_identity import ServiceIdentityPayload
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


class ServiceIdentityService:
    def __init__(self, service_identity: ServiceIdentityRepository, client: ClientRepository):
        self.service_identity = service_identity
        self.client = client

    async def create_service_identity(
        self, session: AsyncSession, payload: ServiceIdentityPayload
    ) -> ServiceIdentityModel:
        client = await self.client.get_by_id(client_id=payload.client_id, session=session)

        if client is None or not client.is_active:
            raise ClientNotFoundError("Client not found")

        try:
            serv_identity = await self.service_identity.create(
                session=session,
                description=payload.description,
                name=payload.name,
                client_id=payload.client_id,
            )
            await session.commit()
            return serv_identity
        except IntegrityError as exc:
            await session.rollback()
            raise DatabaseIntegrityError(
                "Service Identity could not be created due to a database constraint"
            ) from exc

    async def get_service_identity_by_id(
        self, session: AsyncSession, service_id: UUID
    ) -> ServiceIdentityModel:
        try:
            db_result = await self.service_identity.get_by_id(
                session=session, service_id=service_id
            )

            if db_result is None:
                raise ServiceIdentityNotFound("Service identity not found")

            return db_result
        except IntegrityError as exc:
            raise DatabaseIntegrityError("Error while fetching service identity") from exc

    async def get_service_identities(self, session: AsyncSession) -> list[ServiceIdentityModel]:
        try:
            db_result = await self.service_identity.get_all(session=session)
            print("db-result", db_result)
            return db_result
        except IntegrityError as exc:
            raise DatabaseIntegrityError("Error while fetching service identity") from exc

    async def update_service_identity(
        self, session: AsyncSession, service_identity_id: UUID, updates: dict[str, Any]
    ) -> ServiceIdentityModel:
        service_identity_db = await self.get_service_identity_by_id(
            service_id=service_identity_id, session=session
        )

        allowed_fields = {"name", "description", "is_active"}

        invalid_fields = set(updates) - allowed_fields

        if invalid_fields:
            raise InvalidServiceIdentityError(
                f"Unsupported fields: {', '.join(sorted(invalid_fields))}"
            )

        if not updates:
            raise InvalidServiceIdentityError("Atleast one field must be provided")

        try:
            upated_service_identity = await self.service_identity.update(
                service_identity=service_identity_db, updates=updates, session=session
            )

            await session.commit()
            return upated_service_identity
        except IntegrityError as exc:
            await session.rollback()
            raise DatabaseIntegrityError(
                "Service identity could not be updated due to database constraints"
            ) from exc
