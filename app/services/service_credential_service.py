from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.data_access.service_credentials_data_access import ServiceCredentialsRepository
from app.data_access.service_identity_data_access import ServiceIdentityRepository
from app.exceptions.database import DatabaseIntegrityError
from app.exceptions.service_credentials import (
    InvalidServiceCredntialError,
    ServiceCredentialNotFound,
)
from app.exceptions.service_identity import ServiceIdentityNotFound
from app.schemas.service_credential import (
    ServiceCredentialPayload,
    ServiceCredentialResponse,
    ServiceCredentialResponseById,
    ServiceCredentialVerification,
    ServiceCredtialResponseByServiceIdentityId,
)
from app.security.credential_manager import CredentialManager
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


class ServiceCredtialsService:
    def __init__(
        self,
        service_credential_data_access: ServiceCredentialsRepository,
        service_identity_data_access: ServiceIdentityRepository,
        hmac_key_version: str,
        hmac_keys: dict[str, Any],
    ):
        self.service_credential_data_access = service_credential_data_access
        self.service_identity_data_access = service_identity_data_access
        self.hmac_key_version = hmac_key_version
        self.hmac_keys = hmac_keys

    async def create_service_credetial(
        self,
        session: AsyncSession,
        payload: ServiceCredentialPayload,
        service_identity_id: UUID,
    ) -> ServiceCredentialResponse:
        service_identity_data = await self.service_identity_data_access.get_by_id(
            session=session, service_id=service_identity_id
        )

        if service_identity_data is None:
            raise ServiceIdentityNotFound("Service identity not found")

        credential_id = CredentialManager.generate_credential_id()
        secret = CredentialManager.generate_secret()

        credential_hash = CredentialManager.generate_verifier(
            hmac_key=self.hmac_keys[self.hmac_key_version], secret=secret
        )

        try:
            not_before = datetime.now(UTC)
            await self.service_credential_data_access.create(
                session=session,
                credential_id=credential_id,
                credential_hash=credential_hash,
                not_before=not_before,
                name=payload.name,
                key_version=self.hmac_key_version,
                service_identity_id=service_identity_id,
            )
            await session.commit()

            return ServiceCredentialResponse.model_validate(
                {
                    "credential": f"{credential_id}:{secret}",
                    "service_identity_id": service_identity_id,
                    "name": payload.name,
                    "not_before": not_before,
                }
            )
        except IntegrityError as exc:
            await session.rollback()
            raise DatabaseIntegrityError(
                "Service credentials could not be created due to database constraints"
            ) from exc

    async def get_by_credential_id(
        self, session: AsyncSession, credential_id: str, hash: bool = False
    ) -> ServiceCredentialResponseById | ServiceCredentialVerification:
        db_result = await self.service_credential_data_access.get_by_credential_id(
            session=session, credential_id=credential_id, hash=hash
        )

        if db_result is None:
            raise ServiceCredentialNotFound(
                f"No related data was found related to service credential: {credential_id}"
            )

        if hash:
            return ServiceCredentialVerification.model_validate(db_result)

        return ServiceCredentialResponseById.model_validate(db_result)

    async def get_service_credentials(
        self, session: AsyncSession, service_identity_id: UUID
    ) -> list[ServiceCredtialResponseByServiceIdentityId]:
        db_result = await self.service_credential_data_access.get_credetials_details_by_service_id(
            session=session, service_identity_id=service_identity_id
        )
        return [ServiceCredtialResponseByServiceIdentityId.model_validate(row) for row in db_result]

    async def update_service_credential_by_id(
        self, session: AsyncSession, credential_id: str
    ) -> int:
        try:
            result = await self.service_credential_data_access.revoke_by_credential_id(
                session=session, credential_id=credential_id
            )

            await session.commit()
            return result
        except InterruptedError as exc:
            await session.rollback()
            raise DatabaseIntegrityError(
                f"Error while revoking service credential: {credential_id}"
            ) from exc

    async def rotate_credentials(
        self, session: AsyncSession, credential_id: str
    ) -> ServiceCredentialResponse:
        try:
            service_credential_data = (
                await self.service_credential_data_access.get_by_credential_id(
                    session=session,
                    credential_id=credential_id,
                )
            )

            if service_credential_data is None:
                raise ServiceCredentialNotFound(f"Service credential not found: {credential_id}")

            if service_credential_data["revoked_at"] is not None:
                raise InvalidServiceCredntialError("Cannot rotate an already revoked credential")

            new_credential_id = CredentialManager.generate_credential_id()
            new_secret = CredentialManager.generate_secret()

            credential_hash = CredentialManager.generate_verifier(
                hmac_key=self.hmac_keys[self.hmac_key_version],
                secret=new_secret,
            )

            current_time = datetime.now(UTC)

            await self.service_credential_data_access.revoke_by_credential_id(
                session=session,
                credential_id=credential_id,
            )

            await self.service_credential_data_access.create(
                session=session,
                service_identity_id=service_credential_data["service_identity_id"],
                key_version=self.hmac_key_version,
                name=service_credential_data["name"],
                not_before=current_time,
                credential_id=new_credential_id,
                credential_hash=credential_hash,
            )

            await session.commit()

            return ServiceCredentialResponse.model_validate(
                {
                    "credential": f"{new_credential_id}:{new_secret}",
                    "service_identity_id": service_credential_data["service_identity_id"],
                    "name": service_credential_data["name"],
                    "not_before": current_time,
                }
            )

        except ServiceCredentialNotFound, InvalidServiceCredntialError:
            await session.rollback()
            raise

        except IntegrityError as exc:
            await session.rollback()
            raise DatabaseIntegrityError(
                f"Database error while rotating credential: {credential_id}"
            ) from exc
