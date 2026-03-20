"""
SAKA Delivery KDS - Backend Server
FastAPI com integração iFood, sistema SaaS de pacotes pré-pagos, e KDS.
"""
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .database import init_db
from .routers import webhook, orders, auth, pacotes, pedidos_saas, repasse, webhook_pagamento, faturamento, payments, ws

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


# ============================================================
# CORS — DEVE ser o PRIMEIRO middleware adicionado via add_middleware
# Em Starlette, add_middleware é LIFO: último adicionado = roda primeiro.
# Por isso, adicionamos CORS PRIMEIRO para que ele seja o mais externo.
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8000",
        "http://localhost:8001",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:8000",
        "http://0.0.0.0:3000",
        "http://0.0.0.0:5173",
        # Allow Mercado Pago webhook URLs
        "https://api.mercadopago.com",
        "https://webhook.mercadopago.com",
    ],
    allow_origin_regex=r"https?://(.*\.(repl\.co|replit\.dev|replit\.app)|localhost|127\.0\.0\.1|0\.0\.0\.0)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler — garante que erros 500 retornem CORS headers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Captura exceções não tratadas e retorna um JSON com CORS headers.
    Sem isso, uvicorn retorna 500 sem headers CORS, e o browser
    reporta 'CORS error' em vez de 'Internal Server Error'.
    """
    origin = request.headers.get("origin", "")
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    
    headers = {}
    if origin:
        headers["access-control-allow-origin"] = origin
        headers["access-control-allow-credentials"] = "true"
    
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"},
        headers=headers,
    )


# Registra todos os routers
app.include_router(auth.router)
app.include_router(orders.router)
app.include_router(webhook.router)
app.include_router(pacotes.router)
app.include_router(pedidos_saas.router)
app.include_router(repasse.router)
app.include_router(webhook_pagamento.router)
app.include_router(faturamento.router)
app.include_router(payments.router)
app.include_router(ws.router)


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
