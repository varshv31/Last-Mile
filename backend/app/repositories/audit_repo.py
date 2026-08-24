"""Audit log repository."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.repositories.base import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(AuditLog, db)

    async def log(
        self,
        *,
        actor_user_id: UUID | None,
        action: str,
        entity_type: str,
        entity_id: str,
        old_value: dict[str, Any] | None = None,
        new_value: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        return await self.create(
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_value,
            new_value=new_value,
            metadata_=metadata,
        )
