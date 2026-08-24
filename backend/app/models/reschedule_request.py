"""Reschedule request model — customer-initiated rescheduling after failed delivery."""
from __future__ import annotations

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RescheduleStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class RescheduleRequest(Base):
    __tablename__ = "reschedule_requests"
    __table_args__ = (
        Index("ix_reschedule_requests_order_id", "order_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    previous_attempt_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("delivery_attempts.id", ondelete="SET NULL"), nullable=True
    )
    requested_date: Mapped[date] = mapped_column(Date, nullable=False)
    requested_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[RescheduleStatus] = mapped_column(
        Enum(RescheduleStatus), nullable=False, default=RescheduleStatus.APPROVED
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="reschedule_requests")
    previous_attempt: Mapped["DeliveryAttempt | None"] = relationship("DeliveryAttempt")
    requester: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return f"<RescheduleRequest order={self.order_id} date={self.requested_date}>"
