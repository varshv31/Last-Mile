"""COD surcharge model — database-driven COD pricing."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.rate_card import OrderType


class SurchargeType(str, enum.Enum):
    FIXED = "FIXED"
    PERCENTAGE = "PERCENTAGE"


class CODSurcharge(Base):
    __tablename__ = "cod_surcharges"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_type: Mapped[OrderType] = mapped_column(
        Enum(OrderType), nullable=False, unique=True, index=True
    )
    surcharge_type: Mapped[SurchargeType] = mapped_column(
        Enum(SurchargeType), nullable=False
    )
    value: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False,
        comment="Fixed amount in INR or percentage (e.g. 2.5 = 2.5%)"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<CODSurcharge {self.order_type} {self.surcharge_type} {self.value}>"
