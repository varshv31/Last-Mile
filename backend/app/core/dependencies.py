"""FastAPI dependency injection: DB session, current user, role guards."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AuthError, ForbiddenError
from app.core.security import decode_token
from app.models.user import User, UserRole

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Extract and validate JWT, return the active user."""
    if credentials is None:
        raise AuthError("Missing authentication token.")
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise AuthError("Invalid token type.")
        user_id: str = payload.get("sub", "")
    except JWTError:
        raise AuthError("Invalid or expired token.")

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise AuthError("User not found.")
    if not user.is_active:
        raise AuthError("User account is inactive.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*roles: UserRole):
    """Dependency factory that enforces one or more roles."""

    async def _check(user: CurrentUser) -> User:
        if user.role not in roles:
            raise ForbiddenError(
                f"Access denied. Required roles: {[r.value for r in roles]}."
            )
        return user

    return Depends(_check)


# Convenience role dependencies
AdminUser = Annotated[User, require_role(UserRole.ADMIN)]
CustomerUser = Annotated[User, require_role(UserRole.CUSTOMER)]
AgentUser = Annotated[User, require_role(UserRole.AGENT)]
AdminOrCustomerUser = Annotated[User, require_role(UserRole.ADMIN, UserRole.CUSTOMER)]
