"""Order package model — stores package dimensions and weight."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class OrderPackage(Base):
    __tablename__ = "order_packages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    length_cm: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    breadth_cm: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    height_cm: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    actual_weight_kg: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    order: Mapped["Order"] = relationship("Order", back_populates="package")

    def __repr__(self) -> str:
        return f"<OrderPackage {self.length_cm}x{self.breadth_cm}x{self.height_cm} {self.actual_weight_kg}kg>"
