"""API v1 root router — includes all sub-routers."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import agent, auth, orders
from app.api.v1.admin.router import router as admin_router

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(orders.router)
router.include_router(agent.router)
router.include_router(admin_router)
