"""
Router para endpoints de faturas
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import uuid

from integrations.shared.database import get_db_session, Invoice

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.get("/{invoice_id}")
async def get_invoice(invoice_id: str, db: AsyncSession = Depends(get_db_session)):
    """Busca fatura por ID"""
    try:
        inv_uuid = uuid.UUID(invoice_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID da fatura inválido")
    
    result = await db.execute(
        select(Invoice).where(Invoice.invoice_id == inv_uuid)
    )
    invoice = result.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Fatura não encontrada")
    
    return {
        "invoice_id": str(invoice.invoice_id),
        "customer_id": str(invoice.customer_id),
        "invoice_number": invoice.invoice_number,
        "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
        "amount": float(invoice.amount),
        "amount_paid": float(invoice.amount_paid),
        "status": invoice.status.value,
        "days_overdue": invoice.days_overdue or 0,
        "safra": invoice.safra,
        "contract_id": invoice.contract_id,
        "description": invoice.description,
        "interest_rate": float(invoice.interest_rate),
        "fine_rate": float(invoice.fine_rate),
        "created_at": invoice.created_at.isoformat() if invoice.created_at else None
    }
