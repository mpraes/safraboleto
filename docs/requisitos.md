# Agente de Renegociação e Cobrança Digital B2B (Agronegócio)

## 1. Contexto e objetivo

- Segmento-alvo: empresas do agronegócio que vendem insumos/serviços para outras empresas (revendas, cooperativas, produtores PJ etc.).
- Problema: alto volume de boletos em aberto, cobrança manual (telefone/e-mail), perda de histórico de tratativas e baixa previsibilidade de recebimentos. [web:26][web:33]
- Objetivo do agente:
  - Automatizar o contato inicial e recorrente de cobrança B2B por canais digitais (WhatsApp, portal, e-mail com link de chat). [web:27][web:31]. Iniciar com a feature somente com portal webapp primeiro para poder usar rapidamente, após isso partir para outros canais.
  - Permitir que o próprio cliente empresarial consulte faturas em aberto, negocie opções de pagamento dentro das regras de crédito e gere os boletos/PIX. [web:28][web:39]
  - Preservar relacionamento (tom respeitoso, empático, não agressivo) e reduzir prazo médio de recebimento (PMR). [web:26][web:30]

## 2. Atores e personas

- Credor (empresa agro):
  - CFO / gestor financeiro.
  - Time de contas a receber / cobrança.
  - Equipe comercial (que acompanha situação de clientes-chave).
- Devedor (cliente B2B):
  - Responsável financeiro/contas a pagar da empresa compradora.
  - Dono/gestor (em pequenas operações rurais).
- Sistemas:
  - ERP financeiro / módulo de contas a receber.
  - Gateway de pagamentos (boleto, PIX, eventualmente cartão). [web:28][web:35]
  - CRM / sistema de relacionamento (opcional).

## 3. Escopo funcional (MVP)

### 3.1. Jornada principal – cliente chega com “preciso do boleto” / “quero negociar”

1. Identificação/autenticação:
   - Entrada por link com token, QR em boleto, botão no e-mail de cobrança ou mensagem de WhatsApp iniciada pela régua de cobrança. [web:27][web:36]
   - Validações mínimas: CNPJ + número de fatura, ou CNPJ + código do cliente, ou link autenticado.
   - Armazenar no estado do agente: `company_id`, `cnpj`, `contact_name`, `channel`, `validated` (bool).

2. Consulta de posições em aberto:
   - Listar faturas/boletos abertos, vencidos e a vencer para aquela empresa. [web:26][web:28]
   - Permitir filtros: por data de vencimento, por valor, por safra/contrato.
   - Armazenar no estado: lista resumida de faturas relevantes na sessão (`open_invoices_session`).

3. Seleção de faturas para tratamento:
   - Usuário pode:
     - Pedir um boleto específico.
     - Selecionar várias faturas para “negociar em conjunto”.
   - Atualizar estado: `selected_invoices_ids`.

4. Opções de ação:
   - Gerar segunda via simples de boleto/PIX para pagamento à vista.
   - Solicitar renegociação (parcelamento, alongamento, desconto por pagamento rápido), conforme regras do credor. [web:30][web:31]
   - Encaminhar para atendimento humano quando ticket ultrapassar critérios (valor alto, cliente estratégico, limite de políticas). [web:27][web:33]

5. Propostas de renegociação automáticas:
   - Aplicar política de crédito definida (exemplos):
     - Máximo de X parcelas.
     - Valor mínimo de parcela.
     - Faixa de descontos permitida por faixa de atraso e rating do cliente. [web:33][web:30]
   - Gerar 2–3 cenários:
     - Cenário 1: pagamento à vista com pequeno desconto.
     - Cenário 2: parcelamento curto sem desconto.
     - Cenário 3: parcelamento mais longo com juros.
   - Armazenar no estado: `current_offer_set` (opções apresentadas, parâmetros).

6. Negociação na sessão (short-term memory):
   - Registrar preferências e restrições mencionadas pelo usuário:
     - "Não posso pagar nada esse mês."
     - "Consigo dar uma entrada de X."
     - "Preciso que todas fiquem para depois da colheita."
   - Atualizar o estado com `session_constraints` (capacidade de entrada, máximo mensal, janela de datas).
   - Recalcular propostas dentro dos limites das regras de crédito, usando o contexto da sessão para não repetir perguntas.

