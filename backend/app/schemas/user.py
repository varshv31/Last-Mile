"""User schemas."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.user import UserRole


class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    phone: str | None
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
