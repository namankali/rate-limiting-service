from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ServiceCredentialPayload(BaseModel):
    name: str


class ServiceCredentialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    credential: str
    service_identity_id: UUID
    name: str
    not_before: datetime


class ServiceCredentialResponseById(BaseModel):
    id: UUID
    name: str
    revoked_at: datetime | None = None
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    service_credential_is_active: bool
    service_identity_id: UUID
    service_identity_name: str
    service_identity_is_active: bool
    key_version: str


class ServiceCredentialVerification(BaseModel):
    id: UUID
    credential_hash: bytes
    key_version: str
    service_credential_is_active: bool
    service_identity_id: UUID
    service_identity_is_active: bool
    revoked_at: datetime | None = None
    expires_at: datetime | None = None
    not_before: datetime
    client_id: UUID
    client_name: str


class ServiceCredtialResponseByServiceIdentityId(BaseModel):
    service_identity_id: UUID
    credential_id: str
    name: str
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    service_identity_name: str
    service_identity_label: str
