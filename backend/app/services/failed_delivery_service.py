"""Failed delivery service — handles the FAILED workflow."""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, InvalidStatusTransitionError, OrderNotFoundError
from app.models.delivery_attempt import AttemptOutcome, DeliveryAttempt, FailureReason
from app.models.notification import NotificationEvent
from app.models.order import Order, OrderStatus
from app.models.order_status_history import OrderStatusHistory
from app.models.user import User, UserRole
from app.repositories.attempt_repo import AttemptRepository
from app.repositories.order_repo import OrderRepository
from app.services.notification_service import NotificationService


class FailedDeliveryService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.order_repo = OrderRepository(db)
        self.attempt_repo = AttemptRepository(db)
        self.notif_service = NotificationService(db)

    async def mark_failed(
        self,
        order_id: UUID,
        agent: User,
        failure_reason: FailureReason,
        remarks: str | None = None,
    ) -> Order:
        """
        Agent marks an order as FAILED.
        
        - Validates agent is assigned to this order.
        - Validates order is in OUT_FOR_DELIVERY state.
        - Updates order status to FAILED.
        - Records immutable status history.
        - Closes the current delivery attempt.
        - Releases the agent.
        - Notifies the customer.
        """
        order = await self.order_repo.get_with_relations(order_id)
        if order is None:
            raise OrderNotFoundError(f"Order {order_id} not found.")

        # Only the assigned agent can mark as failed
        if agent.role == UserRole.AGENT and order.assigned_agent_id != agent.id:
            raise ForbiddenError("You can only update orders assigned to you.")

        if order.status != OrderStatus.OUT_FOR_DELIVERY:
            raise InvalidStatusTransitionError(
                f"Order must be OUT_FOR_DELIVERY to mark as failed. "
                f"Current status: {order.status.value}"
            )

        # Update order status
        old_status = order.status
        order.status = OrderStatus.FAILED
        self.db.add(order)

        # Immutable history
        self.db.add(OrderStatusHistory(
            order_id=order.id,
            previous_status=old_status,
            new_status=OrderStatus.FAILED,
            actor_user_id=agent.id,
            actor_role=agent.role,
            remarks=f"FAILED: {failure_reason.value}. {remarks or ''}".strip(),
        ))

        # Close current delivery attempt
        attempt = await self.attempt_repo.get_latest_for_order(order_id)
        if attempt and attempt.outcome == AttemptOutcome.PENDING:
            attempt.outcome = AttemptOutcome.FAILED
            attempt.failure_reason = failure_reason
            attempt.remarks = remarks
            attempt.completed_at = datetime.now(UTC)
            self.db.add(attempt)

        # Release agent
        from app.models.delivery_agent import AvailabilityStatus
        from app.repositories.agent_repo import AgentRepository
        agent_repo = AgentRepository(self.db)
        delivery_agent = await agent_repo.get_by_user_id(agent.id)
        if delivery_agent:
            delivery_agent.availability_status = AvailabilityStatus.AVAILABLE
            self.db.add(delivery_agent)

        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(order)

        # Notify customer (non-fatal)
        try:
            if order.customer:
                await self.notif_service.notify_order_event(
                    NotificationEvent.ORDER_FAILED, order, order.customer
                )
                await self.db.commit()
        except Exception:
            pass

        return await self.order_repo.get_with_relations(order.id)
