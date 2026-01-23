# Especificações Técnicas de Regras de Negócio - SafraBoleto

Este documento contém as especificações técnicas detalhadas ("Aprofundamento") que os desenvolvedores utilizarão para implementar a lógica de negócio complexa nos sistemas mock. Estas especificações garantem que a simulação reflita comportamentos realistas de software enterprise.

## 1. Tabela de Tiers de Clientes

O sistema classifica clientes em três tiers baseado em critérios de negócio. O tier impacta diretamente nas condições comerciais oferecidas.

| Tier | Critérios de Classificação | Prazo de Pagamento | Limite de Crédito | Máx. Parcelas | Desconto Máx. Auto | Juros Mensal |
|------|---------------------------|-------------------|-------------------|---------------|-------------------|--------------|
| **Ouro** | Volume anual > R$ 5M<br/>Rating A<br/>Histórico > 2 anos sem atrasos | Até 60 dias | R$ 500.000 | 6 parcelas | 5% | 0,0% - 2,5% |
| **Prata** | Volume anual R$ 1M - R$ 5M<br/>Rating A ou B<br/>Histórico > 1 ano | Até 45 dias | R$ 200.000 | 4 parcelas | 3% | 1,5% - 3,3% |
| **Bronze** | Volume anual < R$ 1M<br/>Rating B, C ou D<br/>Histórico variável | Até 30 dias | R$ 100.000 | 3 parcelas | 1% | 2,5% - 5,0% |

### Lógica de Classificação de Tier

```python
def calcular_tier(cliente):
    """
    Calcula o tier do cliente baseado em múltiplos critérios
    """
    score = 0
    
    # Critério 1: Volume anual
    if cliente.volume_anual > 5_000_000:
        score += 3
    elif cliente.volume_anual > 1_000_000:
        score += 2
    else:
        score += 1
    
    # Critério 2: Rating
    rating_scores = {"A": 3, "B": 2, "C": 1, "D": 0}
    score += rating_scores.get(cliente.rating, 0)
    
    # Critério 3: Histórico de pagamento
    if cliente.dias_sem_atraso > 730:  # > 2 anos
        score += 3
    elif cliente.dias_sem_atraso > 365:  # > 1 ano
        score += 2
    else:
        score += 1
    
    # Classificação final
    if score >= 8:
        return "Ouro"
    elif score >= 5:
        return "Prata"
    else:
        return "Bronze"
```

## 2. Pseudocódigo do Motor de Crédito

### 2.1. Cálculo de Dívida Total com Juros Compostos e Multa

```pseudocódigo
FUNÇÃO calcular_divida_total(faturas[], data_calculo):
    divida_total = 0
    
    PARA CADA fatura EM faturas:
        valor_original = fatura.valor
        data_vencimento = fatura.data_vencimento
        dias_atraso = calcular_dias_entre(data_vencimento, data_calculo)
        
        SE dias_atraso > 0:
            // Calcular multa pro-rata dia
            percentual_multa = fatura.percentual_multa  // Ex: 2% ao mês
            dias_mes = 30
            multa_pro_rata = (percentual_multa / dias_mes) * dias_atraso
            valor_com_multa = valor_original * (1 + multa_pro_rata)
            
            // Calcular juros compostos mensais
            taxa_juros_mensal = obter_taxa_juros(fatura.cliente.rating)
            meses_atraso = dias_atraso / 30.0
            
            // Juros compostos: M = C * (1 + i)^n
            valor_final = valor_com_multa * (1 + taxa_juros_mensal) ^ meses_atraso
            
            divida_total += valor_final
        SENÃO:
            divida_total += valor_original
    
    RETORNAR divida_total
FIM FUNÇÃO
```

### 2.2. Geração de Cenários de Renegociação

