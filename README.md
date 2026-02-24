<p align="center">
  <img src="https://img.shields.io/badge/S.A.K.A-Delivery-blueviolet?style=for-the-badge&logo=uber&logoColor=white" alt="SAKA Delivery" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React" />
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript" />
</p>

<h1 align="center">🛵 S.A.K.A Delivery</h1>

<p align="center">
  <strong>Plataforma SaaS de gestão de delivery com pacotes pré-pagos, KDS e integração iFood.</strong>
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-tech-stack">Tech Stack</a> •
  <a href="#-como-rodar">Como Rodar</a> •
  <a href="#-api-endpoints">API</a> •
  <a href="#-arquitetura">Arquitetura</a> •
  <a href="#-deploy">Deploy</a>
</p>

---

## ✨ Features

| Feature | Status | Descrição |
|---------|--------|-----------|
| 🔐 **Autenticação JWT** | ✅ | Register/Login com tokens Bearer + bcrypt |
| 💰 **Pacotes Pré-pagos** | ✅ | Compra de créditos (R$5.000 / 1.000 pedidos) |
| 🧾 **Dedução de Crédito** | ✅ | R$5.00 por pedido com verificação de saldo |
| 💸 **Repasse Financeiro** | ✅ | 30% (R$1.50) para pedidos `via_arnaldo` |
| 📊 **Relatório Mensal** | ✅ | SUM de repasses pendentes / pagos |
| 🏠 **Dashboard SaaS** | ✅ | Saldo, pedidos restantes, gráficos Chart.js |
| 📋 **KDS Kanban** | ✅ | Board drag‑and‑drop conectado ao backend |
| 🔔 **Webhook iFood** | ✅ | Eventos com validação HMAC SHA256 |
| 💳 **Webhook Pagamento** | 🔜 | Stub OpenPix (pronto para integrar) |

---

## 🛠 Tech Stack

### Backend
- **FastAPI** — Framework async de alta performance
- **PostgreSQL** + **asyncpg** — Banco relacional async
- **SQLAlchemy 2.0** — ORM com suporte async
- **Alembic** — Migrações de banco de dados
- **JWT** (python-jose) + **bcrypt** (passlib) — Autenticação
- **Pydantic v2** — Validação de dados com Settings

### Frontend
- **React 19** + **TypeScript** — SPA tipada
- **Vite** — Build tool ultrarrápido
- **React Router v7** — Navegação SPA
- **Axios** — HTTP client com JWT interceptor
- **Chart.js** — Gráficos de uso mensal
- **Tailwind CSS** (CDN) — Styling utilitário
- **Lucide React** — Ícones modernos

### Testes
- **pytest** + **pytest-asyncio** — Backend (15 testes)
- **vitest** + **jsdom** — Frontend

---

## 🚀 Como Rodar

### Pré-requisitos

| Ferramenta | Versão |
|------------|--------|
| Python | 3.11+ |
| Node.js | 18+ |
| PostgreSQL | 15+ |

### 1️⃣ Banco de Dados

```sql
-- No pgAdmin ou psql:
CREATE DATABASE saka_delivery;
```

### 2️⃣ Backend

```bash
cd backend

# Ambiente virtual
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

# Dependências
pip install -r requirements.txt

# Configurar ambiente
copy .env.example .env         # ajuste DATABASE_URL se necessário

# Migrações
python -m alembic upgrade head

# Iniciar servidor
python run.py
# → http://localhost:8000/docs
```

### 3️⃣ Frontend

```bash
# Na raiz do projeto
npm install
npm run dev
# → http://localhost:5173
```

### 4️⃣ Testes

```bash
# Backend
cd backend
pytest tests/ -v

# Frontend
npm test
```

---

## 📡 API Endpoints

> Documentação interativa em **http://localhost:8000/docs**

### Autenticação
| Método | Rota | Auth | Descrição |
|--------|------|:----:|-----------|
| `POST` | `/auth/register` | ❌ | Criar conta |
| `POST` | `/auth/login` | ❌ | Login → JWT |
| `GET` | `/auth/me` | 🔒 | Dados do usuário logado |

