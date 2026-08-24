"""Notification model — tracks EMAIL and SMS delivery outcomes."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class NotificationChannel(str, enum.Enum):
    EMAIL = "EMAIL"
    SMS = "SMS"


class NotificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class NotificationEvent(str, enum.Enum):
    ORDER_CREATED = "ORDER_CREATED"
    ORDER_PICKED_UP = "ORDER_PICKED_UP"
    ORDER_IN_TRANSIT = "ORDER_IN_TRANSIT"
    ORDER_OUT_FOR_DELIVERY = "ORDER_OUT_FOR_DELIVERY"
    ORDER_DELIVERED = "ORDER_DELIVERED"
    ORDER_FAILED = "ORDER_FAILED"
    ORDER_CANCELLED = "ORDER_CANCELLED"
    ORDER_RESCHEDULED = "ORDER_RESCHEDULED"


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_id", "user_id"),
        Index("ix_notifications_order_id", "order_id"),
        Index("ix_notifications_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="SET NULL"), nullable=True
    )
    channel: Mapped[NotificationChannel] = mapped_column(Enum(NotificationChannel), nullable=False)
    event_type: Mapped[NotificationEvent] = mapped_column(Enum(NotificationEvent), nullable=False)
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(500), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    provider_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus), nullable=False, default=NotificationStatus.PENDING
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")
    order: Mapped["Order | None"] = relationship("Order", back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification {self.channel} {self.event_type} {self.status}>"
