"""
Database configuration for PostgreSQL
"""
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Boolean, DateTime, Numeric, Integer, Text, Enum, ARRAY, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from enum import Enum as PyEnum

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://safraboleto:safraboleto123@localhost:5433/safraboleto"
)

engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class CustomerRating(PyEnum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class CustomerTier(PyEnum):
    Bronze = "Bronze"
    Prata = "Prata"
    Ouro = "Ouro"


class CustomerStatus(PyEnum):
    active = "active"
    inactive = "inactive"
    blocked = "blocked"


class ContactRole(PyEnum):
    COMPRADOR = "COMPRADOR"
    FINANCEIRO = "FINANCEIRO"
    GESTOR = "GESTOR"


class InvoiceStatus(PyEnum):
    open = "open"
    overdue = "overdue"
    paid = "paid"
    cancelled = "cancelled"


class AgreementStatus(PyEnum):
    rascunho = "rascunho"
    pendente_aprovacao = "pendente_aprovacao"
    aprovado = "aprovado"
    boletos_gerados = "boletos_gerados"
    concluido = "concluido"
    rejeitado = "rejeitado"
    cancelado = "cancelado"
    expirado = "expirado"


class PaymentType(PyEnum):
    boleto = "boleto"
    pix = "pix"


class PaymentStatus(PyEnum):
    pendente = "pendente"
    processando = "processando"
    confirmado = "confirmado"
    falhou = "falhou"
    cancelado = "cancelado"
    expirado = "expirado"


class NotificationChannel(PyEnum):
    whatsapp = "whatsapp"
    sms = "sms"
    email = "email"


class NotificationStatus(PyEnum):
    pending = "pending"
    sent = "sent"
    delivered = "delivered"
    read = "read"
    failed = "failed"


class InteractionEventType(PyEnum):
    proposal_presented = "proposal_presented"
    proposal_accepted = "proposal_accepted"
    proposal_rejected = "proposal_rejected"
    escalation = "escalation"
    agreement_created = "agreement_created"
    payment_generated = "payment_generated"
    session_started = "session_started"
    session_ended = "session_ended"


class Customer(Base):
    __tablename__ = "customers"
    
    customer_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cnpj = Column(String(14), unique=True, nullable=False)
    company_name = Column(String(255), nullable=False)
    rating = Column(Enum(CustomerRating), nullable=False, default=CustomerRating.B)
    tier = Column(Enum(CustomerTier), nullable=False, default=CustomerTier.Bronze)
    credit_limit = Column(Numeric(15, 2), nullable=False, default=0)
    current_balance = Column(Numeric(15, 2), nullable=False, default=0)
    business_segment = Column(String(100))
    status = Column(Enum(CustomerStatus), nullable=False, default=CustomerStatus.active)
    registration_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_payment_date = Column(DateTime)
    payment_history_score = Column(Integer, nullable=False, default=50)
    volume_annual = Column(Numeric(15, 2), nullable=False, default=0)
    days_without_delay = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Address(Base):
    __tablename__ = "addresses"
    
    address_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), nullable=False)
    street = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(2), nullable=False)
    zipcode = Column(String(8), nullable=False)
    complement = Column(String(100))
    is_primary = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class Contact(Base):
    __tablename__ = "contacts"
    
    contact_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    role = Column(Enum(ContactRole), nullable=False, default=ContactRole.COMPRADOR)
    is_primary = Column(Boolean, nullable=False, default=False)
    permissions = Column(JSON, default=[])
    last_interaction = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Invoice(Base):
    __tablename__ = "invoices"
    
    invoice_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), nullable=False)
    invoice_number = Column(String(50), nullable=False)
    due_date = Column(DateTime, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    amount_paid = Column(Numeric(15, 2), nullable=False, default=0)
    status = Column(Enum(InvoiceStatus), nullable=False, default=InvoiceStatus.open)
    days_overdue = Column(Integer, nullable=False, default=0)
    safra = Column(String(50))
    contract_id = Column(String(50))
    description = Column(Text)
    interest_rate = Column(Numeric(5, 4), nullable=False, default=0.01)
    fine_rate = Column(Numeric(5, 4), nullable=False, default=0.02)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    paid_at = Column(DateTime)


class Agreement(Base):
    __tablename__ = "agreements"
    
    agreement_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), nullable=False)
    invoice_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False)
    agreement_type = Column(String(50), nullable=False)
    status = Column(Enum(AgreementStatus), nullable=False, default=AgreementStatus.rascunho)
    total_amount = Column(Numeric(15, 2), nullable=False)
    original_amount = Column(Numeric(15, 2), nullable=False)
    discount_amount = Column(Numeric(15, 2), nullable=False, default=0)
    discount_percentage = Column(Numeric(5, 2), nullable=False, default=0)
    interest_rate = Column(Numeric(5, 4), nullable=False, default=0)
    total_interest = Column(Numeric(15, 2), nullable=False, default=0)
    requires_approval = Column(Boolean, nullable=False, default=False)
    approved_by = Column(String(255))
    approval_reason = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_at = Column(DateTime)
    expires_at = Column(DateTime)
    completed_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    cancellation_reason = Column(Text)
    session_metadata = Column(JSON, default={})


