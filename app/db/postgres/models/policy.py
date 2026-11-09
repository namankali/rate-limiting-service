import uuid
from datetime import datetime
from typing import Any

from app.db.postgres.base import Base
from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    identifier: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    resource: Mapped[str] = mapped_column(String(100), nullable=False)

    route: Mapped[str] = mapped_column(String(255), nullable=False)

    algorithm: Mapped[str] = mapped_column(String(50), nullable=False)

    identity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    quota_scope: Mapped[str] = mapped_column(String(50), nullable=False)

    algorithm_config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
