from datetime import datetime
from typing import Any, Self
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from app.policies.policy import (
    IdentityTypes,
    QuotaScope,
    RateLimitAlgorithms,
    Resources,
)

# Algorithm configuration schemas


class FixedWindowConfigSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int = Field(gt=0)
    window_seconds: float = Field(gt=0, allow_inf_nan=False)


class SlidingWindowConfigSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int = Field(gt=0)
    window_seconds: float = Field(gt=0, allow_inf_nan=False)


class TokenBucketConfigSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capacity: int = Field(gt=0)
    refill_rate: float = Field(gt=0, allow_inf_nan=False)


class LeakyBucketConfigSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capacity: int = Field(gt=0)
    leak_rate: float = Field(gt=0, allow_inf_nan=False)


# Policy create schema


class PolicyCreate(BaseModel):
    client_id: UUID
    name: str = Field(min_length=2, max_length=150)
    resource: Resources
    method: str
    route: str = Field(min_length=1, max_length=255)
    algorithm: RateLimitAlgorithms
    algorithm_config: dict[str, Any]

    identity_type: IdentityTypes
    quota_scope: QuotaScope = QuotaScope.PER_IDENTITY

    @model_validator(mode="after")
    def validate_algorithm_config(self) -> Self:
        config_schemas: dict[RateLimitAlgorithms, type[BaseModel]] = {
            RateLimitAlgorithms.FIXED_WINDOW: FixedWindowConfigSchema,
            RateLimitAlgorithms.SLIDING_WINDOW_LOG: SlidingWindowConfigSchema,
            RateLimitAlgorithms.TOKEN_BUCKET: TokenBucketConfigSchema,
            RateLimitAlgorithms.LEAKY_BUCKET: LeakyBucketConfigSchema,
        }

        config_schema = config_schemas[self.algorithm]

        validated_config = config_schema.model_validate(self.algorithm_config)

        self.algorithm_config = validated_config.model_dump()

        return self


# Policy update schema


class PolicyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    resource: Resources | None = None
    route: str | None = Field(default=None, min_length=1, max_length=255)

    algorithm: RateLimitAlgorithms | None = None
    algorithm_config: dict[str, Any] | None = None

    identity_type: IdentityTypes | None = None
    quota_scope: QuotaScope | None = None

    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_update(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")

        for field_name in self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")

        return self


# Policy response schemas


class PolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    identifier: str
    client_id: UUID
    name: str
    resource: str
    route: str
    algorithm: str
    algorithm_config: dict[str, Any]
    identity_type: str
    quota_scope: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
