-- SafraBoleto Database Schema
-- PostgreSQL 15

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- ENUMS
-- ============================================

CREATE TYPE customer_rating AS ENUM ('A', 'B', 'C', 'D');
CREATE TYPE customer_tier AS ENUM ('Bronze', 'Prata', 'Ouro');
CREATE TYPE customer_status AS ENUM ('active', 'inactive', 'blocked');
CREATE TYPE contact_role AS ENUM ('COMPRADOR', 'FINANCEIRO', 'GESTOR');
CREATE TYPE invoice_status AS ENUM ('open', 'overdue', 'paid', 'cancelled');
CREATE TYPE agreement_status AS ENUM ('rascunho', 'pendente_aprovacao', 'aprovado', 'boletos_gerados', 'concluido', 'rejeitado', 'cancelado', 'expirado');
CREATE TYPE payment_type AS ENUM ('boleto', 'pix');
CREATE TYPE payment_status AS ENUM ('pendente', 'processando', 'confirmado', 'falhou', 'cancelado', 'expirado');
CREATE TYPE notification_channel AS ENUM ('whatsapp', 'sms', 'email');
CREATE TYPE notification_status AS ENUM ('pending', 'sent', 'delivered', 'read', 'failed');
CREATE TYPE interaction_event_type AS ENUM ('proposal_presented', 'proposal_accepted', 'proposal_rejected', 'escalation', 'agreement_created', 'payment_generated', 'session_started', 'session_ended');

-- ============================================
-- CUSTOMERS
-- ============================================

