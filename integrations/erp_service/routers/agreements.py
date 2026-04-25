"""
Router para endpoints de acordos de renegociação
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from typing import List, Optional
import uuid
from pydantic import BaseModel

from integrations.shared.database import (
    get_db_session, Agreement, AgreementInstallment, AgreementStatus,
    AgreementHistory, Invoice, Customer
)

router = APIRouter(prefix="/agreements", tags=["agreements"])


class Installment(BaseModel):
    installment_number: int
    due_date: str
    amount: float
    discount: float


class AgreementScenario(BaseModel):
    total_amount: float
    installments: List[Installment]
    interest_rate: float
    total_discount: float


class CreateAgreementRequest(BaseModel):
    customer_id: str
    invoice_ids: List[str]
    agreement_type: str
    scenario: AgreementScenario
    session_metadata: dict


class AgreementInstallmentResponse(BaseModel):
    installment_id: str
    installment_number: int
    due_date: str
    amount: float
    status: str


class AgreementResponse(BaseModel):
    agreement_id: str
    customer_id: str
    status: str
    created_at: str
    approved_at: Optional[str]
    expires_at: Optional[str]
    total_amount: float
    installments: List[AgreementInstallmentResponse]
    payment_methods_available: List[str]


@router.post("", response_model=AgreementResponse)
async def create_agreement(request: CreateAgreementRequest, db: AsyncSession = Depends(get_db_session)):
    """Cria um novo acordo de renegociação"""
    try:
        cust_uuid = uuid.UUID(request.customer_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID do cliente inválido")
    
    cust_result = await db.execute(
        select(Customer).where(Customer.customer_id == cust_uuid)
    )
    customer = cust_result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    invoice_uuids = []
    for inv_id in request.invoice_ids:
        try:
            invoice_uuids.append(uuid.UUID(inv_id))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"ID de fatura inválido: {inv_id}")
    
    agreement = Agreement(
        customer_id=cust_uuid,
        invoice_ids=invoice_uuids,
        agreement_type=request.agreement_type,
        status=AgreementStatus.rascunho,
        total_amount=request.scenario.total_amount,
        original_amount=request.scenario.total_amount + request.scenario.total_discount,
        discount_amount=request.scenario.total_discount,
        discount_percentage=(request.scenario.total_discount / (request.scenario.total_amount + request.scenario.total_discount) * 100) if request.scenario.total_amount > 0 else 0,
        interest_rate=request.scenario.interest_rate,
        session_metadata=request.session_metadata,
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    db.add(agreement)
    await db.flush()
    
    for inst in request.scenario.installments:
        installment = AgreementInstallment(
            agreement_id=agreement.agreement_id,
            installment_number=inst.installment_number,
            due_date=datetime.fromisoformat(inst.due_date) if isinstance(inst.due_date, str) else inst.due_date,
            amount=inst.amount,
            discount=inst.discount
        )
        db.add(installment)
    
    history = AgreementHistory(
        agreement_id=agreement.agreement_id,
        new_status=AgreementStatus.rascunho,
        context={"action": "created", "session_metadata": request.session_metadata}
    )
    db.add(history)
    
    await db.commit()
    await db.refresh(agreement)
    
    installments_result = await db.execute(
        select(AgreementInstallment).where(AgreementInstallment.agreement_id == agreement.agreement_id)
    )
    installments = installments_result.scalars().all()
    
    return AgreementResponse(
        agreement_id=str(agreement.agreement_id),
        customer_id=str(agreement.customer_id),
        status=agreement.status.value,
        created_at=agreement.created_at.isoformat(),
        approved_at=agreement.approved_at.isoformat() if agreement.approved_at else None,
        expires_at=agreement.expires_at.isoformat() if agreement.expires_at else None,
        total_amount=float(agreement.total_amount),
        installments=[
            AgreementInstallmentResponse(
                installment_id=str(i.installment_id),
                installment_number=i.installment_number,
                due_date=i.due_date.isoformat() if i.due_date else "",
                amount=float(i.amount),
                status=i.status.value
            ) for i in installments
        ],
        payment_methods_available=["boleto", "pix"]
    )


@router.get("/{agreement_id}", response_model=AgreementResponse)
async def get_agreement(agreement_id: str, db: AsyncSession = Depends(get_db_session)):
    """Consulta status de um acordo"""
    try:
        agr_uuid = uuid.UUID(agreement_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID do acordo inválido")
    
    result = await db.execute(
        select(Agreement).where(Agreement.agreement_id == agr_uuid)
    )
    agreement = result.scalar_one_or_none()
    
    if not agreement:
        raise HTTPException(status_code=404, detail="Acordo não encontrado")
    
    installments_result = await db.execute(
        select(AgreementInstallment).where(AgreementInstallment.agreement_id == agreement.agreement_id)
    )
    installments = installments_result.scalars().all()
    
    return AgreementResponse(
        agreement_id=str(agreement.agreement_id),
        customer_id=str(agreement.customer_id),
        status=agreement.status.value,
        created_at=agreement.created_at.isoformat(),
        approved_at=agreement.approved_at.isoformat() if agreement.approved_at else None,
        expires_at=agreement.expires_at.isoformat() if agreement.expires_at else None,
        total_amount=float(agreement.total_amount),
        installments=[
            AgreementInstallmentResponse(
                installment_id=str(i.installment_id),
                installment_number=i.installment_number,
                due_date=i.due_date.isoformat() if i.due_date else "",
                amount=float(i.amount),
                status=i.status.value
            ) for i in installments
        ],
        payment_methods_available=["boleto", "pix"]
    )


@router.post("/{agreement_id}/approve")
async def approve_agreement(agreement_id: str, approved_by: str, db: AsyncSession = Depends(get_db_session)):
    """Aprova um acordo"""
    try:
        agr_uuid = uuid.UUID(agreement_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID do acordo inválido")
    
    result = await db.execute(
        select(Agreement).where(Agreement.agreement_id == agr_uuid)
    )
    agreement = result.scalar_one_or_none()
    
    if not agreement:
        raise HTTPException(status_code=404, detail="Acordo não encontrado")
    
    if agreement.status not in [AgreementStatus.rascunho, AgreementStatus.pendente_aprovacao]:
        raise HTTPException(status_code=400, detail=f"Acordo não pode ser aprovado no status {agreement.status.value}")
    
    previous_status = agreement.status
    agreement.status = AgreementStatus.aprovado
    agreement.approved_by = approved_by
    agreement.approved_at = datetime.utcnow()
    
    history = AgreementHistory(
        agreement_id=agreement.agreement_id,
        previous_status=previous_status,
        new_status=AgreementStatus.aprovado,
        changed_by=approved_by,
        context={"action": "approved"}
    )
    db.add(history)
    
    await db.commit()
    
    return {"agreement_id": agreement_id, "status": "aprovado", "approved_at": agreement.approved_at.isoformat()}


@router.post("/{agreement_id}/reject")
async def reject_agreement(agreement_id: str, reason: str, rejected_by: str, db: AsyncSession = Depends(get_db_session)):
    """Rejeita um acordo"""
    try:
        agr_uuid = uuid.UUID(agreement_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID do acordo inválido")
    
    result = await db.execute(
        select(Agreement).where(Agreement.agreement_id == agr_uuid)
    )
    agreement = result.scalar_one_or_none()
    
    if not agreement:
        raise HTTPException(status_code=404, detail="Acordo não encontrado")
    
    previous_status = agreement.status
    agreement.status = AgreementStatus.rejeitado
    agreement.approval_reason = reason
    
    history = AgreementHistory(
        agreement_id=agreement.agreement_id,
        previous_status=previous_status,
        new_status=AgreementStatus.rejeitado,
        changed_by=rejected_by,
        reason=reason,
        context={"action": "rejected"}
    )
    db.add(history)
    
    await db.commit()
    
    return {"agreement_id": agreement_id, "status": "rejeitado", "reason": reason}
