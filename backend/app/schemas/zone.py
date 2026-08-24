"""Zone schemas."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ZoneCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=50)
    description: str | None = None
    is_active: bool = True

    model_config = {"json_schema_extra": {"example": {
        "name": "Mumbai North", "code": "MUM-N", "description": "Northern Mumbai zone", "is_active": True,
    }}}


class ZoneUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    is_active: bool | None = None


class ZoneResponse(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
