# SAKA Delivery KDS - Backend

Backend FastAPI para integração com iFood via Webhook.

## 🚀 Funcionalidades

- ✅ **Webhook iFood** - Recebe eventos com validação HMAC SHA256
- ✅ **Resposta Rápida** - Processa em background para responder em < 5 segundos
- ✅ **Banco de Dados** - SQLite para persistência de pedidos
- ✅ **API REST** - Endpoints para o frontend KDS consumir
- ✅ **CORS** - Configurado para o frontend
- ✅ **Autenticação** - Sistema de login e registro de usuários
- ✅ **Reset Diário** - Limpa pedidos automaticamente a cada dia

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
- `GET /orders/stats` - Estatísticas de pedidos por status
- `PATCH /orders/{id}/status` - Atualiza status do pedido
- `POST /orders/drivers/{name}/pay` - Marca motorista como pago
- `DELETE /orders/{id}` - Exclui um pedido específico
- `DELETE /orders` - Remove todos os pedidos (reset)
- `POST /orders/daily-reset` - Verifica e executa reset diário

### Autenticação
- `POST /auth/login` - Login de usuário
- `POST /auth/register` - Registro de novo usuário
- `GET /auth/users` - Lista todos os usuários
- `DELETE /auth/users/{id}` - Exclui um usuário

### Utilitários
- `GET /` - Informações da API
- `GET /health` - Health check
- `GET /docs` - Documentação Swagger
- `GET /redoc` - Documentação ReDoc

## 👤 Credenciais Padrão

| Usuário | Senha | Função |
|---------|-------|--------|
| admin | admin123 | ADMIN |
| cozinha | 123 | KITCHEN |

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
│   ├── models.py         # Modelos SQLAlchemy (Order, User, etc)
│   ├── schemas.py        # Schemas Pydantic
│   ├── security.py       # Validação HMAC
│   ├── routers/
│   │   ├── webhook.py    # Endpoint /webhook
│   │   ├── orders.py     # Endpoints /orders
│   │   └── auth.py       # Endpoints /auth (login/registro)
│   └── services/
│       ├── order_service.py    # Lógica de pedidos
│       ├── user_service.py     # Lógica de usuários
│       └── webhook_service.py  # Processamento de eventos
├── tests/
├── requirements.txt
├── run.py
└── .env
```
