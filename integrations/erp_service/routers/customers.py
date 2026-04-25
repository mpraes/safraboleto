"""
Router para endpoints de clientes
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from datetime import datetime
import uuid

from integrations.shared.database import (
    get_db_session, Customer, Address, Contact, Invoice,
    CustomerRating, CustomerTier, CustomerStatus, ContactRole
)

router = APIRouter(prefix="/customers", tags=["customers"])


class AddressResponse(BaseModel):
    street: str
    city: str
    state: str
    zipcode: str


class ContactResponse(BaseModel):
    name: str
    role: str
    email: str
    phone: str


class CustomerResponse(BaseModel):
    customer_id: str
    cnpj: str
    company_name: str
    rating: str
    tier: str
    credit_limit: float
    current_balance: float
    contacts: List[ContactResponse]
    address: Optional[AddressResponse]
    registration_date: str
    last_payment_date: Optional[str]
    payment_history_score: int
    business_segment: Optional[str]
    status: str


class InvoiceResponse(BaseModel):
    invoice_id: str
    customer_id: str
    invoice_number: str
    due_date: str
    amount: float
    amount_paid: float
    status: str
    days_overdue: int
    safra: Optional[str]
    contract_id: Optional[str]
    description: Optional[str]
    created_at: str
    interest_rate: float
    fine_rate: float


class InvoiceListResponse(BaseModel):
    customer_id: str
    invoices: List[InvoiceResponse]
    total_count: int
    total_amount: float


from pydantic import BaseModel


@router.get("/{cnpj}", response_model=CustomerResponse)
async def get_customer_by_cnpj(cnpj: str, db: AsyncSession = Depends(get_db_session)):
    """Busca cliente por CNPJ"""
    cnpj_clean = cnpj.replace(".", "").replace("/", "").replace("-", "")
    
    result = await db.execute(
        select(Customer).where(Customer.cnpj == cnpj_clean)
    )
    customer = result.scalar_one_or_none()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    addr_result = await db.execute(
        select(Address).where(Address.customer_id == customer.customer_id, Address.is_primary == True)
    )
    address = addr_result.scalar_one_or_none()
    
    contacts_result = await db.execute(
        select(Contact).where(Contact.customer_id == customer.customer_id)
    )
    contacts = contacts_result.scalars().all()
    
    return CustomerResponse(
        customer_id=str(customer.customer_id),
        cnpj=customer.cnpj,
        company_name=customer.company_name,
        rating=customer.rating.value,
        tier=customer.tier.value,
        credit_limit=float(customer.credit_limit),
        current_balance=float(customer.current_balance),
        contacts=[
            ContactResponse(
                name=c.name,
                role=c.role.value,
                email=c.email,
                phone=c.phone
            ) for c in contacts
        ],
        address=AddressResponse(
            street=address.street,
            city=address.city,
            state=address.state,
            zipcode=address.zipcode
        ) if address else None,
        registration_date=customer.registration_date.isoformat() if customer.registration_date else "",
        last_payment_date=customer.last_payment_date.isoformat() if customer.last_payment_date else None,
        payment_history_score=customer.payment_history_score,
        business_segment=customer.business_segment,
        status=customer.status.value
    )


@router.get("/{customer_id}/invoices", response_model=InvoiceListResponse)
async def get_customer_invoices(
    customer_id: str,
    status: Optional[str] = "open,overdue",
    due_date_from: Optional[str] = None,
    due_date_to: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    safra: Optional[str] = None,
    contract_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """Lista faturas do cliente com filtros"""
    try:
        cust_uuid = uuid.UUID(customer_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID do cliente inválido")
    
    query = select(Invoice).where(Invoice.customer_id == cust_uuid)
    
    status_list = [s.strip() for s in status.split(",")]
    status_enums = []
    for s in status_list:
        try:
            status_enums.append(InvoiceStatus(s))
        except ValueError:
            pass
    if status_enums:
        query = query.where(Invoice.status.in_(status_enums))
    
    if due_date_from:
        query = query.where(Invoice.due_date >= datetime.fromisoformat(due_date_from))
    if due_date_to:
        query = query.where(Invoice.due_date <= datetime.fromisoformat(due_date_to))
    if min_amount is not None:
        query = query.where(Invoice.amount >= min_amount)
    if max_amount is not None:
        query = query.where(Invoice.amount <= max_amount)
    if safra:
        query = query.where(Invoice.safra == safra)
    if contract_id:
        query = query.where(Invoice.contract_id == contract_id)
    
    query = query.order_by(Invoice.due_date.desc())
    
    result = await db.execute(query)
    invoices = result.scalars().all()
    
    total_amount = sum(float(inv.amount) for inv in invoices)
    
    return InvoiceListResponse(
        customer_id=customer_id,
        invoices=[
            InvoiceResponse(
                invoice_id=str(inv.invoice_id),
                customer_id=str(inv.customer_id),
                invoice_number=inv.invoice_number,
                due_date=inv.due_date.isoformat() if inv.due_date else "",
                amount=float(inv.amount),
                amount_paid=float(inv.amount_paid),
                status=inv.status.value,
                days_overdue=inv.days_overdue or 0,
                safra=inv.safra,
                contract_id=inv.contract_id,
                description=inv.description,
                created_at=inv.created_at.isoformat() if inv.created_at else "",
                interest_rate=float(inv.interest_rate),
                fine_rate=float(inv.fine_rate)
            ) for inv in invoices
        ],
        total_count=len(invoices),
        total_amount=total_amount
    )


@router.get("/{customer_id}/contacts")
async def get_customer_contacts(customer_id: str, db: AsyncSession = Depends(get_db_session)):
    """Lista contatos do cliente"""
    try:
        cust_uuid = uuid.UUID(customer_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID do cliente inválido")
    
    result = await db.execute(
        select(Contact).where(Contact.customer_id == cust_uuid)
    )
    contacts = result.scalars().all()
    
    return {
        "customer_id": customer_id,
        "contacts": [
            {
                "contact_id": str(c.contact_id),
                "name": c.name,
                "role": c.role.value,
                "email": c.email,
                "phone": c.phone,
                "is_primary": c.is_primary
            } for c in contacts
        ]
    }


@router.get("/{customer_id}/tier")
async def get_customer_tier(customer_id: str, db: AsyncSession = Depends(get_db_session)):
    """Consulta tier e benefícios do cliente"""
    try:
        cust_uuid = uuid.UUID(customer_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID do cliente inválido")
    
    result = await db.execute(
        select(Customer).where(Customer.customer_id == cust_uuid)
    )
    customer = result.scalar_one_or_none()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    tier_result = await db.execute(
        select(TierConfig).where(TierConfig.tier == customer.tier)
    )
    tier_config = tier_result.scalar_one_or_none()
    
    return {
        "customer_id": customer_id,
        "tier": customer.tier.value,
        "benefits": {
            "payment_days_limit": tier_config.payment_days_limit if tier_config else 30,
            "credit_limit": float(tier_config.credit_limit) if tier_config else 100000,
            "max_installments": tier_config.max_installments if tier_config else 3,
            "max_discount_auto": float(tier_config.max_discount_auto) if tier_config else 1.0
        } if tier_config else {}
    }


from integrations.shared.database import TierConfig, InvoiceStatus
