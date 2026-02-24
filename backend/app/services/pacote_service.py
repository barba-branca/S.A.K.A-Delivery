"""
Serviço para pacotes pré-pagos.
"""
import logging
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models import Pacote, User

logger = logging.getLogger(__name__)

# Definição dos pacotes disponíveis
PACOTES = {
    "padrao": {
        "valor_pago": Decimal("5000.00"),
        "qtd_pedidos": 1000,
    }
}


async def comprar_pacote(db: AsyncSession, user_id: int, tipo: str = "padrao") -> Pacote:
    """
    Simula compra de pacote e adiciona crédito ao saldo do usuário.
    """
    config = PACOTES.get(tipo)
    if not config:
        raise ValueError(f"Tipo de pacote inválido: {tipo}")
    
    # Busca usuário
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError("Usuário não encontrado")
    
    # Cria registro do pacote
    pacote = Pacote(
        user_id=user_id,
        valor_pago=config["valor_pago"],
        qtd_pedidos=config["qtd_pedidos"],
        data_compra=datetime.utcnow(),
    )
    db.add(pacote)
    
    # Adiciona crédito ao saldo
    user.saldo_credito = Decimal(str(user.saldo_credito or 0)) + config["valor_pago"]
    
    await db.commit()
    await db.refresh(pacote)
    await db.refresh(user)
    
    logger.info(f"Pacote comprado: user={user_id}, valor={config['valor_pago']}, novo_saldo={user.saldo_credito}")
    return pacote


async def listar_pacotes(db: AsyncSession, user_id: int) -> list:
    """Lista todos os pacotes do usuário."""
    result = await db.execute(
        select(Pacote)
        .where(Pacote.user_id == user_id)
        .order_by(Pacote.data_compra.desc())
    )
    return list(result.scalars().all())
