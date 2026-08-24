"""User repository."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_role(self, role: UserRole) -> list[User]:
        result = await self.db.execute(select(User).where(User.role == role, User.is_active == True))
        return list(result.scalars().all())

    async def email_exists(self, email: str) -> bool:
        return await self.get_by_email(email) is not None
