"""Zone detection service — postal code → area → zone."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AreaNotFoundError, ZoneNotFoundError
from app.models.area import Area
from app.models.zone import Zone
from app.repositories.area_repo import AreaRepository
from app.repositories.zone_repo import ZoneRepository


class ZoneService:
    """
    Detects the zone for a given postal code via database lookup.

    Design: postal_code → areas table → zones table.
    This can be extended to a geo-provider (Google Maps, etc.) by
    implementing the same interface and swapping the provider here.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.area_repo = AreaRepository(db)
        self.zone_repo = ZoneRepository(db)

    async def detect_zone_by_postal_code(self, postal_code: str) -> tuple[Area, Zone]:
        """
        Resolve postal code → Area → Zone.

        Returns:
            (Area, Zone) tuple.

        Raises:
            AreaNotFoundError: if no active area found for the postal code.
            ZoneNotFoundError: if the area's zone is missing or inactive.
        """
        postal_code = postal_code.strip()
        area = await self.area_repo.get_by_postal_code(postal_code)
        if area is None:
            raise AreaNotFoundError(
                f"No service area found for postal code '{postal_code}'. "
                "Please contact support if you believe this is an error."
            )

        zone = await self.zone_repo.get(area.zone_id)
        if zone is None or not zone.is_active:
            raise ZoneNotFoundError(
                f"Zone for postal code '{postal_code}' is not currently active."
            )

        return area, zone
