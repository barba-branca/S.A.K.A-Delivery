"""
SAKA Delivery KDS - Backend Server
FastAPI com integração iFood, sistema SaaS de pacotes pré-pagos, e KDS.
"""
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .database import init_db
from .routers import webhook, orders, auth, pacotes, pedidos_saas, repasse, webhook_pagamento

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação."""
    logger.info("🚀 Iniciando SAKA Delivery KDS Backend...")
    await init_db()
    logger.info("✅ Banco de dados inicializado")
    logger.info(f"📡 Servidor rodando em http://{settings.host}:{settings.port}")
    logger.info(f"📚 Docs: http://{settings.host}:{settings.port}/docs")
    
    yield
    
    logger.info("👋 Encerrando servidor...")


app = FastAPI(
    title="SAKA Delivery KDS API",
    description="""
    API Backend para o KDS (Kitchen Display System) e SaaS de gestão de delivery.
    
    ## Funcionalidades
    
    * **Webhook iFood** - Recebe e processa eventos do iFood
    * **API de Pedidos KDS** - CRUD de pedidos para o frontend
    * **Autenticação JWT** - Register/Login com tokens
    * **Pacotes Pré-pagos** - Compra de créditos para pedidos
    * **Pedidos SaaS** - Criação com dedução de crédito
    * **Repasse Financeiro** - Relatório mensal de repasses
    """,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra todos os routers
app.include_router(auth.router)
app.include_router(orders.router)
app.include_router(webhook.router)
app.include_router(pacotes.router)
app.include_router(pedidos_saas.router)
app.include_router(repasse.router)
app.include_router(webhook_pagamento.router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "name": "SAKA Delivery KDS API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "features": ["KDS", "SaaS Pacotes", "JWT Auth", "Repasse"],
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0.0",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=settings.debug)
