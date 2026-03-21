# Churn Dashboard — Challenge 001

Dashboard de diagnóstico de churn para gestores de Customer Success. Analisa o dataset SaaS de churn (Kaggle, MIT) e expõe segmentação de risco, causas raiz e recomendações de retenção com apoio de LLM.

---

## O que faz

Permite ao gestor identificar **quais segmentos churnam mais, por quê, e quais contas ativas estão em risco** — tudo a partir dos dados reais do CSV, sem análise manual.

---

## Rotas do app

| Rota | Descrição |
|------|-----------|
| `/overview` | Visão geral: churn rate, MRR churned/retained, contas em risco, distribuição por indústria/canal/plano |
| `/diagnostic` | Diagnóstico de causas: feature usage churn vs retidos, análise de suporte, top razões |
| `/segments` | Contas ativas em risco (tenure < 6m ou plano mensal) |
| `/recommendations` | Ações de retenção priorizadas geradas via LLM (ou banner se sem API key) |

---

## Como rodar

**Pré-requisito:** dataset SaaS Subscription & Churn Analytics em `data/` (CSV do Kaggle, MIT).

```bash
# Da raiz do monorepo
pnpm dev:churn-dashboard    # http://localhost:3002

# Ou isolado
pnpm dev
```

**Docker:**

```bash
docker compose up churn-dashboard --build
```

**Variáveis de ambiente (opcionais):**

```bash
OPENROUTER_API_KEY=sk-or-v1-...   # Ativa insights e recomendações via LLM
```

Sem a API key, insights exibem `null` e recomendações mostram banner explicativo — o dashboard funciona normalmente.

---

## Findings principais

- Taxa de churn concentrada nos primeiros 6 meses (onboarding crítico)
- Clientes em planos mensais churnam 3–4× mais que anuais
- Ausência de engajamento com suporte nos primeiros 30 dias é sinal de risco antecipado

---

## Arquitetura de dados

DuckDB rodando server-side no Next.js — queries SQL diretas sobre o CSV em memória. Sem banco externo, sem ORM. Insights LLM via OpenRouter com cache 24h por chave de dados.
