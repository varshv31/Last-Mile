"""Reschedule service — customer-initiated rescheduling after failed delivery."""
from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import OrderNotEligibleForRescheduleError, OrderNotFoundError
from app.models.delivery_attempt import AttemptOutcome, DeliveryAttempt
from app.models.notification import NotificationEvent
from app.models.order import Order, OrderStatus
from app.models.order_status_history import OrderStatusHistory
from app.models.reschedule_request import RescheduleRequest, RescheduleStatus
from app.models.user import User
from app.repositories.attempt_repo import AttemptRepository
from app.repositories.order_repo import OrderRepository
from app.repositories.reschedule_repo import RescheduleRepository
from app.services.notification_service import NotificationService


class RescheduleService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.order_repo = OrderRepository(db)
        self.attempt_repo = AttemptRepository(db)
        self.reschedule_repo = RescheduleRepository(db)
        self.notif_service = NotificationService(db)

    async def reschedule(
        self,
        order_id: UUID,
        new_date: date,
        customer: User,
    ) -> tuple[Order, RescheduleRequest]:
        """
        Process a reschedule request.
        
        Rules:
        - Only FAILED orders can be rescheduled.
        - Customer must own the order.
        - Creates a new delivery attempt.
        - Releases the previous agent.
        - Sets order back to CREATED.
        - Records everything in history + reschedule_requests.
        - Triggers agent reassignment (auto-assign after commit).
        """
        order = await self.order_repo.get_with_relations(order_id)
        if order is None:
            raise OrderNotFoundError(f"Order {order_id} not found.")

        if order.customer_id != customer.id:
            raise OrderNotFoundError(f"Order {order_id} not found.")

        if order.status != OrderStatus.FAILED:
            raise OrderNotEligibleForRescheduleError(
                "Only failed orders can be rescheduled."
            )

        # Get the last failed attempt
        last_attempt = await self.attempt_repo.get_latest_for_order(order_id)
        attempt_count = await self.attempt_repo.count_for_order(order_id)

        # Create reschedule request record
        reschedule_req = RescheduleRequest(
            order_id=order.id,
            previous_attempt_id=last_attempt.id if last_attempt else None,
            requested_date=new_date,
            requested_by=customer.id,
            status=RescheduleStatus.APPROVED,
        )
        self.db.add(reschedule_req)

        # Create new delivery attempt
        new_attempt = DeliveryAttempt(
            order_id=order.id,
            attempt_number=attempt_count + 1,
            scheduled_date=new_date,
            outcome=AttemptOutcome.PENDING,
        )
        self.db.add(new_attempt)

        # Release the previously assigned agent
        if order.assigned_agent_id:
            from app.models.delivery_agent import AvailabilityStatus
            from app.repositories.agent_repo import AgentRepository
            agent_repo = AgentRepository(self.db)
            delivery_agent = await agent_repo.get_by_user_id(order.assigned_agent_id)
            if delivery_agent:
                delivery_agent.availability_status = AvailabilityStatus.AVAILABLE
                self.db.add(delivery_agent)
            order.assigned_agent_id = None

        # Reset order to CREATED for reassignment
        old_status = order.status
        order.status = OrderStatus.CREATED
        self.db.add(order)

        # Immutable history
        self.db.add(OrderStatusHistory(
            order_id=order.id,
            previous_status=old_status,
            new_status=OrderStatus.CREATED,
            actor_user_id=customer.id,
            actor_role=customer.role,
            remarks=f"Rescheduled for {new_date}",
        ))

        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(order)
        await self.db.refresh(reschedule_req)

        # Notify (non-fatal)
        try:
            await self.notif_service.notify_order_event(
                NotificationEvent.ORDER_RESCHEDULED, order, customer
            )
            await self.db.commit()
        except Exception:
            pass

        return order, reschedule_req
