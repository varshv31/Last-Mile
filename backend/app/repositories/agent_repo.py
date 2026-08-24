"""Delivery agent repository."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.delivery_agent import AvailabilityStatus, DeliveryAgent
from app.repositories.base import BaseRepository


class AgentRepository(BaseRepository[DeliveryAgent]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(DeliveryAgent, db)

    async def get_by_user_id(self, user_id: UUID) -> DeliveryAgent | None:
        result = await self.db.execute(
            select(DeliveryAgent)
            .where(DeliveryAgent.user_id == user_id)
            .options(selectinload(DeliveryAgent.user), selectinload(DeliveryAgent.current_zone))
        )
        return result.scalar_one_or_none()

    async def get_available_agents(self, zone_id: UUID | None = None) -> list[DeliveryAgent]:
        """Return AVAILABLE agents, optionally filtered by current zone."""
        stmt = (
            select(DeliveryAgent)
            .where(DeliveryAgent.availability_status == AvailabilityStatus.AVAILABLE)
            .options(selectinload(DeliveryAgent.user))
        )
        if zone_id:
            stmt = stmt.where(DeliveryAgent.current_zone_id == zone_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_all_available_agents(self) -> list[DeliveryAgent]:
        """Return all AVAILABLE agents regardless of zone (for distance-based fallback)."""
        result = await self.db.execute(
            select(DeliveryAgent)
            .where(DeliveryAgent.availability_status == AvailabilityStatus.AVAILABLE)
            .options(selectinload(DeliveryAgent.user))
        )
        return list(result.scalars().all())

    async def lock_for_assignment(self, agent_id: UUID) -> DeliveryAgent | None:
        """SELECT FOR UPDATE — prevents concurrent assignment of the same agent."""
        result = await self.db.execute(
            select(DeliveryAgent)
            .where(
                DeliveryAgent.id == agent_id,
                DeliveryAgent.availability_status == AvailabilityStatus.AVAILABLE,
            )
            .with_for_update(skip_locked=True)
        )
        return result.scalar_one_or_none()
