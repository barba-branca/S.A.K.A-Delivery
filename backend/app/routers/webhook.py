"""
Router para webhook do iFood.
Implementa recebimento e validação de eventos.
"""
import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, Header, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import validate_ifood_signature
from ..services.webhook_service import save_webhook_event, process_webhook_event, mark_event_as_processed
from ..config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["Webhook"])

settings = get_settings()


@router.post(
    "",
    status_code=202,
    summary="Recebe eventos do webhook iFood",
    description="""
    Endpoint para receber eventos do iFood.
    
    O iFood envia eventos de pedido (PLC, CFM, RTP, DSP, CAN, etc) via POST.
    Este endpoint:
    1. Valida a assinatura HMAC SHA256 no header X-iFood-Signature
    2. Salva o evento no banco de dados
    3. Responde com 202 Accepted imediatamente
    4. Processa o evento em background
    
    **Importante**: Resposta em menos de 5 segundos conforme requisito do iFood.
    """
)
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    x_ifood_signature: str = Header(None, alias="X-iFood-Signature")
):
    """
    Recebe e processa webhooks do iFood.
    
    Args:
        request: Objeto da requisição
        background_tasks: Tarefas em background do FastAPI
        db: Sessão do banco de dados
        x_ifood_signature: Assinatura HMAC do iFood
    
    Returns:
        202 Accepted em caso de sucesso
    """
    # Lê o body da requisição
    body = await request.body()
    
    # Valida a assinatura (bypass em modo debug se não houver secret configurado)
    if settings.ifood_client_secret:
        if not validate_ifood_signature(body, x_ifood_signature):
            logger.warning("Webhook rejeitado: assinatura inválida")
            raise HTTPException(
                status_code=401,
                detail="Assinatura inválida"
            )
    else:
        logger.warning("IFOOD_CLIENT_SECRET não configurado - validação de assinatura desabilitada")
    
    # Parse do JSON
    try:
        event_data: Dict[str, Any] = await request.json()
    except Exception as e:
        logger.error(f"Erro ao fazer parse do JSON: {e}")
        raise HTTPException(
            status_code=400,
            detail="Corpo da requisição inválido"
        )
    
    # Salva o evento imediatamente
    event = save_webhook_event(db, event_data)
    
    # Agenda processamento em background para responder rapidamente
    background_tasks.add_task(
        process_event_background,
        event.event_id,
        event_data
    )
    
    # Responde com 202 Accepted imediatamente
    return JSONResponse(
        status_code=202,
        content={"message": "Evento recebido", "eventId": event.event_id}
    )


async def process_event_background(event_id: str, event_data: Dict[str, Any]):
    """
    Processa evento em background.
    
    Executado após a resposta ser enviada para garantir
    tempo de resposta < 5 segundos.
    """
    from ..database import SessionLocal
    
    db = SessionLocal()
    try:
        success = process_webhook_event(db, event_data)
        mark_event_as_processed(db, event_id, success)
        
        if success:
            logger.info(f"Evento {event_id} processado com sucesso em background")
        else:
            logger.warning(f"Evento {event_id} processado com falhas")
            
    except Exception as e:
        logger.error(f"Erro ao processar evento {event_id}: {e}")
        mark_event_as_processed(db, event_id, False, str(e))
    finally:
        db.close()


@router.get(
    "/status",
    summary="Verifica status do webhook",
    description="Endpoint para verificar se o webhook está funcionando"
)
async def webhook_status():
    """Retorna status do endpoint de webhook."""
    return {
        "status": "active",
        "message": "Webhook endpoint is ready to receive iFood events"
    }
