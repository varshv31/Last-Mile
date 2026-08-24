"""Authentication service — register, login, token refresh."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthError, DuplicateEmailError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User, UserRole
from app.repositories.user_repo import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from jose import JWTError


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = UserRepository(db)
        self.db = db

    async def register(self, data: RegisterRequest) -> User:
        if await self.repo.email_exists(data.email):
            raise DuplicateEmailError(f"Email '{data.email}' is already registered.")

        user = await self.repo.create(
            name=data.name,
            email=data.email,
            phone=data.phone,
            password_hash=hash_password(data.password),
            role=data.role,
        )

        # Auto-create a DeliveryAgent profile so agents can immediately use /agent/* endpoints.
        from app.models.user import UserRole as _UserRole
        if data.role == _UserRole.AGENT:
            from app.models.delivery_agent import AvailabilityStatus, DeliveryAgent
            agent_profile = DeliveryAgent(
                user_id=user.id,
                availability_status=AvailabilityStatus.OFFLINE,
            )
            self.db.add(agent_profile)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def login(self, data: LoginRequest) -> TokenResponse:
        user = await self.repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.password_hash):
            raise AuthError("Invalid email or password.")
        if not user.is_active:
            raise AuthError("Account is inactive.")

        return TokenResponse(
            access_token=create_access_token(str(user.id), user.role.value),
            refresh_token=create_refresh_token(str(user.id)),
            token_type="bearer",
        )

    async def refresh(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise AuthError("Invalid token type.")
            user_id = payload.get("sub")
        except JWTError:
            raise AuthError("Invalid or expired refresh token.")

        from uuid import UUID
        user = await self.repo.get(UUID(user_id))
        if not user or not user.is_active:
            raise AuthError("User not found or inactive.")

        return TokenResponse(
            access_token=create_access_token(str(user.id), user.role.value),
            refresh_token=create_refresh_token(str(user.id)),
            token_type="bearer",
        )
