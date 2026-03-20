# Entry 001b — Análise do EDA: esperado vs encontrado

**Data:** 2026-03-20
**Fonte:** entry_001_eda_output.md
**Autor:** Lucas Reis

---

## 🚨 RED FLAG CRÍTICO — Discrepância na taxa de churn

**Encontrado:** dois números de churn radicalmente diferentes no mesmo dataset:

| Fonte | Contas churned | Taxa |
|-------|---------------|------|
| `accounts.churn_flag = True` | 110 / 500 | **22.0%** |
| `churn_events` (deduplicado por account_id) | 352 / 500 | **70.4%** |

**Por que existe essa discrepância:**

O `churn_events` tem 600 linhas para 352 `account_id` únicos — média de 1.7 eventos por conta.
A deduplicação removeu 248 linhas (não apenas os 61 marcados como `is_reactivation=True`).
Isso significa que **muitas contas têm múltiplos eventos de churn sem flag de reativação** —
provavelmente registros de cancelamento de subscrições individuais, não do account inteiro.

**Conclusão:** `churn_events` captura cancelamentos no nível de subscrição.
`accounts.churn_flag` captura churn no nível de conta (saída definitiva da plataforma).

**Impacto direto nos agents:**

O Agent 02 usa `latest_churn` como fonte de `churned = 1`, o que marcaria 352/500 contas
como churned (70.4%). Isso é semanticamente errado para o problema de negócio.

**Correção necessária no Agent 02:**
Usar `a.churn_flag` (de `accounts.csv`) como target principal.
Usar `churn_events` apenas para variáveis explicativas: `reason_code`, `preceding_downgrade_flag`, `preceding_upgrade_flag`.

---

## Findings por tabela: esperado vs encontrado

### accounts.csv

| Dimensão | Esperado | Encontrado | Avaliação |
|----------|---------|-----------|----------|
| Nulos | Alguns campos com null | ZERO nulos em todas as 10 colunas | ✅ Dado limpo |
| Churn rate | ~20–30% | 22.0% (110 contas) | ✅ Dentro do esperado |
| Distribuição de indústria | Alguma concentração | Quase uniforme: DevTools 22.6%, FinTech 22.4%, Cyber 20%, HealthTech 19.2%, EdTech 15.8% | 🔍 Distribuição mais uniforme que o real |
| is_trial | ~10–15% | 19.4% (97 contas) | ⚠️ Proporção alta de trials |
| plan_tier | Maioria Basic ou Pro | Pro 35.6%, Basic 33.6%, Enterprise 30.8% | 🔍 Distribuição quase uniforme — incomum |

**Número que chamou atenção:** Distribuição de `plan_tier` extremamente uniforme entre os 3 tiers.
Em datasets reais, Basic costuma dominar (75%+) e Enterprise é minoria (<10%). Aqui é quase 33% cada.
Isso é um artefato da geração sintética e pode limitar a diferenciação de churn por plano.

---

### subscriptions.csv

| Dimensão | Esperado | Encontrado | Avaliação |
|----------|---------|-----------|----------|
| end_date nulo | Alto (planos ativos) | 90.28% nulo | ✅ Confirma maioria das subs ativa |
| MRR min = 0 | Não esperado | Ocorre em todos os tiers | ⚠️ Trials com MRR=0 ou planos gratuitos |
| auto_renew_flag = False | ~20% | 19.9% (995 subs) | ✅ Consistente com expectativa |
| downgrade_flag | Baixo | 4.4% (218 subs) | ✅ Razoável |
| upgrade_flag | Moderado | 10.6% (529 subs) | 🔍 Mais upgrades que downgrades (529 vs 218) |
| billing_frequency | Maioria mensal | Quase 50/50 (50.8% monthly) | 🔍 Annual mais alto que esperado |

**Número que chamou atenção:** `MRR min = 0` em todos os planos, incluindo Enterprise.
Isso sugere trials ou contas cortesia. Precisa filtrar ou criar flag `mrr_is_zero`.

