"""
Testes para autenticação JWT.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Testa registro de novo usuário."""
    response = await client.post("/auth/register", json={
        "username": "testuser",
        "full_name": "Test User",
        "password": "test123",
        "email": "test@example.com",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Conta criada com sucesso"
    assert "access_token" in data
    assert data["user"]["username"] == "testuser"


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient):
    """Testa registro com username duplicado."""
    await client.post("/auth/register", json={
        "username": "duplicate",
        "full_name": "User",
        "password": "pass123",
    })
    response = await client.post("/auth/register", json={
        "username": "duplicate",
        "full_name": "Another User",
        "password": "pass456",
    })
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Testa login com credenciais válidas (admin padrão)."""
    response = await client.post("/auth/login", json={
        "username": "admin",
        "password": "admin123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["role"] == "ADMIN"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    """Testa login com credenciais inválidas."""
    response = await client.post("/auth/login", json={
        "username": "nonexistent",
        "password": "wrong",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(client: AsyncClient):
    """Testa endpoint /auth/me com token válido."""
    # Login first
    login_resp = await client.post("/auth/login", json={
        "username": "admin",
        "password": "admin123",
    })
    token = login_resp.json()["access_token"]
    
    # Get me
    response = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "admin"


@pytest.mark.asyncio
async def test_get_me_no_token(client: AsyncClient):
    """Testa endpoint /auth/me sem token."""
    response = await client.get("/auth/me")
    assert response.status_code == 401
