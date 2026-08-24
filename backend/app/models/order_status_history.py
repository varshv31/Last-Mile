"""Immutable order status history — append-only tracking timeline."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.order import OrderStatus
from app.models.user import UserRole


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"
    __table_args__ = (
        Index("ix_order_status_history_order_id", "order_id"),
        Index("ix_order_status_history_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    previous_status: Mapped[OrderStatus | None] = mapped_column(Enum(OrderStatus), nullable=True)
    new_status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), nullable=False)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    actor_role: Mapped[UserRole | None] = mapped_column(Enum(UserRole), nullable=True)
    remarks: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="status_history")
    actor: Mapped["User | None"] = relationship("User", foreign_keys=[actor_user_id])

    def __repr__(self) -> str:
        return f"<OrderStatusHistory {self.previous_status}→{self.new_status}>"
