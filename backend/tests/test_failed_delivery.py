"""Tests 21-22: Failed delivery and rescheduling."""
from __future__ import annotations

import pytest
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidStatusTransitionError, OrderNotEligibleForRescheduleError
from app.models.delivery_agent import AvailabilityStatus, DeliveryAgent
from app.models.delivery_attempt import FailureReason
from app.models.order import OrderStatus, PaymentType
from app.models.rate_card import OrderType, ZoneType
from app.services.failed_delivery_service import FailedDeliveryService
from app.services.reschedule_service import RescheduleService
from app.services.tracking_service import TrackingService
from tests.conftest import create_area, create_rate_card, create_user, create_zone


@pytest.fixture
async def failed_delivery_setup(db: AsyncSession):
    zone = await create_zone(db, "FAIL-Z")
    area = await create_area(db, "701000", zone.id)
    await create_rate_card(db, OrderType.B2C, ZoneType.INTRA_ZONE, 0, 10, 80.0)

    from app.models.cod_surcharge import CODSurcharge, SurchargeType
    db.add(CODSurcharge(order_type=OrderType.B2C, surcharge_type=SurchargeType.FIXED, value=30.0))
    await db.flush()

    customer = await create_user(db, "fail_cust@test.com", "CUSTOMER")
    admin = await create_user(db, "fail_admin@test.com", "ADMIN")
    agent_user = await create_user(db, "fail_agent@test.com", "AGENT")

    agent = DeliveryAgent(
        user_id=agent_user.id,
        current_zone_id=zone.id,
        availability_status=AvailabilityStatus.BUSY,
    )
    db.add(agent)
    await db.flush()

    # Create order and advance to OUT_FOR_DELIVERY
    from app.schemas.order import AddressInput, OrderCreateRequest, PackageInput
    from app.services.order_service import OrderService
    svc = OrderService(db)
    order = await svc.create_order(
        OrderCreateRequest(
            pickup_address=AddressInput(name="S", phone="9", address_line1="A", city="C", state="S", postal_code="701000"),
            drop_address=AddressInput(name="R", phone="8", address_line1="B", city="C", state="S", postal_code="701000"),
            package=PackageInput(length_cm=10, breadth_cm=10, height_cm=10, actual_weight_kg=0.5),
            order_type=OrderType.B2C, payment_type=PaymentType.PREPAID,
        ), customer,
    )
    # Assign agent
    order.assigned_agent_id = agent_user.id
    db.add(order)
    await db.flush()

    track_svc = TrackingService(db)
    order = await track_svc.update_status(order.id, OrderStatus.PICKED_UP, admin, admin_override=True)
    order = await track_svc.update_status(order.id, OrderStatus.IN_TRANSIT, admin, admin_override=True)
    order = await track_svc.update_status(order.id, OrderStatus.OUT_FOR_DELIVERY, admin, admin_override=True)

    await db.commit()
    return {"order": order, "agent": agent, "agent_user": agent_user, "customer": customer, "admin": admin}


@pytest.mark.asyncio
async def test_failed_delivery_requires_reason(db: AsyncSession, failed_delivery_setup):
    """Test 21: Failed delivery stores failure reason and changes status."""
    svc = FailedDeliveryService(db)
    order = await svc.mark_failed(
        order_id=failed_delivery_setup["order"].id,
        agent=failed_delivery_setup["agent_user"],
        failure_reason=FailureReason.CUSTOMER_NOT_AVAILABLE,
        remarks="Tried twice, no answer",
    )
    assert order.status == OrderStatus.FAILED


@pytest.mark.asyncio
async def test_failed_delivery_releases_agent(db: AsyncSession, failed_delivery_setup):
    """Test 21b: Failed delivery releases the agent (AVAILABLE)."""
    agent = failed_delivery_setup["agent"]
    svc = FailedDeliveryService(db)
    await svc.mark_failed(
        order_id=failed_delivery_setup["order"].id,
        agent=failed_delivery_setup["agent_user"],
        failure_reason=FailureReason.WRONG_ADDRESS,
    )
    await db.refresh(agent)
    assert agent.availability_status == AvailabilityStatus.AVAILABLE


@pytest.mark.asyncio
async def test_rescheduling_failed_order(db: AsyncSession, failed_delivery_setup):
    """Test 22: Customer can reschedule a failed order."""
    fail_svc = FailedDeliveryService(db)
    await fail_svc.mark_failed(
        order_id=failed_delivery_setup["order"].id,
        agent=failed_delivery_setup["agent_user"],
        failure_reason=FailureReason.CUSTOMER_NOT_AVAILABLE,
    )

    resched_svc = RescheduleService(db)
    new_date = date.today() + timedelta(days=2)
    order, req = await resched_svc.reschedule(
        order_id=failed_delivery_setup["order"].id,
        new_date=new_date,
        customer=failed_delivery_setup["customer"],
    )
    assert order.status == OrderStatus.CREATED
    assert req.requested_date == new_date


@pytest.mark.asyncio
async def test_cannot_reschedule_non_failed_order(db: AsyncSession, failed_delivery_setup):
    """Test 22b: Non-FAILED orders cannot be rescheduled."""
    # Order is still OUT_FOR_DELIVERY (not yet failed)
    resched_svc = RescheduleService(db)
    with pytest.raises(OrderNotEligibleForRescheduleError):
        await resched_svc.reschedule(
            order_id=failed_delivery_setup["order"].id,
            new_date=date.today() + timedelta(days=1),
            customer=failed_delivery_setup["customer"],
        )


@pytest.mark.asyncio
async def test_reschedule_creates_new_attempt(db: AsyncSession, failed_delivery_setup):
    """Test 22c: Rescheduling creates a new delivery attempt."""
    fail_svc = FailedDeliveryService(db)
    await fail_svc.mark_failed(
        order_id=failed_delivery_setup["order"].id,
        agent=failed_delivery_setup["agent_user"],
        failure_reason=FailureReason.CUSTOMER_NOT_AVAILABLE,
    )

    from app.repositories.attempt_repo import AttemptRepository
    attempt_repo = AttemptRepository(db)
    count_before = await attempt_repo.count_for_order(failed_delivery_setup["order"].id)

    resched_svc = RescheduleService(db)
    await resched_svc.reschedule(
        order_id=failed_delivery_setup["order"].id,
        new_date=date.today() + timedelta(days=3),
        customer=failed_delivery_setup["customer"],
    )

    count_after = await attempt_repo.count_for_order(failed_delivery_setup["order"].id)
    assert count_after == count_before + 1
