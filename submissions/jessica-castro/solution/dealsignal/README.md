# DealSignal — AI-Powered Deal Rating Engine

DealSignal ajuda times de vendas a priorizar oportunidades com base em **win probability** e **expected revenue**, usando uma abordagem inspirada em modelos de risco de crédito bancário.

---

## Arquitetura

```
CSVs → Enrichment → Feature Engineering (79 features) → Target Encoding + Scaler
     → L1 Feature Selection → Logistic Regression → Rating → Health → Priority Engine
     → Streamlit Dashboard
     → FastAPI REST (scoring em tempo real + envio de email)
```

### Componentes

| Módulo | Responsabilidade |
|---|---|
| `api.py` | API REST (FastAPI): `/score`, `/notify-email`, `/notify-email/preview` |
| `config/` | Constantes centralizadas: rating thresholds, paletas de cores, parâmetros WoE |
| `enrichment/` | Enriquecimento via BrasilAPI, BuiltWith, Similarweb (+ mock determinístico) |
| `features/` | 79 features (V3+V4): deal momentum, seller/product stats, account strength, lead/geo, interaction terms |
| `model/` | Target encoder, StandardScaler, LogisticRegression, health/priority engines |
| `engine/` | Friction engine (execucao/decisao/urgencia/valor) + Next Best Action |
| `utils/` | Logger, cache, explainability, sinais, geração de relatórios PDF/CSV |
| `app/` | Interface Streamlit com filtros, KPIs e Top 10 prioritization |
| `app/ui/` | Módulos de UI: formatters, loaders, filtros, signal builder, deal panel |

---

## Estrutura de Pastas

```
dealsignal/
├── api.py                        # API REST FastAPI (score + notify-email)
├── run_pipeline.py               # Orquestrador do pipeline completo
├── requirements.txt
├── config/
│   └── constants.py          # Constantes centralizadas (ratings, paletas, thresholds)
├── app/
│   ├── streamlit_app.py      # Entry point da UI (~150 linhas)
│   └── ui/
│       ├── ui_constants.py   # CSS, estilos de gráficos, textos de interpretação
│       ├── formatters.py     # Formatadores de valores e badges HTML
│       ├── data_loaders.py   # Carregamento e cache dos dados
│       ├── filters.py        # Lógica de filtros em cascata
│       ├── signals_builder.py# Payload de sinais por deal
│       └── deal_panel.py     # Renderização do painel de análise
├── features/
│   ├── feature_columns.py    # FEATURE_COLS_V2, STAGE_INDEX, normalização
│   ├── data_merger.py        # Joins dos CSVs + colunas base numéricas
│   ├── feature_engineering.py# Orquestrador de features (chama todos os módulos)
│   ├── deal_features.py      # Features de momentum e tamanho do deal
│   ├── seller_features.py    # Features do vendedor (win rate, velocidade, load)
│   ├── product_features.py   # Features de produto (win rate, ciclo de venda)
│   ├── account_features.py   # Features de conta (tamanho, idade, score)
│   ├── risk_features.py      # Flags de risco (estagnação, sobrecarga, produto fraco)
│   ├── interaction_features.py# [EXPERIMENTAL] V3: interaction terms e buckets
│   └── feature_store.py      # Persistência Parquet/CSV
├── model/
│   ├── logistic_model.py     # DealScoringModel (LogRegCV + calibração)
│   ├── woe_transformer.py    # WoE binning e transformação
│   ├── feature_selection_iv.py# Seleção por Information Value
│   ├── rating_engine.py      # AAA–CCC rating assignment
│   ├── health_engine.py      # Deal health score (0-100)
│   ├── priority_engine.py    # Priority tier (win_prob × value × health)
│   └── artifacts/            # .pkl e .json do modelo treinado
├── enrichment/
│   ├── api_clients.py        # REST clients com retry (BrasilAPI, BuiltWith, Similarweb)
│   ├── company_enrichment.py # CNPJ lookup via BrasilAPI
│   └── digital_enrichment.py # Maturidade digital + mock determinístico
├── utils/
│   ├── logger.py             # Logging (console + arquivo)
│   ├── cache.py              # Serialização de artefatos (.pkl)
│   ├── signals.py            # Mapeamento feature → engine e badges de sinal
│   ├── explainability.py     # Contribuição local por feature (top fatores)
│   └── report.py             # Exportação PDF e CSV
├── experiments/              # Scripts de ablation e comparação de modelos
├── data/                     # CSVs de entrada e resultados
└── .env.example              # Template de variáveis de ambiente
```