class AgreementInstallment(Base):
    __tablename__ = "agreement_installments"
    
    installment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agreement_id = Column(UUID(as_uuid=True), nullable=False)
    installment_number = Column(Integer, nullable=False)
    due_date = Column(DateTime, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    discount = Column(Numeric(15, 2), nullable=False, default=0)
    status = Column(Enum(InvoiceStatus), nullable=False, default=InvoiceStatus.open)
    paid_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class Payment(Base):
    __tablename__ = "payments"
    
    payment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True))
    installment_id = Column(UUID(as_uuid=True))
    agreement_id = Column(UUID(as_uuid=True))
    type = Column(Enum(PaymentType), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    due_date = Column(DateTime, nullable=False)
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.pendente)
    barcode = Column(String(100))
    digitable_line = Column(String(100))
    pdf_url = Column(String(500))
    pix_key = Column(String(100))
    qr_code_url = Column(String(500))
    qr_code_base64 = Column(Text)
    webhook_url = Column(String(500))
    webhook_attempts = Column(Integer, nullable=False, default=0)
    paid_at = Column(DateTime)
    paid_amount = Column(Numeric(15, 2))
    payment_method = Column(String(50))
    confirmation_code = Column(String(100))
    failure_reason = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime)


class Session(Base):
    __tablename__ = "sessions"
    
    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), nullable=False)
    contact_id = Column(UUID(as_uuid=True))
    channel = Column(String(50), nullable=False, default="web")
    status = Column(String(50), nullable=False, default="active")
    state_data = Column(JSON, default={})
    selected_invoice_ids = Column(ARRAY(UUID(as_uuid=True)), default=[])
    session_constraints = Column(JSON, default={})
    proposals_presented = Column(JSON, default=[])
    context_data = Column(JSON, default={})
    last_interaction_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime)


class Notification(Base):
    __tablename__ = "notifications"
    
    notification_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True))
    session_id = Column(UUID(as_uuid=True))
    channel = Column(Enum(NotificationChannel), nullable=False)
    template = Column(String(100), nullable=False)
    recipient_name = Column(String(255), nullable=False)
    recipient_phone = Column(String(20))
    recipient_email = Column(String(255))
    variables = Column(JSON, default={})
    attachments = Column(JSON, default=[])
    status = Column(Enum(NotificationStatus), nullable=False, default=NotificationStatus.pending)
    message_id = Column(String(255))
    error_message = Column(Text)
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    read_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Interaction(Base):
    __tablename__ = "interactions"
    
    interaction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), nullable=False)
    customer_id = Column(UUID(as_uuid=True), nullable=False)
    event_type = Column(Enum(InteractionEventType), nullable=False)
    event_data = Column(JSON, default={})
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class CreditRulesConfig(Base):
    __tablename__ = "credit_rules_config"
    
    config_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rating = Column(Enum(CustomerRating), nullable=False, unique=True)
    min_interest_rate = Column(Numeric(5, 4), nullable=False)
    max_interest_rate = Column(Numeric(5, 4), nullable=False)
    approval_threshold = Column(Numeric(15, 2), nullable=False)
    max_discount_auto = Column(Numeric(5, 2), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class TierConfig(Base):
    __tablename__ = "tier_config"
    
    config_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tier = Column(Enum(CustomerTier), nullable=False, unique=True)
    payment_days_limit = Column(Integer, nullable=False)
    credit_limit = Column(Numeric(15, 2), nullable=False)
    max_installments = Column(Integer, nullable=False)
    max_discount_auto = Column(Numeric(5, 2), nullable=False)
    min_interest_rate = Column(Numeric(5, 4), nullable=False)
    max_interest_rate = Column(Numeric(5, 4), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


async def get_db_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session
