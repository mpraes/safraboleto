"""
Motor de regras de crédito
Implementa a lógica de geração de cenários de renegociação
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import uuid


def load_credit_rules() -> dict:
    """Carrega regras de crédito do arquivo de configuração"""
    config_path = Path(__file__).parent / "config" / "credit_rules.json"
    with open(config_path, "r") as f:
        return json.load(f)


def calculate_debt_with_interest(
    original_amount: float,
    days_overdue: int,
    interest_rate: float,
    fine_rate: float = 0.02
) -> dict:
    """
    Calcula dívida total com juros compostos e multa pro-rata dia
    
    Args:
        original_amount: Valor original da fatura
        days_overdue: Dias de atraso
        interest_rate: Taxa de juros mensal
        fine_rate: Taxa de multa mensal (padrão 2%)
    
    Returns:
        dict com valor_original, multa, juros, valor_total
    """
    if days_overdue <= 0:
        return {
            "original_amount": original_amount,
            "fine_amount": 0.0,
            "interest_amount": 0.0,
            "total_amount": original_amount
        }
    
    days_in_month = 30
    
    fine_pro_rata = (fine_rate / days_in_month) * days_overdue
    value_with_fine = original_amount * (1 + fine_pro_rata)
    
    months_overdue = days_overdue / days_in_month
    compound_factor = (1 + interest_rate) ** months_overdue
    final_value = value_with_fine * compound_factor
    
    interest_amount = final_value - value_with_fine
    
    return {
        "original_amount": round(original_amount, 2),
        "fine_amount": round(value_with_fine - original_amount, 2),
        "interest_amount": round(interest_amount, 2),
        "total_amount": round(final_value, 2)
    }


def get_interest_rate_for_rating(rating: str, rules: dict) -> float:
    """Obtém taxa de juros média para o rating"""
    rating_rules = rules.get("rating_rules", {}).get(rating, {})
    rate_range = rating_rules.get("interest_rate_range", [0.02, 0.04])
    return (rate_range[0] + rate_range[1]) / 2


def generate_renegotiation_scenarios(
    customer_profile: dict,
    selected_invoices: List[dict],
    session_constraints: dict,
    rules: dict
) -> List[dict]:
    """
    Gera cenários de renegociação baseados em regras de crédito
    
    Args:
        customer_profile: Perfil do cliente (rating, tier, etc.)
        selected_invoices: Lista de faturas selecionadas
        session_constraints: Restrições da sessão (entrada, parcelas, etc.)
        rules: Regras de crédito
    
    Returns:
        Lista de cenários de renegociação
    """
    rating = customer_profile.get("rating", "B")
    tier = customer_profile.get("tier", "Bronze")
    
    rating_rules = rules.get("rating_rules", {}).get(rating, {})
    max_installments = rating_rules.get("max_installments", 3)
    min_installment_amount = rating_rules.get("min_installment_amount", 1000.0)
    max_discount_percentage = rating_rules.get("max_discount_percentage", 1.0)
    approval_threshold = rating_rules.get("requires_approval_threshold", 100000.0)
    
    interest_rate = get_interest_rate_for_rating(rating, rules)
    
    total_debt = 0
    total_original = 0
    max_days_overdue = 0
    
    for invoice in selected_invoices:
        amount = invoice.get("amount", 0)
        days_overdue = invoice.get("days_overdue", 0)
        total_original += amount
        
        debt_calc = calculate_debt_with_interest(
            amount, days_overdue, interest_rate
        )
        total_debt += debt_calc["total_amount"]
        max_days_overdue = max(max_days_overdue, days_overdue)
    
    scenarios = []
    today = datetime.utcnow()
    
    discount_by_days = rules.get("overdue_rules", {}).get("discount_by_days", {})
    overdue_discount = 0
    for range_key, discount_info in discount_by_days.items():
        if range_key == "91+" and max_days_overdue > 90:
            overdue_discount = discount_info.get("max_discount", 0)
            break
        elif "-" in range_key:
            min_d, max_d = map(int, range_key.split("-"))
            if min_d <= max_days_overdue <= max_d:
                overdue_discount = discount_info.get("max_discount", 0)
                break
    
    effective_max_discount = min(max_discount_percentage, overdue_discount + max_discount_percentage)
    
    if session_constraints.get("max_down_payment"):
        max_down_payment = session_constraints["max_down_payment"]
    else:
        max_down_payment = total_debt
    
    if session_constraints.get("max_installments"):
        max_installments = min(max_installments, session_constraints["max_installments"])
    
    if session_constraints.get("max_monthly_payment"):
        max_monthly = session_constraints["max_monthly_payment"]
        max_installments = min(max_installments, int(total_debt / max_monthly) + 1)
    
    scenario_1_discount = min(effective_max_discount, 5.0)
    scenario_1_total = total_debt * (1 - scenario_1_discount / 100)
    
    if scenario_1_total >= min_installment_amount:
        requires_approval = scenario_1_discount > 5.0 or scenario_1_total > approval_threshold
        scenarios.append({
            "scenario_id": str(uuid.uuid4()),
            "name": "Pagamento à Vista com Desconto",
            "type": "discount",
            "total_amount": round(scenario_1_total, 2),
            "original_amount": round(total_debt, 2),
            "discount_amount": round(total_debt - scenario_1_total, 2),
            "discount_percentage": round(scenario_1_discount, 2),
            "installments": [{
                "installment_number": 1,
                "due_date": (today + timedelta(days=5)).strftime("%Y-%m-%d"),
                "amount": round(scenario_1_total, 2),
                "discount": round(total_debt - scenario_1_total, 2)
            }],
            "interest_rate": 0.0,
            "total_interest": 0.0,
            "recommended": True,
            "requires_approval": requires_approval
        })
    
    num_installments_short = min(3, max_installments)
    installment_short = total_debt / num_installments_short
    
    if installment_short >= min_installment_amount:
        scenarios.append({
            "scenario_id": str(uuid.uuid4()),
            "name": f"Parcelamento em {num_installments_short}x sem Juros",
            "type": "installment",
            "total_amount": round(total_debt, 2),
            "original_amount": round(total_debt, 2),
            "discount_amount": 0.0,
            "discount_percentage": 0.0,
            "installments": [
                {
                    "installment_number": i + 1,
                    "due_date": (today + timedelta(days=30 * (i + 1))).strftime("%Y-%m-%d"),
                    "amount": round(installment_short, 2),
                    "discount": 0.0
                }
                for i in range(num_installments_short)
            ],
            "interest_rate": 0.0,
            "total_interest": 0.0,
            "recommended": False,
            "requires_approval": total_debt > approval_threshold
        })
    
    if rating != "D" and max_installments > 3:
        num_installments_long = max_installments
        months = num_installments_long
        total_with_interest = total_debt * (1 + interest_rate) ** (months / 12)
        installment_long = total_with_interest / num_installments_long
        
        if installment_long >= min_installment_amount:
            scenarios.append({
                "scenario_id": str(uuid.uuid4()),
                "name": f"Parcelamento em {num_installments_long}x com Juros",
                "type": "installment_with_interest",
                "total_amount": round(total_with_interest, 2),
                "original_amount": round(total_debt, 2),
                "discount_amount": 0.0,
                "discount_percentage": 0.0,
                "installments": [
                    {
                        "installment_number": i + 1,
                        "due_date": (today + timedelta(days=30 * (i + 1))).strftime("%Y-%m-%d"),
                        "amount": round(installment_long, 2),
                        "discount": 0.0
                    }
                    for i in range(num_installments_long)
                ],
                "interest_rate": round(interest_rate * 100, 2),
                "total_interest": round(total_with_interest - total_debt, 2),
                "recommended": False,
                "requires_approval": total_with_interest > approval_threshold
            })
    
    return scenarios


def validate_scenario(
    scenario_id: str,
    customer_id: str,
    scenarios: List[dict]
) -> dict:
    """
    Valida se um cenário ainda está dentro das regras
    
    Returns:
        dict com valid, requires_approval, reasons, warnings
    """
    scenario = next((s for s in scenarios if s["scenario_id"] == scenario_id), None)
    
    if not scenario:
        return {
            "valid": False,
            "requires_approval": False,
            "reasons": ["Cenário não encontrado"],
            "warnings": []
        }
    
    reasons = []
    warnings = []
    requires_approval = scenario.get("requires_approval", False)
    
    if requires_approval:
        reasons.append("Este cenário requer aprovação humana")
    
    if scenario.get("discount_percentage", 0) > 5:
        warnings.append("Desconto acima de 5% requer aprovação")
    
    return {
        "valid": True,
        "requires_approval": requires_approval,
        "reasons": reasons,
        "warnings": warnings
    }
