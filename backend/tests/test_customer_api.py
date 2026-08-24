"""Tests for Customer Order API endpoints."""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_area, create_rate_card, create_zone
from app.models.rate_card import OrderType, ZoneType
from app.models.order import PaymentType, OrderStatus


@pytest.fixture
async def order_setup_db(db: AsyncSession):
    zone = await create_zone(db, "CUST-ZONE")
    await create_area(db, "505050", zone.id)
    await create_rate_card(db, OrderType.B2C, ZoneType.INTRA_ZONE, 0, 5, 50.0)
    
    from app.models.cod_surcharge import CODSurcharge, SurchargeType
    db.add(CODSurcharge(order_type=OrderType.B2C, surcharge_type=SurchargeType.FIXED, value=30.0))
    await db.commit()
    return {"zone": zone}


@pytest.mark.asyncio
async def test_calculate_order(customer_client: AsyncClient, order_setup_db):
    payload = {
        "pickup_address": {
            "name": "Sender", "phone": "9999999999", "address_line1": "123",
            "city": "City", "state": "State", "postal_code": "505050"
        },
        "drop_address": {
            "name": "Receiver", "phone": "8888888888", "address_line1": "456",
            "city": "City", "state": "State", "postal_code": "505050"
        },
        "package": {"length_cm": 10, "breadth_cm": 10, "height_cm": 10, "actual_weight_kg": 1.0},
        "order_type": "B2C",
        "payment_type": "COD"
    }
    
    resp = await customer_client.post("/api/v1/orders/calculate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_charge" in data
    assert data["base_charge"] == 50.0
    assert data["cod_surcharge"] == 30.0
    assert data["total_charge"] == 80.0


@pytest.mark.asyncio
async def test_create_and_get_order(customer_client: AsyncClient, order_setup_db):
    payload = {
        "pickup_address": {
            "name": "Sender", "phone": "9999999999", "address_line1": "123",
            "city": "City", "state": "State", "postal_code": "505050"
        },
        "drop_address": {
            "name": "Receiver", "phone": "8888888888", "address_line1": "456",
            "city": "City", "state": "State", "postal_code": "505050"
        },
        "package": {"length_cm": 10, "breadth_cm": 10, "height_cm": 10, "actual_weight_kg": 1.0},
        "order_type": "B2C",
        "payment_type": "PREPAID"
    }
    
    # 1. Create order
    resp = await customer_client.post("/api/v1/orders", json=payload)
    assert resp.status_code == 201
    order = resp.json()
    assert order["status"] == "CREATED"
    assert order["total_charge"] == 50.0
    order_id = order["id"]
    
    # 2. Get order details
    resp_get = await customer_client.get(f"/api/v1/orders/{order_id}")
    assert resp_get.status_code == 200
    assert resp_get.json()["id"] == order_id
    
    # 3. List orders
    resp_list = await customer_client.get("/api/v1/orders")
    assert resp_list.status_code == 200
    assert len(resp_list.json()) >= 1
    assert any(o["id"] == order_id for o in resp_list.json())

    # 4. Get Tracking
    resp_track = await customer_client.get(f"/api/v1/orders/{order_id}/tracking")
    assert resp_track.status_code == 200
    track_data = resp_track.json()
    assert len(track_data["timeline"]) == 1
    assert track_data["timeline"][0]["new_status"] == "CREATED"


@pytest.mark.asyncio
async def test_reschedule_order_invalid_status(customer_client: AsyncClient, order_setup_db):
    # Only FAILED orders can be rescheduled by customer.
    payload = {
        "pickup_address": {
            "name": "Sender", "phone": "9999999999", "address_line1": "123",
            "city": "City", "state": "State", "postal_code": "505050"
        },
        "drop_address": {
            "name": "Receiver", "phone": "8888888888", "address_line1": "456",
            "city": "City", "state": "State", "postal_code": "505050"
        },
        "package": {"length_cm": 10, "breadth_cm": 10, "height_cm": 10, "actual_weight_kg": 1.0},
        "order_type": "B2C",
        "payment_type": "PREPAID"
    }
    resp = await customer_client.post("/api/v1/orders", json=payload)
    order_id = resp.json()["id"]

    resp_reschedule = await customer_client.post(f"/api/v1/orders/{order_id}/reschedule", json={"new_delivery_date": "2026-08-25"})
    assert resp_reschedule.status_code == 400
    assert resp_reschedule.json()["code"] == "ORDER_NOT_ELIGIBLE_FOR_RESCHEDULE"
