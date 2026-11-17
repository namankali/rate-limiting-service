from datetime import datetime
from uuid import UUID, uuid4

from app.db.postgres.base import Base
from sqlalchemy import (
    DateTime,
    ForeignKey,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column


class ServicePermissions(Base):
    __tablename__ = "service_permissions"

    __table_args__ = (
        UniqueConstraint(
            "service_identity_id",
            "permission_id",
            name="uq_service_identity_permission",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    service_identity_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("service_identity.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    permission_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
