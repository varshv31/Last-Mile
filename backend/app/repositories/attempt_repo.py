"""Delivery attempt repository."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.delivery_attempt import AttemptOutcome, DeliveryAttempt
from app.repositories.base import BaseRepository


class AttemptRepository(BaseRepository[DeliveryAttempt]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(DeliveryAttempt, db)

    async def get_latest_for_order(self, order_id: UUID) -> DeliveryAttempt | None:
        result = await self.db.execute(
            select(DeliveryAttempt)
            .where(DeliveryAttempt.order_id == order_id)
            .order_by(DeliveryAttempt.attempt_number.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def count_for_order(self, order_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(DeliveryAttempt).where(
                DeliveryAttempt.order_id == order_id
            )
        )
        return result.scalar_one()

    async def list_for_order(self, order_id: UUID) -> list[DeliveryAttempt]:
        result = await self.db.execute(
            select(DeliveryAttempt)
            .where(DeliveryAttempt.order_id == order_id)
            .order_by(DeliveryAttempt.attempt_number)
        )
        return list(result.scalars().all())
