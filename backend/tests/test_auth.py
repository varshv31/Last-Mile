"""Tests 1-4: Authentication — register, login, JWT, role authorization."""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_register_customer(client: AsyncClient, db: AsyncSession):
    """Test 1: Customer registration."""
    resp = await client.post("/api/v1/auth/register", json={
        "name": "Test Customer",
        "email": "testcustomer@example.com",
        "phone": "+919000000010",
        "password": "TestPass@123",
        "role": "CUSTOMER",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "testcustomer@example.com"
    assert data["role"] == "CUSTOMER"
    assert "password_hash" not in data
    assert "password" not in data


@pytest.mark.asyncio
async def test_duplicate_email_rejected(client: AsyncClient, db: AsyncSession):
    """Test 1b: Duplicate email rejected with 409."""
    payload = {
        "name": "Dup User",
        "email": "dup@example.com",
        "phone": "+919000000011",
        "password": "TestPass@123",
        "role": "CUSTOMER",
    }
    await client.post("/api/v1/auth/register", json=payload)
    resp2 = await client.post("/api/v1/auth/register", json=payload)
    assert resp2.status_code == 409
    assert resp2.json()["code"] == "DUPLICATE_EMAIL"


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, db: AsyncSession):
    """Test 2: Login returns JWT tokens."""
    await client.post("/api/v1/auth/register", json={
        "name": "Login User",
        "email": "loginuser@example.com",
        "password": "TestPass@123",
        "role": "CUSTOMER",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "loginuser@example.com",
        "password": "TestPass@123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, db: AsyncSession):
    """Test 2b: Wrong password returns 401."""
    await client.post("/api/v1/auth/register", json={
        "name": "Bad Pass User",
        "email": "badpass@example.com",
        "password": "TestPass@123",
        "role": "CUSTOMER",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "badpass@example.com",
        "password": "WrongPassword!",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_jwt_authentication(client: AsyncClient, db: AsyncSession):
    """Test 3: Valid JWT allows access to protected endpoint."""
    await client.post("/api/v1/auth/register", json={
        "name": "JWT Test", "email": "jwttest@example.com",
        "password": "TestPass@123", "role": "CUSTOMER",
    })
    login = await client.post("/api/v1/auth/login", json={
        "email": "jwttest@example.com", "password": "TestPass@123",
    })
    token = login.json()["access_token"]

    me_resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "jwttest@example.com"


@pytest.mark.asyncio
async def test_invalid_jwt_rejected(client: AsyncClient):
    """Test 3b: Invalid token returns 401."""
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_role_authorization_admin_endpoint(client: AsyncClient, db: AsyncSession):
    """Test 4: Customer cannot access admin endpoint."""
    await client.post("/api/v1/auth/register", json={
        "name": "Customer", "email": "cust_role@example.com",
        "password": "TestPass@123", "role": "CUSTOMER",
    })
    login = await client.post("/api/v1/auth/login", json={
        "email": "cust_role@example.com", "password": "TestPass@123",
    })
    token = login.json()["access_token"]

    resp = await client.get("/api/v1/admin/zones", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_token_refresh(client: AsyncClient, db: AsyncSession):
    """Test 3c: Refresh token returns new access token."""
    await client.post("/api/v1/auth/register", json={
        "name": "Refresh Test", "email": "refreshtest@example.com",
        "password": "TestPass@123", "role": "CUSTOMER",
    })
    login = await client.post("/api/v1/auth/login", json={
        "email": "refreshtest@example.com", "password": "TestPass@123",
    })
    refresh_token = login.json()["refresh_token"]

    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()
