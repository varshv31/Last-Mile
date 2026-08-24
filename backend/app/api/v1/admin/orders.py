"""Admin order management endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AdminUser
from app.core.exceptions import OrderNotFoundError
from app.models.order import OrderStatus, PaymentType
from app.models.rate_card import OrderType
from app.repositories.order_repo import OrderRepository
from app.schemas.assignment import AssignmentResponse, ManualAssignRequest
from app.schemas.order import AdminOrderCreateRequest, AdminStatusUpdateRequest, OrderResponse
from app.services.assignment_service import AssignmentService
from app.services.order_service import OrderService
from app.services.tracking_service import TrackingService

router = APIRouter(prefix="/orders", tags=["Admin"])


@router.post("", response_model=OrderResponse, status_code=201, summary="Admin: create order for customer")
async def admin_create_order(
    data: AdminOrderCreateRequest,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OrderResponse:
    svc = OrderService(db)
    order = await svc.create_order(data, current_user, customer_id=data.customer_id)
    return OrderResponse.model_validate(order)


@router.get("", response_model=list[OrderResponse], summary="Admin: list orders with filters")
async def list_orders(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: AdminUser,
    status: OrderStatus | None = Query(None),
    pickup_zone_id: UUID | None = Query(None),
    drop_zone_id: UUID | None = Query(None),
    agent_id: UUID | None = Query(None),
    order_type: OrderType | None = Query(None),
    payment_type: PaymentType | None = Query(None),
    customer_id: UUID | None = Query(None),
    created_from: datetime | None = Query(None),
    created_to: datetime | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[OrderResponse]:
    repo = OrderRepository(db)
    orders, total = await repo.list_admin(
        status=status,
        pickup_zone_id=pickup_zone_id,
        drop_zone_id=drop_zone_id,
        agent_id=agent_id,
        order_type=order_type,
        payment_type=payment_type,
        customer_id=customer_id,
        created_from=created_from,
        created_to=created_to,
        limit=limit,
        offset=offset,
    )
    return [OrderResponse.model_validate(o) for o in orders]


@router.get("/{order_id}", response_model=OrderResponse, summary="Admin: get order detail")
async def get_order(
    order_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: AdminUser,
) -> OrderResponse:
    repo = OrderRepository(db)
    order = await repo.get_with_relations(order_id)
    if order is None:
        raise OrderNotFoundError(f"Order {order_id} not found.")
    return OrderResponse.model_validate(order)


@router.patch("/{order_id}/status", response_model=OrderResponse, summary="Admin: override order status")
async def admin_update_status(
    order_id: UUID,
    data: AdminStatusUpdateRequest,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OrderResponse:
    svc = TrackingService(db)
    order = await svc.update_status(
        order_id=order_id,
        new_status=data.status,
        actor=current_user,
        remarks=data.reason,
        admin_override=True,
    )
    return OrderResponse.model_validate(order)


@router.post("/{order_id}/assign-agent", response_model=AssignmentResponse, status_code=201,
             summary="Admin: manually assign agent to order")
async def assign_agent(
    order_id: UUID,
    data: ManualAssignRequest,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AssignmentResponse:
    svc = AssignmentService(db)
    result = await svc.assign_manual(order_id, data.agent_id, current_user)
    from datetime import UTC
    return AssignmentResponse(
        agent_user_id=result.agent.user_id,
        agent_name=result.agent.user.name if result.agent.user else "Unknown",
        assignment_type=result.assignment_type,
        distance_km=result.distance_km,
        reason=result.reason,
        assigned_at=result.assignment.assigned_at,
    )


@router.post("/{order_id}/auto-assign", response_model=AssignmentResponse, status_code=201,
             summary="Admin: auto-assign nearest available agent")
async def auto_assign_agent(
    order_id: UUID,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AssignmentResponse:
    svc = AssignmentService(db)
    result = await svc.assign_auto(order_id, current_user)
    return AssignmentResponse(
        agent_user_id=result.agent.user_id,
        agent_name=result.agent.user.name if result.agent.user else "Unknown",
        assignment_type=result.assignment_type,
        distance_km=result.distance_km,
        reason=result.reason,
        assigned_at=result.assignment.assigned_at,
    )
