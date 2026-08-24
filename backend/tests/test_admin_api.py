"""Tests for Admin API endpoints."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_admin_zones_crud(admin_client: AsyncClient):
    # 1. Create Zone
    payload = {"name": "Test Admin Zone", "code": "AD-Z1", "is_active": True}
    resp_create = await admin_client.post("/api/v1/admin/zones", json=payload)
    assert resp_create.status_code == 201
    zone = resp_create.json()
    assert zone["code"] == "AD-Z1"
    zone_id = zone["id"]

    # 2. List Zones
    resp_list = await admin_client.get("/api/v1/admin/zones")
    assert resp_list.status_code == 200
    assert any(z["id"] == zone_id for z in resp_list.json())

    # 3. Update Zone
    resp_update = await admin_client.patch(f"/api/v1/admin/zones/{zone_id}", json={"name": "Updated Zone", "is_active": False})
    assert resp_update.status_code == 200
    assert resp_update.json()["name"] == "Updated Zone"

    # 4. Delete Zone
    resp_delete = await admin_client.delete(f"/api/v1/admin/zones/{zone_id}")
    assert resp_delete.status_code == 204


@pytest.mark.asyncio
async def test_admin_areas_crud(admin_client: AsyncClient):
    # Create Zone first
    resp_zone = await admin_client.post("/api/v1/admin/zones", json={"name": "Zone for Area", "code": "ZA-1"})
    zone_id = resp_zone.json()["id"]

    # 1. Create Area
    payload = {"name": "Test Area", "postal_code": "888888", "zone_id": zone_id, "is_active": True}
    resp_create = await admin_client.post("/api/v1/admin/areas", json=payload)
    assert resp_create.status_code == 201
    area = resp_create.json()
    assert area["postal_code"] == "888888"
    area_id = area["id"]

    # 2. List Areas
    resp_list = await admin_client.get("/api/v1/admin/areas")
    assert resp_list.status_code == 200
    assert any(a["id"] == area_id for a in resp_list.json())

    # 3. Update Area
    resp_update = await admin_client.patch(f"/api/v1/admin/areas/{area_id}", json={"name": "Updated Area"})
    assert resp_update.status_code == 200
    assert resp_update.json()["name"] == "Updated Area"

    # 4. Delete Area
    resp_delete = await admin_client.delete(f"/api/v1/admin/areas/{area_id}")
    assert resp_delete.status_code == 204


@pytest.mark.asyncio
async def test_admin_rate_cards_crud(admin_client: AsyncClient):
    # 1. Create Rate Card
    payload = {
        "order_type": "B2C", "zone_type": "INTRA_ZONE",
        "min_weight": 0, "max_weight": 5, "price": 45.0, "is_active": True
    }
    resp_create = await admin_client.post("/api/v1/admin/rates", json=payload)
    assert resp_create.status_code == 201
    rate = resp_create.json()
    assert rate["price"] == 45.0
    rate_id = rate["id"]

    # 2. List Rates
    resp_list = await admin_client.get("/api/v1/admin/rates")
    assert resp_list.status_code == 200
    assert any(r["id"] == rate_id for r in resp_list.json())

    # 3. Update Rate
    resp_update = await admin_client.patch(f"/api/v1/admin/rates/{rate_id}", json={"price": 50.0})
    assert resp_update.status_code == 200
    assert resp_update.json()["price"] == 50.0

    # 4. Delete Rate
    resp_delete = await admin_client.delete(f"/api/v1/admin/rates/{rate_id}")
    assert resp_delete.status_code == 204


@pytest.mark.asyncio
async def test_admin_cod_surcharges_crud(admin_client: AsyncClient):
    # 1. Create COD Surcharge
    payload = {
        "order_type": "B2C", "surcharge_type": "FIXED",
        "value": 30.0, "is_active": True
    }
    resp_create = await admin_client.post("/api/v1/admin/cod-surcharges", json=payload)
    assert resp_create.status_code == 201
    surcharge = resp_create.json()
    assert surcharge["value"] == 30.0
    surcharge_id = surcharge["id"]

    # 2. List COD Surcharges
    resp_list = await admin_client.get("/api/v1/admin/cod-surcharges")
    assert resp_list.status_code == 200
    assert any(s["id"] == surcharge_id for s in resp_list.json())

    # 3. Update COD Surcharge
    resp_update = await admin_client.patch(f"/api/v1/admin/cod-surcharges/{surcharge_id}", json={"value": 35.0})
    assert resp_update.status_code == 200
    assert resp_update.json()["value"] == 35.0

    # 4. Delete COD Surcharge
    resp_delete = await admin_client.delete(f"/api/v1/admin/cod-surcharges/{surcharge_id}")
    assert resp_delete.status_code == 204


@pytest.mark.asyncio
async def test_admin_orders_endpoints(admin_client: AsyncClient, db):
    # Setup some dummy data using direct models since we are testing endpoints
    from app.models.zone import Zone
    from app.models.area import Area
    from app.models.user import User, UserRole
    from app.models.order import Order, OrderStatus, PaymentType
    from app.services.order_service import OrderService
    from app.schemas.order import OrderCreateRequest, AddressInput, PackageInput
    from app.models.rate_card import OrderType, ZoneType
    from app.models.delivery_agent import DeliveryAgent, AvailabilityStatus
    from tests.conftest import create_area, create_rate_card

    zone = Zone(name="Test Admin Zone", code="ADM-Z", is_active=True)
    db.add(zone)
    await db.flush()

    await create_area(db, "500000", zone.id)
    await create_rate_card(db, OrderType.B2C, ZoneType.INTRA_ZONE, 0, 5, 50.0)

    customer = User(name="Test Customer", email="admin_test_cust@example.com", password_hash="dummy", role=UserRole.CUSTOMER)
    db.add(customer)
    await db.flush()

    agent_user = User(name="Test Agent", email="admin_test_agent@example.com", password_hash="dummy", role=UserRole.AGENT)
    db.add(agent_user)
    await db.flush()

    agent = DeliveryAgent(user_id=agent_user.id, current_zone_id=zone.id, availability_status=AvailabilityStatus.AVAILABLE, current_latitude=10.0, current_longitude=10.0)
    db.add(agent)
    await db.commit()

    req = OrderCreateRequest(
        pickup_address=AddressInput(name="S", phone="9999999999", address_line1="1", city="C", state="S", postal_code="500000"),
        drop_address=AddressInput(name="D", phone="8888888888", address_line1="2", city="C", state="S", postal_code="500000"),
        package=PackageInput(length_cm=1, breadth_cm=1, height_cm=1, actual_weight_kg=1),
        order_type=OrderType.B2C, payment_type=PaymentType.PREPAID
    )
    svc = OrderService(db)
    order = await svc.create_order(req, customer)

    # 1. Admin List Orders
    resp_list = await admin_client.get("/api/v1/admin/orders")
    assert resp_list.status_code == 200
    assert any(o["id"] == str(order.id) for o in resp_list.json())

    # 2. Admin Get Order
    resp_get = await admin_client.get(f"/api/v1/admin/orders/{order.id}")
    assert resp_get.status_code == 200
    assert resp_get.json()["id"] == str(order.id)

    # 3. Admin Assign Agent
    assign_payload = {"agent_id": str(agent.user_id)}
    resp_assign = await admin_client.post(f"/api/v1/admin/orders/{order.id}/assign-agent", json=assign_payload)
    assert resp_assign.status_code == 201
    assert resp_assign.json()["agent_user_id"] == str(agent.user_id)

    # 4. Admin Override Status
    status_payload = {"status": "DELIVERED", "reason": "Admin force delivered"}
    resp_status = await admin_client.patch(f"/api/v1/admin/orders/{order.id}/status", json=status_payload)
    assert resp_status.status_code == 200
    assert resp_status.json()["status"] == "DELIVERED"

