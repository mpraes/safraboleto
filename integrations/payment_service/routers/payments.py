"""
Router para endpoints de pagamentos
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from typing import Optional
import uuid
import random
import asyncio
from pydantic import BaseModel

from integrations.shared.database import (
    get_db_session, Payment, PaymentHistory, PaymentType, PaymentStatus
)

router = APIRouter(prefix="/payments", tags=["payments"])


class PayerInfo(BaseModel):
    name: str
    cnpj: str
    address: Optional[str] = None


class GenerateBoletoRequest(BaseModel):
    invoice_id: Optional[str] = None
    installment_id: Optional[str] = None
    amount: float
    due_date: str
    payer_info: PayerInfo
    description: str


class GeneratePixRequest(BaseModel):
    invoice_id: Optional[str] = None
    installment_id: Optional[str] = None
    amount: float
    due_date: str
    payer_info: PayerInfo
    description: str


class PaymentResponse(BaseModel):
    payment_id: str
    type: str
    amount: float
    due_date: str
    created_at: str
    expires_at: str
    barcode: Optional[str] = None
    digitable_line: Optional[str] = None
    pdf_url: Optional[str] = None
    pix_key: Optional[str] = None
    qr_code_url: Optional[str] = None
    qr_code_base64: Optional[str] = None


class PaymentStatusResponse(BaseModel):
    payment_id: str
    status: str
    paid_at: Optional[str] = None
    paid_amount: Optional[float] = None
    payment_method: Optional[str] = None


def generate_barcode():
    """Gera código de barras fictício"""
    return "".join([str(random.randint(0, 9)) for _ in range(48)])


def generate_digitable_line():
    """Gera linha digitável fictícia"""
    return ".".join([
        "".join([str(random.randint(0, 9)) for _ in range(5)])
        for _ in range(4)
    ])


def generate_pix_key():
    """Gera chave PIX fictícia"""
    return str(uuid.uuid4())


async def simulate_bank_confirmation(payment_id: str, db_session: AsyncSession):
    """Simula confirmação bancária assíncrona (10-30 segundos)"""
    delay = random.randint(10, 30)
    await asyncio.sleep(delay)
    
    async with db_session.begin():
        result = await db_session.execute(
            select(Payment).where(Payment.payment_id == uuid.UUID(payment_id))
        )
        payment = result.scalar_one_or_none()
        
        if not payment:
            return
        
        success = random.random() < 0.95
        
        previous_status = payment.status
        if success:
            payment.status = PaymentStatus.confirmado
            payment.paid_at = datetime.utcnow()
            payment.paid_amount = payment.amount
            payment.confirmation_code = f"CONF-{random.randint(100000, 999999)}"
        else:
            payment.status = PaymentStatus.falhou
            payment.failure_reason = random.choice([
                "Falha na comunicação bancária",
                "Dados do pagador inválidos",
                "Limite de transação excedido"
            ])
        
        payment.webhook_attempts += 1
        
        history = PaymentHistory(
            payment_id=payment.payment_id,
            previous_status=previous_status,
            new_status=payment.status,
            reason="Simulação de confirmação bancária",
            metadata={"delay_seconds": delay, "success": success}
        )
        db_session.add(history)


@router.post("/boleto", response_model=PaymentResponse)
async def generate_boleto(
    request: GenerateBoletoRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session)
):
    """Gera boleto bancário"""
    payment = Payment(
        type=PaymentType.boleto,
        amount=request.amount,
        due_date=datetime.fromisoformat(request.due_date),
        status=PaymentStatus.pendente,
        barcode=generate_barcode(),
        digitable_line=generate_digitable_line(),
        pdf_url=f"https://boleto.safraboleto.com/{uuid.uuid4()}.pdf",
        expires_at=datetime.utcnow() + timedelta(days=3)
    )
    
    if request.invoice_id:
        try:
            payment.invoice_id = uuid.UUID(request.invoice_id)
        except ValueError:
            pass
    
    if request.installment_id:
        try:
            payment.installment_id = uuid.UUID(request.installment_id)
        except ValueError:
            pass
    
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    
    return PaymentResponse(
        payment_id=str(payment.payment_id),
        type="boleto",
        amount=float(payment.amount),
        due_date=payment.due_date.isoformat(),
        created_at=payment.created_at.isoformat(),
        expires_at=payment.expires_at.isoformat() if payment.expires_at else None,
        barcode=payment.barcode,
        digitable_line=payment.digitable_line,
        pdf_url=payment.pdf_url
    )


@router.post("/pix", response_model=PaymentResponse)
async def generate_pix(
    request: GeneratePixRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session)
):
    """Gera cobrança PIX"""
    payment = Payment(
        type=PaymentType.pix,
        amount=request.amount,
        due_date=datetime.fromisoformat(request.due_date),
        status=PaymentStatus.pendente,
        pix_key=generate_pix_key(),
        qr_code_url=f"https://pix.safraboleto.com/qr/{uuid.uuid4()}",
        qr_code_base64=f"base64encodedqrcode{random.randint(100000, 999999)}",
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    
    if request.invoice_id:
        try:
            payment.invoice_id = uuid.UUID(request.invoice_id)
        except ValueError:
            pass
    
    if request.installment_id:
        try:
            payment.installment_id = uuid.UUID(request.installment_id)
        except ValueError:
            pass
    
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    
    return PaymentResponse(
        payment_id=str(payment.payment_id),
        type="pix",
        amount=float(payment.amount),
        due_date=payment.due_date.isoformat(),
        created_at=payment.created_at.isoformat(),
        expires_at=payment.expires_at.isoformat() if payment.expires_at else None,
        pix_key=payment.pix_key,
        qr_code_url=payment.qr_code_url,
        qr_code_base64=payment.qr_code_base64
    )


@router.get("/{payment_id}/status", response_model=PaymentStatusResponse)
async def get_payment_status(payment_id: str, db: AsyncSession = Depends(get_db_session)):
    """Consulta status de um pagamento"""
    try:
        pay_uuid = uuid.UUID(payment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID do pagamento inválido")
    
    result = await db.execute(
        select(Payment).where(Payment.payment_id == pay_uuid)
    )
    payment = result.scalar_one_or_none()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")
    
    return PaymentStatusResponse(
        payment_id=str(payment.payment_id),
        status=payment.status.value,
        paid_at=payment.paid_at.isoformat() if payment.paid_at else None,
        paid_amount=float(payment.paid_amount) if payment.paid_amount else None,
        payment_method=payment.payment_method
    )


@router.get("/{payment_id}/history")
async def get_payment_history(payment_id: str, db: AsyncSession = Depends(get_db_session)):
    """Histórico de estados do pagamento"""
    try:
        pay_uuid = uuid.UUID(payment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID do pagamento inválido")
    
    result = await db.execute(
        select(PaymentHistory).where(PaymentHistory.payment_id == pay_uuid)
        .order_by(PaymentHistory.created_at.desc())
    )
    history = result.scalars().all()
    
    return {
        "payment_id": payment_id,
        "history": [
            {
                "history_id": str(h.history_id),
                "previous_status": h.previous_status.value if h.previous_status else None,
                "new_status": h.new_status.value,
                "reason": h.reason,
                "created_at": h.created_at.isoformat()
            }
            for h in history
        ]
    }


@router.post("/{payment_id}/webhook")
async def payment_webhook(
    payment_id: str,
    status: str,
    confirmation_code: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """Endpoint para receber confirmações bancárias (simulado)"""
    try:
        pay_uuid = uuid.UUID(payment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID do pagamento inválido")
    
    result = await db.execute(
        select(Payment).where(Payment.payment_id == pay_uuid)
    )
    payment = result.scalar_one_or_none()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")
    
    previous_status = payment.status
    
    try:
        payment.status = PaymentStatus(status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Status inválido")
    
    if status == "confirmado":
        payment.paid_at = datetime.utcnow()
        payment.confirmation_code = confirmation_code
    
    history = PaymentHistory(
        payment_id=payment.payment_id,
        previous_status=previous_status,
        new_status=payment.status,
        reason="Webhook recebido",
        metadata={"confirmation_code": confirmation_code}
    )
    db.add(history)
    
    await db.commit()
    
    return {"payment_id": payment_id, "status": status, "updated": True}
