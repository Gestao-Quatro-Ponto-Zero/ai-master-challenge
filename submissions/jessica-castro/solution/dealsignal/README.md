# DealSignal — AI-Powered Deal Rating Engine

DealSignal ajuda times de vendas a priorizar oportunidades com base em **win probability** e **expected revenue**, usando uma abordagem inspirada em modelos de risco de crédito bancário.

---

## Arquitetura

```
CSVs → Enrichment → Feature Engineering → WoE → IV Selection → Logistic Regression → Rating → Streamlit
```

### Componentes

| Módulo | Responsabilidade |
|---|---|
| `enrichment/` | Enriquecimento via BrasilAPI, BuiltWith, Similarweb (+ mock determinístico) |
| `features/` | 16 features: deal momentum, deal size, seller/product stats, account strength |
| `model/` | WoETransformer, IV selector, LogisticRegressionCV + calibração isotônica |
| `utils/` | Logger, cache, explainability |
| `app/` | Interface Streamlit com filtros, KPIs e Top 10 prioritization |

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

## APIs externas (opcional)

O sistema funciona sem chaves de API — usa dados mock determinísticos por padrão.

Para ativar enriquecimento real:

```bash
export BUILTWITH_API_KEY=your_key_here
export SIMILARWEB_API_KEY=your_key_here
```

---

## Features

| Feature | Categoria | Descrição |
|---|---|---|
| `days_since_engage` | Deal Momentum | snapshot_date − engage_date |
| `pipeline_velocity` | Deal Momentum | days_since_engage / stage_index |
| `effective_value` | Deal Size | close_value ou sales_price (proxy) |
| `deal_value_percentile` | Deal Size | Percentile rank do valor |
| `agent_win_rate` | Seller Performance | Taxa histórica de vitória do agente |
| `agent_avg_deal_value` | Seller Performance | Valor médio dos deals ganhos |
| `product_win_rate` | Product Performance | Taxa de vitória por produto |
| `product_avg_deal_value` | Product Performance | Valor médio por produto |
| `revenue` | Account Strength | Receita da empresa |
| `employees` | Account Strength | Número de funcionários |
| `revenue_per_employee` | Account Strength | Receita / funcionários |
| `company_age` | Account Strength | Idade da empresa (anos) |
| `company_age_score` | Account Strength | company_age normalizado 0-1 |
| `digital_maturity_index` | Enrichment | Maturidade digital (0-1) |
| `digital_presence_score` | Enrichment | Presença digital (0-1) |
| `tech_stack_count` | Enrichment | Qtd. de tecnologias detectadas |

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
