"""Tests for Agent API endpoints."""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.delivery_agent import DeliveryAgent, AvailabilityStatus
from tests.conftest import create_area, create_zone


@pytest.fixture
async def assigned_order(db: AsyncSession, agent_client: AsyncClient):
    # agent_client creates a user and agent, we need their IDs.
    user_res = await db.execute(select(User).where(User.email == "agent_client@test.com"))
    agent_user = user_res.scalar_one()
    
    agent_res = await db.execute(select(DeliveryAgent).where(DeliveryAgent.user_id == agent_user.id))
    agent = agent_res.scalar_one()

    # Create an order and assign it to the agent
    from app.services.order_service import OrderService
    from app.schemas.order import OrderCreateRequest, AddressInput, PackageInput
    from app.models.rate_card import OrderType, ZoneType
    from app.models.order import PaymentType, OrderStatus
    from tests.conftest import create_area, create_rate_card
    
    zone = await create_zone(db, "AGT-ZONE")
    await create_area(db, "333333", zone.id)
    await create_rate_card(db, OrderType.B2C, ZoneType.INTRA_ZONE, 0, 5, 50.0)

    req = OrderCreateRequest(
        pickup_address=AddressInput(name="S", phone="9999999999", address_line1="1", city="C", state="S", postal_code="333333"),
        drop_address=AddressInput(name="D", phone="8888888888", address_line1="2", city="C", state="S", postal_code="333333"),
        package=PackageInput(length_cm=1, breadth_cm=1, height_cm=1, actual_weight_kg=1),
        order_type=OrderType.B2C, payment_type=PaymentType.PREPAID
    )
    svc = OrderService(db)
    order = await svc.create_order(req, agent_user)
    
    # Force assign and set status
    order.assigned_agent_id = agent.user_id
    order.status = OrderStatus.OUT_FOR_DELIVERY
    await db.commit()
    await db.refresh(order)
    return order, agent


@pytest.mark.asyncio
async def test_get_agent_profile(agent_client: AsyncClient):
    resp = await agent_client.get("/api/v1/agent/profile")
    assert resp.status_code == 200
    data = resp.json()
    assert data["availability_status"] == "AVAILABLE"
    assert "current_latitude" in data


@pytest.mark.asyncio
async def test_update_agent_location(agent_client: AsyncClient):
    payload = {"latitude": 12.34, "longitude": 56.78}
    resp = await agent_client.patch("/api/v1/agent/location", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["current_latitude"] == 12.34
    assert data["current_longitude"] == 56.78


@pytest.mark.asyncio
async def test_update_agent_availability(agent_client: AsyncClient):
    payload = {"availability_status": "BUSY"}
    resp = await agent_client.patch("/api/v1/agent/availability", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["availability_status"] == "BUSY"


@pytest.mark.asyncio
async def test_list_and_get_agent_orders(agent_client: AsyncClient, assigned_order):
    order, _ = assigned_order
    
    # 1. List orders
    resp_list = await agent_client.get("/api/v1/agent/orders")
    assert resp_list.status_code == 200
    assert len(resp_list.json()) == 1
    assert resp_list.json()[0]["id"] == str(order.id)
    
    # 2. Get order
    resp_get = await agent_client.get(f"/api/v1/agent/orders/{order.id}")
    assert resp_get.status_code == 200
    assert resp_get.json()["id"] == str(order.id)


@pytest.mark.asyncio
async def test_update_order_status(agent_client: AsyncClient, assigned_order):
    order, _ = assigned_order
    
    # OUT_FOR_DELIVERY -> DELIVERED
    payload = {"status": "DELIVERED", "remarks": "Delivered to neighbor"}
    resp = await agent_client.patch(f"/api/v1/agent/orders/{order.id}/status", json=payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "DELIVERED"


@pytest.mark.asyncio
async def test_fail_delivery(agent_client: AsyncClient, assigned_order):
    order, _ = assigned_order
    
    # OUT_FOR_DELIVERY -> FAILED
    payload = {"reason": "CUSTOMER_NOT_AVAILABLE", "remarks": "Door locked"}
    resp = await agent_client.post(f"/api/v1/agent/orders/{order.id}/fail", json=payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "FAILED"
