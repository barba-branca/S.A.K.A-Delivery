# SAKA Delivery KDS - Backend

Backend FastAPI para integração com iFood via Webhook.

## 🚀 Funcionalidades

- ✅ **Webhook iFood** - Recebe eventos com validação HMAC SHA256
- ✅ **Resposta Rápida** - Processa em background para responder em < 5 segundos
- ✅ **Banco de Dados** - SQLite para persistência de pedidos
- ✅ **API REST** - Endpoints para o frontend KDS consumir
- ✅ **CORS** - Configurado para o frontend

## 📋 Requisitos

- Python 3.9+
- pip

## 🔧 Instalação

```bash
# Entre na pasta do backend
cd backend

# Crie um ambiente virtual
python -m venv venv

# Ative o ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
```

## ⚙️ Configuração

1. Copie o arquivo `.env.example` para `.env`:
```bash
cp .env.example .env
```

2. Configure suas credenciais do iFood:
```env
IFOOD_CLIENT_ID=seu_client_id
IFOOD_CLIENT_SECRET=seu_client_secret
```

## 🏃 Executando

```bash
# Desenvolvimento
python run.py

# Ou diretamente com uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

O servidor estará disponível em: http://localhost:8000

## 📡 Endpoints

### Webhook iFood
- `POST /webhook` - Recebe eventos do iFood
- `GET /webhook/status` - Verifica status do webhook

### Pedidos (API REST)
- `GET /orders` - Lista todos os pedidos
- `GET /orders/{id}` - Busca pedido por ID
- `PATCH /orders/{id}/status` - Atualiza status do pedido
- `POST /orders/drivers/{name}/pay` - Marca motorista como pago

### Utilitários
- `GET /` - Informações da API
- `GET /health` - Health check
- `GET /docs` - Documentação Swagger
- `GET /redoc` - Documentação ReDoc

## 🔐 Segurança

O webhook valida a assinatura `X-iFood-Signature` usando HMAC SHA256.

## 🧪 Testando

```bash
# Simular webhook localmente
python simulate_webhook.py

# Executar testes
pytest tests/
```

## 📁 Estrutura

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # Aplicação FastAPI
│   ├── config.py         # Configurações
│   ├── database.py       # Configuração SQLite
│   ├── models.py         # Modelos SQLAlchemy
│   ├── schemas.py        # Schemas Pydantic
│   ├── security.py       # Validação HMAC
│   ├── routers/
│   │   ├── webhook.py    # Endpoint /webhook
│   │   └── orders.py     # Endpoints /orders
│   └── services/
│       ├── order_service.py    # Lógica de pedidos
│       └── webhook_service.py  # Processamento de eventos
├── tests/
├── requirements.txt
├── run.py
└── .env
```
