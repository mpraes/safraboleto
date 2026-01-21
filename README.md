# SafraBoleto - Agente de Renegociação e Cobrança Digital B2B

Sistema de automação de cobrança e renegociação B2B para empresas do agronegócio, utilizando agentes de IA para interagir com clientes e facilitar o processo de negociação de faturas em aberto.

## 📋 Sobre o Projeto

O SafraBoleto é uma solução que automatiza o contato inicial e recorrente de cobrança B2B por canais digitais, permitindo que clientes empresariais consultem faturas em aberto, negociem opções de pagamento dentro das regras de crédito e gerem boletos/PIX de forma autônoma.

### Objetivos

- Automatizar cobrança B2B por canais digitais (portal web, WhatsApp, e-mail)
- Permitir que clientes consultem e negociem faturas em aberto
- Gerar boletos e PIX automaticamente após acordo
- Preservar relacionamento com tom respeitoso e empático
- Reduzir prazo médio de recebimento (PMR)

## 🚀 Como Começar

### Pré-requisitos

- Python 3.10 ou superior
- [uv](https://github.com/astral-sh/uv) (gerenciador de dependências)

### Instalação

1. Clone o repositório:
```bash
git clone <url-do-repositorio>
cd safraboleto
```

2. Crie o ambiente virtual e instale as dependências:
```bash
uv venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows

uv sync
```

### Executando os Sistemas Externos

Os sistemas externos (APIs mock) podem ser executados independentemente:

```bash
# Serviço ERP (Porta 8001)
cd integrations/erp_service
uv run python main.py

# Serviço de Pagamentos (Porta 8002)
cd integrations/payment_service
uv run python main.py

# Motor de Regras de Crédito (Porta 8003)
cd integrations/credit_service
uv run python main.py

# Serviço de Notificações (Porta 8004)
cd integrations/notification_service
uv run python main.py

# Session Store (Porta 8005)
cd integrations/session_service
uv run python main.py

# Serviço de Logging (Porta 8006)
cd integrations/logging_service
uv run python main.py
```

Cada serviço expõe documentação automática em:
- Swagger UI: `http://localhost:PORT/docs`
- Health check: `http://localhost:PORT/health`

## 📁 Estrutura do Projeto

```
safraboleto/
├── integrations/          # Sistemas externos (APIs mock)
│   ├── erp_service/       # Porta 8001 - Clientes, faturas e acordos
│   ├── payment_service/   # Porta 8002 - Boletos e PIX
│   ├── credit_service/    # Porta 8003 - Regras de crédito
│   ├── notification_service/ # Porta 8004 - Notificações
│   ├── session_service/   # Porta 8005 - Armazenamento de sessões
│   └── logging_service/   # Porta 8006 - Logging de interações
├── backend/              # Aplicação backend principal (a criar)
├── frontend/             # Aplicação frontend (a criar)
├── docker/               # Infraestrutura Docker (a criar)
├── docs/                 # Documentação
│   ├── requisitos.md     # Requisitos e especificações
│   └── cnpomapa30092019.xlsx  # Dados de referência para mock
├── pyproject.toml        # Dependências do projeto
└── README.md
```

## 🔧 Sistemas Externos

### 1. Serviço ERP Financeiro (Porta 8001)

API mock que simula o sistema ERP de contas a receber.

**Endpoints principais:**
- `GET /customers/{cnpj}` - Busca cliente por CNPJ
- `GET /customers/{customer_id}/invoices` - Lista faturas do cliente
- `POST /agreements` - Cria acordo de renegociação
- `GET /agreements/{agreement_id}` - Consulta status do acordo

**Dados mock:** Serão gerados a partir do arquivo `docs/cnpomapa30092019.xlsx`

### 2. Serviço de Pagamentos (Porta 8002)

API mock para geração de boletos e PIX.

**Endpoints principais:**
- `POST /payments/boleto` - Gera boleto bancário
- `POST /payments/pix` - Gera cobrança PIX
- `GET /payments/{payment_id}/status` - Consulta status do pagamento

### 3. Motor de Regras de Crédito (Porta 8003)

API que gera cenários de renegociação baseados em regras de crédito.

**Endpoints principais:**
- `POST /credit-rules/generate-options` - Gera cenários de renegociação
- `POST /credit-rules/validate-scenario` - Valida cenário escolhido

**Regras:** Configuradas em `integrations/credit_service/config/credit_rules.json`

### 4. Serviço de Notificações (Porta 8004)

API mock para simular envio de mensagens (WhatsApp, SMS, Email).

**Endpoints principais:**
- `POST /notifications/send` - Envia notificação
- `GET /notifications/{notification_id}/status` - Consulta status

### 5. Session Store (Porta 8005)

Armazena estado da sessão do agente.

**Endpoints principais:**
- `POST /sessions` - Cria sessão
- `GET /sessions/{session_id}` - Recupera sessão
- `PUT /sessions/{session_id}` - Atualiza sessão
- `DELETE /sessions/{session_id}` - Remove sessão

### 6. Serviço de Logging (Porta 8006)

Registra interações e eventos do chatbot.

**Endpoints principais:**
- `POST /interactions/log` - Registra evento
- `GET /interactions/{customer_id}/history` - Histórico do cliente

## 🛠️ Desenvolvimento

### Comandos Úteis

```bash
# Instalar dependências
uv sync

# Executar testes
pytest

# Verificar lint
ruff check .

# Formatar código
ruff format .

# Executar serviço específico
cd integrations/erp_service
uv run python main.py
```

### Adicionando Novas Dependências

```bash
# Adicionar dependência
uv add nome-do-pacote

# Adicionar dependência de desenvolvimento
uv add --dev nome-do-pacote
```

## 📚 Documentação

- **Requisitos completos:** Ver `docs/requisitos.md`
- **Especificações técnicas:** Cada serviço tem documentação Swagger em `/docs`
- **Dados de referência:** `docs/cnpomapa30092019.xlsx` (usado para gerar dados mock)

## 🎯 Status do Projeto

### ✅ Concluído

- [x] Estrutura de sistemas externos criada
- [x] Modelos de dados definidos
- [x] Estrutura de routers criada
- [x] Documentação de requisitos organizada

### ⏳ Em Progresso

- [ ] Implementação dos endpoints dos serviços
- [ ] Geração de dados mock do xlsx
- [ ] Integração com LangGraph agent
- [ ] Implementação do backend principal
- [ ] Implementação do frontend

## 📝 Licença

[Adicionar licença quando aplicável]

## 🤝 Contribuindo

[Adicionar guia de contribuição quando aplicável]
