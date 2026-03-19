import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..core.ws_manager import manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSockets"])

@router.websocket("/ws/kds/{tenant_id}")
async def websocket_kds_endpoint(websocket: WebSocket, tenant_id: int):
    """
    Endpoint em tempo real consumido pelo Frontend.
    Ao alterar um pedido, o backend disparará eventos por aqui.
    """
    await manager.connect(websocket, tenant_id)
    try:
        while True:
            # Loop infinito para manter conexão HTTP evoluída para WS.
            # Também útil se criamos corações lógicos ping/pong.
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, tenant_id)
    except Exception as e:
        logger.error(f"Erro inesperado no WebSocket: {e}")
        manager.disconnect(websocket, tenant_id)
