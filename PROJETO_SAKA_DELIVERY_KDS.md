# S.A.K.A Delivery KDS - Documentação Técnica Completa

## Visão Geral do Projeto

S.A.K.A Delivery KDS é um sistema SaaS (Software as a Service) completo de gestão para delivery, desenvolvido com arquitetura moderna separating frontend e backend. O sistema oferece gestão de pedidos em tempo real, Kitchen Display System (KDS), integração com iFood, sistema de pagamentos via PIX/QR Code, pacotes pré-pagos e gerenciamento de repasses para entregadores.

O projeto foi criado utilizando Google AI Studio como ferramenta辅助de desenvolvimento e sigue os princípios de Clean Architecture com separação clara de responsabilidades entre as camadas de apresentação, lógica de negócio e persistência de dados.

---

## Stack Tecnológico

### Frontend

O frontend foi desenvolvido utilizando as seguintes tecnologias:

**Framework Principal:**
- React 19 - Biblioteca principal para construção da interface de usuário
- TypeScript - Linguagem com tipagem estática para maior segurança e manutenibilidade do código

**Build e Configuração:**
- Vite 7.3.1 - Build tool moderna e extremamente rápida
- Tailwind CSS 4.2.1 - Framework de CSS utilitário para estilização
- PostCSS - Processador de CSS para transformação de estilos

**Principais Dependências:**
- react-router-dom (v7) - Roteamento de páginas SPA
- axios - Cliente HTTP para comunicação com API
- lucide-react - Biblioteca de ícones
- @tailwindcss/vite - Plugin Tailwind para Vite

**Configuração de Desenvolvimento:**
- Porta: 3000
- Host: 0.0.0.0 (aceita conexões de qualquer interface)
- Hot Module Replacement (HMR) ativado

### Backend

O backend foi desenvolvido com:

**Framework:**
- FastAPI - Framework Python moderno e de alto desempenho
- Uvicorn - Servidor ASGI de produção

**Banco de Dados:**
- SQLite com SQLAlchemy ORM (async)
- Alembic - Ferramenta de migração de banco de dados
- aiosqlite - Driver async para SQLite

**Autenticação:**
- Python-JOSE - Geração e validação de tokens JWT
- Passlib + Bcrypt - Hashing de senhas

**Principais Dependências Python:**
- fastapi
- uvicorn
- sqlalchemy
- alembic
- pydantic
- python-jose
- passlib
- bcrypt

**Configuração de Desenvolvimento:**
- Porta: 8000
- Host: 0.0.0.0
- Documentação automática: /docs e /redoc

---

## Estrutura de Pastas e Arquivos

### Frontend (c:/Users/Kaue_Martins/Desktop/saka-delivery-kds/)

```
saka-delivery-kds/
├── App.tsx                    # Componente principal com rotas
├── index.html                 # HTML principal
├── index.tsx                  # Entry point React
├── package.json               # Dependências npm
├── vite.config.ts            # Configuração Vite
├── tsconfig.json             # Configuração TypeScript
├── types.ts                  # Tipos TypeScript globais
├── src/
│   ├── index.css            # Estilos Tailwind globais
│   ├── components/
│   │   └── Sidebar.tsx      # Menu lateral
│   ├── contexts/
│   │   └── AuthContext.tsx  # Contexto de autenticação
│   ├── pages/
│   │   ├── LoginPage.tsx    # Página de login/registro
│   │   ├── DashboardPage.tsx # Dashboard principal
│   │   ├── PedidosPage.tsx  # Gestão de pedidos
│   │   ├── KDSPage.tsx     # Kitchen Display System
│   │   └── FaturamentoPage.tsx # Pagamentos PIX/QR
│   └── services/
│       └── api.ts           # Cliente API Axios
├── components/              # Componentes reutilizáveis
│   ├── KanbanBoard.tsx     # Quadro Kanban pedidos
│   ├── DriverPayouts.tsx   # Pagamento entregadores
│   ├── NewOrderModal.tsx   # Modal criar pedido
│   ├── OrderCard.tsx       # Card de pedido
│   ├── Login.tsx           # Componente login
│   └── Timer.tsx          # Cronômetro
└── services/
    └── mockDb.ts           # Fallback localStorage
```

### Backend (c:/Users/Kaue_Martins/Desktop/saka-delivery-kds/backend/)

