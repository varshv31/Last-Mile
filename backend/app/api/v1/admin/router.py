"""Admin sub-router — aggregates all admin endpoints under /admin."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.admin import areas, cod_surcharges, orders, rates, zones

router = APIRouter(prefix="/admin")

router.include_router(zones.router)
router.include_router(areas.router)
router.include_router(rates.router)
router.include_router(cod_surcharges.router)
router.include_router(orders.router)
