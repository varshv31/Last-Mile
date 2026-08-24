"""Tests 17-20: Agent assignment — manual, auto, Haversine, availability."""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AgentNotAvailableError, NoAvailableAgentError
from app.models.delivery_agent import AvailabilityStatus, DeliveryAgent
from app.models.order import OrderStatus, PaymentType
from app.models.rate_card import OrderType, ZoneType
from app.services.assignment_service import AssignmentService
from app.utils.haversine import haversine_km
from tests.conftest import create_area, create_rate_card, create_user, create_zone


@pytest.fixture
async def assignment_setup(db: AsyncSession):
    zone = await create_zone(db, "ASSIGN-Z")
    area = await create_area(db, "601000", zone.id)
    await create_rate_card(db, OrderType.B2C, ZoneType.INTRA_ZONE, 0, 10, 80.0)
    await db.flush()

    customer = await create_user(db, "assign_cust@test.com", "CUSTOMER")
    admin = await create_user(db, "assign_admin@test.com", "ADMIN")
    agent_user = await create_user(db, "assign_agent@test.com", "AGENT")

    agent = DeliveryAgent(
        user_id=agent_user.id,
        current_latitude=19.0760,
        current_longitude=72.8777,
        current_zone_id=zone.id,
        availability_status=AvailabilityStatus.AVAILABLE,
    )
    db.add(agent)
    await db.flush()
    await db.commit()

    # Create an order
    from app.schemas.order import AddressInput, OrderCreateRequest, PackageInput
    from app.services.order_service import OrderService

    from app.models.cod_surcharge import CODSurcharge, SurchargeType
    db.add(CODSurcharge(order_type=OrderType.B2C, surcharge_type=SurchargeType.FIXED, value=30.0))
    await db.flush()

    svc = OrderService(db)
    order = await svc.create_order(
        OrderCreateRequest(
            pickup_address=AddressInput(name="S", phone="9", address_line1="A", city="C", state="S", postal_code="601000"),
            drop_address=AddressInput(name="R", phone="8", address_line1="B", city="C", state="S", postal_code="601000"),
            package=PackageInput(length_cm=10, breadth_cm=10, height_cm=10, actual_weight_kg=0.5),
            order_type=OrderType.B2C, payment_type=PaymentType.PREPAID,
        ),
        customer,
    )
    return {"zone": zone, "agent": agent, "agent_user": agent_user, "admin": admin, "order": order, "customer": customer}


@pytest.mark.asyncio
async def test_manual_agent_assignment(db: AsyncSession, assignment_setup):
    """Test 17: Manual agent assignment."""
    svc = AssignmentService(db)
    result = await svc.assign_manual(
        order_id=assignment_setup["order"].id,
        agent_user_id=assignment_setup["agent_user"].id,
        admin=assignment_setup["admin"],
    )
    from app.models.agent_assignment import AssignmentType
    assert result.assignment_type == AssignmentType.MANUAL
    assert result.agent.user_id == assignment_setup["agent_user"].id


@pytest.mark.asyncio
async def test_unavailable_agent_rejected(db: AsyncSession, assignment_setup):
    """Test 20: Busy/unavailable agent cannot be assigned."""
    agent = assignment_setup["agent"]
    agent.availability_status = AvailabilityStatus.BUSY
    db.add(agent)
    await db.flush()

    svc = AssignmentService(db)
    with pytest.raises(AgentNotAvailableError):
        await svc.assign_manual(
            order_id=assignment_setup["order"].id,
            agent_user_id=assignment_setup["agent_user"].id,
            admin=assignment_setup["admin"],
        )


@pytest.mark.asyncio
async def test_auto_assignment_selects_available_agent(db: AsyncSession, assignment_setup):
    """Test 18: Auto assignment selects available agents in pickup zone."""
    # Reset agent to available
    agent = assignment_setup["agent"]
    agent.availability_status = AvailabilityStatus.AVAILABLE
    db.add(agent)
    await db.flush()

    svc = AssignmentService(db)
    result = await svc.assign_auto(
        order_id=assignment_setup["order"].id,
        admin=assignment_setup["admin"],
    )
    from app.models.agent_assignment import AssignmentType
    assert result.assignment_type == AssignmentType.AUTO


@pytest.mark.asyncio
async def test_no_available_agent_raises_error(db: AsyncSession, assignment_setup):
    """Test 18b: Auto assignment fails when no agents available."""
    agent = assignment_setup["agent"]
    agent.availability_status = AvailabilityStatus.OFFLINE
    db.add(agent)
    await db.flush()

    svc = AssignmentService(db)
    with pytest.raises(NoAvailableAgentError):
        await svc.assign_auto(
            order_id=assignment_setup["order"].id,
            admin=assignment_setup["admin"],
        )


@pytest.mark.asyncio
async def test_haversine_distance_calculation():
    """Test 19: Haversine formula correctness."""
    # Mumbai to Delhi ≈ 1150 km
    distance = haversine_km(19.0760, 72.8777, 28.6139, 77.2090)
    assert 1100 < distance < 1200

    # Same point → 0
    assert haversine_km(19.0760, 72.8777, 19.0760, 72.8777) == 0.0


@pytest.mark.asyncio
async def test_agent_marked_busy_after_assignment(db: AsyncSession, assignment_setup):
    """Test 20b: Agent is marked BUSY after successful assignment."""
    agent = assignment_setup["agent"]
    agent.availability_status = AvailabilityStatus.AVAILABLE
    db.add(agent)
    await db.flush()

    svc = AssignmentService(db)
    await svc.assign_manual(
        order_id=assignment_setup["order"].id,
        agent_user_id=assignment_setup["agent_user"].id,
        admin=assignment_setup["admin"],
    )

    await db.refresh(agent)
    assert agent.availability_status == AvailabilityStatus.BUSY
