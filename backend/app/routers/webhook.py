"""
Router para webhook do iFood (async).
"""
import logging
from typing import Any, Dict
from fastapi import APIRouter, Header, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse

from ..security import validate_ifood_signature
from ..config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["Webhook iFood"])

settings = get_settings()


@router.post("", status_code=202, summary="Recebe eventos do webhook iFood")
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_ifood_signature: str = Header(None, alias="X-iFood-Signature"),
):
    """Recebe e processa webhooks do iFood."""
    body = await request.body()
    
    if settings.ifood_client_secret:
        if not validate_ifood_signature(body, x_ifood_signature):
            logger.warning("Webhook rejeitado: assinatura inválida")
            raise HTTPException(status_code=401, detail="Assinatura inválida")
    else:
        logger.warning("IFOOD_CLIENT_SECRET não configurado - validação desabilitada")
    
    try:
        event_data: Dict[str, Any] = await request.json()
    except Exception as e:
        logger.error(f"Erro ao fazer parse do JSON: {e}")
        raise HTTPException(status_code=400, detail="Corpo da requisição inválido")
    
    # Save and process in background
    background_tasks.add_task(process_event_background, event_data)
    
    return JSONResponse(
        status_code=202,
        content={"message": "Evento recebido", "eventId": event_data.get("id", "")},
    )


async def process_event_background(event_data: Dict[str, Any]):
    """Processa evento em background usando sessão async."""
    from ..database import AsyncSessionLocal
    from ..services.webhook_service import save_webhook_event, process_webhook_event, mark_event_as_processed
    
    async with AsyncSessionLocal() as db:
        try:
            event = await save_webhook_event(db, event_data)
            success = await process_webhook_event(db, event_data)
            await mark_event_as_processed(db, event.event_id, success)
            
            if success:
                logger.info(f"Evento {event.event_id} processado com sucesso em background")
            else:
                logger.warning(f"Evento {event.event_id} processado com falhas")
        except Exception as e:
            logger.error(f"Erro ao processar evento: {e}")


@router.get("/status", summary="Verifica status do webhook")
async def webhook_status():
    return {"status": "active", "message": "Webhook endpoint is ready to receive iFood events"}
