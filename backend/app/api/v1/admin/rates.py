"""Admin rate card endpoints."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AdminUser
from app.core.exceptions import NotFoundError, OverlappingRateCardError
from app.repositories.audit_repo import AuditRepository
from app.repositories.rate_card_repo import RateCardRepository
from app.schemas.rate_card import RateCardCreate, RateCardResponse, RateCardUpdate

router = APIRouter(prefix="/rates", tags=["Rates"])


@router.post("", response_model=RateCardResponse, status_code=201, summary="Create a rate card")
async def create_rate_card(
    data: RateCardCreate,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RateCardResponse:
    repo = RateCardRepository(db)
    # Overlap validation
    overlapping = await repo.find_overlapping(data.order_type, data.zone_type, data.min_weight, data.max_weight)
    if overlapping:
        raise OverlappingRateCardError(
            f"Weight range {data.min_weight}-{data.max_weight}kg overlaps with existing active rate cards."
        )
    rate = await repo.create(**data.model_dump())
    await AuditRepository(db).log(
        actor_user_id=current_user.id, action="CREATE_RATE_CARD",
        entity_type="RateCard", entity_id=str(rate.id), new_value=data.model_dump(mode="json"),
    )
    await db.commit()
    await db.refresh(rate)
    return RateCardResponse.model_validate(rate)


@router.get("", response_model=list[RateCardResponse], summary="List all rate cards")
async def list_rate_cards(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: AdminUser,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> list[RateCardResponse]:
    repo = RateCardRepository(db)
    rates = await repo.list_all(limit=limit, offset=offset)
    return [RateCardResponse.model_validate(r) for r in rates]


@router.get("/{rate_id}", response_model=RateCardResponse, summary="Get rate card by ID")
async def get_rate_card(
    rate_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: AdminUser,
) -> RateCardResponse:
    repo = RateCardRepository(db)
    rate = await repo.get(rate_id)
    if rate is None:
        raise NotFoundError(f"Rate card {rate_id} not found.")
    return RateCardResponse.model_validate(rate)


@router.patch("/{rate_id}", response_model=RateCardResponse, summary="Update a rate card")
async def update_rate_card(
    rate_id: UUID,
    data: RateCardUpdate,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RateCardResponse:
    repo = RateCardRepository(db)
    rate = await repo.get(rate_id)
    if rate is None:
        raise NotFoundError(f"Rate card {rate_id} not found.")
    old = {"price": float(rate.price), "is_active": rate.is_active}
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    rate = await repo.update(rate, **update_data)
    await AuditRepository(db).log(
        actor_user_id=current_user.id, action="UPDATE_RATE_CARD",
        entity_type="RateCard", entity_id=str(rate_id), old_value=old, new_value=update_data,
    )
    await db.commit()
    await db.refresh(rate)
    return RateCardResponse.model_validate(rate)


@router.delete("/{rate_id}", status_code=204, response_model=None, summary="Delete a rate card")
async def delete_rate_card(
    rate_id: UUID,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    repo = RateCardRepository(db)
    rate = await repo.get(rate_id)
    if rate is None:
        raise NotFoundError(f"Rate card {rate_id} not found.")
    await repo.delete(rate)
    await AuditRepository(db).log(
        actor_user_id=current_user.id, action="DELETE_RATE_CARD",
        entity_type="RateCard", entity_id=str(rate_id),
    )
    await db.commit()
