# Process Log — Diagnóstico de Churn RavenStack

**Candidato:** Lucas Caldeira Liberato Souza  
**AI utilizada:** Claude (Anthropic)  
**Data:** Março 2026

---

## Objetivo do Log

Documentar o processo de análise mostrando como a AI foi utilizada para chegar às conclusões do diagnóstico. Este documento é parte obrigatória da entrega.

---

## Fluxo do Processo

```
DADOS BRUTOS (5 CSVs)
        ↓
[1] INVENTÁRIO E EXPLORAÇÃO
        ↓
[2] ANÁLISE POR CATEGORIA
        ↓
[3] CRUZAMENTO ENTRE TABELAS
        ↓
[4] GERAÇÃO DE HIPÓTESES
        ↓
[5] VALIDAÇÃO/REFUTAÇÃO
        ↓
[6] RECOMENDAÇÕES
        ↓
DELIVERABLE FINAL
```

---

## Etapa 1: Inventário e Exploração

**Prompt para AI:**
> "Extraia o arquivo e faça um inventário completo dos dados"

**Ações da AI:**
- Extraiu archive.zip
- Identificou 5 arquivos CSV
- Mapeou estrutura de cada tabela
- Identificou chaves de relacionamento

**Output:**
```
ravenstack_accounts.csv      → 500 registros, 10 colunas
ravenstack_subscriptions.csv → 5,000 registros, 10 colunas  
ravenstack_feature_usage.csv → 25,000 registros, 7 colunas
ravenstack_support_tickets.csv → 2,000 registros, 8 colunas
ravenstack_churn_events.csv  → 600 registros, 6 colunas
```

**Decisão humana:** Prosseguir com análise exploratória por categoria.

---

## Etapa 2: Análise por Categoria

### 2.1 Métricas gerais

**Prompt:**
> "Calcule as métricas básicas de churn"

**Output AI:**
- Total accounts: 500
- Churned: 110 (22%)
- MRR perdido: $254,952
- MRR médio: $2,437

### 2.2 Segmentação por indústria

**Prompt:**
> "Analise churn rate por indústria"

**Output AI:**
| Industry | Churn Rate |
|----------|------------|
| DevTools | 31.0% ⚠️ |
| FinTech | 22.3% |
| HealthTech | 21.9% |
| Cybersecurity | 16.0% |
| EdTech | 16.5% |

**Insight identificado:** DevTools tem 41% mais churn que a média.

### 2.3 Segmentação por canal

**Prompt:**
> "Analise churn rate por canal de aquisição"

**Output AI:**
| Channel | Churn Rate |
|---------|------------|
| Event | 30.2% ⚠️ |
| Partner | 14.6% ✓ |

**Insight identificado:** Event tem 2x mais churn que Partner.

### 2.4 Análise temporal

**Prompt:**
> "Mostre a evolução do churn ao longo do tempo"

**Output AI:**
- Q1-Q2 2023: 2.8 eventos/mês
- Q3-Q4 2024: 63.5 eventos/mês
- Aumento de +562%

**Decisão humana:** Algo mudou no segundo semestre de 2024. Investigar.

---

## Etapa 3: Cruzamento entre Tabelas

**Prompt:**
> "Cruze as 5 tabelas para encontrar padrões que não aparecem em análises isoladas"

**Ações da AI:**
1. Criou dataset master com todas as variáveis
2. Calculou métricas agregadas por account
3. Identificou "core features" (top 10 de ativos)
4. Calculou % de uso em core features por account

**Cruzamentos realizados:**
- accounts ↔ subscriptions (MRR, plano)
- accounts ↔ support_tickets (tickets, CSAT, escalações)
- accounts ↔ churn_events (motivos, timing)
- subscriptions ↔ feature_usage (adoção)

**Output crítico:**
```
DevTools + Partner: 25.0% core adoption | 12.5% churn
DevTools + Event:   25.0% core adoption | 43.5% churn
```

**Insight:** Mesma adoção de features, 3.5x mais churn. O problema não é o cliente — é o canal.

---

## Etapa 4: Geração de Hipóteses

**Prompt:**
> "Baseado nos dados, quais hipóteses explicam o churn?"

**Hipóteses geradas pela AI:**
1. DevTools não tem product-market fit
2. Canal Event traz clientes com expectativa inflada
3. Upgrades falham por expectativa não entregue
4. Enterprise tem suporte pior que Basic
5. Adoção de features é o driver principal

**Decisão humana:** Testar cada hipótese contra os dados.

---

## Etapa 5: Validação das Hipóteses

### 5.1 Questionamento Crítico

Após a AI apresentar as hipóteses e uma primeira conclusão, foi solicitada validação rigorosa:

**Prompt:**
> "Esse diagnóstico pode ser confirmado pelos dados? E pelo cruzamento de dados entre tabelas? Se sim, resposta 1 ok."

**Resposta da AI:**
> "Vou validar rigorosamente se o diagnóstico está suportado pelo cruzamento real entre as 5 tabelas."

A AI então executou uma série de testes cruzando accounts + subscriptions + feature_usage + support_tickets + churn_events para validar cada hipótese.

---

