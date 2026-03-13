# RavenStack Churn Intelligence

Sistema de inteligência de churn para a RavenStack — uma plataforma SaaS B2B de gerenciamento de projetos. O negócio enfrenta churn crescente e este sistema entrega respostas às causas raiz, não apenas dashboards.

---

## O que o sistema entrega

- **Pipeline de dados** — raw → bronze → silver → gold usando DuckDB + Parquet
- **Dashboard interativo** — análise exploratória de churn com filtros por segmento, período e fator de risco (Streamlit + Plotly)
- **Agente de IA** — responde perguntas de negócio sobre churn em linguagem natural (Agno + Claude)

---

## Arquitetura

```
data/raw/*.csv
      │
      ▼
┌─────────────┐
│   BRONZE    │  pipeline/bronze/run_bronze.py
│  (Parquet)  │  Ingestão direta, sem transformação
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   SILVER    │  pipeline/silver/run_silver.py
│  (Parquet)  │  Limpeza, tipagem, deduplicação, enriquecimento
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    GOLD     │  pipeline/gold/run_gold.py
│  (Parquet)  │  Métricas agregadas, risk scores, drivers de churn
└──────┬──────┘
       │
       ├──────────────────────┐
       ▼                      ▼
┌─────────────┐      ┌──────────────────┐
│  DASHBOARD  │      │     AGENTE       │
│  Streamlit  │      │  Agno + Claude   │
│ :8501       │      │  (via terminal)  │
└─────────────┘      └──────────────────┘
```

---

## Como rodar

### Docker (recomendado)

**Pré-requisito:** Docker Desktop instalado e `ANTHROPIC_API_KEY` disponível.

```bash
# Clone o repositório
git clone <url-do-repo>
cd ai-master-challenge

# Defina sua chave da API (ou coloque em um arquivo .env)
export ANTHROPIC_API_KEY=sk-ant-...

# Suba o sistema
docker compose up
```

Na primeira execução, o pipeline roda automaticamente e gera os parquets em `./data/`. Execuções subsequentes reutilizam os parquets existentes sem rodar o pipeline novamente.

Dashboard disponível em: **http://localhost:8501**

### Local (uv)

**Pré-requisito:** [uv](https://docs.astral.sh/uv/) instalado e Python 3.12+.

```bash
# Clone e instale dependências
git clone <url-do-repo>
cd ai-master-challenge
uv sync

# Configure a chave da API
cp .env.example .env   # edite com sua ANTHROPIC_API_KEY

# Execute o pipeline
uv run python pipeline/bronze/run_bronze.py
uv run python pipeline/silver/run_silver.py
uv run python pipeline/gold/run_gold.py

# Suba o dashboard
uv run streamlit run app/dashboard/main.py

# (opcional) Inicie o agente conversacional
uv run python main.py
```

---

## Variáveis de ambiente

| Variável | Obrigatório | Descrição |
|----------|-------------|-----------|
| `ANTHROPIC_API_KEY` | Sim | Chave da API Anthropic para o agente de IA |

---

## Estrutura do projeto

```
ai-master-challenge/
├── Dockerfile              # Imagem Docker com pipeline + Streamlit
├── docker-compose.yml      # Orquestração com volume para persistir dados
├── entrypoint.sh           # Roda pipeline se necessário, depois sobe dashboard
├── pyproject.toml          # Dependências (gerenciadas com uv)
├── main.py                 # Entrypoint do agente conversacional
├── data/
│   ├── raw/                # CSVs originais — imutáveis
│   ├── bronze/             # Parquet pós-ingestão
│   ├── silver/             # Parquet pós-transformação (modelo dimensional)
│   └── gold/               # Parquet com métricas agregadas e risk scores
├── pipeline/
│   ├── bronze/run_bronze.py
│   ├── silver/run_silver.py
│   └── gold/run_gold.py
├── app/
│   ├── dashboard/          # Streamlit: main.py + queries.py
│   └── agent/              # Agno: agent.py + tools.py
└── docs/
    ├── 01-business/        # Regras de negócio, KPIs, playbook de retenção
    ├── 02-product/         # Casos de uso, deliverables, playbook CS
    └── 03-engineering/     # Arquitetura, modelo de dados, ADRs
```

---

## As 3 perguntas diagnósticas

O sistema é construído para responder estas perguntas para qualquer período:

**P1 — O que está causando o churn?**
Causa raiz identificada via cruzamento de `churn_events` × `feature_usage` × `support_tickets` × `subscriptions`. Cada causa com percentual do total de churns.

**P2 — Quais segmentos estão mais em risco?**
Segmentação por `industry`, `plan_tier`, `country` e `referral_source`. Contas específicas com risk score mais alto (nome + MRR em risco).

**P3 — O que a empresa deveria fazer?**
2–3 ações concretas com público-alvo definido e impacto estimado em MRR ou redução de churn rate.

Use o agente para fazer estas perguntas diretamente em linguagem natural.

---

## Stack

| Tecnologia | Versão | Papel |
|------------|--------|-------|
| Python | 3.12 | Runtime |
| DuckDB | 1.5+ | Motor de queries SQL analíticas |
| Parquet | — | Formato de armazenamento colunar |
| Streamlit | 1.55+ | Dashboard interativo |
| Plotly | 6.6+ | Visualizações interativas |
| Agno | 1.4+ | Framework de agentes de IA |
| Claude (Anthropic) | claude-sonnet-4-6 | LLM do agente |
| uv | latest | Gerenciamento de dependências e execução |
