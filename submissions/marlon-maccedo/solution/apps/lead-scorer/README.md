# Lead Scorer — Challenge 003

Ferramenta de priorização do pipeline de vendas para o **vendedor**, não para o gestor. Dado um conjunto de deals abertos, o scorer ranqueia cada oportunidade de 0 a 100 e classifica em Hot / Warm / Cold para que o vendedor saiba em qual deal agir primeiro.

---

## O que faz e para quem

O vendedor abre o Pipeline, vê os deals ordenados por score decrescente e clica em qualquer deal para entender **por que** aquele score — cada um dos 6 componentes é exibido com seu valor numérico. A visão "Time" (ou "Minha Carteira" quando filtrada por agente) mostra a distribuição de scores da carteira própria.

---

## Modelo de Scoring

Score total = soma dos 6 componentes, clampeado entre 0 e 100.

| Componente | Regra | Pontos | Origem do threshold |
|------------|-------|--------|---------------------|
| **Stage** | Engaging | 30 | Stage de maior engajamento no funil |
| | Prospecting | 15 | |
| **Valor** | `sales_price ≥ $4.000` | 25 | GTX Pro ($4.821) — único produto premium acima de $4k |
| | `≥ $1.000` | 15 | |
| | `≥ $500` | 8 | |
| | `< $500` | 3 | |
| **Conta** | `revenue > $2.741M` | 20 | Q3 de `accounts.csv` |
| | `> $1.224M` | 14 | Q2 de `accounts.csv` |
| | `> $497M` | 8 | Q1 de `accounts.csv` |
| | `≤ $497M` | 4 | |
| **Aging** | `days_in_pipeline > 300` | −15 | Break natural da distribuição de `engage_date` |
| | `> 200` | −10 | |
| | `> 120` | −5 | |
| | `≤ 120` | 0 | |
| **Série** | GTK | 15 | Maior win rate histórico por série |
| | GTX | 8 | |
| | MG | 0 | |
| **Agente** | Linear 55–70%, clamped 0–10 | 0–10 | Distribuição real de win_rate no dataset; média = 62,5% |

**Interpretação do score total:**

| Label | Range | Ação sugerida |
|-------|-------|---------------|
| 🔴 Hot | ≥ 70 | Prioridade máxima — agir esta semana |
| 🟡 Warm | 40–69 | Acompanhar; identificar o que falta para Hot |
| 🔵 Cold | < 40 | Reavaliar viabilidade ou aguardar maturação |

---

## Como rodar

**Pré-requisito:** dataset CRM no diretório `data/` (5 CSVs — veja tabela abaixo).

```bash
# Da raiz do monorepo
pnpm dev:lead-scorer        # inicia em http://localhost:3001

# Ou isolado (dentro de apps/lead-scorer)
pnpm dev
```

**Docker (da raiz do monorepo):**

```bash
docker compose up lead-scorer --build
```

Nenhuma variável de ambiente é obrigatória. Para ativar sugestões de ação via LLM:

```bash
# Copiar e preencher
cp apps/lead-scorer/.env.example apps/lead-scorer/.env.local
# Preencher OPENROUTER_API_KEY=sk-or-v1-...
```

---

## Dataset — 5 CSVs

| Arquivo | Conteúdo |
|---------|----------|
| `sales_pipeline.csv` | Deals históricos e abertos: `opportunity_id`, `sales_agent`, `product`, `account`, `deal_stage`, `engage_date`, `close_value` |
| `products.csv` | Catálogo de produtos: `product`, `series`, `sales_price` |
| `accounts.csv` | Dados das contas: `account`, `sector`, `revenue`, `employees`, `office_location` |
| `sales_teams.csv` | Estrutura de times: `sales_agent`, `manager`, `regional_office` |
| `sales_pipeline.csv` (filtro) | Deals Won/Lost usados para computar win rate histórico por agente via CTE `agent_stats` |

---

## Rotas do app

| Rota | Descrição |
|------|-----------|
| `/` | Dashboard — KPIs (total, pipeline value, Hot/Warm/Cold, avg score, por aging) |
| `/pipeline` | Tabela paginada de todos os deals abertos, filtros por stage/região/agente |
| `/pipeline/[id]` | Drill-down de um deal — score breakdown com os 6 componentes |
| `/team` | Ranking de agentes por avg score, hot deals e pipeline value |
| `/team/[agent]` | Carteira individual do agente |
| `/api/pipeline` | API REST — aceita `page`, `pageSize`, `sort`, `order`, `q`, `stage`, `region`, `agent` |
| `/api/team` | API REST — lista de AgentStats |
