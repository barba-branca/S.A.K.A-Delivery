"""
Router para webhook de pagamento do Mercado Pago.

Este módulo implementa a integração com webhooks do Mercado Pago para:
- Receber notificações de pagamentos
- Validar autenticidade das requisições via HMAC-SHA256
- Adicionar créditos ao saldo dos usuários
- Implementar idempotência para evitar processamento duplicado
- Registrar logs de auditoria completos
- Implementar retry automático com backoff exponencial

Suporta os eventos:
- payment.created: novo pagamento criado
- payment.updated: pagamento atualizado
- payment.approved: pagamento aprovado
- payment.rejected: pagamento rejeitado
- order.created: ordem criada
- order.updated: ordem atualizada
"""
import asyncio
import hashlib
import hmac
import json
import logging
import os
import time
from datetime import datetime
from decimal import Decimal
from typing import Optional
from functools import lru_cache

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..config import get_settings
from ..database import get_db
from ..models import User, WebhookMercadoPagoLog

# Configuração de logging com rotação de arquivos
def setup_logging() -> logging.Logger:
    """
    Configura o sistema de logging com rotação de arquivos.
    Cria um logger específico para webhooks com rotação diária.
    """
    logger = logging.getLogger(__name__)
    
    # Evita configuração duplicada
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Criar diretório de logs se não existir
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Configurar handler com rotação de arquivos
    log_file = os.path.join(log_dir, "webhook_mercadopago.log")
    
    # Handler para arquivo com rotação
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=30,  # Manter 30 dias de logs
        encoding='utf-8'
    )
    
    # Formato detalhado do log
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | '
        '%(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Também adicionar handler para console em modo debug
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# Importar logging.handlers para rotação
import logging.handlers

logger = setup_logging()
router = APIRouter(prefix="/webhook", tags=["Webhook Mercado Pago"])
settings = get_settings()

# Constantes
MAX_RETRIES = settings.webhook_max_retries
RETRY_DELAY = settings.webhook_retry_delay


# ============== Modelos Pydantic ==============

class MercadoPagoWebhookPayload(BaseModel):
    """Payload do webhook do Mercado Pago."""
    id: int
    live_mode: bool
    type: str
    date_created: str
    user_id: int
    api_version: str
    action: str
    data: dict
    
    class Config:
        extra = "allow"


class MercadoPagoPaymentResponse(BaseModel):
    """Resposta da API de pagamento do Mercado Pago."""
    id: int
    status: str
    status_detail: str
    payment_method_id: str
    transaction_amount: float
    currency_id: str
    external_reference: Optional[str] = None
    description: Optional[str] = None
    payer: Optional[dict] = None
    
    class Config:
        extra = "allow"


class WebhookPagamentoPayload(BaseModel):
    """Payload esperado do webhook de pagamento (OpenPix - Legado)."""
    txid: str
    valor: float
    user_id: int


# ============== Funções de Validação de Assinatura ==============