```pseudocódigo
FUNÇÃO gerar_cenarios_renegociacao(cliente, faturas[], restricoes_sessao):
    cenarios = []
    divida_total = calcular_divida_total(faturas, data_atual)
    tier = cliente.tier
    rating = cliente.rating
    
    // Obter limites do tier
    limites = obter_limites_tier(tier)
    
    // CENÁRIO 1: Pagamento à vista com desconto
    desconto_max = limites.desconto_max_auto
    desconto_aplicado = min(desconto_max, 0.05)  // Máximo 5% para à vista
    
    SE divida_total * desconto_aplicado <= limites.limite_aprovacao_auto:
        valor_final = divida_total * (1 - desconto_aplicado)
        cenario1 = {
            tipo: "A_VISTA",
            valor_total: valor_final,
            desconto_percentual: desconto_aplicado * 100,
            parcelas: 1,
            valor_parcela: valor_final,
            data_vencimento: data_atual + 5 dias,
            requer_aprovacao: false
        }
        cenarios.adicionar(cenario1)
    
    // CENÁRIO 2: Parcelamento curto sem desconto
    num_parcelas = min(3, limites.max_parcelas)
    valor_parcela = divida_total / num_parcelas
    
    SE valor_parcela >= limites.valor_min_parcela:
        cenario2 = {
            tipo: "PARCELADO_CURTO",
            valor_total: divida_total,
            desconto_percentual: 0,
            parcelas: num_parcelas,
            valor_parcela: valor_parcela,
            intervalo_dias: 30,
            requer_aprovacao: false
        }
        cenarios.adicionar(cenario2)
    
    // CENÁRIO 3: Parcelamento longo com juros (se permitido)
    SE tier != "Bronze" E rating != "D":
        num_parcelas_longo = limites.max_parcelas
        taxa_juros = obter_taxa_juros(rating)
        
        // Calcular valor futuro com juros
        valor_futuro = divida_total * (1 + taxa_juros) ^ (num_parcelas_longo / 12.0)
        valor_parcela_longo = valor_futuro / num_parcelas_longo
        
        SE valor_parcela_longo >= limites.valor_min_parcela:
            cenario3 = {
                tipo: "PARCELADO_LONGO",
                valor_total: valor_futuro,
                valor_original: divida_total,
                juros_total: valor_futuro - divida_total,
                desconto_percentual: 0,
                parcelas: num_parcelas_longo,
                valor_parcela: valor_parcela_longo,
                intervalo_dias: 30,
                taxa_juros_mensal: taxa_juros * 100,
                requer_aprovacao: verificar_alçada_aprovacao(valor_futuro, desconto_aplicado)
            }
            cenarios.adicionar(cenario3)
    
    // Aplicar restrições da sessão se informadas
    SE restricoes_sessao.existe:
        cenarios = filtrar_cenarios_por_restricoes(cenarios, restricoes_sessao)
    
    RETORNAR cenarios
FIM FUNÇÃO
```

### 2.3. Validação de Alçadas de Aprovação

```pseudocódigo
FUNÇÃO verificar_alçada_aprovacao(valor_total, desconto_percentual, cliente):
    requer_aprovacao = false
    
    // Regra 1: Desconto > 10% sempre requer aprovação
    SE desconto_percentual > 10:
        requer_aprovacao = true
        motivo = "Desconto acima de 10%"
    
    // Regra 2: Desconto entre 5% e 10% requer aprovação para rating C ou D
    SENÃO SE desconto_percentual > 5 E cliente.rating EM ["C", "D"]:
        requer_aprovacao = true
        motivo = "Desconto acima de 5% para cliente rating " + cliente.rating
    
    // Regra 3: Rating D nunca recebe desconto automático
    SENÃO SE cliente.rating == "D" E desconto_percentual > 0:
        requer_aprovacao = true
        motivo = "Cliente rating D não pode receber desconto automático"
    
    // Regra 4: Valor acima do threshold de aprovação automática
    threshold = obter_threshold_aprovacao(cliente.rating)
    SE valor_total > threshold:
        requer_aprovacao = true
        motivo = "Valor acima do threshold de aprovação automática"
    
    RETORNAR {requer_aprovacao, motivo}
FIM FUNÇÃO
```

### 2.4. Obtenção de Taxa de Juros por Rating

```pseudocódigo
FUNÇÃO obter_taxa_juros(rating):
    taxas = {
        "A": [0.0, 0.025],      // 0% a 2,5% ao mês
        "B": [0.015, 0.033],    // 1,5% a 3,3% ao mês
        "C": [0.025, 0.05],     // 2,5% a 5% ao mês
        "D": [0.033, 0.10]      // 3,3% a 10% ao mês
    }
    
    [taxa_min, taxa_max] = taxas[rating]
    
    // Retornar taxa média ou aleatória dentro do range
    // Para simulação, usar taxa média
    RETORNAR (taxa_min + taxa_max) / 2
FIM FUNÇÃO
```

## 3. Fluxo de Estados do Pedido/Acordo

O sistema implementa uma máquina de estados para rastrear o ciclo de vida completo de acordos de renegociação.

### 3.1. Diagrama de Estados

