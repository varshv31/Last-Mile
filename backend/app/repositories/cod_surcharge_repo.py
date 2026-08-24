"""COD surcharge repository."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cod_surcharge import CODSurcharge
from app.models.rate_card import OrderType
from app.repositories.base import BaseRepository


class CODSurchargeRepository(BaseRepository[CODSurcharge]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(CODSurcharge, db)

    async def get_by_order_type(self, order_type: OrderType) -> CODSurcharge | None:
        result = await self.db.execute(
            select(CODSurcharge).where(
                CODSurcharge.order_type == order_type,
                CODSurcharge.is_active == True,
            )
        )
        return result.scalar_one_or_none()
