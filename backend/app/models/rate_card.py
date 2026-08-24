"""Rate card model — configurable weight-slab pricing."""
from __future__ import annotations

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class OrderType(str, enum.Enum):
    B2B = "B2B"
    B2C = "B2C"


class ZoneType(str, enum.Enum):
    INTRA_ZONE = "INTRA_ZONE"
    INTER_ZONE = "INTER_ZONE"


class RateCard(Base):
    __tablename__ = "rate_cards"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_type: Mapped[OrderType] = mapped_column(Enum(OrderType), nullable=False, index=True)
    zone_type: Mapped[ZoneType] = mapped_column(Enum(ZoneType), nullable=False, index=True)
    min_weight: Mapped[float] = mapped_column(Float, nullable=False)
    max_weight: Mapped[float] = mapped_column(Float, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<RateCard {self.order_type}/{self.zone_type} "
            f"{self.min_weight}-{self.max_weight}kg ₹{self.price}>"
        )
