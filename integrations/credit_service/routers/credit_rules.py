"""
Router para endpoints de regras de crédito
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel

from integrations.shared.database import (
    get_db_session, Customer, Invoice, CreditRulesConfig, TierConfig,
    CustomerRating
)
from integrations.credit_service.rules_engine import (
    load_credit_rules,
    calculate_debt_with_interest,
    generate_renegotiation_scenarios,
    get_interest_rate_for_rating
)

router = APIRouter(prefix="/credit-rules", tags=["credit-rules"])


class CustomerProfile(BaseModel):
    rating: str
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
    type: str
    total_amount: float
    original_amount: float
    discount_amount: float
    discount_percentage: float
    installments: List[InstallmentScenario]
    interest_rate: float
    total_interest: float
    recommended: bool
    requires_approval: bool


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


class CalculateDebtRequest(BaseModel):
    invoices: List[SelectedInvoice]
    rating: str


class CalculateDebtResponse(BaseModel):
    original_total: float
    fine_total: float
    interest_total: float
    total_debt: float
    calculation_date: str


@router.post("/generate-options", response_model=GenerateOptionsResponse)
async def generate_options(
    request: GenerateOptionsRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Gera cenários de renegociação baseados em regras de crédito"""
    rules = load_credit_rules()
    
    invoices_data = [
        {
            "invoice_id": inv.invoice_id,
            "amount": inv.amount,
            "days_overdue": inv.days_overdue,
            "due_date": inv.due_date
        }
        for inv in request.selected_invoices
    ]
    
    customer_profile = {
        "rating": request.customer_profile.rating,
        "credit_limit": request.customer_profile.credit_limit,
        "current_balance": request.customer_profile.current_balance,
        "payment_history_score": request.customer_profile.payment_history_score
    }
    
    session_constraints = request.session_constraints.model_dump()
    
    scenarios = generate_renegotiation_scenarios(
        customer_profile,
        invoices_data,
        session_constraints,
        rules
    )
    
    rules_applied = [
        f"Rating: {request.customer_profile.rating}",
        f"Max parcelas: {rules['rating_rules'].get(request.customer_profile.rating, {}).get('max_installments', 3)}",
        f"Max desconto: {rules['rating_rules'].get(request.customer_profile.rating, {}).get('max_discount_percentage', 1)}%"
    ]
    
    requires_approval = any(s.get("requires_approval", False) for s in scenarios)
    
    return GenerateOptionsResponse(
        scenarios=[
            Scenario(
                scenario_id=s["scenario_id"],
                name=s["name"],
                type=s["type"],
                total_amount=s["total_amount"],
                original_amount=s["original_amount"],
                discount_amount=s["discount_amount"],
                discount_percentage=s["discount_percentage"],
                installments=[
                    InstallmentScenario(
                        installment_number=i["installment_number"],
                        due_date=i["due_date"],
                        amount=i["amount"],
                        discount=i["discount"]
                    )
                    for i in s["installments"]
                ],
                interest_rate=s["interest_rate"],
                total_interest=s["total_interest"],
                recommended=s["recommended"],
                requires_approval=s["requires_approval"]
            )
            for s in scenarios
        ],
        rules_applied=rules_applied,
        requires_approval=requires_approval
    )


@router.post("/validate-scenario", response_model=ValidateScenarioResponse)
async def validate_scenario(request: ValidateScenarioRequest):
    """Valida se um cenário escolhido ainda está dentro das regras"""
    rules = load_credit_rules()
    
    rating_rules = rules.get("rating_rules", {}).get("B", {})
    
    valid = True
    reasons = []
    warnings = []
    requires_approval = False
    
    if request.agreement_type == "discount":
        requires_approval = True
        reasons.append("Acordos com desconto requerem aprovação")
    
    return ValidateScenarioResponse(
        valid=valid,
        requires_approval=requires_approval,
        reasons=reasons,
        warnings=warnings
    )


@router.post("/calculate-debt", response_model=CalculateDebtResponse)
async def calculate_debt(request: CalculateDebtRequest):
    """Calcula dívida total com juros compostos e multa"""
    rules = load_credit_rules()
    interest_rate = get_interest_rate_for_rating(request.rating, rules)
    
    original_total = 0
    fine_total = 0
    interest_total = 0
    
    for invoice in request.invoices:
        calc = calculate_debt_with_interest(
            invoice.amount,
            invoice.days_overdue,
            interest_rate
        )
        original_total += calc["original_amount"]
        fine_total += calc["fine_amount"]
        interest_total += calc["interest_amount"]
    
    total_debt = original_total + fine_total + interest_total
    
    return CalculateDebtResponse(
        original_total=round(original_total, 2),
        fine_total=round(fine_total, 2),
        interest_total=round(interest_total, 2),
        total_debt=round(total_debt, 2),
        calculation_date=__import__("datetime").datetime.utcnow().isoformat()
    )


@router.post("/check-approval")
async def check_approval(
    customer_id: str,
    discount_percentage: float,
    total_amount: float,
    rating: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Verifica se cenário requer aprovação humana"""
    rules = load_credit_rules()
    
    rating_rules = rules.get("rating_rules", {}).get(rating, {})
    approval_threshold = rating_rules.get("requires_approval_threshold", 100000)
    max_discount = rating_rules.get("max_discount_percentage", 1.0)
    
    requires_approval = False
    reasons = []
    
    if discount_percentage > 10:
        requires_approval = True
        reasons.append("Desconto acima de 10% requer aprovação")
    elif discount_percentage > 5 and rating in ["C", "D"]:
        requires_approval = True
        reasons.append(f"Desconto acima de 5% para rating {rating} requer aprovação")
    elif rating == "D" and discount_percentage > 0:
        requires_approval = True
        reasons.append("Cliente rating D não pode receber desconto automático")
    elif total_amount > approval_threshold:
        requires_approval = True
        reasons.append(f"Valor acima do threshold de aprovação (R$ {approval_threshold:,.2f})")
    
    return {
        "requires_approval": requires_approval,
        "reasons": reasons,
        "approval_threshold": approval_threshold,
        "max_discount_auto": max_discount
    }
