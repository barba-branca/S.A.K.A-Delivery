"""
Testes para repasse financeiro.
"""
import pytest
from httpx import AsyncClient


async def _setup_user_with_credit(client: AsyncClient) -> str:
    """Helper: cria user, compra pacote, retorna token."""
    await client.post("/auth/register", json={
        "username": "repasseuser",
        "full_name": "Repasse Test User",
        "password": "test123",
        "role": "SUPER_ADMIN"
    })
    resp = await client.post("/auth/login", json={
        "username": "repasseuser",
        "password": "test123",
    })
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    await client.post("/pacotes/comprar", json={"tipo": "padrao"}, headers=headers)
    return token


@pytest.mark.asyncio
async def test_repasse_mensal_empty(client: AsyncClient):
    """Testa relatório mensal sem repasses."""
    await client.post("/auth/register", json={
        "username": "emptyuser",
        "full_name": "Empty User",
        "password": "test123",
        "role": "SUPER_ADMIN"
    })
    resp = await client.post("/auth/login", json={
        "username": "emptyuser",
        "password": "test123",
    })
    token = resp.json()["access_token"]
    
    response = await client.get(
        "/repasse/mensal",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_pendente"] == 0
    assert data["quantidade_pendente"] == 0


@pytest.mark.asyncio
async def test_repasse_multiple_orders(client: AsyncClient):
    """Testa acumulação de repasses com múltiplos pedidos via_arnaldo."""
    token = await _setup_user_with_credit(client)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Cria 3 pedidos via arnaldo
    for _ in range(3):
        await client.post("/pedidos", json={"via_arnaldo": True}, headers=headers)
    
    # Verifica: 3 * R$1.50 = R$4.50
    response = await client.get("/repasse/mensal", headers=headers)
    data = response.json()
    assert data["total_pendente"] == 4.5
    assert data["quantidade_pendente"] == 3


@pytest.mark.asyncio
async def test_marcar_repasse_como_pago(client: AsyncClient):
    """Testa marcação de repasses como pagos."""
    token = await _setup_user_with_credit(client)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Cria pedido via arnaldo
    await client.post("/pedidos", json={"via_arnaldo": True}, headers=headers)
    
    # Verifica pendente
    resp1 = await client.get("/repasse/mensal", headers=headers)
    assert resp1.json()["quantidade_pendente"] == 1
    
    # Marca como pago
    pay_resp = await client.post("/repasse/pagar", headers=headers)
    assert pay_resp.status_code == 200
    assert pay_resp.json()["quantidade"] == 1
    
    # Verifica que não há mais pendentes
    resp2 = await client.get("/repasse/mensal", headers=headers)
    assert resp2.json()["quantidade_pendente"] == 0
    assert resp2.json()["total_pago"] == 1.5