**Número que chamou atenção:** 10.6% de upgrades vs 4.4% de downgrades — mais contas
estão subindo de plano do que descendo. Mas o EDA de churn_events mostra 18.2% de churners
tiveram upgrade antes de sair. Hipótese emergente: **upgrade → expectativa não atendida → churn**.

---

### feature_usage.csv

| Dimensão | Esperado | Encontrado | Avaliação |
|----------|---------|-----------|----------|
| Nulos | Algum em usage | ZERO nulos em 8 colunas | ✅ Dado limpo |
| Nomes de features | Descritivos | `feature_1` a `feature_40` (genéricos) | ⚠️ Dataset sintético — sem semântica de negócio |
| Distribuição de uso | Cauda longa (Pareto) | Muito uniforme: top feature com só 2.7% | 🔍 Sem features dominantes |
| Sessão média | 15–30 min | 50.7 min média, 46 min mediana | ⚠️ Sessões longas — usuários muito engajados? |
| is_beta_feature | ~10% | 10.2% (2544 eventos) | ✅ Exato conforme README |
| error_count | Baixo | Máx 0.669 por evento (feature_4) | 🔍 Não é zero — correlação com churn a verificar |

**Números que chamaram atenção:**

1. **Sessão mediana de 46 minutos** — isso é extremamente alto para um produto SaaS B2B.
   Pode indicar que o dataset usa unidade errada ou que as sessões incluem tempo de background.
   A usar com cuidado — verificar se correlaciona com churn de forma esperada (mais uso = menos churn).

2. **Features nomeadas genericamente** (`feature_1` a `feature_40`) — impossível interpretar
   quais features de produto são mais críticas sem mapeamento. O churn por feature será
   um número sem contexto de negócio real.

3. **Distribuição de uso uniformíssima** (top 10 cada uma com ~2.6%) — em produtos reais,
   20% das features concentram 80% do uso. Aqui é basicamente uniforme. Limita a hipótese
   de "features killer que ancoram o usuário".

---

### support_tickets.csv

| Dimensão | Esperado | Encontrado | Avaliação |
|----------|---------|-----------|----------|
| satisfaction_score nulo | ~20–30% | **41.2% (825 tickets)** | 🚨 Muito alto |
| Distribuição de priority | Maioria low/medium | Quase uniforme: urgent 25.7%, high 25.5% | ⚠️ Muitos tickets urgentes |
| escalation_flag | ~5–10% | 4.8% | ✅ Razoável |
| Tempo resposta urgent | Menor que outros | 85.5 min (menor, mas marginal) | 🚨 SLA inaceitável |
| satisfaction_score médio | ~3.5–4.0 | 3.98 / 5.0 | 🔍 Relativamente alto |

**Números que chamaram atenção:**

1. **41.2% de satisfaction_score null** — quase metade dos tickets não têm resposta de pesquisa.
   Mais alto que esperado (README sugeria nulls mas não em tal proporção).
   Isso reforça que `satisfaction_no_response_rate` será uma feature poderosa no modelo.

2. **Tickets urgentes respondidos em 85.5 min** — sem diferença significativa entre urgent (85.5 min)
   e low (91.2 min). A ordenação é correta (urgent < low) mas a margem é irrisória.
   Em SaaS B2B, urgente deveria ser respondido em <30 min. O SLA está quebrado.
   **Esta é uma causa provável de churn por suporte.**

3. **Proporção de urgent (25.7%)** — 1 em 4 tickets é urgente. Isso é anormalmente alto.
   Ou o produto tem muitos problemas críticos, ou os clientes estão frustrados e escalando
   tickets para chamar atenção.

---

### churn_events.csv

