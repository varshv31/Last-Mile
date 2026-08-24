"""Area repository."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.area import Area
from app.repositories.base import BaseRepository


class AreaRepository(BaseRepository[Area]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Area, db)

    async def get_by_postal_code(self, postal_code: str) -> Area | None:
        result = await self.db.execute(
            select(Area)
            .where(Area.postal_code == postal_code, Area.is_active == True)
            .options(selectinload(Area.zone))
        )
        return result.scalar_one_or_none()

    async def list_by_zone(self, zone_id) -> list[Area]:
        result = await self.db.execute(
            select(Area).where(Area.zone_id == zone_id, Area.is_active == True)
        )
        return list(result.scalars().all())
