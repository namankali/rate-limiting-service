from ipaddress import ip_address
from typing import Any, Self

from pydantic import BaseModel, Field, model_validator

from app.policies.policy import IdentityTypes, Resources


class RateLimitRequest(BaseModel):
    resource: Resources
    route: str = Field(min_length=1)
    identity_type: str
    method: str
    identity_value: str = Field(min_length=1)

    @model_validator(mode="before")
    @classmethod
    def normalise_input(cls, data: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(data, dict):
            return data

        data = data.copy()

        for field in ("resource", "route", "identity_type", "identity_value"):
            value = data.get(field)

            if isinstance(value, str):
                data[field] = value.strip()

        return data

    @model_validator(mode="after")
    def validate_identity(self) -> Self:
        if not self.route:
            raise ValueError("Route cannot be empty")

        if not self.identity_value:
            raise ValueError("Identity value cannot be empty")

        if self.identity_type == IdentityTypes.IP_ADDRESS:
            try:
                ip_address(self.identity_value)
            except ValueError:
                raise ValueError("Invalid IP address") from None

        self.method = self.method.lower()

        return self


class RateLimitResponse(BaseModel):
    allowed: bool
    policy: str | None = None
    limit: int | None = Field(default=None, gt=0)
    remaining: int | None = Field(default=None, ge=0)
    retry_after: float | None = Field(default=None, ge=0.0)
