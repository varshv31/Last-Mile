"""Order address model — separate pickup and drop addresses."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AddressType(str, enum.Enum):
    PICKUP = "PICKUP"
    DROP = "DROP"


class OrderAddress(Base):
    __tablename__ = "order_addresses"
    __table_args__ = (
        Index("ix_order_addresses_order_id", "order_id"),
        Index("ix_order_addresses_postal_code", "postal_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    address_type: Mapped[AddressType] = mapped_column(Enum(AddressType), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    address_line1: Mapped[str] = mapped_column(String(500), nullable=False)
    address_line2: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[str] = mapped_column(String(255), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="India")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    order: Mapped["Order"] = relationship("Order", back_populates="addresses")

    def __repr__(self) -> str:
        return f"<OrderAddress {self.address_type} {self.postal_code}>"
