"""Zone model — geographic delivery zones."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Zone(Base):
    __tablename__ = "zones"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    areas: Mapped[list["Area"]] = relationship("Area", back_populates="zone")
    pickup_orders: Mapped[list["Order"]] = relationship(
        "Order", foreign_keys="Order.pickup_zone_id", back_populates="pickup_zone"
    )
    drop_orders: Mapped[list["Order"]] = relationship(
        "Order", foreign_keys="Order.drop_zone_id", back_populates="drop_zone"
    )
    agents: Mapped[list["DeliveryAgent"]] = relationship(
        "DeliveryAgent", back_populates="current_zone"
    )

    def __repr__(self) -> str:
        return f"<Zone id={self.id} code={self.code}>"
