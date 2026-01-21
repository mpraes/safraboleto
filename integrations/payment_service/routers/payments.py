"""
Router para endpoints de pagamentos
"""
from fastapi import APIRouter, HTTPException
from ..models import GenerateBoletoRequest, GeneratePixRequest, PaymentResponse, PaymentStatus

router = APIRouter(prefix="/payments", tags=["payments"])

# TODO: Implementar endpoints
# POST /payments/boleto
# POST /payments/pix
# GET /payments/{payment_id}/status

@router.post("/boleto", response_model=PaymentResponse)
async def generate_boleto(request: GenerateBoletoRequest):
    """Gera boleto bancário"""
    raise HTTPException(status_code=501, detail="Não implementado ainda")

@router.post("/pix", response_model=PaymentResponse)
async def generate_pix(request: GeneratePixRequest):
    """Gera cobrança PIX"""
    raise HTTPException(status_code=501, detail="Não implementado ainda")

@router.get("/{payment_id}/status", response_model=PaymentStatus)
async def get_payment_status(payment_id: str):
    """Consulta status de um pagamento"""
    raise HTTPException(status_code=501, detail="Não implementado ainda")
