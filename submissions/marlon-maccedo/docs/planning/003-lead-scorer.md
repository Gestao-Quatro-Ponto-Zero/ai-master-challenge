# Plan 003 — Lead Scorer

> Status: pronto para implementar
> Primeiro desafio a ser construído — valida toda a stack

---

## Contexto e decisão de arquitetura

O entregável é software que um vendedor abre na segunda-feira e sabe onde focar. O dataset tem 4 CSVs com ~8.800 oportunidades. Deploy no **Railway** com container Node.js persistente.

A escolha é **DuckDB server-side + TanStack Table client-side**:
- API route `/api/pipeline` executa SQL com DuckDB, retorna todos os 8.8K deals já com score calculado
- Client recebe o array completo uma vez (~500KB JSON) e usa TanStack Table para filtros/ordenação instantâneos sem round-trips
- Sem DuckDB-WASM — arquitetura mais simples, sem problemas de bundle size
- CSVs ficam em `/data` no container Railway, lidos diretamente pelo DuckDB

---

## Estrutura de rotas

```
/                        → redireciona para /pipeline
/pipeline                → tabela principal: todos os deals com score e filtros
/pipeline/[id]           → detalhe de um deal: score breakdown, histórico, conta
/team                    → visão gerencial: todos os agentes com stats
/team/[agent]            → pipeline de um vendedor específico, ranqueado por score
```

---

## Dados: schema e joins

```sql
-- Query principal (executada no browser via DuckDB-WASM)
SELECT
  p.opportunity_id,
  p.deal_stage,
  p.engage_date,
  p.close_date,
  p.close_value,
  p.sales_agent,
  p.product,
  p.account,
  t.manager,
  t.regional_office,
  a.sector,
  a.revenue,
  a.employees,
  pr.series,
  pr.price,

  -- Score como coluna derivada
  ROUND(
    LEAST(100,
      -- Stage (0-30 pts)
      CASE p.deal_stage
        WHEN 'Engaging'    THEN 30
        WHEN 'Prospecting' THEN 15
        ELSE 0
      END

      -- Valor do deal (0-25 pts)
      + LEAST(25, p.close_value / 400)

      -- Tamanho da conta (0-20 pts)
      + CASE
          WHEN a.revenue > 1000000 THEN 20
          WHEN a.revenue > 100000  THEN 12
          ELSE 5
        END

      -- Tempo no pipeline: penaliza deals muito velhos (0 a -15 pts)
      + CASE
          WHEN DATEDIFF('day', p.engage_date, CURRENT_DATE) > 90 THEN -15
          WHEN DATEDIFF('day', p.engage_date, CURRENT_DATE) > 60 THEN -8
          ELSE 0
        END

      -- Produto premium (0-10 pts)
      + CASE WHEN pr.series = 'GTX' THEN 10 ELSE 0 END

      -- Win rate histórico do agente (0-15 pts) — calculado separadamente
      -- injetado como constante por agente antes da query principal
    )
  , 1) AS score

FROM read_csv_auto('/data/sales_pipeline.csv') p
LEFT JOIN read_csv_auto('/data/sales_teams.csv')  t  ON p.sales_agent = t.sales_agent
LEFT JOIN read_csv_auto('/data/accounts.csv')      a  ON p.account     = a.account
LEFT JOIN read_csv_auto('/data/products.csv')      pr ON p.product     = pr.product
WHERE p.deal_stage IN ('Prospecting', 'Engaging')   -- só deals abertos
ORDER BY score DESC
```

**Win rate por agente** é pré-calculado (uma query separada sobre deals Won/Lost), injetado como mapa `{agent: winRate}` antes da query principal.

---

## Lógica de scoring: critérios e pesos

| Critério | Peso máx | Raciocínio |
|----------|----------|------------|
| Deal stage | 30 pts | Engaging > Prospecting: já há momentum |
| Valor do deal | 25 pts | ROI direto; normalizado pelo dataset |
| Tamanho da conta | 20 pts | Contas maiores têm ciclo mais previsível |
| Tempo no pipeline | -15 pts | Deal parado é sinal de problema |
| Produto premium | 10 pts | Produtos GTX têm margem maior |
| Win rate do agente | 15 pts | Probabilidade histórica de fechar |

Score final: 0–100. Deals com score ≥ 70 = "hot", 40–69 = "warm", < 40 = "cold".

---

## Explainability: por que este deal tem score X

