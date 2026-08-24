"""Reschedule request repository."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reschedule_request import RescheduleRequest
from app.repositories.base import BaseRepository


class RescheduleRepository(BaseRepository[RescheduleRequest]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(RescheduleRequest, db)

    async def list_for_order(self, order_id: UUID) -> list[RescheduleRequest]:
        result = await self.db.execute(
            select(RescheduleRequest)
            .where(RescheduleRequest.order_id == order_id)
            .order_by(RescheduleRequest.created_at)
        )
        return list(result.scalars().all())
