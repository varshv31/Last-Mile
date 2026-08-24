"""Order model — central entity for the delivery platform."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.rate_card import OrderType, ZoneType


class OrderStatus(str, enum.Enum):
    CREATED = "CREATED"
    PICKED_UP = "PICKED_UP"
    IN_TRANSIT = "IN_TRANSIT"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class PaymentType(str, enum.Enum):
    PREPAID = "PREPAID"
    COD = "COD"


# Legal state-machine transitions
VALID_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.CREATED: {OrderStatus.PICKED_UP, OrderStatus.CANCELLED},
    OrderStatus.PICKED_UP: {OrderStatus.IN_TRANSIT, OrderStatus.CANCELLED},
    OrderStatus.IN_TRANSIT: {OrderStatus.OUT_FOR_DELIVERY, OrderStatus.CANCELLED},
    OrderStatus.OUT_FOR_DELIVERY: {OrderStatus.DELIVERED, OrderStatus.FAILED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.FAILED: {OrderStatus.CREATED},  # after reschedule
    OrderStatus.CANCELLED: set(),
}


def is_valid_transition(current: OrderStatus, next_status: OrderStatus) -> bool:
    return next_status in VALID_TRANSITIONS.get(current, set())


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        Index("ix_orders_order_number", "order_number"),
        Index("ix_orders_status", "status"),
        Index("ix_orders_customer_id", "customer_id"),
        Index("ix_orders_assigned_agent_id", "assigned_agent_id"),
        Index("ix_orders_pickup_zone_id", "pickup_zone_id"),
        Index("ix_orders_drop_zone_id", "drop_zone_id"),
        Index("ix_orders_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_number: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    pickup_zone_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("zones.id", ondelete="RESTRICT"), nullable=True
    )
    drop_zone_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("zones.id", ondelete="RESTRICT"), nullable=True
    )
    order_type: Mapped[OrderType] = mapped_column(Enum(OrderType), nullable=False)
    payment_type: Mapped[PaymentType] = mapped_column(Enum(PaymentType), nullable=False)
    zone_type: Mapped[ZoneType | None] = mapped_column(Enum(ZoneType), nullable=True)

    actual_weight: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)
    volumetric_weight: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)
    billable_weight: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)
    base_charge: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    cod_charge: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    total_charge: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), nullable=False, default=OrderStatus.CREATED
    )
    assigned_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    customer: Mapped["User"] = relationship("User", foreign_keys=[customer_id], back_populates="orders")
    pickup_zone: Mapped["Zone | None"] = relationship("Zone", foreign_keys=[pickup_zone_id], back_populates="pickup_orders")
    drop_zone: Mapped["Zone | None"] = relationship("Zone", foreign_keys=[drop_zone_id], back_populates="drop_orders")
    addresses: Mapped[list["OrderAddress"]] = relationship("OrderAddress", back_populates="order", cascade="all, delete-orphan")
    package: Mapped["OrderPackage | None"] = relationship("OrderPackage", back_populates="order", uselist=False, cascade="all, delete-orphan")
    status_history: Mapped[list["OrderStatusHistory"]] = relationship("OrderStatusHistory", back_populates="order", order_by="OrderStatusHistory.created_at")
    assignments: Mapped[list["AgentAssignment"]] = relationship("AgentAssignment", back_populates="order")
    delivery_attempts: Mapped[list["DeliveryAttempt"]] = relationship("DeliveryAttempt", back_populates="order")
    notifications: Mapped[list["Notification"]] = relationship("Notification", back_populates="order")
    reschedule_requests: Mapped[list["RescheduleRequest"]] = relationship("RescheduleRequest", back_populates="order")

    def __repr__(self) -> str:
        return f"<Order {self.order_number} status={self.status}>"
