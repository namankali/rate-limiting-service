from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ServicePermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    service_identity_id: UUID
    permission_id: UUID
    created_at: datetime


class ServicePermissionByServiceIdentity(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    service_identity_id: UUID
    permission_id: UUID
    permission_name: str
    permission_description: str
    created_at: datetime
