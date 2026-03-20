# Entry 001 — Output bruto do EDA (Agent 01)

**Data:** 2026-03-20
**Comando executado:** `python3 submissions/lucas-reis/solution/agents/01_eda_agent.py`
**Duração:** < 5s
**Status:** ✅ Sucesso

---

## Output completo do terminal

```
============================================================
  ravenstack_accounts.csv
============================================================

Shape: 500 linhas × 10 colunas

Colunas e tipos:
  account_id                object
  account_name              object
  industry                  object
  country                   object
  signup_date               datetime64[us]
  referral_source           object
  plan_tier                 object
  seats                     int64
  is_trial                  bool
  churn_flag                bool

% nulos por coluna:
  account_id                0.00%
  account_name              0.00%
  industry                  0.00%
  country                   0.00%
  signup_date               0.00%
  referral_source           0.00%
  plan_tier                 0.00%
  seats                     0.00%
  is_trial                  0.00%
  churn_flag                0.00%

Valores únicos — colunas categóricas:

  industry (5 únicos):
    DevTools                   113  (22.6%)
    FinTech                    112  (22.4%)
    Cybersecurity              100  (20.0%)
    HealthTech                  96  (19.2%)
    EdTech                      79  (15.8%)

  country (7 únicos):
    US                         291  (58.2%)
    UK                          58  (11.6%)
    IN                          49  (9.8%)
    AU                          32  (6.4%)
    DE                          25  (5.0%)
    CA                          23  (4.6%)
    FR                          22  (4.4%)

  referral_source (5 únicos):
    organic                    114  (22.8%)
    other                      103  (20.6%)
    ads                         98  (19.6%)
    event                       96  (19.2%)
    partner                     89  (17.8%)

  plan_tier (3 únicos):
    Pro                        178  (35.6%)
    Basic                      168  (33.6%)
    Enterprise                 154  (30.8%)

  is_trial = True: 97 contas (19.4%)
  churn_flag = True: 110 contas (22.0%)

============================================================
  ravenstack_subscriptions.csv
============================================================

Shape: 5000 linhas × 14 colunas

% nulos por coluna:
  subscription_id                0.00%
  account_id                     0.00%
  start_date                     0.00%
  end_date                       90.28% ⚠️
  plan_tier                      0.00%
  seats                          0.00%
  mrr_amount                     0.00%
  arr_amount                     0.00%
  is_trial                       0.00%
  upgrade_flag                   0.00%
  downgrade_flag                 0.00%
  churn_flag                     0.00%
  billing_frequency              0.00%
  auto_renew_flag                0.00%

MRR por plan_tier (médio | mediano | min | max):
  Basic        mean=  474.68  median=  380.00  min=   0.00  max= 3097.00  n=1602
  Enterprise   mean= 4917.71  median= 3781.00  min=   0.00  max=33830.00  n=1723
  Pro          mean= 1256.77  median=  980.00  min=   0.00  max= 9261.00  n=1675

  downgrade_flag = True: 218 (4.4%)
  upgrade_flag = True: 529 (10.6%)
  auto_renew_flag = False: 995 (19.9%)

Distribuição billing_frequency:
  monthly          2539  (50.8%)
  annual           2461  (49.2%)

============================================================
  ravenstack_feature_usage.csv
============================================================

Shape: 25000 linhas × 8 colunas

% nulos por coluna:
  usage_id                       0.00%
  subscription_id                0.00%
  usage_date                     0.00%
  feature_name                   0.00%
  usage_count                    0.00%
  usage_duration_secs            0.00%
  error_count                    0.00%
  is_beta_feature                0.00%

Top 10 features por uso total (usage_count):
  feature_32                              6686  (2.7% do total)
  feature_15                              6621  (2.6% do total)
  feature_6                               6546  (2.6% do total)
  feature_20                              6541  (2.6% do total)
  feature_34                              6536  (2.6% do total)
  feature_12                              6534  (2.6% do total)
  feature_11                              6533  (2.6% do total)
  feature_2                               6525  (2.6% do total)
  feature_38                              6478  (2.6% do total)
  feature_26                              6470  (2.6% do total)

Média de error_count por feature (top 10 com mais erros):
  feature_4                           0.669 erros/evento
  feature_9                           0.647 erros/evento
  feature_26                          0.643 erros/evento
  feature_16                          0.637 erros/evento
  feature_18                          0.628 erros/evento
  feature_2                           0.625 erros/evento
  feature_40                          0.612 erros/evento
  feature_34                          0.611 erros/evento
  feature_13                          0.608 erros/evento
  feature_19                          0.598 erros/evento

  is_beta_feature = True: 2544 eventos (10.2%)

usage_duration_secs:
  média:   3042.2s  (50.7 min)
  mediana: 2760.0s  (46.0 min)
  p95:     6855.0s  (114.2 min)
  max:     12696.0s  (211.6 min)

============================================================
  ravenstack_support_tickets.csv
============================================================

Shape: 2000 linhas × 9 colunas

% nulos por coluna:
  ticket_id                           0.00%
  account_id                          0.00%
  submitted_at                        0.00%
  closed_at                           0.00%
  resolution_time_hours               0.00%
  priority                            0.00%
  first_response_time_minutes         0.00%
  satisfaction_score                  41.25% ⚠️
  escalation_flag                     0.00%

Distribuição de priority:
  urgent       514  (25.7%)
  high         510  (25.5%)
  medium       491  (24.6%)
  low          485  (24.2%)

  escalation_flag = True: 95 tickets (4.8%)

  satisfaction_score:
    média (respondidos):  3.98 / 5.0
    nulos (não-resposta): 825 (41.2%)  ← sinal de desengajamento

  first_response_time_minutes (média por priority):
    urgent     85.5 min
    medium     85.9 min
    low        91.2 min
    high       91.4 min

  resolution_time_hours: média=35.9h  p95=69.0h

============================================================
  ravenstack_churn_events.csv
============================================================

Shape ANTES deduplicação: 600 linhas × 9 colunas
Shape APÓS deduplicação (1 por account_id): 352 linhas
  Registros de reativação removidos: 248 (is_reactivation=True em 61 registros originais)

% nulos por coluna (dataset completo):
  churn_event_id                      0.00%
  account_id                          0.00%
  churn_date                          0.00%
  reason_code                         0.00%
  refund_amount_usd                   0.00%
  preceding_upgrade_flag              0.00%
  preceding_downgrade_flag            0.00%
  is_reactivation                     0.00%
  feedback_text                       24.67% ⚠️

Top 5 reason_code:
  features               67  (19.0%)
  support                62  (17.6%)
  budget                 62  (17.6%)
  competitor             56  (15.9%)
  unknown                55  (15.6%)

  is_reactivation = True (deduplicado): 37 (10.5%)
  preceding_downgrade_flag = True: 30 (8.5%)
  preceding_upgrade_flag = True: 64 (18.2%)

  refund_amount_usd:
    total: $5,030.58
    contas com reembolso: 89 (25.3%)

============================================================
  RESUMO EXECUTIVO
============================================================

Taxa de churn geral: 352 / 500 contas = 70.4%
  (accounts.churn_flag confirma: 22.0%)

Maior RED FLAG encontrado nos dados:
  → A identificar após EDA completo (ver entry_001_eda_analysis.md)

3 hipóteses sugeridas pelos números:
  H1: Contas com baixo distinct_features_used têm maior churn
  H2: Tickets escalados (escalation_flag=True) precedem churns
  H3: Clientes com billing_frequency=monthly têm maior churn que annual
```

---

## Dependências instaladas durante execução

```bash
pip3 install duckdb pandas numpy
```

Motivo: ambiente sem virtualenv configurado. `duckdb` e `pandas` não estavam disponíveis
no Python 3 do sistema (`/usr/bin/python3`). Instalados via pip3 do sistema e funcionando.
