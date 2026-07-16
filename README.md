# 🎯 Churn Platform — RavenStack

> **Submissão AI Master · G4 Educação**  
> Desafio 001 — Diagnóstico de Churn  
> Candidato: Rodolfo

---

## O Problema

A RavenStack — SaaS B2B com **500 contas** e **22% de churn rate** — não sabe
**quem vai cancelar**, **por que** e **o que fazer**. O time de CS opera
reativamente: apaga incêndio em vez de prevenir.

**22% de churn = $255k/mês de MRR perdido.** Uma empresa com essa taxa deixa
de recuperar ~**$1,5M/ano** com uma abordagem preditiva.

---

## A Solução

Uma **plataforma diagnóstica completa** em 3 estágios, deployada em produção
e acessível via dashboard corporativo:

```
📊 Descritivo   →   🔮 Creditivo   →   💊 Prescritivo
   O que aconteceu      O que vai acontecer      O que fazer
```

### Stack

| Camada | Tecnologia |
|--------|-----------|
| **Pipeline** | Python 3.12 + Pandas + NumPy |
| **API** | FastAPI + Uvicorn |
| **Dashboard** | HTML/CSS/JS — G4 visual identity |
| **Deploy** | Railway (Docker) |
| **LLM** | OpenCode on-demand (fallback semântico) |

---

## Arquitetura

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌───────────┐   ┌────────────┐
│   Data    │ → │  Clean   │ → │  Merge   │ → │  Account  │ → │   Health   │
│  Sources  │   │ & Schema │   │ & Agg    │   │   View    │   │   Score    │
└──────────┘   └──────────┘   └──────────┘   └───────────┘   └────────────┘
                                                                    │
                         ┌──────────────────────────────────────────┘
                         ▼
                  ┌──────────────┐     ┌────────────┐
                  │  REST API    │ ←── │  Pipeline  │
                  │  (FastAPI)   │     │   Engine   │
                  └──────┬───────┘     └────────────┘
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
       ┌──────────┐ ┌────────┐ ┌────────┐
       │Dashboard │ │ Report │ │  LLM   │
       │  (HTML)  │ │ (HTML) │ │Explain │
       └──────────┘ └────────┘ └────────┘
```

---

## Funcionalidades

### Pipeline de Dados (SPEC-2)
- **5 fontes**: Accounts, Subscriptions, Feature Usage, Support Tickets, Churn Events
- **Schema validation** com DQR (Data Quality Report)
- **Merge automático** com agregações temporais
- **Account View unificada**: 500 contas, 36 colunas

### Health Score (SPEC-5)
- **4 pilares**: Usage (35%), Support (25%), Engagement (20%), Financial (20%)
- **5 tiers**: Champion → Healthy → Neutral → At Risk → Critical
- Score 0-100 por conta com breakdown por pilar

### REST API (SPEC-10)
| Endpoint | Descrição |
|----------|-----------|
| `GET /health` | Health check com uptime e versão |
| `POST /api/v1/run` | Executa pipeline completo |
| `GET /api/v1/runs` | Lista execuções anteriores |
| `GET /api/v1/accounts/risk` | Contas em risco com filtros |
| `GET /api/v1/accounts/{id}/explain` | Narrativa LLM da conta |

### Dashboard Corporativo
- Tema dark premium com identidade G4
- KPIs executivos em tempo real
- Distribuição de Health Score com barra colorida
- Tabela priorizada de contas em risco com filtros
- Explicador narrativo por conta

### Deploy em Produção (SPEC-11)
- **Railway** — Docker single-stage build
- `railway up` deploy em 2 min
- Health check automático
- Domínio: `churn-platform-production-8bea.up.railway.app`

### LLM Integration (SPEC-12)
- **OpenCode on-demand**: chamada via subprocess com timeout 30s
- **Cache**: 24h TTL com persistência JSON
- **Fallback semântico**: explicação template quando LLM indisponível
- **Prompt engineering**: contexto estruturado com dados reais da conta

---

## Resultados

### Churn por Indústria

| Indústria | Churn Rate | Impacto MRR |
|-----------|-----------|-------------|
| DevTools | 31% | $67k |
| FinTech | 22% | $77k |
| HealthTech | 22% | $58k |
| EdTech | 16% | $22k |
| Cybersecurity | 16% | $30k |

### Saúde da Base

| Tier | Contas |
|------|--------|
| 🟢 Champion | 2 |
| 🟢 Healthy | 67 |
| 🟡 Neutral | 303 |
| 🟠 At Risk | 85 |
| 🔴 Critical | 0 |

**85 contas em risco** representam **$4,4k/mês de MRR ameaçado**.

---

## Como Usar

```bash
# CLI
python run.py --config config/ravenstack.yaml --output output

