"""Tests 5-13: Rate engine — zone detection, weight calc, pricing."""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AreaNotFoundError, RateNotConfiguredError
from app.models.rate_card import OrderType, ZoneType
from app.models.order import PaymentType
from app.services.rate_calculation_service import RateCalculationService
from app.services.zone_service import ZoneService
from tests.conftest import create_area, create_rate_card, create_zone


@pytest.fixture
async def seeded_db(db: AsyncSession):
    """Seed zones, areas, and rate cards for rate engine tests."""
    zone_a = await create_zone(db, "ZONE-A")
    zone_b = await create_zone(db, "ZONE-B")

    area_a1 = await create_area(db, "111000", zone_a.id)
    area_b1 = await create_area(db, "222000", zone_b.id)

    # B2C Intra-Zone
    await create_rate_card(db, OrderType.B2C, ZoneType.INTRA_ZONE, 0, 1, 40.0)
    await create_rate_card(db, OrderType.B2C, ZoneType.INTRA_ZONE, 1, 2, 55.0)
    await create_rate_card(db, OrderType.B2C, ZoneType.INTRA_ZONE, 2, 5, 90.0)
    await create_rate_card(db, OrderType.B2C, ZoneType.INTRA_ZONE, 5, 10, 150.0)

    # B2C Inter-Zone
    await create_rate_card(db, OrderType.B2C, ZoneType.INTER_ZONE, 0, 1, 80.0)
    await create_rate_card(db, OrderType.B2C, ZoneType.INTER_ZONE, 1, 2, 110.0)
    await create_rate_card(db, OrderType.B2C, ZoneType.INTER_ZONE, 2, 5, 175.0)

    # B2B Intra
    await create_rate_card(db, OrderType.B2B, ZoneType.INTRA_ZONE, 0, 5, 120.0)
    await create_rate_card(db, OrderType.B2B, ZoneType.INTRA_ZONE, 5, 20, 200.0)

    # B2B Inter
    await create_rate_card(db, OrderType.B2B, ZoneType.INTER_ZONE, 0, 5, 220.0)
    await create_rate_card(db, OrderType.B2B, ZoneType.INTER_ZONE, 5, 20, 380.0)

    # COD surcharges
    from app.models.cod_surcharge import CODSurcharge, SurchargeType
    db.add(CODSurcharge(order_type=OrderType.B2C, surcharge_type=SurchargeType.FIXED, value=30.0))
    db.add(CODSurcharge(order_type=OrderType.B2B, surcharge_type=SurchargeType.PERCENTAGE, value=2.0))
    await db.flush()

    return {"zone_a": zone_a, "zone_b": zone_b, "area_a1": area_a1, "area_b1": area_b1}


@pytest.mark.asyncio
async def test_zone_detection_by_postal_code(db: AsyncSession):
    """Test 5: Postal code → area → zone detection."""
    zone = await create_zone(db, "ZD-TEST")
    area = await create_area(db, "999001", zone.id)

    svc = ZoneService(db)
    detected_area, detected_zone = await svc.detect_zone_by_postal_code("999001")

    assert detected_area.postal_code == "999001"
    assert detected_zone.id == zone.id


@pytest.mark.asyncio
async def test_zone_detection_unknown_postal_code(db: AsyncSession):
    """Test 5b: Unknown postal code raises AreaNotFoundError."""
    svc = ZoneService(db)
    with pytest.raises(AreaNotFoundError):
        await svc.detect_zone_by_postal_code("000000")


@pytest.mark.asyncio
async def test_volumetric_weight_calculation(db: AsyncSession, seeded_db):
    """Test 6: Volumetric weight = (L × B × H) / 5000."""
    svc = RateCalculationService(db)
    result = await svc.calculate(
        pickup_postal_code="111000",
        drop_postal_code="111000",
        length_cm=20, breadth_cm=15, height_cm=10,
        actual_weight_kg=0.3,
        order_type=OrderType.B2C,
        payment_type=PaymentType.PREPAID,
    )
    # Volumetric = (20 * 15 * 10) / 5000 = 3000 / 5000 = 0.6 kg
    assert abs(result.volumetric_weight - 0.6) < 0.001


@pytest.mark.asyncio
async def test_billable_weight_is_max_actual_volumetric(db: AsyncSession, seeded_db):
    """Test 7: Billable weight = max(actual, volumetric)."""
    svc = RateCalculationService(db)

    # Actual > Volumetric
    result = await svc.calculate(
        pickup_postal_code="111000", drop_postal_code="111000",
        length_cm=10, breadth_cm=10, height_cm=10,
        actual_weight_kg=3.0,  # actual 3kg, volumetric = 1000/5000 = 0.2kg
        order_type=OrderType.B2C, payment_type=PaymentType.PREPAID,
    )
    assert result.billable_weight == 3.0

    # Volumetric > Actual
    result2 = await svc.calculate(
        pickup_postal_code="111000", drop_postal_code="111000",
        length_cm=40, breadth_cm=40, height_cm=40,
        actual_weight_kg=0.1,  # volumetric = 64000/5000 = 12.8kg
        order_type=OrderType.B2B, payment_type=PaymentType.PREPAID,
    )
    assert result2.billable_weight > 0.1


