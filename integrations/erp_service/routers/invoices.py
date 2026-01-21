"""
Router para endpoints de faturas
"""
from fastapi import APIRouter

router = APIRouter(prefix="/invoices", tags=["invoices"])

# TODO: Implementar endpoints adicionais de faturas se necessário
