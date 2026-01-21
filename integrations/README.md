# Sistemas Externos - APIs Mock

Este diretório contém os sistemas externos que o agente de renegociação irá interagir.

## Estrutura

```
integrations/
├── erp_service/          # Porta 8001 - Clientes, faturas e acordos
├── payment_service/      # Porta 8002 - Boletos e PIX
├── credit_service/       # Porta 8003 - Regras de crédito e cenários
├── notification_service/ # Porta 8004 - Notificações (WhatsApp, SMS, Email)
├── session_service/      # Porta 8005 - Armazenamento de sessões
└── logging_service/      # Porta 8006 - Logging de interações
```

## Como Executar

Cada serviço pode ser executado independentemente:

```bash
# Serviço ERP
cd integrations/erp_service
uv run python main.py

# Serviço de Pagamentos
cd integrations/payment_service
uv run python main.py

# E assim por diante...
```

## Dados Mock

Os dados mock serão gerados a partir do arquivo `docs/cnpomapa30092019.xlsx`:
- Clientes: extrair CNPJs válidos (1.069 empresas)
- Faturas: gerar 3-8 faturas por cliente

## Status de Implementação

- ✅ Estrutura criada
- ⏳ Implementação dos endpoints (em progresso)
- ⏳ Geração de dados mock do xlsx (pendente)
