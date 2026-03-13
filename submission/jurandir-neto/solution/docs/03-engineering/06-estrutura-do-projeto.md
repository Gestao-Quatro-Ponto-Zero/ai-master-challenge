# Estrutura do Projeto

```
ai-master-challenge/
│
├── data/
│   ├── raw/                        # CSVs brutos do Kaggle (não commitados)
│   │   ├── ravenstack_accounts.csv
│   │   ├── ravenstack_subscriptions.csv
│   │   ├── ravenstack_feature_usage.csv
│   │   ├── ravenstack_support_tickets.csv
│   │   └── ravenstack_churn_events.csv
│   ├── bronze/                     # Parquet — dados crus com metadados de ingestão
│   ├── silver/                     # Parquet — fatos e dimensões limpos
│   └── gold/                       # Parquet — tabelas de consumo do dashboard e agente
│
├── pipeline/
│   ├── bronze/
│   │   └── run_bronze.py           # Carrega CSVs → escreve Parquet bronze
│   ├── silver/
│   │   └── run_silver.py           # bronze → fatos e dimensões silver
│   └── gold/
│       └── run_gold.py             # silver → tabelas gold (dashboard_fact, risk, drivers...)
│
├── app/
│   ├── dashboard/
│   │   └── streamlit_app.py        # Interface do dashboard (filtros + gráficos + chat)
│   └── agent/
│       ├── agent.py                # Definição do agente Agno + tools
│       └── tools.py                # Tools tipadas: query_risk_accounts, lookup_cs_playbook, etc.
│
├── docs/
│   ├── README.md                   # Índice das 3 camadas SDD
│   ├── 01-business/
│   ├── 02-product/
│   └── 03-engineering/
│
├── .gitignore
├── LICENSE
└── README.md
```

## Responsabilidades por arquivo

### pipeline/bronze/run_bronze.py
- Lê cada CSV de `/data/raw/`
- Adiciona `_ingested_at` e `_source_file`
- Escreve um Parquet por tabela em `/data/bronze/`
- Não aplica nenhuma lógica de negócio

### pipeline/silver/run_silver.py
- Lê os Parquets bronze via DuckDB
- Aplica tipagem, limpeza e normalização
- Cria `dim_date`, `dim_account`, `dim_plan`, `dim_feature`
- Cria `fct_subscription`, `fct_feature_usage`, `fct_support_ticket`, `fct_churn_event`
- Escreve Parquets em `/data/silver/`

### pipeline/gold/run_gold.py
- Lê os Parquets silver via DuckDB
- Calcula `risk_score` e `risk_tier` por conta
- Agrega métricas por conta × período para `gold_dashboard_fact`
- Produz `gold_account_risk`, `gold_churn_drivers`, `gold_feature_retention`, `gold_support_health`
- Escreve Parquets em `/data/gold/`

### app/dashboard/streamlit_app.py
- Lê tabelas gold via DuckDB ou Pandas
- Renderiza filtros: seletor de período (year_month), segmentos (industry, country, channel, plan), feature
- Renderiza visualizações: churn rate, MRR perdido, contas em risco, correlação de features
- Renderiza o componente de chat do agente

### app/agent/agent.py
- Define o agente Agno com prompt de sistema contextualizado
- Importa as tools de `tools.py`
- Expõe função `run_agent(user_message, session_id)` usada pelo Streamlit

### app/agent/tools.py
- `query_risk_accounts(tier, limit)` → retorna contas de `gold_account_risk`
- `query_churn_drivers(segment_type, year_month)` → retorna de `gold_churn_drivers`
- `query_dashboard_fact(filters)` → query analítica em `gold_dashboard_fact`
- `lookup_cs_playbook(category)` → lê e retorna a seção correspondente do playbook
- `detect_anomaly(metric, period)` → compara período atual com média histórica