7. Fechamento do acordo:
   - Usuário escolhe um cenário e confirma.
   - Bot valida:
     - A política de crédito ainda é válida naquele momento (checar limite, restrições internas).
     - Se necessário, dispara fluxo de aprovação interna antes da confirmação (status “pendente aprovação”).
   - Ao aprovar:
     - Criar acordo no ERP / sistema de cobrança.
     - Gerar boletos/PIX para as parcelas acordadas. [web:28][web:39]
     - Enviar resumo do acordo (PDF, e-mail, mensagem no canal).

8. Pós-acordo:
   - Registrar no CRM/histórico: condições, data, canal, responsável pelo contato.
   - Disponibilizar ao cliente:
     - Consulta do status do acordo.
     - Reenvio de boleto/PIX.
   - Permitir “atualizar contato” (telefone/e-mail) com validação.

### 3.2. Fluxos auxiliares

- Consultar status de cobrança:
  - "Quais boletos já foram enviados?" / "Qual o status da minha renegociação?"
- Dúvidas frequentes:
  - Juros, multas, política de protesto, impacto em crédito, prazos.
- Escalada para humano:
  - Critérios de saída: valor acima de limite, cliente VIP, múltiplas tentativas de renegociação falha, indícios de conflito.

## 4. Requisitos de short-term memory e experiência

- A memória de curto prazo deve manter:
  - Empresa autenticada e representante (nome/contato).
  - Lista de faturas que o usuário está discutindo naquela sessão.
  - Restrições de negociação informadas pelo usuário (entrada máxima, limite mensal, datas preferenciais).
  - Propostas apresentadas e rejeitadas/ajustadas durante a conversa.
- TTL de sessão configurável (ex.: 30–60 minutos de inatividade).
- Privacidade:
  - Não “misturar” contextos de empresas diferentes.
  - Não reter frases sensíveis além do necessário para operar as regras de negócio (salvo quando explicitamente gravadas em histórico formal).
- Tom de voz:
  - Respeitoso, profissional, orientado para solução, ciente da natureza B2B (evitar tom “cobrador agressivo”). [web:26][web:33]

## 5. Requisitos não funcionais

- Segurança e LGPD:
  - Somente dados necessários para fins de cobrança e renegociação. [web:31][web:9]
  - Logs de conversa com pseudonimização quando possível.
  - Controle de acesso para usuários internos que visualizam acordos.
- Disponibilidade:
  - 24/7 para canal digital, com fallback para fila humana em horário comercial.
- Observabilidade:
  - Métricas: taxa de contato, taxa de conversão em acordo, ticket médio renegociado, tempo médio de sessão, desistências por etapa. [web:30][web:37]
- Canais:
  - WhatsApp (prioritário), webchat no portal B2B, link em e-mails de cobrança. [web:30][web:31]

## 5.1. Requisitos Funcionais (RF) e Regras de Negócio (RN) - Enterprise

### Requisitos Funcionais - Serviço ERP

**RF-ERP-01:** O sistema deve identificar automaticamente o papel do contato (Comprador, Financeiro, Gestor) e adaptar a linguagem e permissões de acesso conforme o papel identificado.

**RF-ERP-02:** O sistema deve suportar hierarquia de contatos, permitindo múltiplos contatos por cliente com papéis distintos e relacionamentos hierárquicos.

**RF-ERP-03:** O sistema deve classificar clientes em tiers (Bronze, Prata, Ouro) baseado em critérios de negócio (volume, histórico, rating) e aplicar condições comerciais diferenciadas por tier.

**RF-ERP-04:** O sistema deve rastrear o ciclo de vida completo de acordos, incluindo estados intermediários (Rascunho, Pendente Aprovação, Aprovado, Rejeitado, Cancelado).

### Requisitos Funcionais - Motor de Crédito

**RF-CREDIT-01:** O cálculo de dívida total deve utilizar juros compostos e multa pro-rata dia, calculados dinamicamente com base na data de vencimento e data atual, não valores estáticos pré-calculados.

**RF-CREDIT-02:** O sistema deve gerar cenários de renegociação dinâmicos considerando capacidade de pagamento informada na sessão, restrições de datas e políticas de crédito do cliente.

**RF-CREDIT-03:** O sistema deve validar alçadas de aprovação antes de confirmar acordos, verificando se o desconto ou condições negociadas ultrapassam os limites automáticos permitidos.

**RF-CREDIT-04:** O sistema deve recalcular propostas em tempo real durante a negociação, incorporando novas restrições informadas pelo cliente sem perder o contexto da sessão.

### Requisitos Funcionais - Serviço de Pagamentos

**RF-PAYMENT-01:** A confirmação de pagamento deve ser assíncrona via Webhook, simulando o comportamento real de gateways bancários com delay de 10-30 segundos.

