"""Tests 24-25: Admin status override + notification failure doesn't break transaction."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import OrderStatus, PaymentType
from app.models.rate_card import OrderType, ZoneType
from app.services.tracking_service import TrackingService
from tests.conftest import create_area, create_rate_card, create_user, create_zone


@pytest.fixture
async def admin_order_setup(db: AsyncSession):
    zone = await create_zone(db, "ADM-Z")
    await create_area(db, "801000", zone.id)
    await create_rate_card(db, OrderType.B2C, ZoneType.INTRA_ZONE, 0, 10, 80.0)
    from app.models.cod_surcharge import CODSurcharge, SurchargeType
    db.add(CODSurcharge(order_type=OrderType.B2C, surcharge_type=SurchargeType.FIXED, value=30.0))
    await db.flush()

    customer = await create_user(db, "adm_cust@test.com", "CUSTOMER")
    admin = await create_user(db, "adm_admin@test.com", "ADMIN")
    await db.flush()

    from app.schemas.order import AddressInput, OrderCreateRequest, PackageInput
    from app.services.order_service import OrderService
    order = await OrderService(db).create_order(
        OrderCreateRequest(
            pickup_address=AddressInput(name="S", phone="9", address_line1="A", city="C", state="S", postal_code="801000"),
            drop_address=AddressInput(name="R", phone="8", address_line1="B", city="C", state="S", postal_code="801000"),
            package=PackageInput(length_cm=10, breadth_cm=10, height_cm=10, actual_weight_kg=0.5),
            order_type=OrderType.B2C, payment_type=PaymentType.PREPAID,
        ), customer,
    )
    await db.commit()
    return {"order": order, "admin": admin, "customer": customer}


@pytest.mark.asyncio
async def test_admin_status_override_creates_audit_log(db: AsyncSession, admin_order_setup):
    """Test 24: Admin override is audited."""
    svc = TrackingService(db)
    order = await svc.update_status(
        order_id=admin_order_setup["order"].id,
        new_status=OrderStatus.PICKED_UP,
        actor=admin_order_setup["admin"],
        remarks="Operational correction",
        admin_override=True,
    )
    assert order.status == OrderStatus.PICKED_UP

    # Check audit log was created
    from sqlalchemy import select
    from app.models.audit_log import AuditLog
    result = await db.execute(
        select(AuditLog).where(
            AuditLog.entity_type == "Order",
            AuditLog.entity_id == str(admin_order_setup["order"].id),
            AuditLog.action == "STATUS_OVERRIDE",
        )
    )
    audit = result.scalar_one_or_none()
    assert audit is not None
    assert audit.new_value["status"] == "PICKED_UP"


@pytest.mark.asyncio
async def test_notification_failure_does_not_rollback_order(db: AsyncSession, admin_order_setup):
    """Test 25: Notification provider failure doesn't roll back order status."""
    from app.services import notification_service

    # Patch email sender to raise exception
    with patch.object(notification_service, "_send_email", new=AsyncMock(side_effect=Exception("SMTP down"))):
        with patch.object(notification_service, "_send_sms", new=AsyncMock(side_effect=Exception("SMS down"))):
            svc = TrackingService(db)
            order = await svc.update_status(
                order_id=admin_order_setup["order"].id,
                new_status=OrderStatus.PICKED_UP,
                actor=admin_order_setup["admin"],
                admin_override=True,
            )

    # Order status must be updated despite notification failure
    assert order.status == OrderStatus.PICKED_UP
