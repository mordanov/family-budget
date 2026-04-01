import pytest
from app.core.config import settings


@pytest.mark.asyncio
async def test_login_success(client, test_user):
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "testpassword"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_login_wrong_password(client, test_user):
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(client):
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "nobody@example.com", "password": "pass"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_with_user_name(client, test_user):
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "Test User", "password": "testpassword"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_register(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"name": "New User", "email": "new@example.com", "password": "newpassword"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "new@example.com"
    assert data["name"] == "New User"
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client, test_user):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"name": "Dup", "email": "test@example.com", "password": "pass123"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_protected_endpoint_without_token(client):
    resp = await client.get("/api/v1/users/")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_robot_token_access(client, test_user):
    old_tokens = settings.ROBOT_API_TOKENS
    settings.ROBOT_API_TOKENS = "robot-token-1:test@example.com"
    try:
        resp = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer robot-token-1"},
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == "test@example.com"
    finally:
        settings.ROBOT_API_TOKENS = old_tokens

