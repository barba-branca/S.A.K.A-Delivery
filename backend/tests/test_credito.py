"""
Testes para dedução de crédito e criação de pedidos SaaS.
"""
import pytest
from httpx import AsyncClient


async def _get_auth_token(client: AsyncClient) -> str:
    """Helper: registra e loga para obter token."""
    await client.post("/auth/register", json={
        "username": "credituser",
        "full_name": "Credit Test User",
        "password": "test123",
    })
    resp = await client.post("/auth/login", json={
        "username": "credituser",
        "password": "test123",
    })
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_insufficient_credit(client: AsyncClient):
    """Testa erro ao criar pedido sem saldo suficiente."""
    token = await _get_auth_token(client)
    
    response = await client.post(
        "/pedidos",
        json={"via_arnaldo": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert "insuficiente" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_comprar_pacote_and_create_order(client: AsyncClient):
    """Testa compra de pacote e criação de pedido com dedução de crédito."""
    token = await _get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Compra pacote
    buy_resp = await client.post("/pacotes/comprar", json={"tipo": "padrao"}, headers=headers)
    assert buy_resp.status_code == 200
    data = buy_resp.json()
    assert data["novo_saldo"] == 5000.0
    
    # Cria pedido
    order_resp = await client.post("/pedidos", json={"via_arnaldo": False}, headers=headers)
    assert order_resp.status_code == 200
    order_data = order_resp.json()
    assert order_data["pedido"]["valor_consumido"] == 5.0
    assert order_data["novo_saldo"] == 4995.0  # 5000 - 5


@pytest.mark.asyncio
async def test_via_arnaldo_creates_repasse(client: AsyncClient):
    """Testa que pedido via_arnaldo cria repasse com 30% (R$1.50)."""
    token = await _get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Compra pacote
    await client.post("/pacotes/comprar", json={"tipo": "padrao"}, headers=headers)
    
    # Cria pedido via arnaldo
    order_resp = await client.post("/pedidos", json={"via_arnaldo": True}, headers=headers)
    assert order_resp.status_code == 200
    
    # Verifica repasse
    repasse_resp = await client.get("/repasse/mensal", headers=headers)
    assert repasse_resp.status_code == 200
    repasse_data = repasse_resp.json()
    assert repasse_data["total_pendente"] == 1.5  # 30% de R$5.00
    assert repasse_data["quantidade_pendente"] == 1


@pytest.mark.asyncio
async def test_credit_deduction_sequential(client: AsyncClient):
    """Testa dedução sequencial de crédito em múltiplos pedidos."""
    token = await _get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Compra pacote
    await client.post("/pacotes/comprar", json={"tipo": "padrao"}, headers=headers)
    
    # Cria 3 pedidos
    for i in range(3):
        resp = await client.post("/pedidos", json={"via_arnaldo": False}, headers=headers)
        assert resp.status_code == 200
    
    # Verifica saldo final: 5000 - (3 * 5) = 4985
    me_resp = await client.get("/auth/me", headers=headers)
    saldo = me_resp.json()["saldoCredito"]
    assert saldo == 4985.0