### Pacotes & Crédito
| Método | Rota | Auth | Descrição |
|--------|------|:----:|-----------|
| `POST` | `/pacotes/comprar` | 🔒 | Comprar pacote (R$5.000) |
| `GET` | `/pacotes` | 🔒 | Listar pacotes |

### Pedidos SaaS
| Método | Rota | Auth | Descrição |
|--------|------|:----:|-----------|
| `POST` | `/pedidos` | 🔒 | Criar pedido (deduz R$5) |
| `GET` | `/pedidos` | 🔒 | Listar pedidos |

### Repasse Financeiro
| Método | Rota | Auth | Descrição |
|--------|------|:----:|-----------|
| `GET` | `/repasse/mensal` | 🔒 | Relatório do mês |
| `POST` | `/repasse/pagar` | 🔒 | Marcar como pago |

### KDS (Kitchen Display)
| Método | Rota | Auth | Descrição |
|--------|------|:----:|-----------|
| `GET` | `/orders` | ❌ | Listar pedidos KDS |
| `POST` | `/orders/create` | ❌ | Criar pedido KDS |
| `PATCH` | `/orders/{id}/status` | ❌ | Atualizar status |
| `POST` | `/orders/drivers/{name}/pay` | ❌ | Pagar motorista |

### Webhooks
| Método | Rota | Auth | Descrição |
|--------|------|:----:|-----------|
| `POST` | `/webhook` | ❌ | Receber evento iFood |
| `POST` | `/webhook/pagamento` | ❌ | Receber pagamento (stub) |

---

## 🏗 Arquitetura

```
saka-delivery-kds/
│
├── 🎨 Frontend (React + Vite + TS)
│   ├── App.tsx                    # React Router + layout protegido
│   ├── src/
│   │   ├── contexts/AuthContext   # JWT auth provider
│   │   ├── services/api.ts        # Axios + interceptor
│   │   ├── pages/
│   │   │   ├── LoginPage          # Login/Register
│   │   │   ├── DashboardPage      # Saldo + gráficos
│   │   │   ├── PedidosPage        # Tabela de pedidos
│   │   │   └── KDSPage            # Kanban board
│   │   └── components/Sidebar     # Navegação
│   └── components/                # KDS: KanbanBoard, OrderCard, Timer
│
├── ⚙️ Backend (FastAPI + PostgreSQL)
│   └── backend/
│       ├── app/
│       │   ├── main.py            # App + routers
│       │   ├── models.py          # User, Pacote, PedidoSaas, Repasse, Order
│       │   ├── security.py        # JWT + bcrypt + HMAC
│       │   ├── routers/           # 7 routers (auth, orders, pacotes, etc.)
│       │   └── services/          # 6 services (business logic)
│       ├── alembic/               # Migrações
│       └── tests/                 # 15 testes pytest
│
└── 📄 Config
    ├── .env.example               # Template de variáveis
    ├── package.json               # Frontend deps
    └── requirements.txt           # Backend deps
```

---

## 🔧 Variáveis de Ambiente

Copie `backend/.env.example` → `backend/.env` e ajuste:

| Variável | Exemplo | Descrição |
|----------|---------|-----------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/saka_delivery` | Conexão PostgreSQL |
| `JWT_SECRET` | `sua-chave-secreta` | Segredo para tokens JWT |
| `JWT_EXPIRE_MINUTES` | `1440` | Tempo de expiração (24h) |
| `IFOOD_CLIENT_ID` | `...` | Credencial iFood |
| `IFOOD_CLIENT_SECRET` | `...` | Segredo iFood (webhook HMAC) |
| `GEMINI_API_KEY` | `...` | Chave da API Gemini |

---

## 🚢 Deploy

### Backend → Render / Railway / Fly.io

```bash
# Start command
uvicorn app.main:app --host 0.0.0.0 --port $PORT

# Env vars obrigatórias: DATABASE_URL, JWT_SECRET
# Set DEBUG=false em produção
```

### Frontend → Vercel / Netlify

```bash
# Build
npm run build
# Output: dist/
```

---

## 👤 Credenciais Demo

| Usuário | Senha | Role |
|---------|-------|------|
| `admin` | `admin123` | ADMIN |
| `cozinha` | `123` | KITCHEN |

---

## 📝 Licença

Projeto privado — **barba-branca** © 2026