**RF-PAYMENT-02:** O sistema deve implementar máquina de estados para pagamentos com transições validadas (Pendente → Processando → Confirmado/Falhou/Cancelado).

**RF-PAYMENT-03:** O sistema deve suportar retentativas de webhook em caso de falha na entrega da confirmação, simulando comportamento resiliente de sistemas bancários.

**RF-PAYMENT-04:** O sistema deve manter histórico completo de estados do pagamento, permitindo auditoria e rastreamento de todas as transições.

### Requisitos Funcionais - Session Service

**RF-SESSION-01:** O sistema deve implementar lógica de "Win-back" para clientes inativos há mais de 90 dias, aplicando estratégias de reengajamento automático quando detectado.

**RF-SESSION-02:** O sistema deve rastrear padrões de comportamento por sessão, incluindo tempo de resposta, taxa de conversão e pontos de abandono.

**RF-SESSION-03:** O sistema deve armazenar estado complexo da negociação, incluindo histórico de propostas apresentadas, restrições coletadas, preferências do cliente e contexto da conversa.

### Regras de Negócio - Motor de Crédito

**RN-CREDIT-01:** Descontos acima de 10% do valor total da dívida exigem aprovação humana simulada. O sistema deve marcar o acordo como "Pendente Aprovação" e aguardar confirmação antes de gerar boletos.

**RN-CREDIT-02:** Descontos entre 5% e 10% podem ser aprovados automaticamente para clientes com rating A ou B, mas requerem aprovação para rating C ou D.

**RN-CREDIT-03:** Clientes com rating D não podem receber descontos automáticos, independente do valor ou tempo de atraso.

**RN-CREDIT-04:** O cálculo de juros compostos deve considerar a taxa mensal definida pelo rating do cliente, aplicada sobre o valor original da fatura mais multa, com capitalização mensal.

**RN-CREDIT-05:** A multa deve ser calculada pro-rata dia, considerando o percentual de multa configurado e o número de dias de atraso desde a data de vencimento até a data de cálculo.

**RN-CREDIT-06:** O número máximo de parcelas permitidas deve respeitar o tier do cliente: Ouro (até 6 parcelas), Prata (até 4 parcelas), Bronze (até 3 parcelas).

**RN-CREDIT-07:** O valor mínimo de parcela deve ser respeitado conforme o rating do cliente, e nenhuma parcela pode ser inferior a R$ 1.000,00.

### Regras de Negócio - Serviço ERP

**RN-ERP-01:** Contatos com papel "Comprador" têm acesso limitado a consulta de faturas e geração de boletos, mas não podem iniciar renegociações.

**RN-ERP-02:** Contatos com papel "Financeiro" têm acesso completo, incluindo renegociação e criação de acordos.

**RN-ERP-03:** A linguagem do agente deve ser adaptada: para "Comprador" usar linguagem mais comercial e explicativa; para "Financeiro" usar linguagem mais técnica e direta.

**RN-ERP-04:** Clientes tier Ouro têm prazos de pagamento estendidos (até 60 dias) e limites de crédito maiores.

**RN-ERP-05:** Clientes tier Bronze têm prazos de pagamento reduzidos (até 30 dias) e condições mais restritivas.

### Regras de Negócio - Session Service

**RN-SESSION-01:** Clientes identificados como inativos há mais de 90 dias devem receber mensagem de win-back personalizada na próxima interação, oferecendo condições especiais de renegociação.

**RN-SESSION-02:** A estratégia de win-back deve considerar o histórico do cliente: clientes com histórico positivo devem receber ofertas mais generosas.

**RN-SESSION-03:** O TTL de sessão deve ser de 60 minutos de inatividade, após o qual o estado é persistido mas a sessão é marcada como inativa.

## 6. Integrações e artefatos/tooling para o LangGraph

### 6.1. Sistemas que devem existir (ou ser criados)

1. Serviço de ERP Financeiro / Contas a Receber (API)
   - Endpoints:
     - `GET /customers/{cnpj}`: dados cadastrais, rating, limites.
     - `GET /customers/{id}/invoices?status=open,overdue`: lista de títulos. [web:28]
     - `POST /agreements`: criar acordo de renegociação.
     - `GET /agreements/{id}`: status do acordo.
   - Responsável por ser a "fonte de verdade" dos títulos.

2. Serviço de Geração de Boletos/PIX
   - Endpoints:
     - `POST /payments/boleto`: gerar boleto para um título ou parcela.
     - `POST /payments/pix`: gerar chave dinâmica/cobrança PIX. [web:28][web:35]
   - Pode ser abstração sobre banco/gateway.

