# Arquitetura Medallion

## Visão geral do fluxo

```
/data/raw/*.csv
      │
      ▼  pipeline/bronze/run_bronze.py
/data/bronze/*.parquet   (dados crus, sem transformação)
      │
      ▼  pipeline/silver/run_silver.py
/data/silver/*.parquet   (limpos, tipificados, fatos e dimensões)
      │
      ▼  pipeline/gold/run_gold.py
/data/gold/*.parquet     (agregados, enriquecidos, prontos para consumo)
      │
      ├──▶ app/dashboard/  (Streamlit)
      └──▶ app/agent/      (Agno)
```

## Camada Bronze — Dados brutos

**Princípio:** Preservar os dados exatamente como vieram da fonte. Zero transformação de negócio.

**O que acontece nessa camada:**
- Leitura dos CSVs de `/data/raw/`
- Inferência mínima de tipos (datas como string, numerics como float)
- Adição de metadados de ingestão: `_ingested_at`, `_source_file`
- Escrita em Parquet particionado por arquivo de origem

**Tabelas produzidas:**

| Tabela | Origem |
|--------|--------|
| `bronze_accounts` | `ravenstack_accounts.csv` |
| `bronze_subscriptions` | `ravenstack_subscriptions.csv` |
| `bronze_feature_usage` | `ravenstack_feature_usage.csv` |
| `bronze_support_tickets` | `ravenstack_support_tickets.csv` |
| `bronze_churn_events` | `ravenstack_churn_events.csv` |

---

## Camada Silver — Dados limpos e modelados

**Princípio:** Dados confiáveis, tipificados corretamente, organizados em fatos e dimensões. Sem agregações — granularidade preservada.

**O que acontece nessa camada:**
- Conversão de tipos (datas, booleans, floats)
- Tratamento de nulos e inconsistências
- Normalização de strings (uppercase em categorias, trim)
- Construção do modelo dimensional (star schema)
- Adição de `_silver_processed_at`

### Tabelas de Dimensão

| Tabela | Chave | Origem | Conteúdo |
|--------|-------|--------|----------|
| `dim_date` | `date_id` | gerada | Calendário completo (ano, mês, trimestre, semana, dia da semana) |
| `dim_account` | `account_id` | bronze_accounts | Indústria, país, canal de aquisição, flag trial — campos limpos |
| `dim_plan` | `plan_id` | bronze_subscriptions | Nome do plano, billing_frequency |
| `dim_feature` | `feature_name` | bronze_feature_usage | Nome da feature, flag is_beta |

### Tabelas Fato

| Tabela | Granularidade | Chaves | Métricas |
|--------|--------------|--------|---------|
| `fct_subscription` | 1 linha por assinatura | `subscription_id`, `account_id`, `plan_id` | `mrr`, `arr`, `has_upgrade`, `has_downgrade` |
| `fct_feature_usage` | 1 linha por (subscription × feature × dia) | `subscription_id`, `feature_name`, `date_id` | `usage_count`, `usage_duration`, `error_count` |
| `fct_support_ticket` | 1 linha por ticket | `ticket_id`, `account_id`, `date_id` | `resolution_time`, `first_response_time`, `satisfaction_score`, `is_escalated` |
| `fct_churn_event` | 1 linha por evento de churn | `account_id`, `date_id` | `reason_code`, `refund_value`, `feedback_text` |

---

## Camada Gold — Dados prontos para consumo

**Princípio:** Tabelas desnormalizadas, pré-agregadas e enriquecidas, otimizadas para o dashboard e o agente. Nenhuma query complexa deve acontecer no Streamlit.

**O que acontece nessa camada:**
- Joins entre fatos e dimensões
- Cálculo de métricas derivadas (churn_rate por segmento, risk_score por conta)
- Agregações por período, segmento e feature
- Janelas temporais para detecção de anomalias

### Tabelas Gold

| Tabela | Consumidor | Descrição |
|--------|-----------|-----------|
| `gold_dashboard_fact` | Streamlit | Tabela principal do dashboard — ver modelo em `03-modelo-de-dados.md` |
| `gold_account_risk` | Streamlit + Agente | Score de risco por conta ativa, com sinais detalhados |
| `gold_churn_drivers` | Agente | Drivers de churn agregados por segmento e período |
| `gold_feature_retention` | Streamlit + Agente | Correlação de uso de features com retenção/churn |
| `gold_support_health` | Streamlit + Agente | Saúde do suporte por conta e período |
