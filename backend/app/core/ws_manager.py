import logging
from typing import Dict, List, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    Gerenciador de WebSockets (Observer Pattern).
    Mantém listas de conexões separadas por tenant_id, 
    garantindo que um restaurante não veja atualizações do outro.
    """
    def __init__(self):
        # Mapeia tenant_id -> lista de WebSockets ativos
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, tenant_id: int):
        await websocket.accept()
        if tenant_id not in self.active_connections:
            self.active_connections[tenant_id] = []
        self.active_connections[tenant_id].append(websocket)
        logger.info(f"Tenant {tenant_id}: Cliente conectado no KDS. (Total: {len(self.active_connections[tenant_id])})")

    def disconnect(self, websocket: WebSocket, tenant_id: int):
        if tenant_id in self.active_connections and websocket in self.active_connections[tenant_id]:
            self.active_connections[tenant_id].remove(websocket)
            if len(self.active_connections[tenant_id]) == 0:
                del self.active_connections[tenant_id]
            logger.info(f"Tenant {tenant_id}: Cliente desconectado.")

    async def broadcast_to_tenant(self, tenant_id: int, message: dict):
        """Notifica todos os KDS atrelados ao estabelecimento (tenant_id)."""
        if tenant_id in self.active_connections:
            connections_to_remove = []
            for connection in self.active_connections[tenant_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"Erro (WS) ao enviar mensagem, removendo socket: {e}")
                    connections_to_remove.append(connection)
            
            for conn in connections_to_remove:
                self.disconnect(conn, tenant_id)

# Instância Singleton visível para toda a aplicação (Services injetarão ou importarão esta instância)
manager = ConnectionManager()