3. Motor de Regras de Crédito / Políticas de Renegociação
   - Entrada:
     - Perfil do cliente (rating, histórico de atraso, volume).
     - Lista de faturas selecionadas.
     - Restrições da sessão (capacidade de pagamento).
   - Saída:
     - Conjunto de cenários possíveis (parcelas, juros, descontos, datas).
   - Implementado como microserviço ou módulo interno versionado.

4. Serviço de Notificação / Comunicação
   - WhatsApp, SMS, e-mail:
     - Envio de mensagens transacionais (link para chat, acordos, boletos).
   - Integração com plataformas de messaging usadas pelo cliente.

5. Data Store de Sessão do Agente
   - Persistência leve de estado do grafo por sessão (ex.: Redis, Dynamo, etc.).
   - Armazena:
     - Estado serializado da short-term memory para retomada de fluxo se necessário.

### 6.2. Tools (interfaces) para o agente LangGraph

Cada tool será um nó de ação no grafo, com schema bem definido:

- `lookup_customer_by_cnpj_tool`
  - Entrada: `cnpj`.
  - Saída: `customer_id`, `rating`, `limits`, `contacts`.
- `list_open_invoices_tool`
  - Entrada: `customer_id`.
  - Saída: lista de faturas (`invoice_id`, `due_date`, `amount`, `safra/contrato`).
- `generate_payment_options_tool`
  - Entrada: `customer_id`, `selected_invoices`, `session_constraints`.
  - Saída: lista de cenários de renegociação.
- `create_agreement_tool`
  - Entrada: cenário escolhido + metadados da sessão.
  - Saída: `agreement_id`, plano de parcelas.
- `issue_boletos_pix_tool`
  - Entrada: `agreement_id` ou lista de parcelas.
  - Saída: links/linha digitável/QR codes.
- `send_notification_tool`
  - Entrada: canal, contato, conteúdo, anexos (PDF, links).
- `log_interaction_tool`
  - Registro de eventos relevantes (apresentação de propostas, aceite, recusa, escalada).

## 7. Visão de grafo (alto nível) para LangGraph

- Nó 1: `RouterIntencao`
  - Decide entre: consultar faturas, renegociar, consultar status de acordo, dúvidas gerais.
- Nó 2: `IdentificarCliente`
  - Usa `lookup_customer_by_cnpj_tool` e atualiza estado.
- Nó 3: `CarregarFaturas`
  - Usa `list_open_invoices_tool`, grava em `open_invoices_session`.
- Nó 4: `SelecionarTitulos`
  - Interação com o usuário para escolher faturas.
- Nó 5: `ColetarRestricoesSessao`
  - Pergunta sobre capacidade de pagamento, datas, etc., preenchendo `session_constraints`.
- Nó 6: `GerarPropostas`
  - Chama `generate_payment_options_tool` e atualiza `current_offer_set`.
- Nó 7: `NegociarLoop`
  - Loop de refinamento de propostas, usando short-term memory.
- Nó 8: `FecharAcordo`
  - Chama `create_agreement_tool` + `issue_boletos_pix_tool`.
- Nó 9: `EncerrarSessao`
  - Resume acordo, dispara `send_notification_tool`, limpa/expira estado sensível.

## 8. Plano de Implementação - Sistemas Externos

### 8.1. Arquitetura dos Sistemas

Os sistemas externos serão implementados como APIs FastAPI independentes, cada uma rodando em uma porta específica:

```
┌─────────────────────────────────────────────────────────┐
│              Chatbot LangGraph Agent                     │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  ERP API     │  │ Payment API  │  │ Credit API   │
│  (Port 8001) │  │ (Port 8002)  │  │ (Port 8003)  │
└──────────────┘  └──────────────┘  └──────────────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Notification │  │ Session Store│  │ Logging API   │
│ API (8004)   │  │ (Redis/8005) │  │ (Port 8006)  │
└──────────────┘  └──────────────┘  └──────────────┘
```

### 8.2. Ordem de Implementação

1. **Serviço ERP Financeiro (Porta 8001)** - PRIORIDADE ALTA
   - Fonte de verdade dos clientes e faturas
   - Endpoints: `/customers/{cnpj}`, `/customers/{id}/invoices`, `/agreements`
   - Dados mock: usar `cnpomapa30092019.xlsx` para gerar clientes e faturas

