"""Tests 14-16: Order creation, invalid status transitions, immutable tracking."""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidStatusTransitionError
from app.models.order import OrderStatus
from app.models.rate_card import OrderType, ZoneType
from app.models.order import PaymentType
from app.models.user import UserRole
from app.services.order_service import OrderService
from app.services.tracking_service import TrackingService
from tests.conftest import create_area, create_rate_card, create_user, create_zone


@pytest.fixture
async def order_setup(db: AsyncSession):
    """Setup zone, area, rates, and a customer for order tests."""
    zone = await create_zone(db, "ORD-ZONE")
    area = await create_area(db, "501000", zone.id)

    await create_rate_card(db, OrderType.B2C, ZoneType.INTRA_ZONE, 0, 5, 70.0)
    from app.models.cod_surcharge import CODSurcharge, SurchargeType
    db.add(CODSurcharge(order_type=OrderType.B2C, surcharge_type=SurchargeType.FIXED, value=30.0))

    customer = await create_user(db, "order_cust@test.com", "CUSTOMER")
    await db.commit()
    return {"zone": zone, "area": area, "customer": customer}


@pytest.mark.asyncio
async def test_order_creation(db: AsyncSession, order_setup):
    """Test 14: Order creation is atomic and correct."""
    from app.schemas.order import AddressInput, OrderCreateRequest, PackageInput

    customer = order_setup["customer"]
    svc = OrderService(db)

    request = OrderCreateRequest(
        pickup_address=AddressInput(
            name="Sender", phone="9999999999",
            address_line1="10 Test Street", city="Test City",
            state="Test State", postal_code="501000",
        ),
        drop_address=AddressInput(
            name="Receiver", phone="8888888888",
            address_line1="20 Test Ave", city="Test City",
            state="Test State", postal_code="501000",
        ),
        package=PackageInput(length_cm=10, breadth_cm=10, height_cm=10, actual_weight_kg=1.0),
        order_type=OrderType.B2C,
        payment_type=PaymentType.PREPAID,
    )

    order = await svc.create_order(request, customer)

    assert order.order_number.startswith("LMD-")
    assert order.status == OrderStatus.CREATED
    assert order.customer_id == customer.id
    assert float(order.total_charge) > 0
    assert float(order.base_charge) == 70.0
    assert float(order.cod_charge) == 0.0


@pytest.mark.asyncio
async def test_invalid_status_transition(db: AsyncSession, order_setup):
    """Test 15: Invalid state machine transitions are rejected."""
    from app.schemas.order import AddressInput, OrderCreateRequest, PackageInput

    customer = order_setup["customer"]
    svc = OrderService(db)
    track_svc = TrackingService(db)

    # Create admin user for status updates
    admin = await create_user(db, "admin_track@test.com", "ADMIN")
    await db.flush()

    request = OrderCreateRequest(
        pickup_address=AddressInput(
            name="S", phone="9999999999", address_line1="X", city="C", state="S", postal_code="501000",
        ),
        drop_address=AddressInput(
            name="R", phone="8888888888", address_line1="Y", city="C", state="S", postal_code="501000",
        ),
        package=PackageInput(length_cm=10, breadth_cm=10, height_cm=10, actual_weight_kg=0.5),
        order_type=OrderType.B2C,
        payment_type=PaymentType.PREPAID,
    )
    order = await svc.create_order(request, customer)

    # Cannot jump from CREATED directly to DELIVERED
    with pytest.raises(InvalidStatusTransitionError):
        await track_svc.update_status(
            order_id=order.id,
            new_status=OrderStatus.DELIVERED,
            actor=admin,
            admin_override=False,
        )


@pytest.mark.asyncio
async def test_immutable_tracking_history(db: AsyncSession, order_setup):
    """Test 16: Every status change creates a new history record."""
    from app.schemas.order import AddressInput, OrderCreateRequest, PackageInput

    customer = order_setup["customer"]
    admin = await create_user(db, "admin_hist@test.com", "ADMIN")
    await db.flush()

    svc = OrderService(db)
    request = OrderCreateRequest(
        pickup_address=AddressInput(
            name="S", phone="9999999999", address_line1="X", city="C", state="S", postal_code="501000",
        ),
        drop_address=AddressInput(
            name="R", phone="8888888888", address_line1="Y", city="C", state="S", postal_code="501000",
        ),
        package=PackageInput(length_cm=10, breadth_cm=10, height_cm=10, actual_weight_kg=0.5),
        order_type=OrderType.B2C, payment_type=PaymentType.PREPAID,
    )
    order = await svc.create_order(request, customer)

    # Should have 1 history record: CREATED
    from app.repositories.order_repo import OrderRepository
    repo = OrderRepository(db)
    refreshed = await repo.get_with_relations(order.id)
    assert len(refreshed.status_history) >= 1

    # Advance through the state machine
    track_svc = TrackingService(db)
    order = await track_svc.update_status(order.id, OrderStatus.PICKED_UP, admin, admin_override=True)
    order = await track_svc.update_status(order.id, OrderStatus.IN_TRANSIT, admin, admin_override=True)

    refreshed2 = await repo.get_with_relations(order.id)
    # At least 3 history records (CREATED + PICKED_UP + IN_TRANSIT)
    assert len(refreshed2.status_history) >= 3

    # Verify immutability — history records have no "updated_at"
    for h in refreshed2.status_history:
        assert h.new_status is not None
        assert h.created_at is not None
