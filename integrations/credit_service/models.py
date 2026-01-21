"""
Modelos Pydantic para o serviço de regras de crédito
"""
from pydantic import BaseModel
from typing import Optional, List

class CustomerProfile(BaseModel):
    rating: str  # A, B, C, D
    credit_limit: float
    current_balance: float
    payment_history_score: int
    days_since_last_payment: int

class SelectedInvoice(BaseModel):
    invoice_id: str
    amount: float
    days_overdue: int
    due_date: str

class SessionConstraints(BaseModel):
    max_down_payment: Optional[float] = None
    max_monthly_payment: Optional[float] = None
    preferred_start_date: Optional[str] = None
    max_installments: Optional[int] = None
    cannot_pay_this_month: bool = False

class GenerateOptionsRequest(BaseModel):
    customer_id: str
    customer_profile: CustomerProfile
    selected_invoices: List[SelectedInvoice]
    session_constraints: SessionConstraints

class InstallmentScenario(BaseModel):
    installment_number: int
    due_date: str
    amount: float
    discount: float

class Scenario(BaseModel):
    scenario_id: str
    name: str
    type: str  # discount, installment
    total_amount: float
    original_amount: float
    discount_amount: float
    discount_percentage: float
    installments: List[InstallmentScenario]
    interest_rate: float
    total_interest: float
    recommended: bool

class GenerateOptionsResponse(BaseModel):
    scenarios: List[Scenario]
    rules_applied: List[str]
    requires_approval: bool

class ValidateScenarioRequest(BaseModel):
    customer_id: str
    scenario_id: str
    agreement_type: str

class ValidateScenarioResponse(BaseModel):
    valid: bool
    requires_approval: bool
    reasons: List[str]
    warnings: List[str]