```
                    ┌─────────────┐
                    │   RASCUNHO  │
                    └──────┬──────┘
                           │
                           │ (cliente confirma)
                           ▼
              ┌────────────────────────┐
              │ PENDENTE_APROVACAO     │◄──┐
              └──────┬─────────────────┘   │
                     │                      │
        ┌────────────┼────────────┐        │
        │            │            │        │
        │ (aprovado) │ (rejeitado)│        │
        ▼            ▼            │        │
   ┌─────────┐  ┌──────────┐     │        │
   │ APROVADO│  │ REJEITADO│     │        │
   └────┬────┘  └──────────┘     │        │
        │                         │        │
        │ (gerar boletos)         │        │
        ▼                         │        │
   ┌─────────────────┐           │        │
   │ BOLETOS_GERADOS │           │        │
   └────┬────────────┘           │        │
        │                        │        │
        │ (pagamento confirmado)  │        │
        ▼                        │        │
   ┌─────────────────┐          │        │
   │ CONCLUIDO       │          │        │
   └─────────────────┘          │        │
                                 │        │
        ┌────────────────────────┘        │
        │                                  │
        │ (cliente cancela)                │
        ▼                                  │
   ┌──────────────┐                       │
   │  CANCELADO   │                       │
   └──────────────┘                       │
                                           │
        ┌──────────────────────────────────┘
        │ (timeout ou expiração)
        ▼
   ┌──────────────┐
   │   EXPIRADO   │
   └──────────────┘
```

### 3.2. Descrição dos Estados

| Estado | Descrição | Transições Permitidas | Ações Automáticas |
|--------|-----------|---------------------|-------------------|
| **RASCUNHO** | Acordo criado mas não confirmado pelo cliente | → PENDENTE_APROVACAO<br/>→ CANCELADO | Nenhuma |
| **PENDENTE_APROVACAO** | Aguardando aprovação humana (se requerida) ou validação automática | → APROVADO<br/>→ REJEITADO<br/>→ CANCELADO<br/>→ EXPIRADO | Enviar notificação para aprovador (se manual)<br/>Timer de expiração (24h) |
| **APROVADO** | Acordo aprovado, pronto para gerar boletos | → BOLETOS_GERADOS<br/>→ CANCELADO | Nenhuma |
| **BOLETOS_GERADOS** | Boletos/PIX gerados e enviados ao cliente | → CONCLUIDO<br/>→ CANCELADO | Enviar notificação com boletos<br/>Registrar no ERP |
| **CONCLUIDO** | Todos os pagamentos foram confirmados | Nenhuma (estado final) | Atualizar saldo do cliente<br/>Arquivar acordo |
| **REJEITADO** | Acordo rejeitado por aprovador ou validação automática | → RASCUNHO (se permitir renegociação) | Enviar notificação de rejeição<br/>Registrar motivo |
| **CANCELADO** | Acordo cancelado pelo cliente ou sistema | Nenhuma (estado final) | Liberar recursos<br/>Registrar motivo do cancelamento |
| **EXPIRADO** | Acordo expirou por timeout (ex: 24h sem ação) | → RASCUNHO (se permitir renovação) | Enviar notificação de expiração<br/>Limpar dados temporários |

### 3.3. Pseudocódigo de Transição de Estados

```pseudocódigo
FUNÇÃO transicionar_estado(acordo, novo_estado, contexto):
    estado_atual = acordo.estado
    
    // Validar transição permitida
    transicoes_permitidas = obter_transicoes_permitidas(estado_atual)
    
    SE novo_estado NÃO EM transicoes_permitidas:
        LANÇAR ERRO("Transição inválida de " + estado_atual + " para " + novo_estado)
    
    // Executar ações pré-transição
    executar_acoes_pre_transicao(estado_atual, novo_estado, acordo, contexto)
    
    // Atualizar estado
    acordo.estado = novo_estado
    acordo.data_ultima_atualizacao = data_atual
    acordo.historico_estados.adicionar({
        estado_anterior: estado_atual,
        estado_novo: novo_estado,
        data: data_atual,
        contexto: contexto
    })
    
    // Executar ações pós-transição
    executar_acoes_pos_transicao(novo_estado, acordo, contexto)
    
    // Persistir
    salvar_acordo(acordo)
    
    RETORNAR acordo
FIM FUNÇÃO

FUNÇÃO executar_acoes_pos_transicao(estado, acordo, contexto):
    SE estado == "APROVADO":
        // Verificar se precisa gerar boletos automaticamente
        SE acordo.gerar_boletos_automatico:
            gerar_boletos(acordo)
            transicionar_estado(acordo, "BOLETOS_GERADOS", contexto)
    
    SENÃO SE estado == "BOLETOS_GERADOS":
        enviar_notificacao_boletos(acordo)
        registrar_no_erp(acordo)
    
    SENÃO SE estado == "CONCLUIDO":
        atualizar_saldo_cliente(acordo)
        arquivar_acordo(acordo)
    
    SENÃO SE estado == "REJEITADO":
        enviar_notificacao_rejeicao(acordo, contexto.motivo)
    
    SENÃO SE estado == "EXPIRADO":
        enviar_notificacao_expiracao(acordo)
        limpar_dados_temporarios(acordo)
FIM FUNÇÃO
```

