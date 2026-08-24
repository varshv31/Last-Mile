"""Order repository — complex queries with filters and pagination."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderStatus
from app.models.rate_card import OrderType
from app.models.order import PaymentType
from app.repositories.base import BaseRepository


class OrderRepository(BaseRepository[Order]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Order, db)

    async def get_with_relations(self, order_id: UUID) -> Order | None:
        result = await self.db.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.customer),
                selectinload(Order.pickup_zone),
                selectinload(Order.drop_zone),
                selectinload(Order.addresses),
                selectinload(Order.package),
                selectinload(Order.status_history),
                selectinload(Order.assignments),
                selectinload(Order.delivery_attempts),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_order_number(self, order_number: str) -> Order | None:
        result = await self.db.execute(
            select(Order).where(Order.order_number == order_number)
        )
        return result.scalar_one_or_none()

    async def list_for_customer(
        self, customer_id: UUID, limit: int = 20, offset: int = 0
    ) -> list[Order]:
        result = await self.db.execute(
            select(Order)
            .where(Order.customer_id == customer_id)
            .options(selectinload(Order.addresses), selectinload(Order.package), selectinload(Order.pickup_zone), selectinload(Order.drop_zone))
            .order_by(Order.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def list_for_agent(
        self, agent_user_id: UUID, limit: int = 20, offset: int = 0
    ) -> list[Order]:
        result = await self.db.execute(
            select(Order)
            .where(Order.assigned_agent_id == agent_user_id)
            .options(selectinload(Order.addresses), selectinload(Order.package), selectinload(Order.pickup_zone), selectinload(Order.drop_zone))
            .order_by(Order.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def list_admin(
        self,
        status: OrderStatus | None = None,
        pickup_zone_id: UUID | None = None,
        drop_zone_id: UUID | None = None,
        agent_id: UUID | None = None,
        order_type: OrderType | None = None,
        payment_type: PaymentType | None = None,
        customer_id: UUID | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Order], int]:
        """Return (orders, total_count) with optional filters."""
        filters = []
        if status:
            filters.append(Order.status == status)
        if pickup_zone_id:
            filters.append(Order.pickup_zone_id == pickup_zone_id)
        if drop_zone_id:
            filters.append(Order.drop_zone_id == drop_zone_id)
        if agent_id:
            filters.append(Order.assigned_agent_id == agent_id)
        if order_type:
            filters.append(Order.order_type == order_type)
        if payment_type:
            filters.append(Order.payment_type == payment_type)
        if customer_id:
            filters.append(Order.customer_id == customer_id)
        if created_from:
            filters.append(Order.created_at >= created_from)
        if created_to:
            filters.append(Order.created_at <= created_to)

        count_stmt = select(func.count()).select_from(Order).where(*filters)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = (
            select(Order)
            .where(*filters)
            .options(selectinload(Order.addresses), selectinload(Order.package), selectinload(Order.pickup_zone), selectinload(Order.drop_zone))
            .order_by(Order.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def generate_order_number(self) -> str:
        """Generate LMD-YYYYMMDD-XXXXXX style order number."""
        from app.utils.order_number import generate_order_number
        return await generate_order_number(self.db)
