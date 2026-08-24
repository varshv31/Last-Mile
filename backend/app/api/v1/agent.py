"""Agent endpoints — profile, orders, location, availability, status updates."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AgentUser, CurrentUser
from app.core.exceptions import AgentNotFoundError, ForbiddenError, OrderNotFoundError
from app.models.delivery_agent import AvailabilityStatus
from app.models.order import OrderStatus
from app.repositories.agent_repo import AgentRepository
from app.repositories.order_repo import OrderRepository
from app.schemas.agent import AgentAvailabilityUpdate, AgentLocationUpdate, AgentProfileResponse
from app.schemas.assignment import FailDeliveryRequest
from app.schemas.order import OrderResponse, StatusUpdateRequest
from app.services.failed_delivery_service import FailedDeliveryService
from app.services.tracking_service import TrackingService

router = APIRouter(prefix="/agent", tags=["Agents"])


@router.get(
    "/profile",
    response_model=AgentProfileResponse,
    summary="Get agent profile",
    description="Returns the delivery agent profile for the current authenticated agent.",
)
async def get_agent_profile(
    current_user: AgentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AgentProfileResponse:
    repo = AgentRepository(db)
    agent = await repo.get_by_user_id(current_user.id)
    if agent is None:
        raise AgentNotFoundError("Agent profile not found.")
    return AgentProfileResponse.model_validate(agent)


@router.get(
    "/orders",
    response_model=list[OrderResponse],
    summary="List orders assigned to agent",
    description="Returns all orders currently or previously assigned to this agent.",
)
async def list_agent_orders(
    current_user: AgentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[OrderResponse]:
    repo = OrderRepository(db)
    orders = await repo.list_for_agent(current_user.id, limit=limit, offset=offset)
    return [OrderResponse.model_validate(o) for o in orders]


@router.get(
    "/orders/{order_id}",
    response_model=OrderResponse,
    summary="Get a specific assigned order",
    description="Returns detail for an order assigned to this agent.",
    responses={404: {"description": "Order not found or not assigned to this agent"}},
)
async def get_agent_order(
    order_id: UUID,
    current_user: AgentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OrderResponse:
    repo = OrderRepository(db)
    order = await repo.get_with_relations(order_id)
    if order is None or order.assigned_agent_id != current_user.id:
        raise OrderNotFoundError("Order not found or not assigned to you.")
    return OrderResponse.model_validate(order)


@router.patch(
    "/location",
    response_model=AgentProfileResponse,
    summary="Update agent location",
    description=(
        "Update the agent's current GPS coordinates and optionally their current zone. "
        "Latitude must be -90 to 90, longitude -180 to 180."
    ),
)
async def update_location(
    data: AgentLocationUpdate,
    current_user: AgentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AgentProfileResponse:
    repo = AgentRepository(db)
    agent = await repo.get_by_user_id(current_user.id)
    if agent is None:
        raise AgentNotFoundError("Agent profile not found.")
    agent.current_latitude = data.latitude
    agent.current_longitude = data.longitude
    if data.zone_id:
        agent.current_zone_id = data.zone_id
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return AgentProfileResponse.model_validate(agent)


@router.patch(
    "/availability",
    response_model=AgentProfileResponse,
    summary="Update agent availability",
    description="Set the agent's availability status: AVAILABLE, BUSY, or OFFLINE.",
)
async def update_availability(
    data: AgentAvailabilityUpdate,
    current_user: AgentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AgentProfileResponse:
    repo = AgentRepository(db)
    agent = await repo.get_by_user_id(current_user.id)
    if agent is None:
        raise AgentNotFoundError("Agent profile not found.")
    agent.availability_status = data.availability_status
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return AgentProfileResponse.model_validate(agent)


@router.patch(
    "/orders/{order_id}/status",
    response_model=OrderResponse,
    summary="Update delivery status",
    description=(
        "Agent updates the status of an assigned order. "
        "Only valid state machine transitions are allowed. "
        "Every update creates an immutable tracking history entry."
    ),
    responses={
        400: {"description": "Invalid status transition"},
        403: {"description": "Order not assigned to this agent"},
        404: {"description": "Order not found"},
    },
)
async def update_order_status(
    order_id: UUID,
    data: StatusUpdateRequest,
    current_user: AgentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OrderResponse:
    svc = TrackingService(db)
    order = await svc.update_status(
        order_id=order_id,
        new_status=data.status,
        actor=current_user,
        remarks=data.remarks,
    )
    return OrderResponse.model_validate(order)


@router.post(
    "/orders/{order_id}/fail",
    response_model=OrderResponse,
    summary="Mark delivery as failed",
    description=(
        "Agent marks a delivery attempt as FAILED. A failure reason is required. "
        "The order becomes eligible for customer rescheduling. The agent is released."
    ),
    tags=["Agents"],
    responses={
        400: {"description": "Order not in OUT_FOR_DELIVERY status"},
        403: {"description": "Not assigned to this agent"},
    },
)
async def fail_delivery(
    order_id: UUID,
    data: FailDeliveryRequest,
    current_user: AgentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OrderResponse:
    svc = FailedDeliveryService(db)
    order = await svc.mark_failed(
        order_id=order_id,
        agent=current_user,
        failure_reason=data.reason,
        remarks=data.remarks,
    )
    return OrderResponse.model_validate(order)
