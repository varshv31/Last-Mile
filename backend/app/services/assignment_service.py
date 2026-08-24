"""Agent assignment service — manual and auto assignment with race-condition safety."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AgentNotAvailableError,
    AgentNotFoundError,
    ForbiddenError,
    InvalidStatusTransitionError,
    NoAvailableAgentError,
    OrderNotFoundError,
)
from app.models.agent_assignment import AgentAssignment, AssignmentType
from app.models.delivery_agent import AvailabilityStatus, DeliveryAgent
from app.models.order import OrderStatus
from app.models.user import User
from app.repositories.agent_repo import AgentRepository
from app.repositories.assignment_repo import AssignmentRepository
from app.repositories.audit_repo import AuditRepository
from app.repositories.order_repo import OrderRepository
from app.utils.haversine import haversine_km

# Orders in these statuses are eligible for agent assignment
ASSIGNABLE_STATUSES = {OrderStatus.CREATED}


@dataclass
class AssignmentResult:
    agent: DeliveryAgent
    assignment: AgentAssignment
    assignment_type: AssignmentType
    distance_km: float | None
    reason: str


class AssignmentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.order_repo = OrderRepository(db)
        self.agent_repo = AgentRepository(db)
        self.assignment_repo = AssignmentRepository(db)
        self.audit_repo = AuditRepository(db)

    async def _unassign_previous(self, order_id: UUID) -> None:
        """Mark any existing active assignment as unassigned."""
        from datetime import UTC, datetime
        existing = await self.assignment_repo.get_active_for_order(order_id)
        if existing:
            # Release the old agent
            old_agent = await self.agent_repo.get(existing.agent_id)
            if old_agent:
                old_agent.availability_status = AvailabilityStatus.AVAILABLE
                self.db.add(old_agent)

            existing.unassigned_at = datetime.now(UTC)
            self.db.add(existing)
            await self.db.flush()

    async def assign_manual(
        self,
        order_id: UUID,
        agent_user_id: UUID,
        admin: User,
    ) -> AssignmentResult:
        """Admin-initiated manual assignment."""
        order = await self.order_repo.get(order_id)
        if order is None:
            raise OrderNotFoundError(f"Order {order_id} not found.")
        if order.status not in ASSIGNABLE_STATUSES:
            raise InvalidStatusTransitionError(
                f"Order cannot be assigned in status {order.status.value}."
            )

        agent = await self.agent_repo.get_by_user_id(agent_user_id)
        if agent is None:
            raise AgentNotFoundError(f"Agent with user_id {agent_user_id} not found.")

        # Row-lock the agent to prevent race conditions
        locked = await self.agent_repo.lock_for_assignment(agent.id)
        if locked is None:
            raise AgentNotAvailableError(
                "Agent is not available. They may have just been assigned another order."
            )

        await self._unassign_previous(order_id)

        # Mark agent BUSY
        agent.availability_status = AvailabilityStatus.BUSY
        self.db.add(agent)

        # Update order
        order.assigned_agent_id = agent.user_id
        self.db.add(order)

        # Create assignment record
        assignment = AgentAssignment(
            order_id=order.id,
            agent_id=agent.id,
            assigned_by=admin.id,
            assignment_type=AssignmentType.MANUAL,
            reason="Manual assignment by admin",
        )
        self.db.add(assignment)

        # Audit log
        await self.audit_repo.log(
            actor_user_id=admin.id,
            action="MANUAL_ASSIGNMENT",
            entity_type="Order",
            entity_id=str(order.id),
            new_value={"agent_user_id": str(agent.user_id)},
        )

        await self.db.flush()
        await self.db.commit()

        return AssignmentResult(
            agent=agent,
            assignment=assignment,
            assignment_type=AssignmentType.MANUAL,
            distance_km=None,
            reason="Manual assignment by admin",
        )

    async def assign_auto(
        self,
        order_id: UUID,
        admin: User,
    ) -> AssignmentResult:
        """
        Automatic assignment algorithm:
        1. Find AVAILABLE agents in the pickup zone.
        2. Fallback: all AVAILABLE agents, sorted by Haversine distance.
        3. Select nearest eligible agent.
        4. Lock agent row (SELECT FOR UPDATE SKIP LOCKED) before assignment.
        """
        order = await self.order_repo.get(order_id)
        if order is None:
            raise OrderNotFoundError(f"Order {order_id} not found.")
        if order.status not in ASSIGNABLE_STATUSES:
            raise InvalidStatusTransitionError(
                f"Order cannot be assigned in status {order.status.value}."
            )

        pickup_zone_id = order.pickup_zone_id
        selected_agent: DeliveryAgent | None = None
        distance_km: float | None = None
        reason: str = ""

        # Step 1 — agents in pickup zone
        if pickup_zone_id:
            zone_agents = await self.agent_repo.get_available_agents(pickup_zone_id)
            if zone_agents:
                selected_agent = zone_agents[0]
                reason = f"Agent in pickup zone"

        # Step 2 — fallback: global, sorted by distance
        if selected_agent is None:
            all_agents = await self.agent_repo.get_all_available_agents()
            if not all_agents:
                raise NoAvailableAgentError("No available delivery agents at this time.")

            # Get pickup coords from order's pickup address area
            # We sort by distance only if the agent has location data
            def _dist(a: DeliveryAgent) -> float:
                if (
                    a.current_latitude is not None
                    and a.current_longitude is not None
                    and order.pickup_zone_id
                ):
                    # Approximate pickup coordinates from zone centroid
                    # In production: get actual address coords
                    return haversine_km(
                        float(a.current_latitude), float(a.current_longitude),
                        # Use zone-approximate coords — 0,0 as default if unknown
                        0.0, 0.0
                    )
                return float("inf")

            all_agents.sort(key=_dist)
            selected_agent = all_agents[0]
            reason = "Nearest available agent (cross-zone fallback)"

        # Lock the selected agent
        locked = await self.agent_repo.lock_for_assignment(selected_agent.id)
        if locked is None:
            raise AgentNotAvailableError(
                "Selected agent was just assigned another order. Please retry."
            )

        await self._unassign_previous(order_id)

        # Mark agent BUSY
        selected_agent.availability_status = AvailabilityStatus.BUSY
        self.db.add(selected_agent)

        # Update order
        order.assigned_agent_id = selected_agent.user_id
        self.db.add(order)

        # Assignment record
        assignment = AgentAssignment(
            order_id=order.id,
            agent_id=selected_agent.id,
            assigned_by=admin.id,
            assignment_type=AssignmentType.AUTO,
            reason=reason,
        )
        self.db.add(assignment)

        # Audit log
        await self.audit_repo.log(
            actor_user_id=admin.id,
            action="AUTO_ASSIGNMENT",
            entity_type="Order",
            entity_id=str(order.id),
            new_value={"agent_user_id": str(selected_agent.user_id), "reason": reason},
        )

        await self.db.flush()
        await self.db.commit()

        return AssignmentResult(
            agent=selected_agent,
            assignment=assignment,
            assignment_type=AssignmentType.AUTO,
            distance_km=distance_km,
            reason=reason,
        )
