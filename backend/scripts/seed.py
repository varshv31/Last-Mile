"""Development seed script — populates the database with sample data.

Run with:
    python scripts/seed.py

Prerequisites:
    - PostgreSQL running
    - .env file configured
    - Alembic migrations applied: alembic upgrade head
"""
from __future__ import annotations

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.area import Area
from app.models.cod_surcharge import CODSurcharge, SurchargeType
from app.models.delivery_agent import AvailabilityStatus, DeliveryAgent
from app.models.rate_card import OrderType, RateCard, ZoneType
from app.models.user import User, UserRole
from app.models.zone import Zone


async def seed(db: AsyncSession) -> None:
    print("🌱 Seeding database...")

    # ── Zones ──────────────────────────────────────────────────
    z_mum_n = Zone(name="Mumbai North", code="MUM-N", description="Northern Mumbai zone", is_active=True)
    z_mum_s = Zone(name="Mumbai South", code="MUM-S", description="Southern Mumbai zone", is_active=True)
    z_pune = Zone(name="Pune", code="PUN", description="Pune zone", is_active=True)
    z_chennai = Zone(name="Chennai", code="CHN", description="Chennai zone", is_active=True)
    z_bangalore = Zone(name="Bangalore", code="BLR", description="Bangalore zone", is_active=True)
    db.add_all([z_mum_n, z_mum_s, z_pune, z_chennai, z_bangalore])
    await db.flush()
    print(f"  ✅ Zones: {[z.code for z in [z_mum_n, z_mum_s, z_pune, z_chennai, z_bangalore]]}")

    # ── Areas / Postal Codes ───────────────────────────────────
    areas = [
        Area(name="Andheri East", postal_code="400069", zone_id=z_mum_n.id),
        Area(name="Andheri West", postal_code="400058", zone_id=z_mum_n.id),
        Area(name="Bandra West", postal_code="400050", zone_id=z_mum_s.id),
        Area(name="Colaba", postal_code="400001", zone_id=z_mum_s.id),
        Area(name="Kothrud", postal_code="411038", zone_id=z_pune.id),
        Area(name="Viman Nagar", postal_code="411014", zone_id=z_pune.id),
        Area(name="T Nagar", postal_code="600017", zone_id=z_chennai.id),
        Area(name="Anna Nagar", postal_code="600040", zone_id=z_chennai.id),
        Area(name="Koramangala", postal_code="560034", zone_id=z_bangalore.id),
        Area(name="Indiranagar", postal_code="560038", zone_id=z_bangalore.id),
    ]
    db.add_all(areas)
    await db.flush()
    print(f"  ✅ Areas: {len(areas)} postal codes added")

    # ── Rate Cards — B2C Intra-Zone ────────────────────────────
    b2c_intra = [
        RateCard(order_type=OrderType.B2C, zone_type=ZoneType.INTRA_ZONE, min_weight=0, max_weight=1, price=40.00),
        RateCard(order_type=OrderType.B2C, zone_type=ZoneType.INTRA_ZONE, min_weight=1, max_weight=2, price=55.00),
        RateCard(order_type=OrderType.B2C, zone_type=ZoneType.INTRA_ZONE, min_weight=2, max_weight=5, price=90.00),
        RateCard(order_type=OrderType.B2C, zone_type=ZoneType.INTRA_ZONE, min_weight=5, max_weight=10, price=150.00),
        RateCard(order_type=OrderType.B2C, zone_type=ZoneType.INTRA_ZONE, min_weight=10, max_weight=999, price=250.00),
    ]
    # B2C Inter-Zone
    b2c_inter = [
        RateCard(order_type=OrderType.B2C, zone_type=ZoneType.INTER_ZONE, min_weight=0, max_weight=1, price=80.00),
        RateCard(order_type=OrderType.B2C, zone_type=ZoneType.INTER_ZONE, min_weight=1, max_weight=2, price=110.00),
        RateCard(order_type=OrderType.B2C, zone_type=ZoneType.INTER_ZONE, min_weight=2, max_weight=5, price=175.00),
        RateCard(order_type=OrderType.B2C, zone_type=ZoneType.INTER_ZONE, min_weight=5, max_weight=10, price=280.00),
        RateCard(order_type=OrderType.B2C, zone_type=ZoneType.INTER_ZONE, min_weight=10, max_weight=999, price=450.00),
    ]
    # B2B Intra-Zone
    b2b_intra = [
        RateCard(order_type=OrderType.B2B, zone_type=ZoneType.INTRA_ZONE, min_weight=0, max_weight=5, price=120.00),
        RateCard(order_type=OrderType.B2B, zone_type=ZoneType.INTRA_ZONE, min_weight=5, max_weight=20, price=200.00),
        RateCard(order_type=OrderType.B2B, zone_type=ZoneType.INTRA_ZONE, min_weight=20, max_weight=999, price=350.00),
    ]
    # B2B Inter-Zone
    b2b_inter = [
        RateCard(order_type=OrderType.B2B, zone_type=ZoneType.INTER_ZONE, min_weight=0, max_weight=5, price=220.00),
        RateCard(order_type=OrderType.B2B, zone_type=ZoneType.INTER_ZONE, min_weight=5, max_weight=20, price=380.00),
        RateCard(order_type=OrderType.B2B, zone_type=ZoneType.INTER_ZONE, min_weight=20, max_weight=999, price=650.00),
    ]
    all_rates = b2c_intra + b2c_inter + b2b_intra + b2b_inter
    db.add_all(all_rates)
    print(f"  ✅ Rate cards: {len(all_rates)} slabs configured")

    # ── COD Surcharges ─────────────────────────────────────────
    db.add(CODSurcharge(order_type=OrderType.B2C, surcharge_type=SurchargeType.FIXED, value=30.00))
    db.add(CODSurcharge(order_type=OrderType.B2B, surcharge_type=SurchargeType.PERCENTAGE, value=2.0))
    print("  ✅ COD surcharges: B2C=₹30 fixed, B2B=2% percentage")

    # ── Admin user ─────────────────────────────────────────────
    admin = User(
        name="Admin User",
        email="admin@lmdtracker.com",
        phone="+919000000000",
        password_hash=hash_password("Admin@12345"),
        role=UserRole.ADMIN,
    )
    db.add(admin)

    # ── Customer ───────────────────────────────────────────────
    customer = User(
        name="Priya Sharma",
        email="priya@example.com",
        phone="+919876543210",
        password_hash=hash_password("Customer@123"),
        role=UserRole.CUSTOMER,
    )
    db.add(customer)

    # ── Agents ─────────────────────────────────────────────────
    agent_data = [
        ("Rajan Kumar", "rajan@lmdtracker.com", "+919111111111", 19.1136, 72.8697, z_mum_n.id),
        ("Pradeep Singh", "pradeep@lmdtracker.com", "+919222222222", 18.9220, 72.8347, z_mum_s.id),
        ("Kavitha Nair", "kavitha@lmdtracker.com", "+919333333333", 18.5204, 73.8567, z_pune.id),
        ("Suresh Pillai", "suresh@lmdtracker.com", "+919444444444", 13.0827, 80.2707, z_chennai.id),
    ]

    await db.flush()

    agents = []
    for name, email, phone, lat, lon, zone_id in agent_data:
        u = User(
            name=name,
            email=email,
            phone=phone,
            password_hash=hash_password("Agent@12345"),
            role=UserRole.AGENT,
        )
        db.add(u)
        await db.flush()
        a = DeliveryAgent(
            user_id=u.id,
            current_latitude=lat,
            current_longitude=lon,
            current_zone_id=zone_id,
            availability_status=AvailabilityStatus.AVAILABLE,
        )
        db.add(a)
        agents.append(name)

    print(f"  ✅ Users: 1 admin, 1 customer, {len(agents)} agents")

    await db.commit()
    print("\n🎉 Seed complete!")
    print("\nLogin credentials:")
    print("  Admin:    admin@lmdtracker.com / Admin@12345")
    print("  Customer: priya@example.com / Customer@123")
    print("  Agent:    rajan@lmdtracker.com / Agent@12345")


async def main() -> None:
    async with AsyncSessionLocal() as db:
        await seed(db)


if __name__ == "__main__":
    asyncio.run(main())
