"""Zone repository."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.zone import Zone
from app.repositories.base import BaseRepository


class ZoneRepository(BaseRepository[Zone]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Zone, db)

    async def get_by_code(self, code: str) -> Zone | None:
        result = await self.db.execute(select(Zone).where(Zone.code == code))
        return result.scalar_one_or_none()

    async def list_active(self) -> list[Zone]:
        result = await self.db.execute(select(Zone).where(Zone.is_active == True))
        return list(result.scalars().all())