```
backend/
├── run.py                   # Script de inicialização
├── requirements.txt         # Dependências Python
├── app/
│   ├── __init__.py
│   ├── main.py             # Aplicação FastAPI principal
│   ├── config.py           # Configurações (variáveis ambiente)
│   ├── database.py         # Conexão SQLAlchemy
│   ├── models.py           # Modelos SQLAlchemy
│   ├── schemas.py          # Schemas Pydantic
│   ├── security.py         # Autenticação JWT
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py         # Login/Registro
│   │   ├── orders.py       # API pedidos KDS
│   │   ├── webhook.py     # Webhook iFood
│   │   ├── pacotes.py      # Pacotes pré-pagos
│   │   ├── pedidos_saas.py # Pedidos SaaS
│   │   ├── repasse.py      # Repasses entregadores
│   │   ├── webhook_pagamento.py # Webhook pagamento
│   │   └── faturamento.py  # QR Code PIX
│   └── services/
│       ├── order_service.py
│       ├── user_service.py
│       ├── pacote_service.py
│       ├── pedido_saas_service.py
│       ├── repasse_service.py
│       └── webhook_service.py
├── alembic/                # Migrações banco dados
└── tests/                  # Testes pytest
```

---

## Funcionalidades Implementadas

### 1. Sistema de Autenticação

O sistema possui autenticação JWT completa com as seguintes características:

- **Registro de usuários**: Endpoint `POST /auth/register` com campos de username, email, full_name, password e role
- **Login**: Endpoint `POST /auth/login` que retorna token JWT
- **Proteção de rotas**: Middleware que verifica token JWT em todas as rotas autenticadas
- **Roles**: ADMIN e KITCHEN para controle de acesso
- **Credenciais demo**: admin/admin123 e cozinha/123

### 2. Kitchen Display System (KDS)

O KDS é o coração do sistema, permitindo gestão visual de pedidos:

- **Quadro Kanban**: 4 colunas (RECEIVED, PREPARING, READY, DELIVERY)
- **Drag and drop**: Arraste pedidos entre colunas para atualizar status
- **Timer**: Tempo decorrido desde criação do pedido
- **Filtros**: Por status e origem (iFood, WhatsApp, etc)
- **Atualização automática**: Refresh a cada 15 segundos
- **Modo offline**: Funciona com localStorage se API indisponível

### 3. Gestão de Pedidos

- **Criação manual**: Modal para criar pedidos via interface
- **Simulação**: Geração automática de pedidos para testes
- **Status workflow**: RECEIVED → PREPARING → READY → DELIVERY
- **Timestamps**: Registro de quando cada status foi atingido
- **Itens do pedido**: Nome, quantidade e observações

### 4. Integração iFood (Webhook)

O sistema recebe webhooks do iFood para pedidos automáticos:

- **Endpoint**: `POST /webhook/ifood`
- **Eventos suportados**: ORDER_PLACED, ORDER_CONFIRMED, ORDER_CANCELLED
- **Processamento**: Decodifica payload e cria/atualiza pedidos
- **Simulador**: Script `simulate_webhook.py` para testes

### 5. Sistema de Pacotes Pré-Pagos (SaaS)

Modelo de negócio onde usuários compram créditos antecipados:

- **Pacotes disponíveis**: R$ 5.000 = 1.000 pedidos (R$ 5,00 por pedido)
- **Compra**: Endpoint `POST /pacotes/comprar`
- **Dedução**: Cada pedido subtrai do saldo automaticamente
- **Controle**: Verificação de saldo antes de criar pedido

### 6. Pagamentos via PIX/QR Code

Sistema de faturamento com geração de QR Code:

- **Geração QR**: `GET /faturamento/qrcode/{valor}`
- **Copia e Cola**: Código PIX formato válido
- **Valores**: Rápidos (R$ 50, 100, 200, 500, 1000) ou personalizado
- **Webhook**: Endpoint `/webhook/pagamento` para confirmação
- **Histórico**: Registro de todas as recargas

### 7. Gerenciamento de Repasses

Sistema para controlar pagamentos de entregadores:

- **Lista entregadores**: Motoristas com pedidos entregues
- **Taxa entrega**: Valor por corrida
- **Marcar pago**: Endpoint para confirmar pagamento
- **Relatório**: Visualização de pendentes e pagos

---

## Modelos de Dados Principais

### User (Usuário)
```python
- id: int (PK)
- username: str (unique)
- email: str (unique)
- full_name: str
- hashed_password: str
- role: str (ADMIN/KITCHEN)
- saldo_credito: Decimal
- is_active: bool
- created_at: datetime
```

