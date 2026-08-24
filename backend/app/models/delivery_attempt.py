"""Delivery attempt model — each physical delivery attempt."""
from __future__ import annotations

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AttemptOutcome(str, enum.Enum):
    PENDING = "PENDING"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"


class FailureReason(str, enum.Enum):
    CUSTOMER_NOT_AVAILABLE = "CUSTOMER_NOT_AVAILABLE"
    WRONG_ADDRESS = "WRONG_ADDRESS"
    CUSTOMER_REJECTED = "CUSTOMER_REJECTED"
    ACCESS_ISSUE = "ACCESS_ISSUE"
    OTHER = "OTHER"


class DeliveryAttempt(Base):
    __tablename__ = "delivery_attempts"
    __table_args__ = (
        Index("ix_delivery_attempts_order_id", "order_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    assigned_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("delivery_agents.id", ondelete="SET NULL"), nullable=True
    )
    scheduled_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    outcome: Mapped[AttemptOutcome] = mapped_column(
        Enum(AttemptOutcome), nullable=False, default=AttemptOutcome.PENDING
    )
    failure_reason: Mapped[FailureReason | None] = mapped_column(Enum(FailureReason), nullable=True)
    remarks: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="delivery_attempts")
    agent: Mapped["DeliveryAgent | None"] = relationship("DeliveryAgent")

    def __repr__(self) -> str:
        return f"<DeliveryAttempt order={self.order_id} attempt={self.attempt_number} outcome={self.outcome}>"