CREATE TABLE customers (
    customer_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cnpj VARCHAR(14) UNIQUE NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    rating customer_rating NOT NULL DEFAULT 'B',
    tier customer_tier NOT NULL DEFAULT 'Bronze',
    credit_limit DECIMAL(15, 2) NOT NULL DEFAULT 0,
    current_balance DECIMAL(15, 2) NOT NULL DEFAULT 0,
    business_segment VARCHAR(100),
    status customer_status NOT NULL DEFAULT 'active',
    registration_date DATE NOT NULL DEFAULT CURRENT_DATE,
    last_payment_date DATE,
    payment_history_score INTEGER NOT NULL DEFAULT 50,
    volume_annual DECIMAL(15, 2) NOT NULL DEFAULT 0,
    days_without_delay INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_customers_cnpj ON customers(cnpj);
CREATE INDEX idx_customers_rating ON customers(rating);
CREATE INDEX idx_customers_tier ON customers(tier);
CREATE INDEX idx_customers_status ON customers(status);

-- ============================================
-- ADDRESSES
-- ============================================

CREATE TABLE addresses (
    address_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    street VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(2) NOT NULL,
    zipcode VARCHAR(8) NOT NULL,
    complement VARCHAR(100),
    is_primary BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_addresses_customer ON addresses(customer_id);

-- ============================================
-- CONTACTS
-- ============================================

CREATE TABLE contacts (
    contact_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    role contact_role NOT NULL DEFAULT 'COMPRADOR',
    is_primary BOOLEAN NOT NULL DEFAULT false,
    permissions JSONB DEFAULT '[]',
    last_interaction TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_contacts_customer ON contacts(customer_id);
CREATE INDEX idx_contacts_role ON contacts(role);
CREATE INDEX idx_contacts_email ON contacts(email);

-- ============================================
-- INVOICES
-- ============================================

CREATE TABLE invoices (
    invoice_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    invoice_number VARCHAR(50) NOT NULL,
    due_date DATE NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    amount_paid DECIMAL(15, 2) NOT NULL DEFAULT 0,
    status invoice_status NOT NULL DEFAULT 'open',
    days_overdue INTEGER NOT NULL DEFAULT 0,
    safra VARCHAR(50),
    contract_id VARCHAR(50),
    description TEXT,
    interest_rate DECIMAL(5, 4) NOT NULL DEFAULT 0.01,
    fine_rate DECIMAL(5, 4) NOT NULL DEFAULT 0.02,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    paid_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(customer_id, invoice_number)
);

CREATE INDEX idx_invoices_customer ON invoices(customer_id);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_due_date ON invoices(due_date);
CREATE INDEX idx_invoices_safra ON invoices(safra);

-- ============================================
-- AGREEMENTS
-- ============================================

CREATE TABLE agreements (
    agreement_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    invoice_ids UUID[] NOT NULL,
    agreement_type VARCHAR(50) NOT NULL,
    status agreement_status NOT NULL DEFAULT 'rascunho',
    total_amount DECIMAL(15, 2) NOT NULL,
    original_amount DECIMAL(15, 2) NOT NULL,
    discount_amount DECIMAL(15, 2) NOT NULL DEFAULT 0,
    discount_percentage DECIMAL(5, 2) NOT NULL DEFAULT 0,
    interest_rate DECIMAL(5, 4) NOT NULL DEFAULT 0,
    total_interest DECIMAL(15, 2) NOT NULL DEFAULT 0,
    requires_approval BOOLEAN NOT NULL DEFAULT false,
    approved_by VARCHAR(255),
    approval_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    approved_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    cancellation_reason TEXT,
    session_metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_agreements_customer ON agreements(customer_id);
CREATE INDEX idx_agreements_status ON agreements(status);
CREATE INDEX idx_agreements_created ON agreements(created_at);

-- ============================================
-- AGREEMENT HISTORY
-- ============================================

CREATE TABLE agreement_history (
    history_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agreement_id UUID NOT NULL REFERENCES agreements(agreement_id) ON DELETE CASCADE,
    previous_status agreement_status,
    new_status agreement_status NOT NULL,
    changed_by VARCHAR(255),
    reason TEXT,
    context JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agreement_history_agreement ON agreement_history(agreement_id);

-- ============================================
-- AGREEMENT INSTALLMENTS
-- ============================================

CREATE TABLE agreement_installments (
    installment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agreement_id UUID NOT NULL REFERENCES agreements(agreement_id) ON DELETE CASCADE,
    installment_number INTEGER NOT NULL,
    due_date DATE NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    discount DECIMAL(15, 2) NOT NULL DEFAULT 0,
    status invoice_status NOT NULL DEFAULT 'open',
    paid_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(agreement_id, installment_number)
);

CREATE INDEX idx_installments_agreement ON agreement_installments(agreement_id);
CREATE INDEX idx_installments_status ON agreement_installments(status);

-- ============================================
-- PAYMENTS
-- ============================================

CREATE TABLE payments (
    payment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id UUID REFERENCES invoices(invoice_id) ON DELETE SET NULL,
    installment_id UUID REFERENCES agreement_installments(installment_id) ON DELETE SET NULL,
    agreement_id UUID REFERENCES agreements(agreement_id) ON DELETE SET NULL,
    type payment_type NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    due_date DATE NOT NULL,
    status payment_status NOT NULL DEFAULT 'pendente',
    barcode VARCHAR(100),
    digitable_line VARCHAR(100),
    pdf_url VARCHAR(500),
    pix_key VARCHAR(100),
    qr_code_url VARCHAR(500),
    qr_code_base64 TEXT,
    webhook_url VARCHAR(500),
    webhook_attempts INTEGER NOT NULL DEFAULT 0,
    paid_at TIMESTAMP WITH TIME ZONE,
    paid_amount DECIMAL(15, 2),
    payment_method VARCHAR(50),
    confirmation_code VARCHAR(100),
    failure_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_payments_invoice ON payments(invoice_id);
CREATE INDEX idx_payments_installment ON payments(installment_id);
CREATE INDEX idx_payments_agreement ON payments(agreement_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_type ON payments(type);

-- ============================================
-- PAYMENT HISTORY
-- ============================================

CREATE TABLE payment_history (
    history_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    payment_id UUID NOT NULL REFERENCES payments(payment_id) ON DELETE CASCADE,
    previous_status payment_status,
    new_status payment_status NOT NULL,
    reason TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_payment_history_payment ON payment_history(payment_id);

-- ============================================
-- SESSIONS
-- ============================================

CREATE TABLE sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    contact_id UUID REFERENCES contacts(contact_id) ON DELETE SET NULL,
    channel VARCHAR(50) NOT NULL DEFAULT 'web',
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    state_data JSONB DEFAULT '{}',
    selected_invoice_ids UUID[] DEFAULT '{}',
    session_constraints JSONB DEFAULT '{}',
    proposals_presented JSONB DEFAULT '[]',
    context_data JSONB DEFAULT '{}',
    last_interaction_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_sessions_customer ON sessions(customer_id);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);

-- ============================================
-- NOTIFICATIONS
-- ============================================

CREATE TABLE notifications (
    notification_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID REFERENCES customers(customer_id) ON DELETE SET NULL,
    session_id UUID REFERENCES sessions(session_id) ON DELETE SET NULL,
    channel notification_channel NOT NULL,
    template VARCHAR(100) NOT NULL,
    recipient_name VARCHAR(255) NOT NULL,
    recipient_phone VARCHAR(20),
    recipient_email VARCHAR(255),
    variables JSONB DEFAULT '{}',
    attachments JSONB DEFAULT '[]',
    status notification_status NOT NULL DEFAULT 'pending',
    message_id VARCHAR(255),
    error_message TEXT,
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    read_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notifications_customer ON notifications(customer_id);
CREATE INDEX idx_notifications_status ON notifications(status);
CREATE INDEX idx_notifications_channel ON notifications(channel);

-- ============================================
-- INTERACTIONS (LOGGING)
-- ============================================

CREATE TABLE interactions (
    interaction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    customer_id UUID NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    event_type interaction_event_type NOT NULL,
    event_data JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_interactions_session ON interactions(session_id);
CREATE INDEX idx_interactions_customer ON interactions(customer_id);
CREATE INDEX idx_interactions_event_type ON interactions(event_type);
CREATE INDEX idx_interactions_created ON interactions(created_at);

-- ============================================
-- CREDIT RULES CONFIG
-- ============================================

CREATE TABLE credit_rules_config (
    config_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rating customer_rating NOT NULL UNIQUE,
    min_interest_rate DECIMAL(5, 4) NOT NULL,
    max_interest_rate DECIMAL(5, 4) NOT NULL,
    approval_threshold DECIMAL(15, 2) NOT NULL,
    max_discount_auto DECIMAL(5, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

INSERT INTO credit_rules_config (rating, min_interest_rate, max_interest_rate, approval_threshold, max_discount_auto) VALUES
('A', 0.0000, 0.0250, 200000.00, 5.0),
('B', 0.0150, 0.0330, 150000.00, 4.0),
('C', 0.0250, 0.0500, 100000.00, 2.0),
('D', 0.0330, 0.1000, 50000.00, 0.0);

-- ============================================
-- TIER CONFIG
-- ============================================

CREATE TABLE tier_config (
    config_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tier customer_tier NOT NULL UNIQUE,
    payment_days_limit INTEGER NOT NULL,
    credit_limit DECIMAL(15, 2) NOT NULL,
    max_installments INTEGER NOT NULL,
    max_discount_auto DECIMAL(5, 2) NOT NULL,
    min_interest_rate DECIMAL(5, 4) NOT NULL,
    max_interest_rate DECIMAL(5, 4) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

INSERT INTO tier_config (tier, payment_days_limit, credit_limit, max_installments, max_discount_auto, min_interest_rate, max_interest_rate) VALUES
('Ouro', 60, 500000.00, 6, 5.0, 0.0000, 0.0250),
('Prata', 45, 200000.00, 4, 3.0, 0.0150, 0.0330),
('Bronze', 30, 100000.00, 3, 1.0, 0.0250, 0.0500);

-- ============================================
-- FUNCTIONS
-- ============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE OR REPLACE FUNCTION update_days_overdue()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status IN ('open', 'overdue') AND NEW.due_date < CURRENT_DATE THEN
        NEW.days_overdue = CURRENT_DATE - NEW.due_date;
    ELSE
        NEW.days_overdue = 0;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers for updated_at
CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_contacts_updated_at BEFORE UPDATE ON contacts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_invoices_updated_at BEFORE UPDATE ON invoices FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_invoices_days_overdue BEFORE INSERT OR UPDATE ON invoices FOR EACH ROW EXECUTE FUNCTION update_days_overdue();
CREATE TRIGGER update_agreements_updated_at BEFORE UPDATE ON agreements FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_payments_updated_at BEFORE UPDATE ON payments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_notifications_updated_at BEFORE UPDATE ON notifications FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_credit_rules_config_updated_at BEFORE UPDATE ON credit_rules_config FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_tier_config_updated_at BEFORE UPDATE ON tier_config FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- VIEWS
-- ============================================

CREATE VIEW v_customer_summary AS
SELECT 
    c.customer_id,
    c.cnpj,
    c.company_name,
    c.rating,
    c.tier,
    c.credit_limit,
    c.current_balance,
    c.status,
    COUNT(DISTINCT i.invoice_id) AS total_invoices,
    COALESCE(SUM(CASE WHEN i.status IN ('open', 'overdue') THEN i.amount ELSE 0 END), 0) AS open_amount,
    COALESCE(SUM(CASE WHEN i.status = 'overdue' THEN i.amount ELSE 0 END), 0) AS overdue_amount,
    MAX(i.due_date) AS latest_due_date
FROM customers c
LEFT JOIN invoices i ON c.customer_id = i.customer_id
GROUP BY c.customer_id;

CREATE VIEW v_overdue_invoices AS
SELECT 
    i.*,
    c.cnpj,
    c.company_name,
    c.rating,
    c.tier
FROM invoices i
JOIN customers c ON i.customer_id = c.customer_id
WHERE i.status = 'overdue'
ORDER BY i.days_overdue DESC;

CREATE VIEW v_active_sessions AS
SELECT 
    s.*,
    c.cnpj,
    c.company_name,
    co.name AS contact_name,
    co.role AS contact_role
FROM sessions s
JOIN customers c ON s.customer_id = c.customer_id
LEFT JOIN contacts co ON s.contact_id = co.contact_id
WHERE s.status = 'active' AND (s.expires_at IS NULL OR s.expires_at > NOW())
ORDER BY s.last_interaction_at DESC;