## 4. Hierarquia de Contatos

### 4.1. Estrutura de Contatos

Cada cliente pode ter múltiplos contatos com papéis distintos:

```python
class Contact:
    contact_id: str
    customer_id: str
    name: str
    email: str
    phone: str
    role: str  # "COMPRADOR", "FINANCEIRO", "GESTOR"
    is_primary: bool
    permissions: List[str]
    created_at: datetime
    last_interaction: datetime
```

### 4.2. Permissões por Papel

| Papel | Consultar Faturas | Gerar Boletos | Iniciar Renegociação | Criar Acordos | Aprovar Acordos |
|-------|------------------|---------------|---------------------|---------------|-----------------|
| **Comprador** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Financeiro** | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Gestor** | ✅ | ✅ | ✅ | ✅ | ✅ (limitado) |

### 4.3. Adaptação de Linguagem

```pseudocódigo
FUNÇÃO adaptar_linguagem(mensagem, contato):
    papel = contato.role
    
    SE papel == "COMPRADOR":
        // Linguagem mais comercial e explicativa
        mensagem_adaptada = mensagem
            .substituir("juros compostos", "taxa de juros")
            .substituir("multa pro-rata", "multa por atraso")
            .adicionar_explicacoes_simples()
    
    SENÃO SE papel == "FINANCEIRO":
        // Linguagem técnica e direta
        mensagem_adaptada = mensagem
            .manter_terminologia_tecnica()
            .remover_explicacoes_redundantes()
    
    SENÃO:  // GESTOR
        // Linguagem executiva, focada em resultados
        mensagem_adaptada = mensagem
            .adicionar_metricas_e_impactos()
            .focar_em_beneficios_comerciais()
    
    RETORNAR mensagem_adaptada
FIM FUNÇÃO
```

## 5. Lógica de Win-back para Clientes Inativos

### 5.1. Detecção de Cliente Inativo

```pseudocódigo
FUNÇÃO identificar_clientes_inativos():
    data_limite = data_atual - 90 dias
    clientes_inativos = []
    
    clientes = obter_todos_clientes()
    
    PARA CADA cliente EM clientes:
        ultima_interacao = obter_ultima_interacao(cliente.id)
        
        SE ultima_interacao == NULL OU ultima_interacao.data < data_limite:
            dias_inativo = calcular_dias_entre(ultima_interacao.data, data_atual)
            
            cliente_inativo = {
                cliente: cliente,
                dias_inativo: dias_inativo,
                historico_positivo: verificar_historico_positivo(cliente),
                valor_divida: calcular_divida_total(cliente.faturas)
            }
            
            clientes_inativos.adicionar(cliente_inativo)
    
    RETORNAR clientes_inativos
FIM FUNÇÃO
```

### 5.2. Estratégia de Win-back

```pseudocódigo
FUNÇÃO aplicar_estrategia_winback(cliente_inativo):
    cliente = cliente_inativo.cliente
    historico_positivo = cliente_inativo.historico_positivo
    
    // Definir oferta baseada no histórico
    SE historico_positivo:
        desconto_especial = 0.08  // 8% para clientes com histórico positivo
        mensagem = "Oferecemos condições especiais para sua retomada"
    SENÃO:
        desconto_especial = 0.05  // 5% para outros clientes
        mensagem = "Temos uma proposta especial para regularizar sua situação"
    
    // Criar proposta de win-back
    proposta = {
        tipo: "WINBACK",
        desconto_percentual: desconto_especial * 100,
        validade_dias: 15,
        mensagem_personalizada: mensagem,
        beneficios: [
            "Desconto especial de " + (desconto_especial * 100) + "%",
            "Condições flexíveis de pagamento",
            "Sem impacto no relacionamento comercial"
        ]
    }
    
    // Disparar notificação na próxima interação
    agendar_notificacao_winback(cliente, proposta)
    
    RETORNAR proposta
FIM FUNÇÃO
```

