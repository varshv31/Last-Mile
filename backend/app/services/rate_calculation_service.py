"""Rate Calculation Service — the core pricing engine.

9-step algorithm:
  1. Detect pickup area & zone from postal code
  2. Detect drop area & zone from postal code
  3. Calculate volumetric weight: (L × B × H) / 5000
  4. Calculate billable weight: max(actual, volumetric)
  5. Determine zone type: INTRA_ZONE if same zone, else INTER_ZONE
  6. Select correct rate card (order_type + zone_type + weight slab)
  7. Calculate base charge from rate card
  8. If COD: look up COD surcharge config and calculate surcharge
  9. final_charge = base_charge + cod_surcharge
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import InvalidCODConfigError, RateNotConfiguredError
from app.models.area import Area
from app.models.cod_surcharge import CODSurcharge, SurchargeType
from app.models.order import PaymentType
from app.models.rate_card import OrderType, RateCard, ZoneType
from app.models.zone import Zone
from app.repositories.cod_surcharge_repo import CODSurchargeRepository
from app.repositories.rate_card_repo import RateCardRepository
from app.services.zone_service import ZoneService


@dataclass
class RateCalculationResult:
    """Full breakdown returned to the caller / exposed via API."""
    # Zones
    pickup_area_name: str
    pickup_postal_code: str
    pickup_zone_id: str
    pickup_zone_name: str
    drop_area_name: str
    drop_postal_code: str
    drop_zone_id: str
    drop_zone_name: str
    zone_type: ZoneType

    # Weights
    actual_weight: float
    volumetric_weight: float
    billable_weight: float

    # Charges
    rate_card_id: str
    base_charge: float
    cod_surcharge: float
    total_charge: float
    order_type: OrderType
    payment_type: PaymentType


class RateCalculationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.zone_service = ZoneService(db)
        self.rate_repo = RateCardRepository(db)
        self.cod_repo = CODSurchargeRepository(db)

    async def calculate(
        self,
        *,
        pickup_postal_code: str,
        drop_postal_code: str,
        length_cm: float,
        breadth_cm: float,
        height_cm: float,
        actual_weight_kg: float,
        order_type: OrderType,
        payment_type: PaymentType,
    ) -> RateCalculationResult:
        """Execute the 9-step rate calculation and return a full breakdown."""

        # Step 1 & 2 — Zone detection
        pickup_area, pickup_zone = await self.zone_service.detect_zone_by_postal_code(pickup_postal_code)
        drop_area, drop_zone = await self.zone_service.detect_zone_by_postal_code(drop_postal_code)

        # Step 3 — Volumetric weight
        volumetric_weight = (length_cm * breadth_cm * height_cm) / settings.VOLUMETRIC_DIVISOR

        # Step 4 — Billable weight
        billable_weight = max(actual_weight_kg, volumetric_weight)

        # Step 5 — Zone type
        zone_type = (
            ZoneType.INTRA_ZONE
            if pickup_zone.id == drop_zone.id
            else ZoneType.INTER_ZONE
        )

        # Step 6 — Rate card lookup
        rate_card = await self.rate_repo.find_rate(order_type, zone_type, billable_weight)
        if rate_card is None:
            raise RateNotConfiguredError(
                f"No active rate configured for {order_type.value} {zone_type.value} "
                f"orders at {billable_weight:.3f} kg. Please contact admin."
            )

        # Step 7 — Base charge
        base_charge = float(rate_card.price)

        # Step 8 — COD surcharge
        cod_surcharge = 0.0
        if payment_type == PaymentType.COD:
            cod_config = await self.cod_repo.get_by_order_type(order_type)
            if cod_config is None:
                raise InvalidCODConfigError(
                    f"No COD surcharge configured for {order_type.value} orders."
                )
            cod_surcharge = self._apply_cod_surcharge(cod_config, base_charge)

        # Step 9 — Final charge
        total_charge = round(base_charge + cod_surcharge, 2)

        return RateCalculationResult(
            pickup_area_name=pickup_area.name,
            pickup_postal_code=pickup_area.postal_code,
            pickup_zone_id=str(pickup_zone.id),
            pickup_zone_name=pickup_zone.name,
            drop_area_name=drop_area.name,
            drop_postal_code=drop_area.postal_code,
            drop_zone_id=str(drop_zone.id),
            drop_zone_name=drop_zone.name,
            zone_type=zone_type,
            actual_weight=round(actual_weight_kg, 3),
            volumetric_weight=round(volumetric_weight, 3),
            billable_weight=round(billable_weight, 3),
            rate_card_id=str(rate_card.id),
            base_charge=base_charge,
            cod_surcharge=round(cod_surcharge, 2),
            total_charge=total_charge,
            order_type=order_type,
            payment_type=payment_type,
        )

    @staticmethod
    def _apply_cod_surcharge(config: CODSurcharge, base_charge: float) -> float:
        if config.surcharge_type == SurchargeType.FIXED:
            return float(config.value)
        elif config.surcharge_type == SurchargeType.PERCENTAGE:
            return base_charge * (float(config.value) / 100.0)
        return 0.0