Cada deal tem um card de breakdown mostrando a contribuição de cada critério:

```
Score: 78 🔥

✅ Stage: Engaging                    +30
✅ Valor: $32.000 (alto)             +22
✅ Conta: receita $2M (grande)       +20
⚠️  Pipeline: 71 dias (longo)        -8
✅ Produto: GTX Pro (premium)         +10
⚠️  Agente: win rate 42% (médio)      +6
                                    ─────
                                      80 → cap: 78
```

Isso é o diferencial principal do produto. O vendedor não vê só o número — entende o que está freando e o que está impulsionando.

---

## Componentes de UI

### `/pipeline` — Tabela principal

- **Filtros (sidebar ou topbar):** deal stage, agente, manager, região, produto, faixa de score
- **Tabela TanStack:** colunas ordenáveis (score, valor, stage, dias no pipeline, conta)
- **Badge de score:** cor por faixa (vermelho/amarelo/verde)
- **Row click** → abre detalhe ou expande inline
- **Contadores rápidos:** "X deals hot, Y warm, Z cold"

### `/pipeline/[id]` — Detalhe do deal

- Score breakdown (card conforme modelo acima)
- Info da conta (setor, receita, funcionários)
- Timeline: engage_date → hoje → close_date esperado
- Info do produto e preço
- Botão "ver outros deals desta conta"

### `/team` — Visão gerencial

- Cards por manager: win rate, pipeline total ($), deals hot/warm/cold
- Tabela de agentes: nome, região, deals abertos, MRR potencial, score médio
- Click em agente → `/team/[agent]`

### `/team/[agent]` — Visão do vendedor

- Mesma tabela de `/pipeline` pré-filtrada por agente
- Header com stats pessoais: win rate histórico, deals ativos, valor total em jogo

---

## Fluxo de dados

```
/data/*.csv  (Railway Volume, gitignored)
  ↓
GET /api/pipeline
  DuckDB lê os 4 CSVs, faz joins, calcula score como coluna SQL
  Cacheia resultado em memória (module-level Map)
  Retorna array JSON com todos os deals + score + breakdown
  ↓
Client recebe array completo (~500KB, uma vez)
  ↓
TanStack Table filtra/ordena client-side (instantâneo)
  Estado de loading: skeleton table na primeira carga (~1-2s)
```

**Cache:** resultado da query fica em memória. Reiniciar o serviço Railway limpa o cache e a próxima request relê os CSVs.

**Locally:** CSVs em `/data` (gitignored). README tem instrução de download do Kaggle + onde colocar.

---

## Estrutura de arquivos da app

```
apps/lead-scorer/
├── data/                        # CSVs aqui (gitignored, Railway Volume)
│   ├── sales_pipeline.csv
│   ├── accounts.csv
│   ├── products.csv
│   └── sales_teams.csv
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx             # redirect → /pipeline
│   │   ├── pipeline/
│   │   │   ├── page.tsx         # tabela principal
│   │   │   └── [id]/page.tsx    # detalhe do deal
│   │   └── team/
│   │       ├── page.tsx         # visão gerencial
│   │       └── [agent]/page.tsx # visão por vendedor
│   ├── components/
│   │   ├── DuckDBProvider.tsx   # contexto com instância DuckDB-WASM
│   │   ├── PipelineTable.tsx    # TanStack Table + filtros
│   │   ├── ScoreCard.tsx        # breakdown de score
│   │   ├── ScoreBadge.tsx       # badge colorido
│   │   └── FilterSidebar.tsx
│   ├── lib/
│   │   ├── duckdb.ts            # init e query helper
│   │   └── scoring.ts           # SQL de scoring como string exportada
│   └── types/
│       └── pipeline.ts          # tipos TypeScript dos dados
├── package.json
└── next.config.ts
```

---

## O que vai no process log

- Print do momento em que decidi usar DuckDB-WASM (e por quê)
- Query SQL de scoring inicial vs. versão refinada após ver os dados reais
- Screenshot dos dados reais carregados pela primeira vez (proof que funciona)
- Iteração na lógica de scoring: o que mudou após explorar o dataset
- Screenshot da tabela com deals ranqueados
- Screenshot do score breakdown de um deal específico

---

## Dependências

```json
{
  "@duckdb/node-api": "latest",
  "@tanstack/react-table": "^8",
  "recharts": "^2",
  "next": "15",
  "tailwindcss": "^4"
}
```
