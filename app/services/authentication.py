from datetime import UTC, datetime

from app.data_access.service_credentials_data_access import ServiceCredentialsRepository
from app.exceptions.authentication_and_authorization import AuthenticationError
from app.exceptions.database import DatabaseIntegrityError
from app.security.credential_manager import CredentialManager
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


class Authentication:
    def __init__(self, service_credential_data_access: ServiceCredentialsRepository, hmac_keys):
        self.service_credential_data_access = service_credential_data_access
        self.hmac_keys = hmac_keys

    async def authenticate(self, credential: str, session: AsyncSession):
        parts = credential.split(":", maxsplit=1)
        if len(parts) != 2 or not all(parts):
            raise AuthenticationError("Invalid credential format")
        credential_id, secret = parts

        try:
            credential_data = await self.service_credential_data_access.get_by_credential_id(
                session=session, credential_id=credential_id, hash=True
            )

            if credential_data is None:
                raise AuthenticationError("Invalid credentials")

            hmac_key = self.hmac_keys.get(credential_data.key_version)

            if hmac_key is None:
                raise AuthenticationError("Credential key version is unavailable")

            verify_credential = CredentialManager.verify_credential(
                hmac_key=hmac_key,
                secret=secret,
                stored_verifier=credential_data.credential_hash,
            )

            current_time = datetime.now(UTC)

            if not verify_credential:
                raise AuthenticationError("Credential mistmatch")
            if not credential_data.service_credential_is_active:
                raise AuthenticationError("Credential inactive")
            if credential_data.revoked_at is not None:
                raise AuthenticationError("Credential revoked")
            if credential_data.not_before > current_time:
                raise AuthenticationError("Credential not valid yet")
            if not credential_data.service_identity_is_active:
                raise AuthenticationError("Service identoty is inactive")
            if (
                credential_data.expires_at is not None
                and credential_data.expires_at <= current_time
            ):
                raise AuthenticationError("Credential expired")

            update_last_used = await self.service_credential_data_access.update_last_used(
                session=session, credential_id=credential_id
            )
            if update_last_used != 1:
                raise AuthenticationError("Credential could not be updated")

            return {
                "service_id": credential_data.service_identity_id,
                "client_id": credential_data.client_id,
                "client_name": credential_data.client_name,
            }

        except IntegrityError as exc:
            raise DatabaseIntegrityError(
                f"Error occured which authenticating credential_id: {credential_id}"
            ) from exc