---

## Instalação

```bash
cd dealsignal
pip install -r requirements.txt
```

---

## Execução

### 1. Pipeline completo (enriquecimento + treino + scoring)

```bash
python run_pipeline.py
```

### 2. Forçar re-execução do enrichment

```bash
python run_pipeline.py --force-enrich
```

### 3. Forçar re-treino do modelo

```bash
python run_pipeline.py --force-train
```

### 4. Subir a API REST (FastAPI)

```bash
uvicorn api:app --reload --port 8000
```

| Interface | URL |
|---|---|
| Swagger UI (docs interativas) | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

### 5. Rodar o dashboard Streamlit

```bash
streamlit run app/streamlit_app.py
```

| Interface | URL |
|---|---|
| Dashboard Streamlit | http://localhost:8501 |

---

## API REST

A API expõe scoring em tempo real e envio de prioridades por email.

### Endpoints

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/health` | Status do servidor e modelo |
| `POST` | `/score` | Recebe dados de um deal e retorna score completo |
| `POST` | `/notify-email` | Envia email com os deals prioritários via SMTP |
| `POST` | `/notify-email/preview` | Retorna o HTML do email sem enviar — sem SMTP necessário |

### POST /score — exemplo

```bash
curl -X POST http://localhost:8000/score \
  -H "Content-Type: application/json" \
  -d '{
    "sales_agent": "Diego Ferreira",
    "product": "Finance Management",
    "effective_value": 25000.0,
    "engage_date": "2024-10-01",
    "deal_stage": "Engaging"
  }'
```

### POST /notify-email — exemplo

```bash
curl -X POST http://localhost:8000/notify-email \
  -H "Content-Type: application/json" \
  -d '{
    "recipients": ["gestor@empresa.com"],
    "deals": [
      {
        "account_name": "Conta Azul",
        "final_score": 42,
        "rating": "C",
        "friction": "high",
        "win_probability": 0.42,
        "days_in_stage": 28,
        "next_action": "Mapear decisor"
      }
    ]
  }'
```

### POST /notify-email/preview — teste sem SMTP

```bash
curl -X POST http://localhost:8000/notify-email/preview \
  -H "Content-Type: application/json" \
  -d '{
    "deals": [
      {
        "account_name": "Conta Azul",
        "final_score": 42,
        "rating": "C",
        "friction": "high",
        "win_probability": 0.42,
        "days_in_stage": 28,
        "next_action": "Mapear decisor"
      }
    ]
  }'
