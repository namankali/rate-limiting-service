from datetime import datetime
from uuid import UUID, uuid4

from app.db.postgres.base import Base
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    LargeBinary,
    String,
    func,
    true,
)
from sqlalchemy.dialects.postgresql import UUID as sql_uuid
from sqlalchemy.orm import Mapped, mapped_column


class ServiceCredentials(Base):
    __tablename__ = "service_credentials"

    __table_args__ = (
        CheckConstraint(
            "expires_at is NULL OR expires_at > not_before",
            name="ck_service_credentials_expiry_after_not_before",
        ),
    )

    id: Mapped[UUID] = mapped_column(sql_uuid(as_uuid=True), primary_key=True, default=uuid4)

    service_identity_id: Mapped[UUID] = mapped_column(
        sql_uuid(as_uuid=True),
        ForeignKey("service_identity.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    credential_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    credential_hash: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False)

    key_version: Mapped[str] = mapped_column(String(100), nullable=False)

    name: Mapped[str] = mapped_column(String(100), nullable=False)

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=true(), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    not_before: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
