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
from .routers import webhook, orders, auth, pacotes, pedidos_saas, repasse, webhook_pagamento, faturamento

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


# ============== Middleware para logging de TODAS as requisições ==============
# Este middleware é executado PRIMEIRO - antes de qualquer outro middleware
# Imprime todas as requisições que chegam ao servidor

@app.middleware("http")
async def log_all_requests(request: Request, call_next):
    """
    Middleware de logging executado ANTES de qualquer outro middleware.
    Imprime TODAS as requisições que chegam ao servidor.
    """
    print(f'>>> CHEGOU: {request.method} {request.url.path}')
    response = await call_next(request)
    return response


# ============== Middleware para rotas públicas (webhooks) ==============
# Este middleware garante que rotas de webhook não precisam de autenticação JWT
# Adicione rotas públicas que não requerem autenticação aqui:
PUBLIC_ROUTES = [
    "/webhook/mercadopago",
    "/webhook/mercadopago/",  # Com barra final
    "/webhook",  # iFood webhook
    "/webhook/pagamento",  # OpenPix legacy
    "/auth/login",
    "/auth/register",
    "/health",
    "/",
    "/docs",
    "/redoc",
    "/openapi.json",
]


@app.middleware("http")
async def skip_auth_for_public_routes(request: Request, call_next):
    """
    Middleware que pula verificação de autenticação para rotas públicas.
    
    Especificamente para /webhook/mercadopago, este middleware garante
    que o Mercado Pago possa entrar sem necessidade de token JWT.
    """
    path = request.url.path
    
    # DEBUG: Ver exatamente como a URL está chegando
    print(f'DEBUG PATH: {path}')
    print(f'DEBUG FULL URL: {request.url}')
    print(f'DEBUG HEADERS: {dict(request.headers)}')
    
    # Normaliza o path: remove barras extras no final e converte para minúsculas
    normalized_path = path.rstrip("/").lower()
    
    # Log para debug
    logger.info(f"🔍 Request: {request.method} {path}")
    
    # ============================================================
    # VERIFICAÇÃO ESPECIAL PARA /webhook/mercadopago
    # ============================================================
    # Se for /webhook/mercadopago, IGNORA QUALQUER verificação de segurança
    if normalized_path == "webhook/mercadopago" or normalized_path.startswith("webhook/mercadopago/"):
        print(f'🚨 ROTA WHITELISTADA: /webhook/mercadopago - PULANDO TODA VERIFICAÇÃO')
        logger.info(f"✅ Rota pública whitelistada: {path} -> pulando autenticação")
        response = await call_next(request)
        return response
    
    # Verifica se a rota é pública (compara ignorando maiúsculas/minúsculas e barras)
    is_public = False
    
    for public_route in PUBLIC_ROUTES:
        normalized_public = public_route.rstrip("/").lower()
        if normalized_path == normalized_public or normalized_path.startswith(normalized_public + "/"):
            is_public = True
            logger.info(f"✅ Rota pública detectada: {path} -> pulando autenticação")
            print(f'✅ ROTA PÚBLICA: {public_route} corresponde a {path}')
            break
    
    # Se não for rota pública, continua para verificação normal (se houver)
    response = await call_next(request)
    return response


# CORS - Configuração para permitir chamadas externas incluindo webhooks
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        # Allow Mercado Pago webhook URLs
        "https://api.mercadopago.com",
        "https://webhook.mercadopago.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=[
        "*",
        # Headers específicos do Mercado Pago para webhook
        "x-signature-v1",
        "x-signature-ts",
        "x-request-id",
        "x-webhook-id",
        # Headers do iFood
        "x-ifood-signature",
        "X-iFood-Signature",
    ],
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