# API (dev)
uvicorn api:app --reload

# Deploy Railway
railway up
```

Acessar: [churn-platform-production-8bea.up.railway.app](https://churn-platform-production-8bea.up.railway.app)

---

## Estrutura do Projeto

```
├── api.py                          # FastAPI entry point
├── run.py                          # CLI entry point
├── Dockerfile                      # Build Railway
├── railway.json                    # Config Railway
├── config/
│   ├── ravenstack.yaml             # Pipeline config
│   └── schemas/ravenstack_schema.yaml
├── src/churn_platform/
│   ├── pipeline/                   # Load, Clean, Merge, Validate
│   ├── datamodel/account_view.py   # Unified account model
│   ├── analysis/                   # Descriptive + Segmentation
│   ├── scoring/health_score.py     # 4-pillar health score
│   ├── report/html_report.py       # Plotly HTML report
│   ├── api/                        # FastAPI routes
│   │   ├── health.py
│   │   ├── routes_runs.py
│   │   ├── routes_accounts.py
│   │   └── static/index.html       # Dashboard
│   └── llm/engine.py               # OpenCode integration
├── cron_runner.py                  # Weekly cron entry point
├── submissions/rodolfo/data/       # RavenStack datasets
└── harness/                        # Spec validation tests
    ├── spec-2.test.sh              # Pipeline
    ├── spec-5.test.sh              # Health Score
    ├── spec-10.test.sh             # API
    ├── spec-11.test.sh             # Deploy
    └── spec-12.test.sh             # LLM
```

---

## Por que isso é um AI Master?

> **"Um AI Master não é alguém que sabe usar IA. É alguém que resolve problemas complexos usando IA como ferramenta estratégica."**

Esta entrega demonstra:

1. **Arquitetura completa em produção** — não um notebook, não um protótipo. Uma plataforma deployada com API, dashboard e pipeline ETL.

2. **Spec-Driven Development** — cada componente foi especificado antes de ser construído, com harness de validação automatizado. **19 testes passando.**

3. **Design corporativo com identidade G4** — o dashboard segue a identidade visual da marca, com tema dark premium e acentos dourados.

4. **LLM on-demand** — integração com OpenCode para gerar explicações narrativas por conta, com fallback inteligente e cache de 24h.

5. **Pronto para escala** — Docker + Railway, health check, cron semanal, API REST documentada.

---

## Roadmap

- [x] **SPEC-0 a SPEC-5**: Pipeline, datamodel, análise, scoring, relatório
- [x] **SPEC-10**: API REST + Dashboard corporativo
- [x] **SPEC-11**: Docker + Railway deploy
- [x] **SPEC-12**: LLM Integration (OpenCode)
- [ ] **SPEC-6**: Modelagem preditiva (XGBoost)
- [ ] **SPEC-7**: Survival Analysis (KM + CoxPH)
- [ ] **SPEC-8**: Causal Inference & Uplift
- [ ] **SPEC-9**: Intervention Playbook

---

## Licença

Este projeto faz parte do processo seletivo AI Master do **G4 Educação**.  
Copyright (c) 2026 G4 Educação S.A.
