"""
Router para geração de QR Code PIX e gerenciamento de faturamento.
Suporta Mercado Pago real e modo simulação (fallback automático).
"""
import logging
import uuid
import zlib
import base64
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
from sqlalchemy import func
from ..models import Order, OrderStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/faturamento", tags=["Faturamento"])

settings = get_settings()


def _gerar_pix_simulado(valor: float, email: str, nome: str) -> dict:
    """
    Gera um código PIX simulado para testes quando a API do Mercado Pago não está disponível.
    O código segue o formato EMV do PIX brasileiro.
    """
    txid = str(uuid.uuid4()).replace("-", "")[:25]
    
    # Gera um código PIX no formato EMV simplificado (simulação)
    pix_payload = (
        f"00020126580014br.gov.bcb.pix"
        f"0136{txid}"
        f"5204000053039865802BR"
        f"5913SAKA DELIVERY"
        f"6008SAOPAULO"
        f"62070503***"
        f"6304"
    )
    # Calcula CRC16 simplificado para completar o payload
    crc = zlib.crc32(pix_payload.encode()) & 0xFFFF
    codigo_pix = f"{pix_payload}{crc:04X}"
    
    logger.info(f"✅ PIX simulado gerado: txid={txid}, valor=R${valor:.2f}")
    
    return {
        "txid": txid,
        "codigo_pix": codigo_pix,
        "chave_pix": "pix@sakdelivery.com.br (Simulação)",
        "qr_code_base64": "",  # Frontend gera via qrcode lib
        "valor": valor,
        "descricao": "Recarga de créditos SAKA (Simulação)",
        "data_criacao": datetime.now().isoformat(),
        "simulado": True,
    }


def gerar_codigo_pix_mp(valor: float, email: str, nome: str) -> dict:
    """
    Gera um código PIX comunicando com a API do Mercado Pago.
    Se a API falhar, usa modo simulação automaticamente.
    """
    try:
        import mercadopago
        
        if not settings.mercadopago_access_token:
            logger.warning("⚠️ Token Mercado Pago não configurado — usando simulação")
            return _gerar_pix_simulado(valor, email, nome)
        
        sdk = mercadopago.SDK(settings.mercadopago_access_token)
        
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
        
        payment_response = sdk.payment().create(payment_data)
        payment = payment_response["response"]
        
        if payment_response["status"] != 201:
            logger.warning(f"⚠️ Mercado Pago retornou status {payment_response['status']}: {payment}")
            logger.info("🔄 Usando modo simulação como fallback")
            return _gerar_pix_simulado(valor, email, nome)
        
        return {
            "txid": payment.get("id"),
            "codigo_pix": payment["point_of_interaction"]["transaction_data"]["qr_code"],
            "chave_pix": "PIX copia e cola pelo código QR",
            "qr_code_base64": payment["point_of_interaction"]["transaction_data"]["qr_code_base64"],
            "valor": valor,
            "descricao": "Recarga de créditos SAKA",
            "data_criacao": datetime.now().isoformat(),
            "simulado": False,
        }
        
    except ImportError:
        logger.warning("⚠️ SDK mercadopago não instalado — usando simulação")
        return _gerar_pix_simulado(valor, email, nome)
    except Exception as e:
        logger.warning(f"⚠️ Erro na API Mercado Pago: {e}")
        logger.info("🔄 Usando modo simulação como fallback")
        return _gerar_pix_simulado(valor, email, nome)


@router.post("/cobranca", response_model=FaturamentoCobrancaResponse)
async def criar_cobranca(
    request: FaturamentoCriarRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Cria uma nova cobrança PIX e retorna o QR Code para pagamento.
    """
    logger.info(f"Criando cobrança PIX: valor={request.valor}, user_id={request.user_id}")
    
    result = await db.execute(select(User).where(User.id == request.user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    try:
        pix_data = gerar_codigo_pix_mp(
            valor=request.valor,
            email=getattr(user, 'email', None),
            nome=getattr(user, 'full_name', None)
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
        "qr_code_url": f"data:image/jpeg;base64,{pix_data.get('qr_code_base64', '')}",
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
    
    return {
        "user_id": user_id,
        "saldo_atual": float(user.saldo_credito or 0),
        "historico": []
    }


@router.get("/rendimento", summary="Retorna o faturamento KDS mensal")
async def rendimento_mensal(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    KDS: Calcula todo o faturamento dos pedidos do restaurante (Tenant) no mês atual.
    """
    now = datetime.now()
    inicio_mes = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    query = select(func.sum(Order.total), func.count(Order.id)).where(
        Order.status != OrderStatus.CANCELLED.value,
        Order.created_at >= inicio_mes
    )
    
    if current_user.tenant_id:
        query = query.where(Order.tenant_id == current_user.tenant_id)
        
    result = await db.execute(query)
    soma_total, contagem = result.first()
    
    meses_pt = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    mes_str = f"{meses_pt[now.month - 1]} / {now.year}"
    
    return {
        "rendimento_mensal": float(soma_total or 0.0),
        "quantidade_pedidos": int(contagem or 0),
        "mes": mes_str
    }


@router.get("/qrcode/{valor}")
async def gerar_qrcode_pix(
    valor: float,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Gera um QR Code PIX para o valor especificado.
    Usa Mercado Pago quando disponível, senão gera simulação.
    """
    if valor <= 0:
        raise HTTPException(status_code=400, detail="Valor deve ser maior que zero")
    
    if valor > 10000:
        raise HTTPException(status_code=400, detail="Valor máximo é R$ 10.000,00")
    
    pix_data = gerar_codigo_pix_mp(
        valor=valor, 
        email=getattr(current_user, 'email', None), 
        nome=getattr(current_user, 'full_name', None)
    )
    return {
        "success": True,
        "data": pix_data
    }
