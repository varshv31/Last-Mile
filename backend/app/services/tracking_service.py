"""Tracking service — enforces state machine transitions and records immutable history."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ForbiddenError,
    InvalidStatusTransitionError,
    OrderNotFoundError,
)
from app.models.notification import NotificationEvent
from app.models.order import Order, OrderStatus, is_valid_transition
from app.models.order_status_history import OrderStatusHistory
from app.models.user import User, UserRole
from app.repositories.audit_repo import AuditRepository
from app.repositories.order_repo import OrderRepository
from app.services.notification_service import NotificationService

# Map order status → notification event
_STATUS_TO_EVENT: dict[OrderStatus, NotificationEvent] = {
    OrderStatus.PICKED_UP: NotificationEvent.ORDER_PICKED_UP,
    OrderStatus.IN_TRANSIT: NotificationEvent.ORDER_IN_TRANSIT,
    OrderStatus.OUT_FOR_DELIVERY: NotificationEvent.ORDER_OUT_FOR_DELIVERY,
    OrderStatus.DELIVERED: NotificationEvent.ORDER_DELIVERED,
    OrderStatus.FAILED: NotificationEvent.ORDER_FAILED,
    OrderStatus.CANCELLED: NotificationEvent.ORDER_CANCELLED,
}


class TrackingService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.order_repo = OrderRepository(db)
        self.audit_repo = AuditRepository(db)
        self.notif_service = NotificationService(db)

    async def update_status(
        self,
        order_id: UUID,
        new_status: OrderStatus,
        actor: User,
        remarks: str | None = None,
        admin_override: bool = False,
    ) -> Order:
        """
        Update order status with full validation, history recording, and notification.
        
        - Agents: can only update orders assigned to them; state machine enforced.
        - Admins: can override any transition, but it is always audited.
        """
        order = await self.order_repo.get_with_relations(order_id)
        if order is None:
            raise OrderNotFoundError(f"Order {order_id} not found.")

        # Agent authorization check
        if actor.role == UserRole.AGENT:
            if order.assigned_agent_id != actor.id:
                raise ForbiddenError("You can only update orders assigned to you.")
            if not is_valid_transition(order.status, new_status):
                raise InvalidStatusTransitionError(
                    f"Cannot transition from {order.status.value} to {new_status.value}."
                )
        elif actor.role == UserRole.ADMIN:
            if not admin_override and not is_valid_transition(order.status, new_status):
                raise InvalidStatusTransitionError(
                    f"Cannot transition from {order.status.value} to {new_status.value}. "
                    "Use admin override endpoint if intentional."
                )
        else:
            # Customers cannot change order status
            raise ForbiddenError("Customers cannot change order status.")

        old_status = order.status

        # Update order
        order.status = new_status
        self.db.add(order)

        # Append-only history record
        history = OrderStatusHistory(
            order_id=order.id,
            previous_status=old_status,
            new_status=new_status,
            actor_user_id=actor.id,
            actor_role=actor.role,
            remarks=remarks,
        )
        self.db.add(history)

        # Admin override audit log
        if admin_override and actor.role == UserRole.ADMIN:
            await self.audit_repo.log(
                actor_user_id=actor.id,
                action="STATUS_OVERRIDE",
                entity_type="Order",
                entity_id=str(order.id),
                old_value={"status": old_status.value},
                new_value={"status": new_status.value},
                metadata={"remarks": remarks},
            )

        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(order)

        # If agent delivered, mark them AVAILABLE
        if new_status == OrderStatus.DELIVERED:
            await self._release_agent(order)
            await self.db.commit()

        # Notification (non-fatal)
        try:
            event = _STATUS_TO_EVENT.get(new_status)
            if event and order.customer:
                await self.notif_service.notify_order_event(event, order, order.customer)
                await self.db.commit()
        except Exception:
            pass

        return await self.order_repo.get_with_relations(order.id)

    async def _release_agent(self, order: Order) -> None:
        """Mark the assigned agent AVAILABLE after order completion."""
        if not order.assigned_agent_id:
            return
        from app.models.delivery_agent import AvailabilityStatus
        from app.repositories.agent_repo import AgentRepository
        agent_repo = AgentRepository(self.db)
        agent = await agent_repo.get_by_user_id(order.assigned_agent_id)
        if agent:
            agent.availability_status = AvailabilityStatus.AVAILABLE
            self.db.add(agent)
            await self.db.flush()

    async def get_tracking_timeline(self, order_id: UUID) -> Order:
        order = await self.order_repo.get_with_relations(order_id)
        if order is None:
            raise OrderNotFoundError(f"Order {order_id} not found.")
        return order
