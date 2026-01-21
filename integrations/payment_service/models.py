"""
Modelos Pydantic para o serviço de pagamentos
"""
from pydantic import BaseModel
from typing import Optional

class PayerInfo(BaseModel):
    name: str
    cnpj: str
    address: Optional[str] = None

class GenerateBoletoRequest(BaseModel):
    invoice_id: Optional[str] = None
    installment_id: Optional[str] = None
    amount: float
    due_date: str
    payer_info: PayerInfo
    description: str

class GeneratePixRequest(BaseModel):
    invoice_id: Optional[str] = None
    installment_id: Optional[str] = None
    amount: float
    due_date: str
    payer_info: PayerInfo
    description: str

class PaymentResponse(BaseModel):
    payment_id: str
    type: str  # boleto ou pix
    amount: float
    due_date: str
    created_at: str
    expires_at: str
    # Campos específicos de boleto
    barcode: Optional[str] = None
    digitable_line: Optional[str] = None
    pdf_url: Optional[str] = None
    # Campos específicos de PIX
    pix_key: Optional[str] = None
    qr_code_url: Optional[str] = None
    qr_code_base64: Optional[str] = None

class PaymentStatus(BaseModel):
    payment_id: str
    status: str  # pending, paid, expired, cancelled
    paid_at: Optional[str] = None
    paid_amount: Optional[float] = None
    payment_method: Optional[str] = None
