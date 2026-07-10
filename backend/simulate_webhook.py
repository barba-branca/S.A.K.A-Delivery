"""
Script para simular webhooks do iFood.
Útil para testar a integração localmente.

Uso:
    python simulate_webhook.py
"""
import json
import requests
import sys
from datetime import datetime
from app.security import generate_signature


# Configurações
WEBHOOK_URL = "http://localhost:8000/webhook"
from app.config import get_settings
settings = get_settings()
CLIENT_SECRET = settings.ifood_client_secret


def create_order_placed_event():
    """Cria evento simulado de novo pedido."""
    return {
        "id": f"evt-{datetime.now().timestamp():.0f}",
        "code": "PLC",
        "orderId": f"order-{datetime.now().timestamp():.0f}",
        "merchantId": "merchant-123",
        "createdAt": datetime.now().isoformat(),
        "metadata": {
            "displayId": "12345",
            "shortReference": "ABC123",
            "customerName": "Cliente Teste",
            "subTotal": 3500,
            "deliveryFee": 500,
            "orderAmount": 4000,
            "items": [
                {"name": "Açaí 500ml", "quantity": 2, "unitPrice": 1500, "totalPrice": 3000},
                {"name": "Leite em pó", "quantity": 1, "unitPrice": 500, "totalPrice": 500}
            ],
            "deliveryAddress": {
                "streetName": "Rua Teste",
                "streetNumber": "123",
                "neighborhood": "Centro",
                "city": "São Paulo"
            }
        }
    }


def send_webhook(event: dict, with_signature: bool = True):
    """Envia webhook para o servidor."""
    payload = json.dumps(event).encode()
    
    headers = {"Content-Type": "application/json"}
    
    if with_signature:
        signature = generate_signature(payload, CLIENT_SECRET)
        headers["X-iFood-Signature"] = signature
        print(f"📝 Assinatura gerada: {signature[:32]}...")
    
    print(f"\n📤 Enviando evento: {event['code']}")
    print(f"   Order ID: {event.get('orderId', 'N/A')}")
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            data=payload,
            headers=headers
        )
        
        print(f"📥 Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        return response
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None


if __name__ == "__main__":
    print("=" * 50)
    print("🔧 Simulador de Webhook iFood")
    print("=" * 50)
    
    event = create_order_placed_event()
    send_webhook(event, with_signature=True)