## 6. Simulação de Delay Bancário e Webhooks

### 6.1. Processamento Assíncrono de Pagamentos

```pseudocódigo
FUNÇÃO processar_pagamento_async(pagamento):
    // Criar pagamento com status inicial
    pagamento.status = "PENDENTE"
    pagamento.data_criacao = data_atual
    salvar_pagamento(pagamento)
    
    // Simular delay bancário (10-30 segundos)
    delay_segundos = aleatorio_entre(10, 30)
    
    // Agendar confirmação assíncrona
    agendar_tarefa_async(
        funcao: confirmar_pagamento_via_webhook,
        parametros: [pagamento.id],
        delay: delay_segundos
    )
    
    // Retornar resposta imediata
    RETORNAR {
        payment_id: pagamento.id,
        status: "PENDENTE",
        mensagem: "Pagamento em processamento. Confirmação será enviada via webhook."
    }
FIM FUNÇÃO

FUNÇÃO confirmar_pagamento_via_webhook(payment_id):
    pagamento = obter_pagamento(payment_id)
    
    // Simular taxa de sucesso (95% dos pagamentos são confirmados)
    sucesso = aleatorio() < 0.95
    
    SE sucesso:
        pagamento.status = "CONFIRMADO"
        pagamento.data_confirmacao = data_atual
        pagamento.codigo_confirmacao = gerar_codigo_confirmacao()
    SENÃO:
        pagamento.status = "FALHOU"
        pagamento.motivo_falha = obter_motivo_falha_aleatorio()
    
    salvar_pagamento(pagamento)
    
    // Enviar webhook (simulado)
    enviar_webhook(pagamento.webhook_url, {
        payment_id: pagamento.id,
        status: pagamento.status,
        data_confirmacao: pagamento.data_confirmacao,
        codigo_confirmacao: pagamento.codigo_confirmacao
    })
    
    // Se falhou, agendar retentativa (máximo 3 tentativas)
    SE pagamento.status == "FALHOU" E pagamento.tentativas_webhook < 3:
        pagamento.tentativas_webhook += 1
        agendar_retentativa_webhook(pagamento, delay: 60 segundos)
FIM FUNÇÃO
```

## 7. Referências de Implementação

### 7.1. Constantes e Configurações

```python
# Configurações de Tiers
TIER_CONFIG = {
    "Ouro": {
        "prazo_pagamento_dias": 60,
        "limite_credito": 500_000,
        "max_parcelas": 6,
        "desconto_max_auto": 0.05,
        "juros_range": [0.0, 0.025]
    },
    "Prata": {
        "prazo_pagamento_dias": 45,
        "limite_credito": 200_000,
        "max_parcelas": 4,
        "desconto_max_auto": 0.03,
        "juros_range": [0.015, 0.033]
    },
    "Bronze": {
        "prazo_pagamento_dias": 30,
        "limite_credito": 100_000,
        "max_parcelas": 3,
        "desconto_max_auto": 0.01,
        "juros_range": [0.025, 0.05]
    }
}

# Thresholds de Aprovação por Rating
APPROVAL_THRESHOLDS = {
    "A": 200_000,
    "B": 150_000,
    "C": 100_000,
    "D": 50_000
}

# Configurações de Multa
MULTA_CONFIG = {
    "percentual_mensal": 0.02,  # 2% ao mês
    "dias_mes_referencia": 30
}

# Configurações de Win-back
WINBACK_CONFIG = {
    "dias_inatividade_minimo": 90,
    "desconto_historico_positivo": 0.08,
    "desconto_geral": 0.05,
    "validade_proposta_dias": 15
}
```

### 7.2. Validações Importantes

- **Valor mínimo de parcela:** R$ 1.000,00 (aplicado a todos os cenários)
- **TTL de sessão:** 60 minutos de inatividade
- **Timeout de aprovação:** 24 horas
- **Delay bancário:** 10-30 segundos (aleatório)
- **Taxa de sucesso de pagamento:** 95% (simulação)
- **Máximo de retentativas de webhook:** 3 tentativas

---

**Nota para Desenvolvedores:** Estas especificações devem ser implementadas nos respectivos serviços mock. A complexidade aqui descrita é intencional para criar uma simulação realista de software enterprise, não apenas um CRUD simples. Todas as fórmulas financeiras devem ser implementadas exatamente como especificado para garantir precisão nos cálculos.