### Order (Pedido KDS)
```python
- id: str (UUID)
- display_id: int
- customer_name: str
- source: str (IFOOD/WHATSAPP/UBER/FOOD99)
- status: str (RECEIVED/PREPARING/READY/DELIVERY/CANCELLED)
- items: relationship (OrderItem)
- delivery_fee: float
- driver_name: str (nullable)
- is_driver_paid: bool
- created_at: datetime
- preparing_at: datetime (nullable)
- ready_at: datetime (nullable)
- delivery_at: datetime (nullable)
```

### Pacote (Pacote Pré-Pago)
```python
- id: int (PK)
- user_id: int (FK)
- valor_pago: float
- qtd_pedidos: int
- data_compra: datetime
```

---

## Rotas de API Principais

### Autenticação
| Método | Endpoint | Descrição |
|--------|----------|------------|
| POST | /auth/register | Criar conta |
| POST | /auth/login | Login JWT |
| GET | /auth/me | Dados usuário |

### Pedidos KDS
| Método | Endpoint | Descrição |
|--------|----------|------------|
| GET | /orders | Lista pedidos |
| POST | /orders/create | Criar pedido |
| PATCH | /orders/{id}/status | Atualizar status |
| DELETE | /orders/{id} | Excluir pedido |
| DELETE | /orders | Limpar todos |
| POST | /orders/daily-reset | Reset diário |

### Pacotes
| Método | Endpoint | Descrição |
|--------|----------|------------|
| GET | /pacotes | Listar pacotes |
| POST | /pacotes/comprar | Comprar pacote |

### Faturamento
| Método | Endpoint | Descrição |
|--------|----------|------------|
| GET | /faturamento/qrcode/{valor} | Gerar QR PIX |
| POST | /faturamento/cobranca | Criar cobrança |
| GET | /faturamento/historico/{user_id} | Histórico |

### Webhooks
| Método | Endpoint | Descrição |
|--------|----------|------------|
| POST | /webhook/ifood | iFood |
| POST | /webhook/pagamento | Pagamento |

---

## Configurações de Ambiente

### Frontend (.env)
```
VITE_API_URL=http://localhost:8000
```

### Backend (.env)
```
DATABASE_URL=sqlite+aiosqlite:///./saka_delivery.db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
FRONTEND_URL=http://localhost:3000
```

---

## Tema Visual

O sistema utiliza um tema escuro profissional:

**Cores Principais:**
- Background: #020617 (slate-950)
- Superfície: #0f172a (slate-900)
- Borda: #1e293b (slate-800)
- Texto primary: #f8fafc (slate-100)
- Texto secondary: #94a3b8 (slate-400)
- Primary: #9333ea (purple-600)
- Success: #22c55e (emerald-500)
- Warning: #f59e0b (amber-500)
- Error: #ef4444 (red-500)

**Tipografia:**
- Fonte: Inter (Google Fonts)
- Pesos: 300, 400, 500, 600, 700, 800

---

## Executando o Projeto

### Pré-requisitos
- Node.js 18+
- Python 3.11+
- npm ou yarn

### Backend
```bash
cd backend
pip install -r requirements.txt
python run.py
# Servidor em http://localhost:8000
# Docs em http://localhost:8000/docs
```

### Frontend
```bash
npm install
npm run dev
# Servidor em http://localhost:3000
```

### Build Produção
```bash
npm run build
# Saída em dist/
```

---

## Como os Módulos se Comunicam

1. **Frontend → Backend**: Comunicação via HTTP REST usando axios com interceptors para adicionar token JWT automaticamente

2. **Backend → Banco**: ORM SQLAlchemy com operações async/await

3. **iFood → Backend**: Webhooks HTTP POST que processam eventos e criam/atualizam pedidos

4. **Pagamento → Backend**: Webhook que confirma pagamento e adiciona saldo ao usuário

5. **Fallback Offline**: Se API indisponível, frontend usa localStorage para funcionar offline

---

## Notas de Implementação

- O sistema usa TypeScript no frontend para segurança de tipos
- Backend async/await para melhor performance com múltiplas requisições
- Tokens JWT com expiração de 30 minutos
- CORS configurado para localhost:3000 e localhost:5173
- Tailwind CSS 4 usa configuração via CSS (@theme)
- QR Code目前 é demonstração - em produção integrar com API bancária
- Banco SQLite para desenvolvimento, facilmente trocável por PostgreSQL

---

## Próximos Passos Sugeridos

1. Integrar com API real de pagamento (MercadoPago/OpenPix)
2. Adicionar notificações push para novos pedidos
3. Implementar relatórios estatísticos avançados
4. Adicionar suporte a múltiplos estabelecimentos
5. Implementar app mobile para entregadores
6. Adicionar logs e monitoramento
7. Configurar CI/CD para deploy automático
