import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user_success(async_client: AsyncClient):
    payload = {
        "full_name": "Test Candidate",
        "email": "candidate_register@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!"
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "user" in data
    assert data["user"]["email"] == "candidate_register@example.com"
    assert data["user"]["onboarding_completed"] is False


@pytest.mark.asyncio
async def test_register_duplicate_email(async_client: AsyncClient):
    payload = {
        "full_name": "Duplicate User",
        "email": "duplicate@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!"
    }
    # First registration
    res1 = await async_client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    # Second registration with same email
    res2 = await async_client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 400
    data = res2.json()
    assert "already exists" in data["detail"].lower()


@pytest.mark.asyncio
async def test_register_password_mismatch(async_client: AsyncClient):
    payload = {
        "full_name": "Mismatch User",
        "email": "mismatch@example.com",
        "password": "Password123!",
        "confirm_password": "DifferentPassword!"
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient):
    # Register user first
    reg_payload = {
        "full_name": "Login User",
        "email": "login_user@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!"
    }
    await async_client.post("/api/v1/auth/register", json=reg_payload)

    # Login
    login_payload = {
        "email": "login_user@example.com",
        "password": "Password123!"
    }
    response = await async_client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "login_user@example.com"


@pytest.mark.asyncio
async def test_login_invalid_password(async_client: AsyncClient):
    reg_payload = {
        "full_name": "Bad Pass User",
        "email": "badpass@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!"
    }
    await async_client.post("/api/v1/auth/register", json=reg_payload)

    login_payload = {
        "email": "badpass@example.com",
        "password": "WrongPassword!"
    }
    response = await async_client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401
    data = response.json()
    assert "invalid" in data["detail"].lower()


@pytest.mark.asyncio
async def test_login_unknown_email(async_client: AsyncClient):
    login_payload = {
        "email": "unknown@example.com",
        "password": "Password123!"
    }
    response = await async_client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401
