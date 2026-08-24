"""Admin zone management endpoints."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AdminUser
from app.core.exceptions import NotFoundError
from app.repositories.audit_repo import AuditRepository
from app.repositories.zone_repo import ZoneRepository
from app.schemas.zone import ZoneCreate, ZoneResponse, ZoneUpdate

router = APIRouter(prefix="/zones", tags=["Zones"])


@router.post("", response_model=ZoneResponse, status_code=201, summary="Create a zone")
async def create_zone(
    data: ZoneCreate,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ZoneResponse:
    repo = ZoneRepository(db)
    zone = await repo.create(**data.model_dump())
    await AuditRepository(db).log(
        actor_user_id=current_user.id, action="CREATE_ZONE",
        entity_type="Zone", entity_id=str(zone.id), new_value=data.model_dump(),
    )
    await db.commit()
    await db.refresh(zone)
    return ZoneResponse.model_validate(zone)


@router.get("", response_model=list[ZoneResponse], summary="List all zones")
async def list_zones(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: AdminUser,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> list[ZoneResponse]:
    repo = ZoneRepository(db)
    zones = await repo.list_all(limit=limit, offset=offset)
    return [ZoneResponse.model_validate(z) for z in zones]


@router.get("/{zone_id}", response_model=ZoneResponse, summary="Get a zone by ID")
async def get_zone(
    zone_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: AdminUser,
) -> ZoneResponse:
    repo = ZoneRepository(db)
    zone = await repo.get(zone_id)
    if zone is None:
        raise NotFoundError(f"Zone {zone_id} not found.")
    return ZoneResponse.model_validate(zone)


@router.patch("/{zone_id}", response_model=ZoneResponse, summary="Update a zone")
async def update_zone(
    zone_id: UUID,
    data: ZoneUpdate,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ZoneResponse:
    repo = ZoneRepository(db)
    zone = await repo.get(zone_id)
    if zone is None:
        raise NotFoundError(f"Zone {zone_id} not found.")
    old = {"name": zone.name, "is_active": zone.is_active}
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    zone = await repo.update(zone, **update_data)
    await AuditRepository(db).log(
        actor_user_id=current_user.id, action="UPDATE_ZONE",
        entity_type="Zone", entity_id=str(zone_id), old_value=old, new_value=update_data,
    )
    await db.commit()
    await db.refresh(zone)
    return ZoneResponse.model_validate(zone)


@router.delete("/{zone_id}", status_code=204, response_model=None, summary="Delete a zone")
async def delete_zone(
    zone_id: UUID,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    repo = ZoneRepository(db)
    zone = await repo.get(zone_id)
    if zone is None:
        raise NotFoundError(f"Zone {zone_id} not found.")
    await repo.delete(zone)
    await AuditRepository(db).log(
        actor_user_id=current_user.id, action="DELETE_ZONE",
        entity_type="Zone", entity_id=str(zone_id),
    )
    await db.commit()
