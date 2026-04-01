# 🛠️ Arquitetura & Stack

## Visão Geral da Arquitetura

O sistema é composto por três camadas independentes que compartilham um núcleo (`core/`) de dados e lógica de negócio.

```
┌─────────────────────────────────────────────────────────┐
│                      DATA SOURCES                        │
│   accounts.csv · products.csv · sales_pipeline.csv      │
│   sales_teams.csv                                        │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                      core/                               │
│   data_loader.py      — CSVs, joins, load_benchmarks()   │
│   scoring_engine.py   — score, viabilidade, ação, etc.  │
│   features.py · pipeline_win_rate_buckets.py — auxiliares│
└──────────┬──────────────────────────┬───────────────────┘
           │                          │
           ▼                          ▼
┌──────────────────┐       ┌─────────────────────────────┐
│  streamlit_app/  │       │           api/               │
│  (Frontend A)    │       │      (FastAPI REST)          │
│                  │       │                              │
│  Análise e       │       │  Expõe os dados via HTTP     │
│  exploração de   │       │  para consumo do frontend    │
│  dados           │       │  React                       │
└──────────────────┘       └──────────┬──────────────────┘
                                      │
                                      ▼
                           ┌─────────────────────────────┐
                           │        frontend/             │
                           │    (React — Frontend B)      │
                           │                              │
                           │  Seller + Manager views      │
                           │  (consome a API)             │
                           └─────────────────────────────┘
```

---

## 📁 Estrutura de Pastas

```
deal-prioritization/
│
├── 📂 core/                          # Motor de dados e scoring (Python puro)
│   ├── data_loader.py                #   CSVs, joins, load_benchmarks(), preprocess
│   ├── scoring_engine.py             #   Urgência · Probabilidade · Valor · Score · Ação
│   ├── features.py                   #   Feature engineering auxiliar
│   ├── pipeline_win_rate_buckets.py  #   Faixas de tempo no pipeline (win rate)
│   └── __init__.py
│
├── 📂 data/
│   └── metrics/                      # CSVs originais do CRM
│       ├── accounts.csv
│       ├── products.csv
│       ├── sales_teams.csv
│       └── sales_pipeline.csv
│
├── 📂 docs/                          # Documentação em Markdown
│   ├── macro.md
│   ├── heuristica.md
│   ├── logica.md
│   ├── limitacoes.md
│   ├── stack.md                      #   Fonte desta página (Streamlit lê o arquivo)
│   ├── inicializacao.md
│   └── README.api.md                 #   Documentação dos endpoints REST
│
├── 📂 api/                           # FastAPI REST — porta 8001
│   ├── main.py                       #   App, CORS, routers, GET /benchmarks, warmup
│   ├── dependencies.py               #   Cache de benchmarks e DataFrame do pipeline
│   └── routers/
│       ├── deals.py                  #   /deals
│       ├── sellers.py                #   /sellers
│       ├── managers.py               #   /managers
│       ├── products.py               #   /products
│       ├── accounts.py               #   /accounts
│       └── analysis.py               #   /analysis/* (actions, pipeline, transfers, regional, products, alerts, …)
│
├── 📂 streamlit_app/                 # Frontend A — análise e exploração
│   ├── app.py                        #   Hub de navegação (st.navigation)
│   └── pages/
│       ├── Navegacao.py              #   Mapa do sistema
│       ├── Inicializacao.py          #   Como rodar os serviços
│       ├── Challenge.py
│       ├── Macro.py
│       ├── Como_funciona.py
│       ├── Heuristica.py
│       ├── Score_Model.py
│       ├── Limitacoes.py
│       ├── Stack.py                  #   Esta página (renderiza `docs/stack.md`)
│       ├── API.py
│       ├── Deal_List.py              #   Tabelas e listas
│       ├── Deal_Details.py
│       ├── Accounts_List.py
│       ├── Products_List.py
│       ├── Sellers_List.py
│       ├── Managers_List.py
│       ├── Raw_Pipeline.py           #   Pré-visualização dos CSVs brutos
│       ├── Raw_Accounts.py
│       ├── Raw_Products.py
│       ├── Raw_Teams.py
│       ├── Deals_Analysis.py         #   Análises e gráficos
│       ├── Action_Analysis.py
│       ├── Products_Analysis.py
│       ├── Regional_Analysis.py
│       ├── Seller_Analysis.py
│       └── Transfer_Analysis.py
│
├── 📂 frontend/                      # Frontend B — React + Vite
│   ├── index.html
│   ├── vite.config.ts                #   Alias @/ → ./src/
│   ├── package.json
│   └── src/
│       ├── main.tsx
│       ├── App.tsx                   #   Rotas, QueryClientProvider
│       ├── types/index.ts            #   Tipos (Deal, Seller, …)
│       ├── api/
│       │   ├── client.ts             #   apiFetch<T>() com VITE_API_URL
│       │   ├── deals.ts · sellers.ts · managers.ts · products.ts · accounts.ts
│       │   └── analysis.ts           #   endpoints de /analysis
│       ├── hooks/                    #   TanStack Query
│       │   ├── useDeals.ts · useSellers.ts · useManagers.ts · useProducts.ts · useAccounts.ts
│       │   ├── useRegionalAnalysis.ts · useProductsAnalysis.ts · useTransferAnalysis.ts
│       │   ├── useWonValueOverTime.ts · useGlobalAlerts.ts
│       │   └── …
│       ├── pages/
│       │   ├── Home.tsx              #   Manager view (dashboard)
│       │   └── SellerPage.tsx        #   Seller view
│       ├── components/
│       │   ├── MacroAnalysisDashboard.tsx · RegionalProductsAnalysis.tsx · GlobalAlertsPanel.tsx
│       │   ├── SellerAnalysisDrilldown.tsx · TransferFeed.tsx · TransferAnalysisCards.tsx
│       │   ├── ProjectCard.tsx · LeftCard.tsx · ProfileCard.tsx · SellerCard.tsx · …
│       │   └── charts/               #   Recharts (WonValueOverTime, ProspectingHealth, …)
│       └── lib/
│           ├── utils.ts              #   cn()
│           └── buildProspectingHealthData.ts
│
├── README.md
└── requirements.txt                  # Dependências Python
```

