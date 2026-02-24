# S.A.K.A Delivery – SaaS de Gestão de Delivery

<p align="center">
  <strong>Sistema de gestão de delivery com pacotes pré-pagos, KDS (Kitchen Display System) e integração iFood.</strong>
</p>

---

## 🏗️ Arquitetura

```
saka-delivery-kds/
├── App.tsx                    # App principal (React Router)
├── index.html                 # Entry point HTML
├── index.tsx                  # React root
├── package.json               # Deps frontend
├── vite.config.ts             # Vite config
├── vitest.config.ts           # Vitest config
├── types.ts                   # Types TypeScript (KDS)
├── components/                # Componentes KDS existentes
│   ├── KanbanBoard.tsx        # Board Kanban drag-and-drop
│   ├── OrderCard.tsx          # Card de pedido
│   ├── Login.tsx              # Login legacy (mantido)
│   ├── DriverPayouts.tsx      # Repasse motoristas
│   └── Timer.tsx              # Timer de preparação
├── services/
│   └── mockDb.ts              # Mock DB (KDS local)
├── src/
│   ├── contexts/
│   │   └── AuthContext.tsx     # Context de autenticação JWT
│   ├── services/
│   │   └── api.ts             # Axios + JWT interceptor
│   ├── pages/
│   │   ├── LoginPage.tsx      # Login/Register (conectado ao backend)
│   │   ├── DashboardPage.tsx  # Dashboard com saldo, gráficos
│   │   ├── PedidosPage.tsx    # Tabela de pedidos SaaS
│   │   └── KDSPage.tsx        # Tela KDS (Kanban)
│   └── components/
│       └── Sidebar.tsx        # Sidebar de navegação
└── backend/
    ├── app/
    │   ├── main.py            # FastAPI app
    │   ├── config.py          # Settings (pydantic-settings)
    │   ├── database.py        # Async PostgreSQL engine
    │   ├── models.py          # SQLAlchemy models
    │   ├── schemas.py         # Pydantic schemas
    │   ├── security.py        # JWT + bcrypt + iFood HMAC
    │   ├── routers/
    │   │   ├── auth.py        # /auth (login, register, me)
    │   │   ├── orders.py      # /orders (KDS CRUD)
    │   │   ├── webhook.py     # /webhook (iFood webhook)
    │   │   ├── pacotes.py     # /pacotes (compra de pacotes)
    │   │   ├── pedidos_saas.py# /pedidos (pedidos SaaS)
    │   │   ├── repasse.py     # /repasse (relatório financeiro)
    │   │   └── webhook_pagamento.py # /webhook/pagamento (OpenPix stub)
    │   └── services/
    │       ├── user_service.py
    │       ├── order_service.py
    │       ├── webhook_service.py
    │       ├── pacote_service.py
    │       ├── pedido_saas_service.py
    │       └── repasse_service.py
    ├── alembic/               # Migrações de banco
    │   ├── env.py
    │   └── versions/
    ├── tests/
    │   ├── conftest.py        # Fixtures (SQLite in-memory)
    │   ├── test_auth.py       # 5 testes de autenticação
    │   ├── test_credito.py    # 4 testes de crédito
    │   ├── test_repasse.py    # 3 testes de repasse
    │   └── test_webhook.py    # 3 testes de webhook
    └── requirements.txt
```

## ✨ Features

| Feature | Status | Descrição |
|---------|--------|-----------|
| **Autenticação JWT** | ✅ | Register/Login com tokens Bearer |
| **Pacotes Pré-pagos** | ✅ | Compra de créditos (R$5.000 / 1.000 pedidos) |
| **Dedução de Crédito** | ✅ | R$5.00 por pedido, verificação de saldo |
| **Repasse Arnaldo** | ✅ | 30% (R$1.50) para pedidos via_arnaldo |
| **Relatório Mensal** | ✅ | SUM de repasses pendentes/pagos |
| **Dashboard SaaS** | ✅ | Saldo, pedidos restantes, gráficos |
| **KDS (Kanban)** | ✅ | Board drag-and-drop de pedidos |
| **Webhook iFood** | ✅ | Recebimento de eventos com HMAC |
| **Webhook Pagamento** | 🔜 | Stub para OpenPix (pronto para integrar) |

## 🚀 Como Rodar

### Pré-requisitos

- **Python 3.11+**
- **Node.js 18+**
- **PostgreSQL 15+** (com um banco chamado `saka_delivery`)

### Backend

```bash
# 1. Entrar na pasta do backend
cd backend

# 2. Criar e ativar ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Criar banco PostgreSQL
# psql -U postgres -c "CREATE DATABASE saka_delivery;"

# 5. Configurar .env (copiar .env.example e ajustar)
copy .env.example .env

# 6. Rodar migrações
alembic upgrade head

# 7. Iniciar servidor
python run.py
# → http://localhost:8000/docs
```

### Frontend

```bash
# 1. Na raiz do projeto
npm install

# 2. Iniciar dev server
npm run dev
# → http://localhost:3000
```

### Testes

```bash
# Backend
cd backend
pip install aiosqlite  # necessário para testes
pytest tests/ -v

# Frontend
npm test
```

## 🔧 Variáveis de Ambiente (.env)

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/saka_delivery

# JWT
JWT_SECRET=your-secret-key-here
JWT_EXPIRE_MINUTES=1440

# iFood
IFOOD_CLIENT_ID=your_client_id
IFOOD_CLIENT_SECRET=your_client_secret

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=true
FRONTEND_URL=http://localhost:5173

# Gemini AI
GEMINI_API_KEY=your_api_key
```

## 📡 API Endpoints

| Método | Endpoint | Auth | Descrição |
|--------|----------|------|-----------|
| POST | `/auth/register` | ❌ | Registrar usuário |
| POST | `/auth/login` | ❌ | Login (retorna JWT) |
| GET | `/auth/me` | ✅ | Dados do usuário logado |
| POST | `/pacotes/comprar` | ✅ | Comprar pacote de créditos |
| GET | `/pacotes` | ✅ | Listar pacotes do usuário |
| POST | `/pedidos` | ✅ | Criar pedido (deduz R$5) |
| GET | `/pedidos` | ✅ | Listar pedidos SaaS |
| GET | `/repasse/mensal` | ✅ | Relatório mensal |
| POST | `/repasse/pagar` | ✅ | Marcar repasses como pagos |
| GET | `/orders` | ❌ | Pedidos KDS |
| POST | `/webhook` | ❌ | Webhook iFood |
| POST | `/webhook/pagamento` | ❌ | Webhook Pagamento (stub) |

## 🚢 Deploy

### Backend (Render / Fly.io)

1. Configure `DATABASE_URL` para o PostgreSQL hospedado
2. Defina `JWT_SECRET` com uma chave forte
3. Set `DEBUG=false` em produção
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Frontend (Vercel / Netlify)

1. Build command: `npm run build`
2. Publish directory: `dist`
3. Configure API URL no código ou via env

## 📝 Credenciais Padrão (Demo)

| Usuário | Senha | Role |
|---------|-------|------|
| `admin` | `admin123` | ADMIN |
| `cozinha` | `123` | KITCHEN |
