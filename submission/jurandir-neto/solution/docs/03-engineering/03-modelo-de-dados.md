# Modelo de Dados

## Star Schema — Camada Silver

```
                        dim_date
                           │
                           │ date_id
                           │
dim_account ──account_id── fct_churn_event
                           fct_support_ticket

dim_account ──account_id──▶ fct_subscription ──subscription_id──▶ fct_feature_usage
                  │                │
              dim_plan ◀──plan_id──┘          dim_feature ◀──feature_name──┘
```

---

## Schemas detalhados — Silver

### dim_date
```
date_id         DATE        PK
year            INT
quarter         INT         (1–4)
month           INT         (1–12)
month_name      VARCHAR
week            INT
day_of_week     INT         (0=segunda)
is_weekend      BOOLEAN
```

### dim_account
```
account_id          VARCHAR     PK
industry            VARCHAR
country             VARCHAR
acquisition_channel VARCHAR
plan_initial        VARCHAR
is_trial            BOOLEAN
_silver_processed_at TIMESTAMP
```

### dim_plan
```
plan_id             VARCHAR     PK   (gerado: plan_name + billing_frequency)
plan_name           VARCHAR
billing_frequency   VARCHAR     ('monthly' | 'annual')
```

### dim_feature
```
feature_name    VARCHAR     PK
is_beta         BOOLEAN
```

### fct_subscription
```
subscription_id     VARCHAR     PK
account_id          VARCHAR     FK → dim_account
plan_id             VARCHAR     FK → dim_plan
mrr                 FLOAT
arr                 FLOAT
has_upgrade         BOOLEAN
has_downgrade       BOOLEAN
start_date          DATE
end_date            DATE        (NULL se ativa)
_silver_processed_at TIMESTAMP
```

### fct_feature_usage
```
subscription_id     VARCHAR     FK → fct_subscription
feature_name        VARCHAR     FK → dim_feature
date_id             DATE        FK → dim_date
usage_count         INT
usage_duration      FLOAT
error_count         INT
_silver_processed_at TIMESTAMP
PK: (subscription_id, feature_name, date_id)
```

### fct_support_ticket
```
ticket_id               VARCHAR     PK
account_id              VARCHAR     FK → dim_account
date_id                 DATE        FK → dim_date
resolution_time         FLOAT       (horas)
first_response_time     FLOAT       (horas)
satisfaction_score      FLOAT       (1–5)
is_escalated            BOOLEAN
_silver_processed_at    TIMESTAMP
```

### fct_churn_event
```
account_id      VARCHAR     FK → dim_account
date_id         DATE        FK → dim_date
reason_code     VARCHAR
refund_value    FLOAT
feedback_text   TEXT
_silver_processed_at TIMESTAMP
PK: (account_id, date_id)
```

---

## Schema principal — Gold

### gold_dashboard_fact

Tabela central do Streamlit. Uma linha por conta por mês. Suporta todos os filtros do dashboard.

```
-- Chaves de segmentação (dimensões desnormalizadas)
account_id              VARCHAR
year_month              VARCHAR     (ex: '2024-11') ← filtro de data
industry                VARCHAR     ← filtro de segmento
country                 VARCHAR     ← filtro de segmento
acquisition_channel     VARCHAR     ← filtro de segmento
plan_name               VARCHAR     ← filtro de segmento
billing_frequency       VARCHAR     ← filtro de segmento
is_trial                BOOLEAN

-- Métricas financeiras
mrr                     FLOAT
arr                     FLOAT
has_downgrade_in_period BOOLEAN
churned_in_period       BOOLEAN
churn_reason_code       VARCHAR     (NULL se não churnou)
mrr_lost                FLOAT       (MRR da conta se churnou, 0 caso contrário)

-- Métricas de uso de features (agregadas por período)
total_usage_count       INT
total_usage_duration    FLOAT
total_error_count       INT
distinct_features_used  INT
top_feature             VARCHAR     ← filtro de feature
error_rate              FLOAT       (total_error_count / total_usage_count)

-- Métricas de suporte
ticket_count            INT
avg_resolution_time     FLOAT
avg_first_response_time FLOAT
avg_satisfaction_score  FLOAT
escalated_tickets       INT

-- Score de risco (calculado na gold)
risk_score              FLOAT       (0.0 – 1.0)
risk_tier               VARCHAR     ('low' | 'medium' | 'high' | 'critical')
```

### gold_account_risk
```
account_id              VARCHAR     PK
account_name            VARCHAR
industry                VARCHAR
country                 VARCHAR
mrr                     FLOAT
risk_score              FLOAT
risk_tier               VARCHAR
signal_low_usage        BOOLEAN
signal_high_errors      BOOLEAN
signal_bad_support      BOOLEAN
signal_downgrade        BOOLEAN
days_since_last_usage   INT
open_tickets            INT
last_satisfaction_score FLOAT
recommended_action      VARCHAR     (categoria do playbook de CS)
_calculated_at          TIMESTAMP
```

### gold_churn_drivers
```
year_month          VARCHAR
segment_type        VARCHAR     ('industry' | 'country' | 'channel' | 'plan')
segment_value       VARCHAR
churned_accounts    INT
total_accounts      INT
churn_rate          FLOAT
mrr_lost            FLOAT
top_reason_code     VARCHAR
_calculated_at      TIMESTAMP
```

### gold_feature_retention
```
feature_name            VARCHAR
year_month              VARCHAR
retained_avg_usage      FLOAT
churned_avg_usage       FLOAT
retained_avg_errors     FLOAT
churned_avg_errors      FLOAT
retention_lift          FLOAT   (razão entre uso de contas retidas vs churned)
_calculated_at          TIMESTAMP
```

### gold_support_health
```
year_month              VARCHAR
industry                VARCHAR
avg_resolution_time     FLOAT
avg_first_response_time FLOAT
avg_satisfaction_score  FLOAT
escalation_rate         FLOAT
pct_accounts_with_ticket FLOAT
churn_rate_high_tickets FLOAT   (churn entre contas com 3+ tickets no período)
_calculated_at          TIMESTAMP
```

---

## Cálculo do risk_score

O `risk_score` em `gold_account_risk` e `gold_dashboard_fact` é calculado como soma ponderada de sinais binários:

| Sinal | Condição | Peso |
|-------|----------|------|
| `signal_low_usage` | usage_count < 20% da média do segmento nos últimos 14 dias | 0.25 |
| `signal_high_errors` | error_rate > 2× a média do segmento nos últimos 7 dias | 0.25 |
| `signal_bad_support` | avg_satisfaction_score < 3.0 ou ticket escalado no último mês | 0.25 |
| `signal_downgrade` | downgrade nos últimos 60 dias | 0.25 |

**risk_tier:**
- `low`: score < 0.25
- `medium`: 0.25 ≤ score < 0.50
- `high`: 0.50 ≤ score < 0.75
- `critical`: score ≥ 0.75
