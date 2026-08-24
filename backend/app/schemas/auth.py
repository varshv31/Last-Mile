"""Auth schemas."""
from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    phone: str | None = Field(None, max_length=20)
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole = UserRole.CUSTOMER

    model_config = {"json_schema_extra": {"example": {
        "name": "Priya Sharma",
        "email": "priya@example.com",
        "phone": "+919876543210",
        "password": "SecurePass123!",
        "role": "CUSTOMER",
    }}}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    model_config = {"json_schema_extra": {"example": {
        "email": "priya@example.com",
        "password": "SecurePass123!",
    }}}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str
