# Entry 004 — Output bruto do Agent Modelo Preditivo

**Data:** 2026-03-20
**Comando:** `python3 submissions/lucas-reis/solution/agents/04_predictive_agent.py`
**Dependências extras instaladas:** `brew install libomp`
**Status:** ✅ Sucesso (com warning SHAP — esperado)

---

## Output completo do terminal

```
/Users/lucasreis/Library/Python/3.9/lib/python/site-packages/shap/explainers/_tree.py:586: UserWarning:
LightGBM binary classifier with TreeExplainer shap values output has changed to a list of ndarray
  warnings.warn(

[MODEL] Iniciando pipeline Agent 04...

============================================================
  Step 1 — Build Features via DuckDB
============================================================
  Shape: (500, 22) | Churn: 22.0%

============================================================
  Step 2 — Treinamento LightGBM
============================================================

  Train: 400 (22.0% churn) | Test: 100 (22.0% churn)

  AUC-ROC:   0.3444

  Classification report (threshold=0.5):
              precision    recall  f1-score   support

    Retained       0.76      0.82      0.79        78
     Churned       0.12      0.09      0.11        22

    accuracy                           0.66       100
   macro avg       0.44      0.46      0.45       100
weighted avg       0.62      0.66      0.64       100


============================================================
  Step 3 — SHAP Analysis
============================================================

  Rank  Feature                              SHAP Importance         Direção
  -------------------------------------------------------------------------
  1     avg_error_count                               0.9159   ↓ menos churn
  2     avg_mrr                                       0.7644   ↓ menos churn
  3     seats                                         0.5851    ↑ mais churn
  4     avg_usage_duration_min                        0.4926   ↓ menos churn
  5     industry                                      0.4556    ↑ mais churn
  6     distinct_features_used                        0.4460    ↑ mais churn
  7     n_upgrades                                    0.2830    ↑ mais churn
  8     avg_session_count                             0.2661   ↓ menos churn
  9     preceding_upgrade_flag                        0.2134   ↓ menos churn
  10    n_urgent_tickets                              0.2073   ↓ menos churn

============================================================
  Step 4 — Churn Scores por Conta
============================================================

  Distribuição de risk_tier:
    HIGH       99 contas  (19.8%)
    MEDIUM      8 contas  (1.6%)
    LOW       393 contas  (78.6%)

============================================================
  Step 5 — Lista de Ação Imediata para CS
============================================================

  Contas HIGH risk e ainda ativas: 10
  MRR total em risco: $12,231

  Top 20 para intervenção imediata do CS:

  Account ID    Score       MRR Industry       Canal      Top Risk Factor                Dias Cliente
  ----------------------------------------------------------------------------------------------------
  A-49b828        73 $   2,222 FinTech        ads        seats                                  1050
  A-94d3da        72 $   1,889 HealthTech     other      avg_error_count                        1052
  A-e36807        97 $   1,257 EdTech         other      avg_usage_duration_min                  672
  A-bad8c1        89 $   1,114 FinTech        organic    avg_error_count                        1115
  A-9289f6        76 $   1,091 EdTech         event      avg_mrr                                1024
  A-5247b3        76 $   1,072 FinTech        partner    avg_mrr                                 738
  A-3cc791        73 $   1,065 EdTech         other      avg_mrr                                 800
  A-6a4e2d        88 $     945 EdTech         partner    avg_mrr                                1078
  A-019782        95 $     928 DevTools       event      avg_mrr                                1066
  A-c42f1f        96 $     647 HealthTech     other      avg_usage_duration_min                  600

  ✅ churn_scores.csv salvo em: .../submissions/lucas-reis/solution/churn_scores.csv

============================================================
  RESUMO FINAL
============================================================
  AUC-ROC:                0.3444
  Contas HIGH risk ativas: 10
  MRR em risco imediato:  $12,231
  Top feature (SHAP):     avg_error_count (↓ menos churn)
```

---

## Artefato gerado

**`solution/churn_scores.csv`** — 500 linhas × 11 colunas:
- account_id, churn_probability, churn_score, risk_tier
- top_risk_factor_1, top_risk_factor_2, top_risk_factor_3
- industry, acquisition_channel, mrr, churned
