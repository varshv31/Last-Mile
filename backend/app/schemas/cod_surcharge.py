"""COD surcharge schemas."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.cod_surcharge import SurchargeType
from app.models.rate_card import OrderType


class CODSurchargeCreate(BaseModel):
    order_type: OrderType
    surcharge_type: SurchargeType
    value: float = Field(..., gt=0)
    is_active: bool = True

    model_config = {"json_schema_extra": {"example": {
        "order_type": "B2C", "surcharge_type": "FIXED", "value": 30.0,
    }}}


class CODSurchargeUpdate(BaseModel):
    surcharge_type: SurchargeType | None = None
    value: float | None = Field(None, gt=0)
    is_active: bool | None = None


class CODSurchargeResponse(BaseModel):
    id: uuid.UUID
    order_type: OrderType
    surcharge_type: SurchargeType
    value: float
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
