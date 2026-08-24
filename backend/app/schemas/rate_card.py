"""Rate card schemas."""
from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from app.models.rate_card import OrderType, ZoneType


class RateCardCreate(BaseModel):
    order_type: OrderType
    zone_type: ZoneType
    min_weight: float = Field(..., ge=0)
    max_weight: float = Field(..., gt=0)
    price: float = Field(..., gt=0)
    is_active: bool = True
    effective_from: date | None = None
    effective_to: date | None = None

    @model_validator(mode="after")
    def check_weight_range(self) -> "RateCardCreate":
        if self.max_weight <= self.min_weight:
            raise ValueError("max_weight must be greater than min_weight")
        return self

    model_config = {"json_schema_extra": {"example": {
        "order_type": "B2C", "zone_type": "INTRA_ZONE",
        "min_weight": 0, "max_weight": 1, "price": 40.0,
    }}}


class RateCardUpdate(BaseModel):
    price: float | None = Field(None, gt=0)
    is_active: bool | None = None
    effective_from: date | None = None
    effective_to: date | None = None


class RateCardResponse(BaseModel):
    id: uuid.UUID
    order_type: OrderType
    zone_type: ZoneType
    min_weight: float
    max_weight: float
    price: float
    is_active: bool
    effective_from: date | None
    effective_to: date | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
