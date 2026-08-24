"""Admin area management endpoints."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AdminUser
from app.core.exceptions import NotFoundError
from app.repositories.area_repo import AreaRepository
from app.repositories.audit_repo import AuditRepository
from app.schemas.area import AreaCreate, AreaResponse, AreaUpdate

router = APIRouter(prefix="/areas", tags=["Areas"])


@router.post("", response_model=AreaResponse, status_code=201, summary="Create an area")
async def create_area(
    data: AreaCreate,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AreaResponse:
    repo = AreaRepository(db)
    area = await repo.create(**data.model_dump())
    await AuditRepository(db).log(
        actor_user_id=current_user.id, action="CREATE_AREA",
        entity_type="Area", entity_id=str(area.id), new_value=data.model_dump(mode="json"),
    )
    await db.commit()
    await db.refresh(area)
    return AreaResponse.model_validate(area)


@router.get("", response_model=list[AreaResponse], summary="List all areas")
async def list_areas(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: AdminUser,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> list[AreaResponse]:
    repo = AreaRepository(db)
    areas = await repo.list_all(limit=limit, offset=offset)
    return [AreaResponse.model_validate(a) for a in areas]


@router.get("/{area_id}", response_model=AreaResponse, summary="Get area by ID")
async def get_area(
    area_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: AdminUser,
) -> AreaResponse:
    repo = AreaRepository(db)
    area = await repo.get(area_id)
    if area is None:
        raise NotFoundError(f"Area {area_id} not found.")
    return AreaResponse.model_validate(area)


@router.patch("/{area_id}", response_model=AreaResponse, summary="Update an area")
async def update_area(
    area_id: UUID,
    data: AreaUpdate,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AreaResponse:
    repo = AreaRepository(db)
    area = await repo.get(area_id)
    if area is None:
        raise NotFoundError(f"Area {area_id} not found.")
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    area = await repo.update(area, **update_data)
    await db.commit()
    await db.refresh(area)
    return AreaResponse.model_validate(area)


@router.delete("/{area_id}", status_code=204, response_model=None, summary="Delete an area")
async def delete_area(
    area_id: UUID,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    repo = AreaRepository(db)
    area = await repo.get(area_id)
    if area is None:
        raise NotFoundError(f"Area {area_id} not found.")
    await repo.delete(area)
    await db.commit()
