"""Tracking schemas — timeline response."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.order import OrderStatus
from app.models.user import UserRole


class TrackingEventResponse(BaseModel):
    id: uuid.UUID
    previous_status: OrderStatus | None
    new_status: OrderStatus
    actor_role: UserRole | None
    actor_name: str | None = None
    remarks: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TrackingTimelineResponse(BaseModel):
    order_id: uuid.UUID
    order_number: str
    current_status: OrderStatus
    timeline: list[TrackingEventResponse]