### 5.2 Validação por Hipótese

#### Hipótese 1: DevTools = problema de produto

**Teste:** Se fosse produto, todos os canais teriam alto churn.

**Resultado:**
- DevTools via Partner: 12.5% churn
- DevTools via Event: 43.5% churn

**Conclusão:** **REFUTADA** — Via Partner funciona. Não é produto.

#### Hipótese 2: Event = expectativa inflada

**Teste:** Event deveria ter mais tickets/escalações.

**Resultado:**
- Tickets/account: Event 4.0 vs Partner 3.8 (similar)
- Escalações: Event 5.1% vs Partner 5.1% (igual)
- Mas: Motivo de churn "support" = 33% em Event

**Conclusão:** **PARCIALMENTE VALIDADA** — Problema é expectativa, não volume de problemas.

#### Hipótese 3: Upgrade = problema

**Teste:** Quem faz upgrade churna mais?

**Resultado:**
- Com upgrade: 20.8% churn
- Sem upgrade: 23.8% churn

**Conclusão:** **REFUTADA** — Upgrade reduz churn.

#### Hipótese 4: Features = driver principal

**Teste:** Correlação entre adoção de core features e churn.

**Resultado:**
- <20% core: 33.3% churn
- 20-40% core: 19.2% churn
- >40% core: 9.1% churn

**Conclusão:** **VALIDADA** — Forte correlação.

---

### 5.3 Descoberta Durante Validação

Durante o cruzamento de dados, a AI identificou que a adoção de core features era igual entre canais (~25%), mas o churn era drasticamente diferente. Isso levou a uma correção importante:

**Output AI:**
```
DevTools + Event:   25.0% core adoption | 43.5% churn
DevTools + Partner: 25.0% core adoption | 12.5% churn
```

**Insight corrigido:** O problema não é adoção de features isoladamente — é a combinação de canal inadequado + falta de onboarding que o Partner naturalmente fornece.

**Decisão humana:** A causa raiz é combinação de canal + onboarding, não fatores isolados.

---

## Etapa 6: Recomendações

**Prompt:**
> "Baseado nas hipóteses validadas, quais ações concretas com impacto estimado?"

**Output AI:**

| Ação | Impacto | Esforço |
|------|---------|---------|
| Intervenção 81 contas | $290K ARR | Baixo |
| GTM DevTools → Partner | $259K ARR | Médio |
| Onboarding core features | $775K ARR | Médio |
| SLA Enterprise | $127K ARR | Alto |

**Decisão humana:** Priorizar ações de baixo esforço primeiro.

---

## Etapa 7: Diferencial — Modelo Preditivo

Após concluir a análise principal, foi avaliada a inclusão de um modelo preditivo de ML como diferenciador.

**Prompt:**
> "Conseguimos fazer um modelo preditivo de churn que funcione, como doc adicional?"

**Ações da AI:**
1. Feature engineering com 15 variáveis derivadas das 5 tabelas
2. Teste de 3 modelos: Random Forest, Gradient Boosting, Logistic Regression
3. Avaliação com cross-validation (5-fold)

**Resultado:**
- Melhor modelo: Logistic Regression (CV AUC: 55.7%)
- Performance limitada devido a dados sintéticos

**Decisão humana:** Incluir com documentação honesta sobre limitações.

---

## Rastreabilidade: Dado → Insight → Ação

| Dado | Insight | Ação Recomendada | Impacto |
|------|---------|------------------|---------|
| DevTools via Event: 43.5% churn vs Partner: 12.5% | Canal Event não qualifica bem DevTools | Redirecionar aquisição DevTools para Partners | $259K ARR |
| <20% core features = 33% churn vs >40% = 9% | Clientes não descobrem features que retêm | Criar onboarding guiado para core features | $775K ARR |
| 81 contas com 3+ fatores de risco | Combinação de fatores aumenta risco exponencialmente | Intervenção imediata de CS | $290K ARR |
| Enterprise resolution time: 37.1h (pior que Basic) | SLA não diferenciado por plano | Implementar SLA diferenciado | $127K ARR |

---

## Resumo do Uso de AI

### O que a AI fez:
- Processamento de dados (pandas)
- Cálculos estatísticos
- Identificação de padrões
- Geração de hipóteses
- Formatação de outputs

### O que o humano fez:
- Definição das perguntas certas
- Exigência de validação pelos dados (não por feeling)
- Análise lógica de hipóteses
- Validação de lógica de negócio
- Decisões de priorização
- Avaliação de inclusão do modelo preditivo
- Aprovação final das conclusões

### Código executado:
- ~40 blocos de Python
- Bibliotecas: pandas, numpy, scikit-learn
- Todas as análises reproduzíveis

---

## Arquivos Gerados

1. `solution/diagnostico_churn_ravenstack.md` — Relatório completo
2. `solution/contas_alto_risco.csv` — Lista de 81 contas para CS
3. `solution/analise_exploratoria.py` — Código Python reproduzível
4. `docs/modelo_preditivo_churn.md` — Documentação do modelo ML
5. `docs/predicoes_churn_ml.csv` — Previsões para accounts ativos
6. `process-log/README.md` — Este documento

---
