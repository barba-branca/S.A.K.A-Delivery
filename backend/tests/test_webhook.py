"""
Testes para o endpoint de webhook (async).
"""
import json
import pytest
from httpx import AsyncClient

from app.security import generate_signature


@pytest.mark.asyncio
async def test_webhook_status(client: AsyncClient):
    """Testa endpoint de status do webhook."""
    response = await client.get("/webhook/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Testa health check."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    """Testa endpoint raiz."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "SAKA Delivery KDS API"
    assert data["version"] == "2.0.0"
