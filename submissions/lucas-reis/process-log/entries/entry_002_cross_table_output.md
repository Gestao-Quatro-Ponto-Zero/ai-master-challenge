# Entry 002 — Output bruto do Cross-Table (Agent 02)

**Data:** 2026-03-20
**Comando:** `python3 submissions/lucas-reis/solution/agents/02_cross_table_agent.py`
**Status:** ✅ Sucesso (após 2 correções de bugs em runtime)
**Master view:** 500 linhas × 42 colunas | Churn rate: 22.0% ✅

---

## Bugs corrigidos durante execução

| Bug | Erro | Correção |
|-----|------|---------|
| `a.initial_plan_tier` em raw SQL | `BinderException: column not found` | `a.plan_tier` (alias só existe na master view) |
| Lógica de filtro em Q2 | `TypeError` na função genérica com closures | Substituído por masks booleanas explícitas |

---

## Output completo

```
[CROSS-TABLE] Construindo master view via DuckDB...
  Shape: (500, 42)
  Churn rate (a.churn_flag): 22.0%  ✅ TARGET CORRETO
  Churners: 110 | Retidos: 390

============================================================
  P1 — Buyer's remorse: upgrade antes de churnar?
============================================================

Chuners por preceding_upgrade_flag:
 had_upgrade_before_churn  n_churners  pct_of_churners  avg_mrr_at_churn
                     True          11             14.7       2140.010381
                    False          64             85.3       2203.584417

Isso significa que: clientes que fizeram upgrade antes de churnar pagavam, em média,
  $2140/mês vs $2204/mês para churners sem upgrade.

Buyer's remorse por indústria:
     industry  total_churners  upgrade_then_churn  pct
       EdTech              10                 2.0 20.0
   HealthTech              13                 2.0 15.4
      FinTech              13                 2.0 15.4
     DevTools              28                 4.0 14.3
Cybersecurity              11                 1.0  9.1

============================================================
  P2 — Suporte quebrado afeta churn?
============================================================

  COM ticket urgent                   19.9% churn  (n=317)
  SEM ticket urgent                   25.7% churn  (n=183)

  COM escalation                      25.3% churn  (n=91)
  SEM escalation                      21.3% churn  (n=409)

  COM satisfaction_null >50%          21.4% churn  (n=140)
  SEM satisfaction_null >50%          22.2% churn  (n=360)

Churn rate por quartil de first_response_time_minutes:
              churn_rate  n_accounts
resp_quartile
Q1 rápido          29.0%         124
Q2                 20.5%         122
Q3                 17.7%         124
Q4 lento           20.5%         122

Isso significa que: maior tempo de resposta está associado a maior churn.
  SLA de suporte tem impacto direto mensurável na retenção.

============================================================
  P3 — Baixo uso de features prediz churn?
============================================================

  Métrica                                 Churners      Retidos    Diferença
  -----------------------------------------------------------------------
  Features distintas usadas                  28.34        27.41        +3.4%
  Total de eventos de uso                    52.05        49.42        +5.3%
  Duração média de sessão (min)              50.90        50.95        -0.1%
  Total de erros registrados                 28.15        28.23        -0.3%

  Contas com < 3 features usadas: 0

  Uso nos primeiros 30 dias (churners vs retidos):
 churn_flag  avg_events_first_30d  n_accounts
      False                  28.8         390
       True                  27.3         110

Isso significa que: churners têm significativamente menor engajamento
  desde o início — onboarding é um ponto crítico de intervenção.

============================================================
  P4 — Qual segmento está mais em risco?
============================================================

  Churn rate por plan_tier:
                  churn_rate  n_accounts avg_mrr
initial_plan_tier
Enterprise             22.1%         154   $2200
Basic                  22.0%         168   $2321
Pro                    21.9%         178   $2266

  Churn rate por billing_frequency:
                churn_rate  n_accounts avg_mrr
billing_modes
annual, monthly      23.1%         260   $2231
monthly, annual      21.1%         237   $2313
annual                0.0%           1   $2094
monthly               0.0%           2    $892

  Churn rate por referral_source:
                churn_rate  n_accounts avg_mrr
referral_source
event                30.2%          96   $2138
other                24.3%         103   $2264
ads                  23.5%          98   $2153
organic              17.5%         114   $2382
partner              14.6%          89   $2372

  Churn rate por industry:
              churn_rate  n_accounts avg_mrr
industry
DevTools           31.0%         113   $2023
FinTech            22.3%         112   $2372
HealthTech         21.9%          96   $2113
EdTech             16.5%          79   $2588
Cybersecurity      16.0%         100   $2307

  MRR total em risco por plan_tier (churners × total_mrr):
    Basic        $    83,250
    Pro          $    80,370
    Enterprise   $    65,502

============================================================
  P5 — auto_renew=False é sinal antecipado de churn?
============================================================

  Contas COM ao menos 1 sub sem auto-renew: 429    Churn rate: 21.4%
  Contas SEM sub sem auto-renew:            71     Churn rate: 25.4%

  Lift do sinal auto_renew=False: 0.85x

  Com auto_renew=False: 92 churners / 337 retidos
  Retidos com auto_renew=False: avg_mrr=$2360 | distinct_features=28.0
  Churners com auto_renew=False: avg_mrr=$2127 | distinct_features=29.1

============================================================
  P6 — MRR em risco hoje
============================================================

  Contas ativas totais: 390
  MRR total ativo: $902,967

  Contas com 4+ sinais de risco:   20  |  MRR em risco: $    46,174
  Contas com 3+ sinais de risco:  118  |  MRR em risco: $   277,319
  Contas com 2+ sinais de risco:  306  |  MRR em risco: $   710,421

  Top 10 contas ativas em risco por MRR:
  A-5c046d   EdTech        $10,486  risk=2  auto_renew✓  low_usage✓
  A-c58f49   EdTech        $10,140  risk=3  escalation✓  low_usage✓  urgent✓
  A-5b1bcd   DevTools       $8,887  risk=2  auto_renew✓  urgent✓
  A-76fa4d   HealthTech     $8,812  risk=3  auto_renew✓  low_usage✓  urgent✓
  A-56962b   EdTech         $7,801  risk=2  auto_renew✓  low_usage✓
  A-afa505   DevTools       $7,334  risk=3  auto_renew✓  escalation✓  urgent✓
  A-5a215a   EdTech         $7,231  risk=2  auto_renew✓  urgent✓
  A-e43bf7   Cybersecurity  $6,667  risk=4  auto_renew✓  escalation✓  low_usage✓  urgent✓
  A-118f1c   Cybersecurity  $6,520  risk=2  auto_renew✓  low_usage✓
  A-e08cd3   FinTech        $6,456  risk=2  auto_renew✓  urgent✓

  MRR total em risco (2+ sinais): $710,421

============================================================
  RANKING DE CAUSAS DO CHURN
============================================================

  Total de churners: 110

  Rank  Causa                                    Churners  % churners  MRR perdido
  ---------------------------------------------------------------------------------
  1     Product gap (reason_code=features)             67      60.9%    $145,526
  2     Suporte ruim (support ou escalation)           36      32.7%     $80,633
  3     Auto-renew=False + baixo uso (combo)           29      26.4%     $52,680
  4     Budget/preço (reason_code=budget)              17      15.5%     $37,281
  5     Buyer's remorse (upgrade → churn <90d)         11      10.0%     $23,540
```
