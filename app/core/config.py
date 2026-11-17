import base64
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    hmac_active_key_version: str
    hmac_keys: dict[str, str]
    redis_host: str
    redis_port: int
    redis_password: str | None = None
    redis_db: int
    environment: str = Field(validation_alias="ENV")

    @property
    def decode_hmac_keys(self) -> dict[str, bytes]:
        new_dict: dict[str, bytes] = {}
        for field, value in self.hmac_keys.items():
            value = base64.urlsafe_b64decode(value)
            new_dict[field] = value
        return new_dict

    @model_validator(mode="after")
    def validate_hmac_keys(self) -> Self:
        if self.hmac_active_key_version not in self.hmac_keys:
            raise ValueError("Active HMAC key is not present")

        for field, value in self.hmac_keys.items():
            if len(base64.urlsafe_b64decode(value)) != 32:
                raise ValueError(f"Invalid hmac key: {field}")

        return self
