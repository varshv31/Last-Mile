"""Delivery agent model — extends User for agent-specific data."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AvailabilityStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    BUSY = "BUSY"
    OFFLINE = "OFFLINE"


class DeliveryAgent(Base):
    __tablename__ = "delivery_agents"
    __table_args__ = (
        Index("ix_delivery_agents_availability_status", "availability_status"),
        Index("ix_delivery_agents_current_zone_id", "current_zone_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    current_latitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    current_longitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    current_zone_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("zones.id", ondelete="SET NULL"), nullable=True
    )
    availability_status: Mapped[AvailabilityStatus] = mapped_column(
        Enum(AvailabilityStatus), nullable=False, default=AvailabilityStatus.OFFLINE
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="delivery_agent")
    current_zone: Mapped["Zone | None"] = relationship("Zone", back_populates="agents")

    def __repr__(self) -> str:
        return f"<DeliveryAgent user_id={self.user_id} status={self.availability_status}>"
