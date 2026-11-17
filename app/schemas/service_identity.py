from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ServiceIdentityPayload(BaseModel):
    client_id: UUID
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=255)


class ServiceIdentityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    client_id: UUID
    id: UUID
    name: str
    description: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ServiceIdentityUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = None
    is_active: bool | None = Field(default=None, min_length=2, max_length=255)

    @model_validator(mode="after")
    def validate_update(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("Atleast one field must. be provided")
        print("filed names ->> model_fields_set", self.model_fields_set)

        for field_name in self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")
        return self
