"""Agent assignment model — tracks MANUAL and AUTO assignments."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AssignmentType(str, enum.Enum):
    MANUAL = "MANUAL"
    AUTO = "AUTO"


class AgentAssignment(Base):
    __tablename__ = "agent_assignments"
    __table_args__ = (
        Index("ix_agent_assignments_order_id", "order_id"),
        Index("ix_agent_assignments_agent_id", "agent_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("delivery_agents.id", ondelete="RESTRICT"), nullable=False
    )
    assigned_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    assignment_type: Mapped[AssignmentType] = mapped_column(
        Enum(AssignmentType), nullable=False
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    unassigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="assignments")
    agent: Mapped["DeliveryAgent"] = relationship("DeliveryAgent")
    assigner: Mapped["User | None"] = relationship("User", foreign_keys=[assigned_by])

    def __repr__(self) -> str:
        return f"<AgentAssignment order={self.order_id} agent={self.agent_id} type={self.assignment_type}>"
