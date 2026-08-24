"""Agent assignment repository."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_assignment import AgentAssignment
from app.repositories.base import BaseRepository


class AssignmentRepository(BaseRepository[AgentAssignment]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(AgentAssignment, db)

    async def get_active_for_order(self, order_id: UUID) -> AgentAssignment | None:
        """Return the assignment that has not been unassigned yet."""
        result = await self.db.execute(
            select(AgentAssignment).where(
                AgentAssignment.order_id == order_id,
                AgentAssignment.unassigned_at == None,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_order(self, order_id: UUID) -> list[AgentAssignment]:
        result = await self.db.execute(
            select(AgentAssignment)
            .where(AgentAssignment.order_id == order_id)
            .order_by(AgentAssignment.assigned_at)
        )
        return list(result.scalars().all())
