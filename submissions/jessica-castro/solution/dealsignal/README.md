# DealSignal — AI-Powered Deal Rating Engine

DealSignal ajuda times de vendas a priorizar oportunidades com base em **win probability** e **expected revenue**, usando uma abordagem inspirada em modelos de risco de crédito bancário.

---

## Arquitetura

```
CSVs → Enrichment → Feature Engineering → WoE → IV Selection → Logistic Regression
     → Rating → Health Engine → Priority Engine → Streamlit
```

### Componentes

| Módulo | Responsabilidade |
|---|---|
| `config/` | Constantes centralizadas: rating thresholds, paletas de cores, parâmetros WoE |
| `enrichment/` | Enriquecimento via BrasilAPI, BuiltWith, Similarweb (+ mock determinístico) |
| `features/` | 16 features V2: deal momentum, deal size, seller/product stats, account strength |
| `model/` | WoETransformer, IV selector, LogisticRegressionCV + calibração, health/priority engines |
| `utils/` | Logger, cache, explainability, geração de relatórios PDF/CSV |
| `app/` | Interface Streamlit com filtros, KPIs e Top 10 prioritization |
| `app/ui/` | Módulos de UI: formatters, loaders, filtros, signal builder, deal panel |

---

## Estrutura de Pastas

```
dealsignal/
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
├── .env.example              # Template de variáveis de ambiente
├── run_pipeline.py           # Orquestrador do pipeline completo
└── requirements.txt
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

### 4. Rodar a aplicação Streamlit

```bash
streamlit run app/streamlit_app.py
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

O sistema funciona sem chaves — usa dados mock determinísticos por padrão.

---

## Features (V2 — produção)

| Feature | Categoria | Descrição |
|---|---|---|
| `seller_win_rate` | Seller Power | Taxa histórica de vitória do vendedor |
| `seller_rank_percentile` | Seller Power | Percentile rank do vendedor no time |
| `seller_close_speed` | Seller Power | Velocidade média de fechamento (dias) |
| `seller_product_experience` | Seller Power | Qtd. de deals pelo combo vendedor×produto |
| `seller_pipeline_load` | Seller Power | Deals em aberto do vendedor |
| `log_days_since_engage` | Deal Momentum | Log(snapshot_date − engage_date) |
| `log_deal_value` | Deal Size | Log(effective_value) |
| `deal_value_percentile` | Deal Size | Percentile rank do valor do deal |
| `is_stale_flag` | Stagnation Risk | Deal na faixa ≥ 75º percentil de idade |
| `product_win_rate` | Product Performance | Taxa histórica de vitória por produto |
| `product_rank_percentile` | Product Performance | Percentile rank do produto |
| `product_avg_sales_cycle` | Product Performance | Ciclo médio de fechamento (dias) |
| `account_size_percentile` | Account Strength | Percentile rank por receita |
| `digital_maturity_index` | Enrichment | Maturidade digital (0-1) |
| `revenue_per_employee` | Account Strength | Receita / funcionários |
| `company_age_score` | Account Strength | Idade da empresa normalizada 0-1 |

### Features experimentais (V3)

O módulo `features/interaction_features.py` implementa features V3 (interaction terms,
buckets, cross-features seller×produto) que foram desenvolvidas e testadas mas excluídas
da produção pois não melhoraram o AUC além do baseline V2. Consulte o docstring do
módulo antes de utilizá-las.

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
