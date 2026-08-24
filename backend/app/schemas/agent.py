"""Agent schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.delivery_agent import AvailabilityStatus


class AgentLocationUpdate(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    zone_id: uuid.UUID | None = None

    model_config = {"json_schema_extra": {"example": {
        "latitude": 19.0760, "longitude": 72.8777, "zone_id": None,
    }}}


class AgentAvailabilityUpdate(BaseModel):
    availability_status: AvailabilityStatus

    model_config = {"json_schema_extra": {"example": {"availability_status": "AVAILABLE"}}}


class AgentProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    availability_status: AvailabilityStatus
    current_latitude: float | None
    current_longitude: float | None
    current_zone_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AgentStatusUpdate(BaseModel):
    status: str
    remarks: str | None = None
