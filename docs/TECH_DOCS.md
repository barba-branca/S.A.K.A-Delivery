# S.A.K.A Delivery KDS - Documentação Técnica (TECH_DOCS)

Este documento descreve a arquitetura refinada, as tecnologias envolvidas e o design das decisões (Design Patterns) adotados no repositório.

## Índice
1. [Visão Geral Arquitetural](#1-visão-geral-arquitetural)
2. [Padrões de Projeto (Design Patterns)](#2-padrões-de-projeto)
3. [Comunicação em Tempo Real (WebSockets)](#3-comunicação-em-tempo-real-websockets)
4. [Estrutura de Pastas](#4-estrutura-de-pastas)
5. [Instalação e Build](#5-instalação-e-build)

---

## 1. Visão Geral Arquitetural

O projeto foi segmentado em duas fortes camadas **desacopladas**:
1. **Frontend (SPA)**: Um aplicativo React 18 usando TypeScript, Vite e Tailwind CSS. Todo o gerenciamento de estado é isolado em `Custom Hooks` (`src/hooks`). A interface gráfica atua puramente como *Presenter*.
2. **Backend (API)**: Uma API em **FastAPI** assíncrona orientada aos princípios **SOLID** e *Clean Architecture*. Conecta-se a um banco de dados PostgreSQL via SQLAlchemy (asyncpg).

---

## 2. Padrões de Projeto (Design Patterns)

Para garantir que o software seja escalável (Multi-Tenant) e testável:

### No Backend (SOLID)
- **Repository Pattern**: O acesso ao banco (SQLAlchemy) não existe nos Controladores e nem nos Serviços de negócio. Todas as mutações e queries ocorrem isoladas na camada `app/repositories/`. 
- **Dependency Inversion (DI)**: Os serviços (`OrderService`, `UserService`) recebem as instâncias dos repositórios via injeção. Isso permite plugar *mocker repositories* nos testes sem acessar um DB real (cumprindo a letra D do S.O.L.I.D).
- **Observer Pattern**: Utilizado via o módulo `ws_manager.py` para injetar comportamentos assíncronos que reagem a mudanças de eventos (mudança de status de um pedido).

### No Frontend (React)
- **Container / Presenter**: Componentes que compõe a marcação HTML são "burros". Toda lógica de *data fetch* provém primariamente de instâncias encapsuladas (`hooks`).
- **Adapter / Facade**: `src/services/api.ts` age como uma *Facade* que encapsula as minúcias do `axios` (tratamento de token via interceptors e tratamento de expiração 401).

---

## 3. Comunicação em Tempo Real (WebSockets)

Para eliminar o longo ciclo de *Polling* (que sobrecarregava o Backend chamando as APIs a cada 15 segundos), implementou-se comunicação em Tempo Real.
1. O Front abre uma conexão `ws://.../ws/kds/{tenant_id}` ao montar no `useOrders.ts`. 
2. O Backend `WebSocketManager` estoca a conexão numa lista segmentada por `tenant_id`.
3. Quando a API REST recebe a mutação (ex: "Driver Pagou o pedido", "Novo pedido do iFood criado"), o repositório atualiza o DB e o *Manager* dispara um JSON `{"action": "ORDER_UPDATED"}` apenas aos clientes daquele restaurante em específico.
4. O *Hook React* reage validando novamente os `orders` garantindo re-render instantâneo na UI.

---

## 4. Estrutura de Pastas

```text
saka-delivery-kds/
├── docs/                     # Central de conhecimento técnico
├── backend/
│   ├── alembic/              # Migrações incrementais do SQLAlchemy
│   ├── app/
│   │   ├── core/             # WS Manager, Configs e Utilities Base
│   │   ├── models/           # DB Schema Models
│   │   ├── repositories/     # (Novo) Camada de abstração DB / CRUDs Isolados
│   │   ├── routers/          # Controladores (FastAPI endpoints)
│   │   ├── schemas/          # Validação e I/O (Pydantic / DTOs)
│   │   └── services/         # (Novo) Regras de Negócio Injetadas (Use Cases)
│   ├── main.py               # Fio de inicialização
│   └── docker-compose.yml    # Infra local (DB Postgres)
├── src/
│   ├── components/           # Componentes puramente visuais (Kanban, etc)
│   ├── contexts/             # Global Contexts (Auth)
│   ├── hooks/                # (Novo) Camada de Controller do React (useOrders, useAuth)
│   ├── pages/                # Renderização das rotas
│   └── services/             # Adaptadores p/ API Externa e MockDB
```

---

## 5. Instalação e Build

### Infraestrutura
O backend requer o PostgreSQL em operação.
```bash
docker-compose up -d db
```

### Backend (Python/FastAPI)
```bash
cd backend
python -m venv venv
venv\Scripts\activate   # ou `source venv/bin/activate` no unix
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend (Node/React)
```bash
npm install
npm run dev
```

> A aplicação estará respondendo em `http://localhost:5173`.