2. **Motor de Regras de Crédito (Porta 8003)** - PRIORIDADE ALTA
   - Gera cenários de renegociação baseados em regras
   - Endpoints: `/credit-rules/generate-options`, `/credit-rules/validate-scenario`
   - Depende do ERP para obter dados do cliente

3. **Serviço de Pagamentos (Porta 8002)** - PRIORIDADE MÉDIA
   - Gera boletos e PIX
   - Endpoints: `/payments/boleto`, `/payments/pix`, `/payments/{id}/status`
   - Dados mock: gera linhas digitáveis e QR codes fictícios

4. **Serviço de Notificações (Porta 8004)** - PRIORIDADE BAIXA
   - Simula envio de mensagens (WhatsApp, SMS, Email)
   - Endpoints: `/notifications/send`, `/notifications/{id}/status`
   - Não envia mensagens reais, apenas simula

5. **Session Store (Porta 8005)** - PRIORIDADE MÉDIA
   - Armazena estado da sessão do agente
   - Usa Redis ou mock em memória
   - Endpoints: `/sessions` (CRUD)

6. **Serviço de Logging (Porta 8006)** - PRIORIDADE BAIXA
   - Registra interações e eventos
   - Endpoints: `/interactions/log`, `/interactions/{customer_id}/history`

### 8.3. Estrutura de Projeto

```
safraboleto/
├── integrations/          # Sistemas externos (APIs mock)
│   ├── erp_service/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── routers/
│   │   │   ├── customers.py
│   │   │   ├── invoices.py
│   │   │   └── agreements.py
│   │   └── mock_data/
│   │       ├── customers.json    # Gerado do xlsx
│   │       └── invoices.json     # Gerado do xlsx
│   ├── payment_service/
│   │   ├── main.py
│   │   ├── models.py
│   │   └── routers/
│   │       └── payments.py
│   ├── credit_service/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── rules_engine.py
│   │   ├── routers/
│   │   │   └── credit_rules.py
│   │   └── config/
│   │       └── credit_rules.json
│   ├── notification_service/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── routers/
│   │   │   └── notifications.py
│   │   └── templates/
│   │       └── messages.json
│   ├── session_service/
│   │   ├── main.py
│   │   └── redis_client.py
│   └── logging_service/
│       ├── main.py
│       ├── models.py
│       └── routers/
│           └── interactions.py
├── docs/
│   ├── requisitos.md
│   └── cnpomapa30092019.xlsx
└── ...
```

### 8.4. Base de Dados

- **Sistema:** PostgreSQL rodando no Docker
- **Uso:** Todos os sistemas externos compartilham a mesma instância PostgreSQL
- **Tabelas principais:**
  - `customers` - Dados cadastrais dos clientes
  - `invoices` - Faturas em aberto
  - `agreements` - Acordos de renegociação
  - `payments` - Boletos e PIX gerados
  - `sessions` - Estado das sessões do agente
  - `interactions` - Log de interações
- **População inicial:**
  - **Fonte:** `docs/cnpomapa30092019.xlsx`
  - **Extração:** Script para extrair CNPJs válidos (1.069 empresas)
  - **Geração:**
    - Clientes: CNPJ, nome, rating (A/B/C/D), limites de crédito, contatos
    - Faturas: 3-8 faturas por cliente com valores e datas variadas
    - Ratings distribuídos: A (28%), B (42%), C (20%), D (10%)

### 8.5. Especificações Técnicas

Cada serviço deve ter:
- Framework: FastAPI
- Health check: `GET /health`
- CORS habilitado para desenvolvimento
- Documentação automática: `/docs` (Swagger)
- Validação de entrada com Pydantic
- Logging estruturado

### 8.6. Dependências Principais

```toml
fastapi>=0.104.1
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
asyncpg>=0.29.0  # Driver PostgreSQL assíncrono
sqlalchemy[asyncio]>=2.0.0  # ORM para PostgreSQL
redis>=5.0.1  # Para session service
pandas>=2.0.0
openpyxl>=3.1.0
```

### 8.7. Próximos Passos

1. ✅ Criar estrutura de pastas `integrations/`
2. ⏳ Configurar PostgreSQL no Docker
3. ⏳ Criar schema do banco de dados (tabelas para todos os serviços)
4. ⏳ Implementar serviço ERP com conexão ao PostgreSQL
5. ⏳ Implementar motor de regras de crédito
6. ⏳ Implementar serviços restantes na ordem de prioridade
7. ⏳ Criar script de população inicial do banco a partir do xlsx
8. ⏳ Testar integração entre serviços

