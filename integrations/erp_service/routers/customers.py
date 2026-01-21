"""
Router para endpoints de clientes
"""
from fastapi import APIRouter, HTTPException
from typing import Optional

router = APIRouter(prefix="/customers", tags=["customers"])

# TODO: Implementar endpoints
# GET /customers/{cnpj}
# GET /customers/{customer_id}/invoices

@router.get("/{cnpj}")
async def get_customer_by_cnpj(cnpj: str):
    """Busca cliente por CNPJ"""
    # TODO: Carregar dados de mock_data/customers.json
    raise HTTPException(status_code=501, detail="Não implementado ainda")

@router.get("/{customer_id}/invoices")
async def get_customer_invoices(
    customer_id: str,
    status: Optional[str] = "open,overdue",
    due_date_from: Optional[str] = None,
    due_date_to: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    safra: Optional[str] = None,
    contract_id: Optional[str] = None
):
    """Lista faturas do cliente com filtros"""
    # TODO: Carregar dados de mock_data/invoices.json e filtrar
    raise HTTPException(status_code=501, detail="Não implementado ainda")
