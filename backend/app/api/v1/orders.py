"""Customer order endpoints."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser, CustomerUser
from app.models.order import OrderStatus
from app.models.rate_card import OrderType
from app.models.order import PaymentType
from app.repositories.order_repo import OrderRepository
from app.schemas.assignment import FailDeliveryRequest, RescheduleRequest, RescheduleResponse
from app.schemas.order import (
    OrderCreateRequest,
    OrderResponse,
    RateCalculateRequest,
    RateCalculateResponse,
)
from app.schemas.tracking import TrackingEventResponse, TrackingTimelineResponse
from app.services.order_service import OrderService
from app.services.rate_calculation_service import RateCalculationService
from app.services.reschedule_service import RescheduleService
from app.services.tracking_service import TrackingService

router = APIRouter(tags=["Orders"])


@router.post(
    "/orders/calculate",
    response_model=RateCalculateResponse,
    summary="Calculate delivery charge (no order created)",
    description=(
        "Run the 9-step rate calculation engine and return a full price breakdown. "
        "No order is created. The frontend should display this result to the customer "
        "before they confirm and call POST /orders."
    ),
    responses={
        200: {"description": "Calculation result"},
        400: {"description": "Zone or rate not configured"},
        401: {"description": "Unauthenticated"},
    },
)
async def calculate_rate(
    data: RateCalculateRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RateCalculateResponse:
    svc = RateCalculationService(db)
    result = await svc.calculate(
        pickup_postal_code=data.pickup_address.postal_code,
        drop_postal_code=data.drop_address.postal_code,
        length_cm=data.package.length_cm,
        breadth_cm=data.package.breadth_cm,
        height_cm=data.package.height_cm,
        actual_weight_kg=data.package.actual_weight_kg,
        order_type=data.order_type,
        payment_type=data.payment_type,
    )
    return RateCalculateResponse(**result.__dict__)


@router.post(
    "/orders",
    response_model=OrderResponse,
    status_code=201,
    summary="Create a new order",
    description=(
        "Create a delivery order. The backend recalculates the rate server-side "
        "to ensure price integrity. Returns the complete order with all charges."
    ),
    responses={
        201: {"description": "Order created"},
        400: {"description": "Zone or rate not configured"},
        401: {"description": "Unauthenticated"},
    },
)
async def create_order(
    data: OrderCreateRequest,
    current_user: CustomerUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OrderResponse:
    svc = OrderService(db)
    order = await svc.create_order(data, current_user)
    return OrderResponse.model_validate(order)


@router.get(
    "/orders",
    response_model=list[OrderResponse],
    summary="List customer's orders",
    description="Returns all orders belonging to the current authenticated customer.",
)
async def list_my_orders(
    current_user: CustomerUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[OrderResponse]:
    repo = OrderRepository(db)
    orders = await repo.list_for_customer(current_user.id, limit=limit, offset=offset)
    return [OrderResponse.model_validate(o) for o in orders]


@router.get(
    "/orders/{order_id}",
    response_model=OrderResponse,
    summary="Get a specific order",
    description="Returns an order detail. Customer can only see their own orders.",
    responses={404: {"description": "Order not found"}},
)
async def get_order(
    order_id: UUID,
    current_user: CustomerUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OrderResponse:
    svc = OrderService(db)
    order = await svc.get_order_for_customer(order_id, current_user.id)
    return OrderResponse.model_validate(order)


@router.get(
    "/orders/{order_id}/tracking",
    response_model=TrackingTimelineResponse,
    summary="Get order tracking timeline",
    description=(
        "Returns the full chronological tracking history for an order, "
        "including actor role, timestamps, and remarks for each event."
    ),
    tags=["Tracking"],
    responses={404: {"description": "Order not found"}},
)
async def get_tracking(
    order_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TrackingTimelineResponse:
    svc = TrackingService(db)
    order = await svc.get_tracking_timeline(order_id)

    events = []
    for h in order.status_history:
        actor_name = None
        if h.actor:
            actor_name = h.actor.name
        events.append(TrackingEventResponse(
            id=h.id,
            previous_status=h.previous_status,
            new_status=h.new_status,
            actor_role=h.actor_role,
            actor_name=actor_name,
            remarks=h.remarks,
            created_at=h.created_at,
        ))

    return TrackingTimelineResponse(
        order_id=order.id,
        order_number=order.order_number,
        current_status=order.status,
        timeline=events,
    )


@router.post(
    "/orders/{order_id}/reschedule",
    response_model=RescheduleResponse,
    status_code=201,
    summary="Reschedule a failed delivery",
    description=(
        "Customer can request a new delivery date after a failed attempt. "
        "Only FAILED orders are eligible. Creates a new delivery attempt and "
        "triggers agent reassignment."
    ),
    tags=["Rescheduling"],
    responses={
        201: {"description": "Rescheduled successfully"},
        400: {"description": "Order not eligible for rescheduling"},
        404: {"description": "Order not found"},
    },
)
async def reschedule_order(
    order_id: UUID,
    data: RescheduleRequest,
    current_user: CustomerUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RescheduleResponse:
    svc = RescheduleService(db)
    order, req = await svc.reschedule(order_id, data.new_delivery_date, current_user)
    return RescheduleResponse(
        order_id=order.id,
        reschedule_id=req.id,
        new_delivery_date=req.requested_date,
        status=req.status.value,
    )
