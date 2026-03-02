"""
Router para geração de QR Code PIX e gerenciamento de faturamento.
"""
import logging
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User
from ..schemas import (
    FaturamentoCriarRequest,
    FaturamentoCobrancaResponse,
)
from ..config import get_settings
from ..security import get_current_user
import mercadopago

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/faturamento", tags=["Faturamento"])

settings = get_settings()

def gerar_codigo_pix_mp(valor: float, email: str, nome: str) -> dict:
    """
    Gera um código PIX real comunicando com a API do Mercado Pago
    """
    # Inicializa o SDK do MercadoPago
    sdk = mercadopago.SDK(settings.mercadopago_access_token)
    
    # Prepara os dados de pagamento
    payment_data = {
        "transaction_amount": float(valor),
        "description": "Recarga de Créditos SAKA Delivery",
        "payment_method_id": "pix",
        "payer": {
            "email": email or "teste@cliente.com",
            "first_name": nome or "Cliente",
            "last_name": "SAKA",
            "identification": {
                "type": "CPF",
                "number": "19119119100"
            }
        }
    }
    
    # Realiza a chamada
    payment_response = sdk.payment().create(payment_data)
    payment = payment_response["response"]
    
    if payment_response["status"] != 201:
        logger.error(f"Erro Mercado Pago: {payment}")
        raise ValueError(f"Falha na API: {payment.get('message', 'Erro desconhecido')}")
        
    return {
        "txid": payment.get("id"),
        "codigo_pix": payment["point_of_interaction"]["transaction_data"]["qr_code"],
        "chave_pix": "PIX copia e cola pelo código QR",
        "qr_code_base64": payment["point_of_interaction"]["transaction_data"]["qr_code_base64"],
        "valor": valor,
        "descricao": "Recarga de créditos SAKA",
        "data_criacao": datetime.now().isoformat()
    }


@router.post("/cobranca", response_model=FaturamentoCobrancaResponse)
async def criar_cobranca(
    request: FaturamentoCriarRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Cria uma nova cobrança PIX e retorna o QR Code para pagamento.
    """
    logger.info(f"Criando cobrança PIX: valor={request.valor}, user_id={request.user_id}")
    
    # Buscar usuário
    result = await db.execute(select(User).where(User.id == request.user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    try:
        pix_data = gerar_codigo_pix_mp(
            valor=request.valor,
            email=getattr(user, 'email', None),
            nome=getattr(user, 'fullName', None)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        "id": str(uuid.uuid4()),
        "user_id": request.user_id,
        "valor": request.valor,
        "status": "PENDENTE",
        "txid": str(pix_data.get("txid", "")),
        "codigo_pix": pix_data["codigo_pix"],
        "chave_pix": pix_data["chave_pix"],
        "descricao": pix_data["descricao"],
        "qr_code_url": f"data:image/jpeg;base64,{pix_data['qr_code_base64']}",
        "data_criacao": pix_data["data_criacao"],
        "data_expiracao": datetime.now().isoformat(),
    }


@router.get("/cobranca/{cobranca_id}", response_model=FaturamentoCobrancaResponse)
async def buscar_cobranca(
    cobranca_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Busca o status de uma cobrança específica.
    """
    # Em produção, buscar do banco de dados
    # Por agora, retornar示例
    raise HTTPException(status_code=404, detail="Cobrança não encontrada")


@router.get("/historico/{user_id}")
async def historico_faturamento(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna o histórico de cobranças/pagamentos do usuário.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Em produção, buscar do banco de dados
    return {
        "user_id": user_id,
        "saldo_atual": float(user.saldo_credito or 0),
        "historico": []
    }


@router.get("/qrcode/{valor}")
async def gerar_qrcode_pix(
    valor: float,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Gera um QR Code PIX para o valor especificado.
    Endpoint simples para演示 purposes.
    """
    if valor <= 0:
        raise HTTPException(status_code=400, detail="Valor deve ser maior que zero")
    
    if valor > 10000:
        raise HTTPException(status_code=400, detail="Valor máximo é R$ 10.000,00")
    
    try:
        pix_data = gerar_codigo_pix_mp(
            valor=valor, 
            email=getattr(current_user, 'email', None), 
            nome=getattr(current_user, 'fullName', None)
        )
        return {
            "success": True,
            "data": pix_data
        }
    except Exception as e:
        logger.error(f"Erro Mercado Pago GET: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Erro ao gerar PIX no gateway: {str(e)}")
