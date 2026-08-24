"""Assignment and reschedule schemas."""
from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.agent_assignment import AssignmentType
from app.models.delivery_attempt import FailureReason


class ManualAssignRequest(BaseModel):
    agent_id: uuid.UUID = Field(..., description="User UUID of the agent to assign")

    model_config = {"json_schema_extra": {"example": {"agent_id": "uuid-here"}}}


class AssignmentResponse(BaseModel):
    agent_user_id: uuid.UUID
    agent_name: str
    assignment_type: AssignmentType
    distance_km: float | None
    reason: str
    assigned_at: datetime

    model_config = {"from_attributes": True}


class RescheduleRequest(BaseModel):
    new_delivery_date: date = Field(..., description="Requested new delivery date (YYYY-MM-DD)")

    model_config = {"json_schema_extra": {"example": {"new_delivery_date": "2026-08-25"}}}


class RescheduleResponse(BaseModel):
    order_id: uuid.UUID
    reschedule_id: uuid.UUID
    new_delivery_date: date
    status: str


class FailDeliveryRequest(BaseModel):
    reason: FailureReason
    remarks: str | None = None

    model_config = {"json_schema_extra": {"example": {
        "reason": "CUSTOMER_NOT_AVAILABLE",
        "remarks": "Customer requested reschedule.",
    }}}
