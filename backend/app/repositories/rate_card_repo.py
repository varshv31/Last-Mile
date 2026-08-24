"""Rate card repository."""
from __future__ import annotations

from datetime import date

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rate_card import OrderType, RateCard, ZoneType
from app.repositories.base import BaseRepository


class RateCardRepository(BaseRepository[RateCard]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(RateCard, db)

    async def find_rate(
        self,
        order_type: OrderType,
        zone_type: ZoneType,
        billable_weight: float,
        reference_date: date | None = None,
    ) -> RateCard | None:
        """Find the active rate card matching the given weight slab."""
        ref = reference_date or date.today()
        stmt = (
            select(RateCard)
            .where(
                RateCard.order_type == order_type,
                RateCard.zone_type == zone_type,
                RateCard.is_active == True,
                RateCard.min_weight <= billable_weight,
                RateCard.max_weight > billable_weight,
                or_(RateCard.effective_from == None, RateCard.effective_from <= ref),
                or_(RateCard.effective_to == None, RateCard.effective_to >= ref),
            )
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_overlapping(
        self,
        order_type: OrderType,
        zone_type: ZoneType,
        min_weight: float,
        max_weight: float,
        exclude_id=None,
    ) -> list[RateCard]:
        """Find active rate cards that overlap with the given weight range."""
        stmt = select(RateCard).where(
            RateCard.order_type == order_type,
            RateCard.zone_type == zone_type,
            RateCard.is_active == True,
            RateCard.min_weight < max_weight,
            RateCard.max_weight > min_weight,
        )
        if exclude_id:
            stmt = stmt.where(RateCard.id != exclude_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