def compute_hmac_sha256(data: str, secret: str) -> str:
    """
    Calcula o HMAC-SHA256 dos dados.
    
    Args:
        data: String com os dados a serem assinados
        secret: Segredo usado para calcular a assinatura
        
    Returns:
        String hex com a assinatura HMAC-SHA256
    """
    return hmac.new(
        secret.encode('utf-8'),
        data.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


def verify_webhook_signature(request: Request, secret: str, raw_body: bytes, payload: dict = None) -> bool:
    """
    Verifica a assinatura do webhook do Mercado Pago usando HMAC-SHA256.
    
    O Mercado Pago envia os cabeçalhos:
    - x-signature-v1: assinatura HMAC-SHA256
    - x-signature-ts: timestamp da assinatura
    - x-request-id: ID da requisição
    
    A assinatura é calculada como:
    HMAC-SHA256(string_to_sign, webhook_secret)
    
    Onde string_to_sign deve ser exatamente:
    id:[ID_DO_RECURSO];request-id:[X-REQUEST-ID];ts:[TIMESTAMP];
    
    Args:
        request: Objeto da requisição FastAPI
        secret: Segredo do webhook (não usado, pegamos do .env diretamente)
        raw_body: Corpo raw da requisição para validação
        payload: Payload JSON parsado (opcional, para extrair data.id)
        
    Returns:
        True se a assinatura for válida, False caso contrário
    """
    print("\n" + "="*60)
    print("🔐 VERIFICAÇÃO DE ASSINATURA DO WEBHOOK MERCADO PAGO")
    print("="*60)
    
    # ========== 0. LOGS DETALHADOS - Headers e Body ==========
    print(f'DEBUG - Headers Recebidos: {dict(request.headers)}')
    
    try:
        body_json_debug = json.loads(raw_body.decode('utf-8')) if isinstance(raw_body, bytes) else json.loads(raw_body)
        print(f'DEBUG - Body Recebido: {body_json_debug}')
    except:
        print(f'DEBUG - Body Recebido: {raw_body}')
    
    # ========== 1. Ler o secret diretamente do .env com strip() ==========
    webhook_secret = os.getenv('MERCADOPAGO_WEBHOOK_SECRET')
    
    if not webhook_secret:
        print("❌ ERRO: MERCADOPAGO_WEBHOOK_SECRET não encontrado no .env")
        return False
    
    # Aplicar strip() para garantir que não haja espaços em branco
    webhook_secret = webhook_secret.strip()
    
    # Mostrar os primeiros 8 caracteres do secret para debug
    print(f"✅ DEBUG - Secret lida do .env: {webhook_secret[:8]}...")
    
    # ========== 2. Extrair headers necessários ==========
    # Usar x-signature-v1 para a assinatura e x-signature-ts para o timestamp
    v1_header = request.headers.get("x-signature-v1", "")
    ts_header = request.headers.get("x-signature-ts", "")
    request_id_header = request.headers.get("x-request-id", "")
    
    print(f"📥 DEBUG - x-signature-v1: {v1_header}")
    print(f"📥 DEBUG - x-signature-ts: {ts_header}")
    print(f"📥 DEBUG - x-request-id: {request_id_header}")
    
    if not v1_header:
        print("❌ ERRO: Cabeçalho x-signature-v1 ausente")
        return False
    
    if not ts_header:
        print("❌ ERRO: Cabeçalho x-signature-ts ausente")
        return False
    
    if not request_id_header:
        print("❌ ERRO: Cabeçalho x-request-id ausente")
        return False
    
    # ========== 3. Extrair data.id do payload ==========
    data_id = None
    
    if payload:
        data_id = payload.get("data", {}).get("id")
    
    if not data_id and raw_body:
        try:
            body_str = raw_body.decode('utf-8') if isinstance(raw_body, bytes) else raw_body
            body_json = json.loads(body_str)
            data_id = body_json.get("data", {}).get("id")
        except:
            pass
    
    if not data_id:
        print("❌ ERRO: data.id não encontrado no payload")
        return False
    
    # ========== 4. Montar a string para Hash (FORMATO EXATO DO MP) ==========
    # Formato: id:[data.id];request-id:[x-request-id];ts:[timestamp];
    string_to_sign = f"id:{data_id};request-id:{request_id_header};ts:{ts_header};"
    
    # ========== 5. Debug prints obrigatórios ==========
    print(f'DEBUG - ID do Recurso: {data_id}')
    print(f'DEBUG - String montada: {string_to_sign}')
    
    # ========== 6. Calcular HMAC-SHA256 ==========
    local_hash = hmac.new(
        webhook_secret.encode('utf-8'),
        string_to_sign.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    print(f'DEBUG - Assinatura Local: {local_hash} | MP: {v1_header}')
    
    # ========== 7. Comparar as assinaturas ==========
    is_valid = hmac.compare_digest(local_hash, v1_header)
    
    if is_valid:
        print("✅ SUCESSO: Assinatura válida!")
        print("="*60 + "\n")
        return True
    else:
        print('ASSINATURA INVÁLIDA')
        print("="*60 + "\n")
        return False


# ============== Funções de Retry com Backoff Exponencial ==============

async def validate_payment_mercadopago_with_retry(
    payment_id: int, 
    max_retries: int = MAX_RETRIES,
    retry_delay: int = RETRY_DELAY
) -> Optional[dict]:
    """
    Valida o pagamento chamando a API do Mercado Pago com retry automático.
    
    Implementa backoff exponencial para retries, aumentando o tempo de espera
    a cada tentativa fracassada.
    
    Args:
        payment_id: ID do pagamento a validar
        max_retries: Número máximo de tentativas (padrão: 3)
        retry_delay: Tempo de espera base entre tentativas em segundos (padrão: 5)
        
    Returns:
        Dados do pagamento se válido, None se falhar após todas as tentativas
    """
    url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
    params = {"access_token": settings.mercadopago_access_token}
    
    last_error = None
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(
                        f"Pagamento validado: id={payment_id}, "
                        f"status={data.get('status')}, "
                        f"transaction_amount={data.get('transaction_amount')}"
                    )
                    return data
                elif response.status_code == 404:
                    logger.warning(f"Pagamento não encontrado: id={payment_id}")
                    return None
                else:
                    logger.warning(
                        f"Erro API (tentativa {attempt + 1}/{max_retries}): "
                        f"status={response.status_code}, response={response.text[:200]}"
                    )
                    last_error = f"Status {response.status_code}: {response.text[:100]}"
                    
        except httpx.TimeoutException:
            logger.warning(
                f"Timeout na tentativa {attempt + 1}/{max_retries} - "
                f"payment_id={payment_id}"
            )
            last_error = "Timeout"
        except httpx.ConnectError as e:
            logger.warning(
                f"Erro de conexão na tentativa {attempt + 1}/{max_retries}: {e}"
            )
            last_error = f"Erro de conexão: {e}"
        except Exception as e:
            logger.error(
                f"Erro na chamada API Mercado Pago: {e} - payment_id={payment_id}"
            )
            last_error = str(e)
        
        # Espera antes de retry com backoff exponencial
        if attempt < max_retries - 1:
            wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
            logger.info(
                f"Aguardando {wait_time}s antes de tentar novamente "
                f"(attempt {attempt + 2}/{max_retries})..."
            )
            await asyncio.sleep(wait_time)
    
    logger.error(
        f"Falha após {max_retries} tentativas para payment_id={payment_id}: "
        f"{last_error}"
    )
    return None


# ============== Funções de Extração de Dados ==============

def extract_user_id_from_payment(payment_data: dict) -> Optional[int]:
    """
    Extrai o user_id do pagamento de várias fontes possíveis.
    
    O user_id pode ser enviado de diferentes formas no pagamento:
    1. external_reference: Campo preenchido na criação do pagamento
    2. description: No formato "user_id:123" ou apenas "123"
    3. payer.identification.number: Número do documento do pagador
    
    Args:
        payment_data: Dados completos do pagamento vindos da API
        
    Returns:
        user_id se encontrado, None caso contrário
    """
    # 1. Tenta via external_reference (recomendado)
    external_ref = payment_data.get("external_reference")
    if external_ref:
        try:
            # Tenta converter para int diretamente
            if str(external_ref).isdigit():
                return int(external_ref)
            # Tenta extrair de formato "user_id:123"
            if ":" in str(external_ref):
                parts = str(external_ref).split(":")
                if len(parts) == 2 and parts[0].lower() == "user_id":
                    return int(parts[1])
        except (ValueError, TypeError):
            pass
    
    # 2. Tenta via description (formato: "user_id:123" ou "123")
    description = payment_data.get("description")
    if description:
        description_str = str(description)
        if description_str.isdigit():
            return int(description_str)
        if ":" in description_str:
            parts = description_str.split(":")
            if len(parts) == 2 and parts[0].lower() == "user_id":
                try:
                    return int(parts[1])
                except ValueError:
                    pass
    
    # 3. Tenta via payer.identification.number
    payer = payment_data.get("payer", {})
    if payer:
        identification = payer.get("identification", {})
        if identification:
            doc_number = identification.get("number")
            if doc_number:
                try:
                    # Tenta converter diretamente
                    if str(doc_number).isdigit():
                        return int(doc_number)
                except (ValueError, TypeError):
                    pass
    
    return None


# ============== Funções de Processamento de Crédito ==============

async def add_credit_to_user(
    db: AsyncSession,
    user_id: int,
    amount: Decimal,
    payment_id: int,
    action: str
) -> tuple[Optional[User], Optional[str]]:
    """
    Adiciona crédito ao saldo do usuário de forma atômica.
    
    Args:
        db: Sessão do banco de dados
        user_id: ID do usuário que receberá o crédito
        amount: Valor a adicionar (Decimal)
        payment_id: ID do pagamento relacionado
        action: Ação do webhook que triggerou o crédito
        
    Returns:
        Tupla (User atualizado, mensagem_de_erro)
        - Se sucesso: (User, None)
        - Se erro: (None, mensagem_de_erro)
    """
    try:
        # Busca usuário com relacionamentos necessários
        result = await db.execute(
            select(User)
            .options(selectinload(User.pacotes))
            .options(selectinload(User.pedidos_saas))
            .where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None, f"Usuário {user_id} não encontrado"
        
        # Registra saldo anterior
        old_balance = Decimal(str(user.saldo_credito or 0))
        
        # Adiciona crédito ao saldo
        new_balance = old_balance + amount
        user.saldo_credito = new_balance
        
        # Commit atômico
        await db.commit()
        await db.refresh(user)
        
        logger.info(
            f"Crédito adicionado com sucesso: "
            f"user_id={user.id}, valor={amount}, payment_id={payment_id}, "
            f"action={action}, old_balance={old_balance}, new_balance={new_balance}"
        )
        
        return user, None
        
    except Exception as e:
        await db.rollback()
        logger.error(
            f"Erro ao adicionar crédito - user_id={user_id}, "
            f"payment_id={payment_id}: {e}"
        )
        return None, str(e)


# ============== Funções de Log e Auditoria ==============

async def check_idempotency(
    db: AsyncSession,
    webhook_id: str,
    payment_id: int
) -> tuple[bool, Optional[WebhookMercadoPagoLog]]:
    """
    Verifica se o webhook já foi processado anteriormente (idempotência).
    
    Args:
        db: Sessão do banco de dados
        webhook_id: ID único da notificação do Mercado Pago
        payment_id: ID do pagamento
        
    Returns:
        Tupla (já_processado, log_existente)
        - Se já processado: (True, log_existente)
        - Se não processado: (False, None)
    """
    if not webhook_id:
        return False, None
    
    # Busca por webhook_id ou payment_id com status de sucesso
    result = await db.execute(
        select(WebhookMercadoPagoLog).where(
            and_(
                WebhookMercadoPagoLog.webhook_id == webhook_id,
                WebhookMercadoPagoLog.status == "success"
            )
        )
    )
    existing_log = result.scalar_one_or_none()
    
    if existing_log:
        logger.info(
            f"Webhook duplicado detectado - webhook_id={webhook_id}, "
            f"payment_id={payment_id}, log_id={existing_log.id}"
        )
        return True, existing_log
    
    return False, None


async def log_webhook_event(
    db: AsyncSession,
    webhook_id: Optional[str],
    payment_id: Optional[int],
    user_id: Optional[int],
    action: str,
    status: str,
    request_payload: dict,
    payment_data: Optional[dict] = None,
    error_message: Optional[str] = None,
    retry_count: int = 0,
    credit_added: Optional[Decimal] = None,
    new_balance: Optional[Decimal] = None,
    transaction_amount: Optional[float] = None,
    payment_status: Optional[str] = None,
    idempotent_repeated: bool = False
) -> WebhookMercadoPagoLog:
    """
    Registra um evento de webhook no banco de dados para auditoria.
    
    Args:
        db: Sessão do banco de dados
        webhook_id: ID da notificação do Mercado Pago
        payment_id: ID do pagamento
        user_id: ID do usuário no sistema
        action: Ação do webhook (payment.created, etc.)
        status: Status do processamento (success, error, ignored, retry, duplicate)
        request_payload: Payload original recebido
        payment_data: Dados retornados da API do MP (opcional)
        error_message: Mensagem de erro (se houver)
        retry_count: Número de retries tentados
        credit_added: Valor do crédito adicionado
        new_balance: Novo saldo do usuário
        transaction_amount: Valor da transação
        payment_status: Status do pagamento
        idempotent_repeated: Se é uma repetição idempotente
        
    Returns:
        Objeto WebhookMercadoPagoLog criado
    """
    log_entry = WebhookMercadoPagoLog(
        webhook_id=webhook_id,
        payment_id=payment_id,
        user_id=user_id,
        action=action,
        status=status,
        request_payload=json.dumps(request_payload, ensure_ascii=False),
        payment_data=json.dumps(payment_data) if payment_data else None,
        error_message=error_message,
        retry_count=retry_count,
        credit_added=credit_added,
        new_balance=new_balance,
        transaction_amount=Decimal(str(transaction_amount)) if transaction_amount else None,
        payment_status=payment_status,
        processed_at=datetime.utcnow() if status in ["success", "error", "duplicate", "ignored"] else None
    )
    
    db.add(log_entry)
    await db.commit()
    await db.refresh(log_entry)
    
    logger.info(
        f"Log de webhook criado - id={log_entry.id}, "
        f"webhook_id={webhook_id}, status={status}"
    )
    
    return log_entry


# ============== Endpoints do Router ==============

@router.post("/mercadopago", summary="Webhook do Mercado Pago", status_code=status.HTTP_200_OK)
async def webhook_mercadopago(
    request: Request,
    x_signature: Optional[str] = Header(None),
    x_request_id: Optional[str] = Header(None),
    x_webhook_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Recebe notificação de pagamento do Mercado Pago e adiciona crédito ao usuário.
    
    Este endpoint processa notificações síncronas e assíncronas do Mercado Pago,
    incluindo:
    - Pagamentos via Checkout Transparente
    - Ordens de pagamento
    - Atualizações de status
    
    O Mercado Pago envía notificações para:
    - payments: quando um pagamento é criado/atualizado
    - orders: quando uma ordem é criada/atualizada
    
    Para garantir idempotência, o sistema verifica se:
    1. O webhook_id já foi processado anteriormente
    2. O payment_id já foi creditado com sucesso
    
    Args:
        request: Objeto da requisição FastAPI
        x_signature: Cabeçalho com assinatura HMAC-SHA256
        x_request_id: ID da requisição (traceability)
        x_webhook_id: ID único da notificação do Mercado Pago
        
    Returns:
        HTTP 200: Notificação processada com sucesso
        HTTP 400: Payload inválido ou dados inconsistentes
        HTTP 401: Assinatura de webhook inválida
        HTTP 500: Erro interno do servidor
    """
    # ========== LOG DE ENTRADA IMEDIATA ==========
    print('\n\n>>> ALGO CHEGOU NO WEBHOOK! <<<')
    print(f"Headers recebidos: {dict(request.headers)}")
    
    request_id = x_request_id or "unknown"
    webhook_id = x_webhook_id or f"local_{int(time.time())}"
    
    logger.info(
        f"Iniciando processamento de webhook - "
        f"webhook_id={webhook_id}, request_id={request_id}"
    )
    
    # ========== 1. Ler e validar payload ==========
    try:
        # Lê o corpo raw para validação de assinatura
        raw_body = await request.body()
        payload = json.loads(raw_body.decode('utf-8'))
        
        logger.info(
            f"Payload recebido - webhook_id={webhook_id}, "
            f"type={payload.get('type')}, action={payload.get('action')}"
        )
        
    except json.JSONDecodeError as e:
        logger.error(f"Payload JSON inválido: {e} - request_id={request_id}")
        await log_webhook_event(
            db=db,
            webhook_id=webhook_id,
            payment_id=None,
            user_id=None,
            action="parse_payload",
            status="error",
            request_payload={"error": str(e)},
            error_message="Payload JSON inválido"
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": "error", "message": "Payload inválido"}
        )
    except Exception as e:
        logger.error(f"Erro ao ler payload: {e} - request_id={request_id}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": "error", "message": "Erro ao processar payload"}
        )
    
    # ========== 2. Validar assinatura do webhook ==========
    if not verify_webhook_signature(
        request, 
        settings.mercadopago_webhook_secret,
        raw_body,
        payload  # Passa o payload para extrair data.id
    ):
        logger.warning(
            f"Assinatura de webhook inválida - "
            f"request_id={request_id}, webhook_id={webhook_id}"
        )
        await log_webhook_event(
            db=db,
            webhook_id=webhook_id,
            payment_id=None,
            user_id=None,
            action=payload.get("action", "unknown"),
            status="error",
            request_payload=payload,
            error_message="Assinatura de webhook inválida"
        )
        print('ASSINATURA INVÁLIDA')
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"status": "error", "message": "Assinatura inválida"}
        )
    
    print("✅ ASSINATURA VÁLIDA - Processando webhook...")
    
    # ========== 3. Verificar idempotência ==========
    payment_id_from_data = payload.get("data", {}).get("id")
    
    if webhook_id:
        is_duplicate, existing_log = await check_idempotency(
            db=db,
            webhook_id=webhook_id,
            payment_id=payment_id_from_data
        )
        
        if is_duplicate and existing_log:
            logger.info(
                f"Webhook duplicado - retornando sucesso sem processar - "
                f"webhook_id={webhook_id}, "
                f"existing_log_id={existing_log.id}"
            )
            
            # Registra que foi uma repetição
            await log_webhook_event(
                db=db,
                webhook_id=webhook_id,
                payment_id=payment_id_from_data,
                user_id=existing_log.user_id,
                action=payload.get("action", "unknown"),
                status="duplicate",
                request_payload=payload,
                credit_added=existing_log.credit_added,
                new_balance=existing_log.new_balance,
                idempotent_repeated=True
            )
            
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "success",
                    "message": "Webhook já processado anteriormente",
                    "webhook_id": webhook_id,
                    "payment_id": payment_id_from_data,
                    "credit_added": float(existing_log.credit_added) if existing_log.credit_added else None,
                    "idempotent_repeated": True
                }
            )
    
    # ========== 4. Verificar tipo de notificação ==========
    notification_type = payload.get("type")
    action = payload.get("action")
    
    # Processa notificações de payment e order
    if notification_type not in ["payment", "order"]:
        logger.info(
            f"Ignorando notificação tipo não suportado - "
            f"webhook_id={webhook_id}, type={notification_type}"
        )
        await log_webhook_event(
            db=db,
            webhook_id=webhook_id,
            payment_id=None,
            user_id=None,
            action=action,
            status="ignored",
            request_payload=payload,
            error_message=f"Tipo {notification_type} não processado"
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "ignored", 
                "message": f"Tipo {notification_type} não processado"
            }
        )
    
    # ========== 5. Obter ID do pagamento ==========
    payment_id = payment_id_from_data
    
    if not payment_id:
        logger.error(
            f"Payment ID não encontrado no payload - "
            f"webhook_id={webhook_id}"
        )
        await log_webhook_event(
            db=db,
            webhook_id=webhook_id,
            payment_id=None,
            user_id=None,
            action=action,
            status="error",
            request_payload=payload,
            error_message="Payment ID não encontrado"
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": "error", "message": "Payment ID não encontrado"}
        )
    
    logger.info(
        f"Processando webhook - "
        f"webhook_id={webhook_id}, type={notification_type}, "
        f"action={action}, payment_id={payment_id}"
    )
    
    # ========== 6. Validar pagamento na API do Mercado Pago ==========
    payment_data = await validate_payment_mercadopago_with_retry(payment_id)
    
    if not payment_data:
        await log_webhook_event(
            db=db,
            webhook_id=webhook_id,
            payment_id=payment_id,
            user_id=None,
            action=action,
            status="error",
            request_payload=payload,
            error_message="Pagamento não encontrado ou inválido na API"
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": "error", "message": "Pagamento não encontrado ou inválido"}
        )
    
    # ========== 7. Verificar status do pagamento ==========
    payment_status = payment_data.get("status")
    
    # Processa apenas pagamentos aprovados
    if payment_status != "approved":
        logger.info(
            f"Pagamento não aprovado - "
            f"webhook_id={webhook_id}, payment_id={payment_id}, "
            f"status={payment_status}"
        )
        
        await log_webhook_event(
            db=db,
            webhook_id=webhook_id,
            payment_id=payment_id,
            user_id=None,
            action=action,
            status="ignored",
            request_payload=payload,
            payment_data=payment_data,
            transaction_amount=payment_data.get("transaction_amount"),
            payment_status=payment_status,
            error_message=f"Pagamento status: {payment_status}"
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "ignored", 
                "message": f"Pagamento status: {payment_status}"
            }
        )
    
    # ========== 8. Extrair valor e user_id ==========
    transaction_amount = payment_data.get("transaction_amount", 0)
    
    if transaction_amount <= 0:
        logger.error(
            f"Valor inválido do pagamento - "
            f"webhook_id={webhook_id}, payment_id={payment_id}, "
            f"amount={transaction_amount}"
        )
        await log_webhook_event(
            db=db,
            webhook_id=webhook_id,
            payment_id=payment_id,
            user_id=None,
            action=action,
            status="error",
            request_payload=payload,
            payment_data=payment_data,
            error_message="Valor inválido"
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": "error", "message": "Valor inválido"}
        )
    
    # Extrai o user_id do pagamento
    user_id = extract_user_id_from_payment(payment_data)
    
    if not user_id:
        # Tenta pegar do payload original como fallback
        user_id = payload.get("user_id")
        if not user_id:
            logger.error(
                f"user_id não encontrado - "
                f"webhook_id={webhook_id}, payment_id={payment_id}"
            )
            await log_webhook_event(
                db=db,
                webhook_id=webhook_id,
                payment_id=payment_id,
                user_id=None,
                action=action,
                status="error",
                request_payload=payload,
                payment_data=payment_data,
                error_message="user_id não encontrado no pagamento"
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"status": "error", "message": "user_id não encontrado no pagamento"}
            )
    
    # ========== 9. Adicionar crédito ao usuário ==========
    user, error = await add_credit_to_user(
        db=db,
        user_id=user_id,
        amount=Decimal(str(transaction_amount)),
        payment_id=payment_id,
        action=action
    )
    
    if error:
        logger.error(
            f"Erro ao adicionar crédito - "
            f"webhook_id={webhook_id}, payment_id={payment_id}, "
            f"user_id={user_id}: {error}"
        )
        await log_webhook_event(
            db=db,
            webhook_id=webhook_id,
            payment_id=payment_id,
            user_id=user_id,
            action=action,
            status="error",
            request_payload=payload,
            payment_data=payment_data,
            error_message=error
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": f"Erro ao adicionar crédito: {error}"}
        )
    
    # ========== 10. Registrar sucesso ==========
    await log_webhook_event(
        db=db,
        webhook_id=webhook_id,
        payment_id=payment_id,
        user_id=user.id,
        action=action,
        status="success",
        request_payload=payload,
        payment_data=payment_data,
        credit_added=Decimal(str(transaction_amount)),
        new_balance=user.saldo_credito,
        transaction_amount=transaction_amount,
        payment_status=payment_status
    )
    
    logger.info(
        f"Webhook processado com sucesso - "
        f"webhook_id={webhook_id}, payment_id={payment_id}, "
        f"user_id={user.id}, valor={transaction_amount}, "
        f"novo_saldo={user.saldo_credito}"
    )
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "success",
            "message": "Crédito adicionado com sucesso",
            "webhook_id": webhook_id,
            "payment_id": payment_id,
            "user_id": user.id,
            "valor": float(transaction_amount),
            "novo_saldo": float(user.saldo_credito),
        }
    )


# ============== Endpoint Legado (OpenPix) ==============

@router.post("/pagamento", summary="Webhook de pagamento (OpenPix - Legado)")
async def webhook_pagamento(
    payload: WebhookPagamentoPayload,
    db: AsyncSession = Depends(get_db),
):
    """
    Recebe notificação de pagamento e adiciona crédito ao usuário.
    STUB: Preparado para integração futura com OpenPix.
    
    Payload esperado:
    - txid: ID da transação
    - valor: Valor pago
    - user_id: ID do usuário
    """
    logger.info(f"Webhook pagamento recebido: txid={payload.txid}, valor={payload.valor}")
    
    result = await db.execute(select(User).where(User.id == payload.user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        return {"status": "error", "message": "Usuário não encontrado"}
    
    # Adiciona crédito ao saldo
    user.saldo_credito = Decimal(str(user.saldo_credito or 0)) + Decimal(str(payload.valor))
    await db.commit()
    
    logger.info(f"Crédito adicionado via webhook: user={user.id}, valor={payload.valor}")
    
    return {
        "status": "success",
        "message": "Crédito adicionado com sucesso",
        "txid": payload.txid,
        "novo_saldo": float(user.saldo_credito),
    }


# ============== Endpoints de Monitoramento ==============

@router.get("/logs", summary="Listar logs de webhook")
async def list_webhook_logs(
    limit: int = 50,
    offset: int = 0,
    status_filter: Optional[str] = None,
    user_id: Optional[int] = None,
    payment_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Lista logs de webhooks do Mercado Pago para fins de auditoria.
    
    Args:
        limit: Número máximo de registros a retornar (padrão: 50)
        offset: Offset para paginação (padrão: 0)
        status_filter: Filtrar por status (success, error, ignored, duplicate)
        user_id: Filtrar por ID do usuário
        payment_id: Filtrar por ID do pagamento
        
    Returns:
        Lista de logs com metadados de paginação
    """
    query = select(WebhookMercadoPagoLog).order_by(WebhookMercadoPagoLog.created_at.desc())
    
    if status_filter:
        query = query.where(WebhookMercadoPagoLog.status == status_filter)
    
    if user_id:
        query = query.where(WebhookMercadoPagoLog.user_id == user_id)
    
    if payment_id:
        query = query.where(WebhookMercadoPagoLog.payment_id == payment_id)
    
    # Obter total antes de aplicar limit/offset
    count_query = select(WebhookMercadoPagoLog)
    if status_filter:
        count_query = count_query.where(WebhookMercadoPagoLog.status == status_filter)
    if user_id:
        count_query = count_query.where(WebhookMercadoPagoLog.user_id == user_id)
    if payment_id:
        count_query = count_query.where(WebhookMercadoPagoLog.payment_id == payment_id)
    
    total_result = await db.execute(count_query)
    total = len(total_result.scalars().all())
    
    # Aplicar paginação
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return {
        "logs": [
            {
                "id": log.id,
                "webhook_id": log.webhook_id,
                "payment_id": log.payment_id,
                "user_id": log.user_id,
                "action": log.action,
                "status": log.status,
                "transaction_amount": float(log.transaction_amount) if log.transaction_amount else None,
                "payment_status": log.payment_status,
                "credit_added": float(log.credit_added) if log.credit_added else None,
                "new_balance": float(log.new_balance) if log.new_balance else None,
                "error_message": log.error_message,
                "retry_count": log.retry_count,
                "created_at": log.created_at.isoformat() if log.created_at else None,
                "processed_at": log.processed_at.isoformat() if log.processed_at else None,
            }
            for log in logs
        ],
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/health", summary="Verificar saúde do webhook")
async def webhook_health():
    """
    Endpoint para verificar se o webhook está configurado corretamente.
    
    Retorna o status de saúde do módulo de webhook, incluindo:
    - Status geral do serviço
    - Se as credenciais do Mercado Pago estão configuradas
    - Se o segredo do webhook está configurado
    """
    return {
        "status": "healthy",
        "service": "webhook_mercadopago",
        "mercadopago_configured": bool(settings.mercadopago_access_token),
        "webhook_secret_configured": bool(settings.mercadopago_webhook_secret),
        "retry_config": {
            "max_retries": MAX_RETRIES,
            "retry_delay": RETRY_DELAY
        }
    }


@router.get("/logs/{log_id}", summary="Detalhar log de webhook específico")
async def get_webhook_log_detail(
    log_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna os detalhes completos de um log de webhook específico,
    incluindo o payload original e os dados do pagamento.
    
    Args:
        log_id: ID do log a ser recuperado
        
    Returns:
        Dados completos do log em formato JSON
    """
    result = await db.execute(
        select(WebhookMercadoPagoLog).where(WebhookMercadoPagoLog.id == log_id)
    )
    log = result.scalar_one_or_none()
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log não encontrado"
        )
    
    return {
        "id": log.id,
        "webhook_id": log.webhook_id,
        "payment_id": log.payment_id,
        "user_id": log.user_id,
        "action": log.action,
        "status": log.status,
        "transaction_amount": float(log.transaction_amount) if log.transaction_amount else None,
        "payment_status": log.payment_status,
        "credit_added": float(log.credit_added) if log.credit_added else None,
        "new_balance": float(log.new_balance) if log.new_balance else None,
        "error_message": log.error_message,
        "retry_count": log.retry_count,
        "request_payload": json.loads(log.request_payload) if log.request_payload else None,
        "payment_data": json.loads(log.payment_data) if log.payment_data else None,
        "created_at": log.created_at.isoformat() if log.created_at else None,
        "processed_at": log.processed_at.isoformat() if log.processed_at else None,
    }