---

## Camadas do Sistema

### `core/` — Motor de dados e scoring

Núcleo compartilhado. Não tem dependência de framework — é Python puro.

| Arquivo | Responsabilidade |
|---|---|
| `data_loader.py` | Lê os CSVs, joins, `load_benchmarks()` (medianas, win rates, distribuições, top contas, etc.) |
| `scoring_engine.py` | Calcula Urgência, Probabilidade, Valor, Score final, Viabilidade e Ação recomendada |
| `features.py` | Feature engineering auxiliar |
| `pipeline_win_rate_buckets.py` | Faixas de tempo no pipeline para análise de win rate |

---

### `streamlit_app/` — Frontend A (análise e exploração)

Interface de análise construída em Python com Streamlit. Acessa o `core/` diretamente — sem API.

**Tecnologia:** Python 3.11 + Streamlit + Plotly + Pandas

**Uso:** Exploração de dados, validação do modelo, apresentação dos resultados.

**Estrutura (resumo):**
```
streamlit_app/
  app.py
  pages/
    Navegacao.py · Inicializacao.py · Challenge.py · Macro.py · Como_funciona.py
    Heuristica.py · Score_Model.py · Limitacoes.py · Stack.py · API.py
    Deal_List.py · Deal_Details.py · Accounts_List.py · Products_List.py
    Sellers_List.py · Managers_List.py
    Raw_Pipeline.py · Raw_Accounts.py · Raw_Products.py · Raw_Teams.py
    Deals_Analysis.py · Action_Analysis.py · Products_Analysis.py
    Regional_Analysis.py · Seller_Analysis.py · Transfer_Analysis.py
```

**Cache:** `@st.cache_data(ttl=3600)` em todas as páginas que carregam dados — evita reprocessamento a cada interação.

---

### `api/` — FastAPI REST

Exposição do motor de scoring via HTTP. É a ponte entre o `core/` e o frontend React.

**Tecnologia:** Python 3.11 + FastAPI + Uvicorn + Pydantic v2

**Rodar:** `uvicorn api.main:app --reload --port 8001` (a partir de `deal-prioritization/`)

**Swagger:** `http://localhost:8001/docs`

**Routers:**

| Prefixo | Endpoints | Descrição |
|---|---|---|
| `/deals` | `GET /deals`, `GET /deals/{id}` | Lista e detalhe de oportunidades com score |
| `/sellers` | `GET /sellers`, `GET /sellers/{agent}` | KPIs por vendedor |
| `/managers` | `GET /managers` | Performance agregada por manager |
| `/products` | `GET /products` | Métricas por produto |
| `/accounts` | `GET /accounts` | Contas com win rate e volume |
| `/analysis` | `GET /analysis/actions`, `/pipeline`, `/pipeline/time-medians`, `/transfers`, `/regional`, `/products`, `/alerts`, … | Agregações, pipeline, alertas |
| `/benchmarks` | `GET /benchmarks` | Medianas e win rates globais |
| `/health` | `GET /health` | Health check |

**Cache:** `functools.lru_cache(maxsize=1)` nos loaders de dados — a cache persiste durante o lifetime do processo Uvicorn.

---

### `frontend/` — Frontend B (React)

UI do **vendedor** (`/sellers/:agent`) e do **manager** (`/` — Home). Consome a API REST.

**Tecnologia:** React 18 + TypeScript + Vite + Tailwind CSS + TanStack Query + React Router v6 + Recharts

**Rodar:** `npm run dev` (a partir de `deal-prioritization/frontend/`)

**URL:** `http://localhost:5173`

**Estrutura:**
```
frontend/src/
  pages/        # Home.tsx (manager), SellerPage.tsx (vendedor)
  components/   # dashboards, feed, alertas, ProjectCard, charts/, …
  api/          # client.ts + fetchers (deals, sellers, analysis, …)
  hooks/        # TanStack Query (useDeals, useGlobalAlerts, useRegionalAnalysis, …)
  types/        # interfaces TypeScript
  lib/          # utils.ts, buildProspectingHealthData.ts, …
  App.tsx · main.tsx
```

**Estado atual:** Rotas principais e painéis (macro, produtos/regional, transfers, seller drilldown, alertas globais, seller view) implementados sobre a API.

---

## Decisões de Design

| Decisão | Motivação |
|---|---|
| Dois frontends | Streamlit permitiu validar o modelo rápido; React é o produto final escalável |
| `core/` desacoplado | Tanto Streamlit quanto FastAPI importam o mesmo código — sem duplicação de lógica |
| `lru_cache` na API | Cache simples sem dependência externa; adequado para dataset estático |
| `@st.cache_data` no Streamlit | Evita reload dos CSVs a cada rerenderização do Streamlit |
| Pydantic v2 | Validação de resposta e documentação automática via FastAPI |
| TanStack Query no React | Server state management com cache, loading e error states out-of-the-box |

---

## Como Rodar

```bash
# Streamlit
cd deal-prioritization
streamlit run streamlit_app/app.py

# API
cd deal-prioritization
uvicorn api.main:app --reload --port 8001

# Frontend React
cd deal-prioritization/frontend
npm run dev
```
