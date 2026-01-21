"""
Modelos Pydantic para o serviço ERP
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class Contact(BaseModel):
    name: str
    role: str
    email: str
    phone: str

class Address(BaseModel):
    street: str
    city: str
    state: str
    zipcode: str

class Customer(BaseModel):
    customer_id: str
    cnpj: str
    company_name: str
    rating: str  # A, B, C, D
    credit_limit: float
    current_balance: float
    contacts: List[Contact]
    address: Address
    registration_date: str
    last_payment_date: Optional[str]
    payment_history_score: int
    business_segment: Optional[str] = None
    status: str

class Invoice(BaseModel):
    invoice_id: str
    customer_id: str
    invoice_number: str
    due_date: str
    amount: float
    amount_paid: float
    status: str  # open, overdue, paid, cancelled
    days_overdue: Optional[int]
    safra: Optional[str]
    contract_id: Optional[str]
    description: str
    created_at: str
    interest_rate: float
    fine_rate: float

class InvoiceListResponse(BaseModel):
    customer_id: str
    invoices: List[Invoice]
    total_count: int
    total_amount: float

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
    agreement_type: str  # installment, extension, discount
    scenario: AgreementScenario
    session_metadata: dict

class AgreementInstallment(BaseModel):
    installment_id: str
    installment_number: int
    due_date: str
    amount: float
    status: str

class Agreement(BaseModel):
    agreement_id: str
    customer_id: str
    status: str  # pending_approval, approved, rejected, active, completed
    created_at: str
    approved_at: Optional[str]
    expires_at: Optional[str]
    total_amount: float
    installments: List[AgreementInstallment]
    payment_methods_available: List[str]
