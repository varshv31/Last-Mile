"""Area schemas."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AreaCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    postal_code: str = Field(..., min_length=1, max_length=20)
    zone_id: uuid.UUID
    is_active: bool = True

    model_config = {"json_schema_extra": {"example": {
        "name": "Andheri East", "postal_code": "400069", "zone_id": "uuid-here", "is_active": True,
    }}}


class AreaUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    zone_id: uuid.UUID | None = None
    is_active: bool | None = None


class AreaResponse(BaseModel):
    id: uuid.UUID
    name: str
    postal_code: str
    zone_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