| Dimensão | Esperado | Encontrado | Avaliação |
|----------|---------|-----------|----------|
| Deduplicação | Remove ~10% (reativações) | Remove 248 de 600 (41.3%!) | 🚨 Muito mais duplicatas que esperado |
| Maior reason_code | pricing | **features (19%)** | 🔍 Produto, não preço, é a causa #1 |
| preceding_downgrade | ~15–20% | **8.5%** | ✅ Mais baixo que esperado |
| preceding_upgrade | Baixo | **18.2%** | 🚨 Mais churners fizeram upgrade que downgrade |
| is_reactivation | ~10% | 10.5% | ✅ Conforme README |
| feedback_text nulo | Alto | 24.7% | ✅ Razoável para campo opcional |

**Números que chamaram atenção:**

1. **features (19%) como maior reason_code** — clientes estão saindo porque o produto
   não entrega o que prometeu, não porque está caro. As ações de retenção devem focar
   em product gaps, não em desconto.

2. **preceding_upgrade_flag = True em 18.2% dos churners vs preceding_downgrade em 8.5%**
   — mais churners fizeram UPGRADE antes de sair do que downgrade. Este é o padrão
   "buyer's remorse": pagou mais, não encontrou valor, saiu.
   Isso inverte a hipótese H7 original (downgrade → churn) — o sinal de alerta real
   pode ser o upgrade seguido de baixo engajamento.

3. **Deduplicação removeu 248 linhas, mas só 61 são is_reactivation=True** — os outros
   187 registros duplicados não são reativações. São eventos de churn para a mesma conta
   sem explicação de reativação. Possível interpretação: cancelamentos de subscrições
   individuais (não de toda a conta) geram eventos nesta tabela.

---

## Hipóteses revisadas após EDA

### Hipóteses que ganharam força

| Hipótese | Evidência do EDA |
|---------|-----------------|
| H2 — tickets escalados → churn | 4.8% de escalation; sem SLA para urgent |
| H6 — auto_renew=False → churn | 19.9% das subs sem auto-renew |
| Novo: upgrade recente → churn | 18.2% dos churners tiveram upgrade recente (maior que downgrade) |
| Novo: churn por feature gap | reason_code "features" é #1 com 19% |

### Hipóteses descartadas ou enfraquecidas

| Hipótese | Por quê descartada |
|---------|------------------|
| H3 — SMB (seats baixo) → mais churn | plan_tier e seats têm distribuição tão uniforme que a diferença pode ser ruído |
| H7 — preceding_downgrade → churn | Apenas 8.5%; o sinal é fraco e o UPRADE (18.2%) é mais relevante |

### Novas hipóteses levantadas pelo EDA

| ID | Hipótese |
|----|---------|
| H8 | Upgrade nos 90 dias antes do churn → maior churn rate (buyer's remorse) |
| H9 | Alta proporção de tickets urgentes por conta → maior churn |
| H10 | Contas com is_trial=True têm maior churn rate |

---

## Correção crítica para o Agent 02

**TARGET VARIABLE ERRADA no código atual.**

O `02_cross_table_agent.py` usa `latest_churn.churned = 1` para marcar churn,
resultando em 352 contas (70.4%) marcadas como churned.

**Correto:** usar `a.churn_flag` de `accounts.csv` como target.
Resultado: 110 contas (22.0%) — churn rate real e utilizável pelo modelo.

**O churn_events deve fornecer apenas variáveis explicativas:**
`reason_code`, `preceding_upgrade_flag`, `preceding_downgrade_flag`, `refund_amount_usd`

Esta correção deve ser feita ANTES de rodar o Agent 02.

---

## O que o Agent 02 deve priorizar

1. **Usar `a.churn_flag` como target** (não churn_events.churned)
2. **Criar feature `preceding_upgrade_before_churn`** (18.2% dos churners — sinal forte)
3. **`satisfaction_no_response_rate`** — 41.2% de nulos é sinal, não ruído
4. **Tickets urgentes por conta** — proporção anormal de 25.7% dos tickets
5. **`auto_renew_false_rate`** — 19.9% das subs sem auto-renew por conta
6. **`mrr_is_zero` flag** — MRR = 0 existe em todos os tiers, precisa ser tratado
7. **`n_features_used`** — verificar se contas churned usam menos features distintas
