"""Admin COD surcharge endpoints."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AdminUser
from app.core.exceptions import NotFoundError
from app.repositories.audit_repo import AuditRepository
from app.repositories.cod_surcharge_repo import CODSurchargeRepository
from app.schemas.cod_surcharge import CODSurchargeCreate, CODSurchargeResponse, CODSurchargeUpdate

router = APIRouter(prefix="/cod-surcharges", tags=["COD Surcharges"])


@router.post("", response_model=CODSurchargeResponse, status_code=201, summary="Create COD surcharge")
async def create_cod_surcharge(
    data: CODSurchargeCreate,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CODSurchargeResponse:
    from sqlalchemy.exc import IntegrityError
    from app.core.exceptions import ConflictError
    
    repo = CODSurchargeRepository(db)
    try:
        surcharge = await repo.create(**data.model_dump())
    except IntegrityError:
        raise ConflictError(f"A COD surcharge for {data.order_type} already exists.")
    await AuditRepository(db).log(
        actor_user_id=current_user.id, action="CREATE_COD_SURCHARGE",
        entity_type="CODSurcharge", entity_id=str(surcharge.id), new_value=data.model_dump(mode="json"),
    )
    await db.commit()
    await db.refresh(surcharge)
    return CODSurchargeResponse.model_validate(surcharge)


@router.get("", response_model=list[CODSurchargeResponse], summary="List COD surcharges")
async def list_cod_surcharges(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: AdminUser,
) -> list[CODSurchargeResponse]:
    repo = CODSurchargeRepository(db)
    surcharges = await repo.list_all()
    return [CODSurchargeResponse.model_validate(s) for s in surcharges]


@router.patch("/{id}", response_model=CODSurchargeResponse, summary="Update COD surcharge")
async def update_cod_surcharge(
    id: UUID,
    data: CODSurchargeUpdate,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CODSurchargeResponse:
    repo = CODSurchargeRepository(db)
    surcharge = await repo.get(id)
    if surcharge is None:
        raise NotFoundError(f"COD surcharge {id} not found.")
    old = {"value": float(surcharge.value), "surcharge_type": surcharge.surcharge_type.value}
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    surcharge = await repo.update(surcharge, **update_data)
    await AuditRepository(db).log(
        actor_user_id=current_user.id, action="UPDATE_COD_SURCHARGE",
        entity_type="CODSurcharge", entity_id=str(id), old_value=old, new_value=update_data,
    )
    await db.commit()
    await db.refresh(surcharge)
    return CODSurchargeResponse.model_validate(surcharge)


@router.delete("/{id}", status_code=204, response_model=None, summary="Delete COD surcharge")
async def delete_cod_surcharge(
    id: UUID,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    repo = CODSurchargeRepository(db)
    surcharge = await repo.get(id)
    if surcharge is None:
        raise NotFoundError(f"COD surcharge {id} not found.")
    await repo.delete(surcharge)
    await db.commit()
