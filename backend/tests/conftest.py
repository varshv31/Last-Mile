"""Pytest configuration and shared fixtures."""
from __future__ import annotations

import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models import *  # noqa: F401, F403 — ensure all models are registered

# Use SQLite in-memory for tests (fast, no external dependency)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(autouse=True)
async def create_tables():
    """Create and drop tables for every test to ensure 100% isolation."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as c:
        yield c
    app.dependency_overrides.clear()


# ── Authenticated Clients ─────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def customer_client(client: AsyncClient, db: AsyncSession) -> AsyncClient:
    await create_user(db, "customer_client@test.com", "CUSTOMER", "TestPass@123")
    resp = await client.post("/api/v1/auth/login", json={"email": "customer_client@test.com", "password": "TestPass@123"})
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client

@pytest_asyncio.fixture
async def agent_client(client: AsyncClient, db: AsyncSession) -> AsyncClient:
    user = await create_user(db, "agent_client@test.com", "AGENT", "TestPass@123")
    from app.models.delivery_agent import DeliveryAgent, AvailabilityStatus
    agent = DeliveryAgent(user_id=user.id, availability_status=AvailabilityStatus.AVAILABLE)
    db.add(agent)
    await db.commit()
    resp = await client.post("/api/v1/auth/login", json={"email": "agent_client@test.com", "password": "TestPass@123"})
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client

@pytest_asyncio.fixture
async def admin_client(client: AsyncClient, db: AsyncSession) -> AsyncClient:
    await create_user(db, "admin_client@test.com", "ADMIN", "TestPass@123")
    resp = await client.post("/api/v1/auth/login", json={"email": "admin_client@test.com", "password": "TestPass@123"})
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


# ── Seed helpers ──────────────────────────────────────────────────────────────

async def create_user(db: AsyncSession, email: str, role: str, password: str = "Test@1234") -> dict:
    """Helper to register a user and return the token."""
    from app.core.security import hash_password
    from app.models.user import User, UserRole
    user = User(
        name="Test User",
        email=email,
        phone="+919000000001",
        password_hash=hash_password(password),
        role=UserRole(role),
    )
    db.add(user)
    await db.flush()
    return user


async def create_zone(db: AsyncSession, code: str = "TEST-Z") -> "Zone":
    from app.models.zone import Zone
    zone = Zone(name="Test Zone", code=code, is_active=True)
    db.add(zone)
    await db.flush()
    return zone


async def create_area(db: AsyncSession, postal_code: str, zone_id) -> "Area":
    from app.models.area import Area
    area = Area(name="Test Area", postal_code=postal_code, zone_id=zone_id, is_active=True)
    db.add(area)
    await db.flush()
    return area


async def create_rate_card(db: AsyncSession, order_type, zone_type, min_w, max_w, price) -> "RateCard":
    from app.models.rate_card import RateCard
    rc = RateCard(
        order_type=order_type,
        zone_type=zone_type,
        min_weight=min_w,
        max_weight=max_w,
        price=price,
        is_active=True,
    )
    db.add(rc)
    await db.flush()
    return rc
