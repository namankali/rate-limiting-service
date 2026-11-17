from datetime import datetime
from uuid import UUID, uuid4

from app.db.postgres.base import Base
from sqlalchemy import Boolean, DateTime, ForeignKey, String, func, true
from sqlalchemy.dialects.postgresql import UUID as sql_uuid
from sqlalchemy.orm import Mapped, mapped_column


class ServiceIdentity(Base):
    __tablename__ = "service_identity"

    id: Mapped[UUID] = mapped_column(sql_uuid(as_uuid=True), primary_key=True, default=uuid4)

    client_id: Mapped[UUID] = mapped_column(
        sql_uuid(as_uuid=True),
        ForeignKey("clients.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    description: Mapped[str] = mapped_column(String(255), nullable=True)

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