@pytest.mark.asyncio
async def test_b2c_intra_zone_pricing(db: AsyncSession, seeded_db):
    """Test 8 & 10: B2C intra-zone — same zone → correct slab."""
    svc = RateCalculationService(db)
    # 0.5 kg → ₹40 slab
    result = await svc.calculate(
        pickup_postal_code="111000", drop_postal_code="111000",
        length_cm=10, breadth_cm=10, height_cm=10,
        actual_weight_kg=0.5,
        order_type=OrderType.B2C, payment_type=PaymentType.PREPAID,
    )
    assert result.zone_type == ZoneType.INTRA_ZONE
    assert result.base_charge == 40.0
    assert result.total_charge == 40.0


@pytest.mark.asyncio
async def test_b2c_inter_zone_pricing(db: AsyncSession, seeded_db):
    """Test 9 & 11: B2C inter-zone — different zones → correct slab."""
    svc = RateCalculationService(db)
    # 1.5 kg inter-zone → ₹110 slab
    result = await svc.calculate(
        pickup_postal_code="111000", drop_postal_code="222000",
        length_cm=10, breadth_cm=10, height_cm=10,
        actual_weight_kg=1.5,
        order_type=OrderType.B2C, payment_type=PaymentType.PREPAID,
    )
    assert result.zone_type == ZoneType.INTER_ZONE
    assert result.base_charge == 110.0


@pytest.mark.asyncio
async def test_b2b_intra_zone_pricing(db: AsyncSession, seeded_db):
    """Test 8: B2B intra-zone."""
    svc = RateCalculationService(db)
    result = await svc.calculate(
        pickup_postal_code="111000", drop_postal_code="111000",
        length_cm=10, breadth_cm=10, height_cm=10,
        actual_weight_kg=2.0,
        order_type=OrderType.B2B, payment_type=PaymentType.PREPAID,
    )
    assert result.zone_type == ZoneType.INTRA_ZONE
    assert result.base_charge == 120.0


@pytest.mark.asyncio
async def test_b2b_inter_zone_pricing(db: AsyncSession, seeded_db):
    """Test 9: B2B inter-zone."""
    svc = RateCalculationService(db)
    result = await svc.calculate(
        pickup_postal_code="111000", drop_postal_code="222000",
        length_cm=10, breadth_cm=10, height_cm=10,
        actual_weight_kg=3.0,
        order_type=OrderType.B2B, payment_type=PaymentType.PREPAID,
    )
    assert result.zone_type == ZoneType.INTER_ZONE
    assert result.base_charge == 220.0


@pytest.mark.asyncio
async def test_cod_surcharge_fixed(db: AsyncSession, seeded_db):
    """Test 12: B2C COD fixed ₹30 surcharge."""
    svc = RateCalculationService(db)
    result = await svc.calculate(
        pickup_postal_code="111000", drop_postal_code="111000",
        length_cm=10, breadth_cm=10, height_cm=10,
        actual_weight_kg=0.5,
        order_type=OrderType.B2C, payment_type=PaymentType.COD,
    )
    assert result.cod_surcharge == 30.0
    assert result.total_charge == result.base_charge + 30.0


@pytest.mark.asyncio
async def test_cod_surcharge_percentage(db: AsyncSession, seeded_db):
    """Test 12b: B2B COD 2% percentage surcharge."""
    svc = RateCalculationService(db)
    result = await svc.calculate(
        pickup_postal_code="111000", drop_postal_code="111000",
        length_cm=10, breadth_cm=10, height_cm=10,
        actual_weight_kg=2.0,
        order_type=OrderType.B2B, payment_type=PaymentType.COD,
    )
    expected_cod = result.base_charge * 0.02
    assert abs(result.cod_surcharge - expected_cod) < 0.01


@pytest.mark.asyncio
async def test_final_charge_calculation(db: AsyncSession, seeded_db):
    """Test 13: Final charge = base + COD surcharge."""
    svc = RateCalculationService(db)
    result = await svc.calculate(
        pickup_postal_code="111000", drop_postal_code="111000",
        length_cm=10, breadth_cm=10, height_cm=10,
        actual_weight_kg=0.5,
        order_type=OrderType.B2C, payment_type=PaymentType.COD,
    )
    assert abs(result.total_charge - (result.base_charge + result.cod_surcharge)) < 0.01


@pytest.mark.asyncio
async def test_rate_not_configured_raises_error(db: AsyncSession, seeded_db):
    """Rate engine raises RateNotConfiguredError for unconfigured weight."""
    svc = RateCalculationService(db)
    with pytest.raises(RateNotConfiguredError):
        await svc.calculate(
            pickup_postal_code="111000", drop_postal_code="111000",
            length_cm=10, breadth_cm=10, height_cm=10,
            actual_weight_kg=999.0,  # above all configured slabs
            order_type=OrderType.B2C, payment_type=PaymentType.PREPAID,
        )
