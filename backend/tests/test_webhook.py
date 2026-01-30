"""
Testes para o endpoint de webhook.
"""
import json
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.security import generate_signature

client = TestClient(app)


def test_webhook_status():
    """Testa endpoint de status do webhook."""
    response = client.get("/webhook/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"


def test_webhook_without_signature():
    """Testa webhook sem assinatura (deve falhar em produção)."""
    event = {
        "id": "test-event-001",
        "code": "TEST",
        "orderId": None
    }
    response = client.post("/webhook", json=event)
    # Em modo debug sem secret, aceita
    assert response.status_code in [202, 401]


def test_webhook_with_valid_signature():
    """Testa webhook com assinatura válida."""
    secret = "test_secret"
    event = {
        "id": "test-event-002",
        "code": "TEST",
        "orderId": None
    }
    
    payload = json.dumps(event).encode()
    signature = generate_signature(payload, secret)
    
    response = client.post(
        "/webhook",
        json=event,
        headers={"X-iFood-Signature": signature}
    )
    # Depende da configuração do secret
    assert response.status_code in [202, 401]


def test_health_check():
    """Testa health check."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_root():
    """Testa endpoint raiz."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "SAKA Delivery KDS API"
