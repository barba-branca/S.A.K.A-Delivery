"""
SAKA Delivery KDS - Backend Server
Servidor FastAPI para integração com iFood via Webhook.

Funcionalidades:
- Recebe webhooks do iFood com validação HMAC SHA256
- Persiste pedidos em banco de dados SQLite
- API REST para o frontend KDS consumir
- Resposta rápida (< 5 segundos) com processamento em background
"""
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .database import init_db
from .routers import webhook, orders, auth

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação."""
    # Startup
    logger.info("🚀 Iniciando SAKA Delivery KDS Backend...")
    init_db()
    logger.info("✅ Banco de dados inicializado")
    logger.info(f"📡 Servidor rodando em http://{settings.host}:{settings.port}")
    logger.info(f"🔗 Webhook endpoint: http://{settings.host}:{settings.port}/webhook")
    
    yield
    
    # Shutdown
    logger.info("👋 Encerrando servidor...")


# Cria a aplicação FastAPI
app = FastAPI(
    title="SAKA Delivery KDS API",
    description="""
    API Backend para o KDS (Kitchen Display System) do SAKA Delivery.
    
    ## Funcionalidades
    
    * **Webhook iFood** - Recebe e processa eventos do iFood
    * **API de Pedidos** - CRUD de pedidos para o frontend
    * **Validação de Segurança** - HMAC SHA256 para webhooks
    
    ## Webhooks
    
    O endpoint `/webhook` recebe eventos do iFood:
    - `PLC` - Pedido colocado
    - `CFM` - Pedido confirmado
    - `RTP` - Pronto para retirada
    - `DSP` - Despachado
    - `CAN` - Cancelado
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuração de CORS para o frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra os routers
app.include_router(webhook.router)
app.include_router(orders.router)
app.include_router(auth.router)


@app.get("/", tags=["Health"])
async def root():
    """Endpoint raiz com informações da API."""
    return {
        "name": "SAKA Delivery KDS API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "webhook": "/webhook"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check para monitoramento."""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