```

Retorna HTML renderizado — ideal para testar via `/docs` sem configurar SMTP.

### Regras de prioridade (`/notify-email`)

Um deal é considerado prioritário se qualquer condição for verdadeira:

- `rating == "C"`
- `friction == "high"`
- `days_in_stage > 20`
- `win_probability < 0.55`

Os 5 deals com maior `priority_score` são incluídos no email:

```
priority_score = (100 - final_score) + (days_in_stage × 1.5) + friction_weight
friction_weight: high=20 | medium=10 | low=0
```

---

## Variáveis de Ambiente

Copie `.env.example` para `.env` e preencha conforme necessário:

```bash
cp .env.example .env
```

| Variável | Obrigatório | Descrição |
|---|---|---|
| `BUILTWITH_API_KEY` | Não | Chave da API BuiltWith para tech-stack enrichment |
| `SIMILARWEB_API_KEY` | Não | Chave da API Similarweb para dados de tráfego |
| `LOG_LEVEL` | Não | Nível de log: `DEBUG` / `INFO` / `WARNING` (padrão: `INFO`) |
| `SMTP_HOST` | Sim (notify-email) | Servidor SMTP (ex: `smtp.gmail.com`) |
| `SMTP_PORT` | Não | Porta SMTP (padrão: `587`) |
| `SMTP_USER` | Sim (notify-email) | Usuário SMTP |
| `SMTP_PASSWORD` | Sim (notify-email) | Senha SMTP |
| `SMTP_SENDER` | Não | Remetente (padrão: `SMTP_USER`) |

O sistema funciona sem chaves de enrichment — usa dados mock determinísticos por padrão.
O endpoint `/notify-email/preview` funciona sem qualquer configuração SMTP.

---

## Features (V3+V4 — produção)

O modelo usa **79 features** divididas em 48 numéricas e 31 target-encoded (TE).

### Numéricas (48)

| Grupo | Features |
|---|---|
| Seller Power | `seller_win_rate`, `seller_rank_percentile`, `seller_close_speed`, `seller_product_experience`, `seller_pipeline_load`, `seller_product_win_rate` |
| Deal Momentum | `log_days_since_engage`, `deal_age_percentile` |
| Deal Size | `log_deal_value`, `deal_value_percentile`, `deal_value_percentile_within_seller`, `deal_value_percentile_within_product`, `deal_value_vs_account_size` |
| Product Performance | `product_win_rate`, `product_rank_percentile`, `product_avg_sales_cycle`, `product_relative_performance` |
| Account Strength | `account_size_percentile`, `digital_maturity_index`, `revenue_per_employee`, `company_age_score` |
| Risk Flags | `is_stale_flag`, `is_very_old_deal`, `seller_overloaded_flag`, `low_product_performance_flag`, `deal_estagnado`, `deal_muito_antigo`, `produto_fraco`, `conta_fraca` |
| Buckets | `bucket_deal_age`, `bucket_deal_value`, `bucket_account_size` |
| Interaction Terms | `interact_seller_product`, `interact_seller_value`, `interact_product_age`, `interact_account_value` |
| Lead / Geo (V4) | `lead_source_wr`, `lead_origin_wr`, `lead_quality_score`, `activity_count`, `has_activity`, `last_activity_is_positive`, `lead_tag_wr`, `country_wr`, `is_india`, `contact_role_wr`, `last_activity_type_wr`, `page_views_per_visit` |

### Target-Encoded (31)

Colunas categóricas (`sales_agent`, `product`, `city`, `country`, `lead_source`, `lead_origin`, `lead_quality`, `lead_tag`, `last_activity_type`, `office`, `manager`, etc.) transformadas com target encoding (mean de `won`, smoothing m=10).

---

## Rating

| Rating | Win Probability |
|---|---|
| AAA | > 90% |
| AA | 80–90% |
| A | 70–80% |
| BBB | 60–70% |
| BB | 50–60% |
| B | 40–50% |
| CCC | < 40% |

**Expected Revenue** = win_probability × effective_value

---

## Outputs

- `data/enriched_accounts.csv` — dados de contas enriquecidos
- `data/results.csv` — deals abertos com win_probability, rating, expected_revenue
- `model/artifacts/` — artefatos do modelo treinado
- `logs/dealsignal.log` — logs de execução

---

## Dados

| Arquivo | Linhas | Descrição |
|---|---|---|
| `accounts.csv` | 85 | Empresas clientes |
| `products.csv` | 7 | Produtos e preços |
| `sales_teams.csv` | 35 | Agentes, managers, offices |
| `sales_pipeline.csv` | ~8.800 | Oportunidades do CRM |
