# Plano Macro — AI Master Challenge (4 desafios)

## Avaliação honesta: o que cada desafio realmente precisa

| ID | Tipo declarado | App obrigatória? | Natureza principal |
|----|---------------|------------------|--------------------|
| 001 — Churn | Análise | Não — mas dashboard é diferencial forte | Cruzamento de dados → diagnóstico → recomendações |
| 002 — Suporte | Diagnóstico + Build | Sim — "quero ver algo rodando" | Análise operacional + protótipo funcional |
| 003 — Lead Scorer | Build | **Sim, obrigatório** — o deliverable é software | Ferramenta que o vendedor usa no dia a dia |
| 004 — Social Media | Análise + Estratégia | Não — mas dashboard é diferencial forte | Análise estatística → estratégia acionável |

**Conclusão:** Todo mundo precisa de app. Mas a ênfase muda:
- 003: a app **é** o entregável
- 002: a app **demonstra** a proposta
- 001 e 004: a app **amplifica** a análise (que precisa acontecer primeiro)

---

## Arquitetura da solução

### Monorepo com pnpm workspaces

```
submissions/marlon-maccedo/
├── apps/
│   ├── churn-dashboard/        # 001 — diagnóstico interativo de churn
│   ├── support-triage/         # 002 — classificador + dashboard operacional
│   ├── lead-scorer/            # 003 — ferramenta de priorização de deals
│   └── social-dashboard/       # 004 — análise e estratégia de social media
├── packages/
│   ├── ui/                     # componentes compartilhados (tabelas, charts, cards de KPI)
│   └── data-utils/             # utilitários de parsing e scoring compartilhados
├── data/                       # datasets CSV do Kaggle (gitignored)
├── process-log/                # capturas, exports de chat, narrativa
├── pnpm-workspace.yaml
├── package.json
└── README.md                   # submission template preenchido
```

### Stack por camada

| Camada | Tecnologia | Motivo |
|--------|-----------|--------|
| Frontend | Next.js 15 (App Router) | RSC para data-fetching server-side |
| Gráficos | Recharts | Leve, composable, funciona bem com RSC |
| Tabelas | TanStack Table | Filtro/sort client-side essencial pro lead scorer |
| Estilo | Tailwind CSS + shadcn/ui | Velocidade de desenvolvimento |
| Dados | DuckDB + `@duckdb/node-api` | SQL direto sobre CSVs, funciona bem no Railway |
| AI features | Anthropic SDK via API routes | Classificador de tickets (002) |
| Deploy | Railway | Container persistente, filesystem disponível |

---

## Estratégia de dados: DuckDB sobre CSV

Os CSVs ficam em `/data` (gitignored). DuckDB lê e consulta os arquivos diretamente com SQL — sem parsing manual, sem joins em JS, sem pré-processamento.

```
data/
  └── *.csv  (gitignored, baixado do Kaggle)
       ↓
DuckDB executa SQL direto sobre os arquivos
  SELECT a.account_id, COUNT(*) as churn_count, SUM(s.mrr) as mrr_at_risk
  FROM read_csv_auto('data/churn_events.csv') c
  JOIN read_csv_auto('data/subscriptions.csv') s USING (account_id)
  GROUP BY a.account_id
       ↓
API route retorna resultado agregado (JSON pequeno)
       ↓
Server/Client Component renderiza
```

**Todos os apps:** `@duckdb/node-api` nas API routes. Railway roda um container Node.js convencional (não serverless), então DuckDB funciona sem restrições — filesystem persistente, sem cold start limitado, sem timeout de função.

Os CSVs ficam em `/data` no container (gitignored no git, populado no deploy via Railway Volume ou na inicialização). DuckDB lê os arquivos diretamente do disco e cacheia em memória após a primeira query.

**Lead Scorer (003):** API route retorna os 8.8K deals já com score calculado pelo DuckDB. O client recebe o array completo uma vez e usa TanStack Table para filtragem/ordenação interativa — sem DuckDB-WASM, sem round-trips por filtro.

---

## O que cada app precisa entregar

### 001 — Churn Dashboard
- KPIs: taxa de churn por segmento, MRR em risco
- Visualização dos cruzamentos-chave: feature usage × churn, suporte × churn
- Tabela de contas em risco com score de risco calculado
- Seção de recomendações priorizadas
- API routes fazem join das 5 tabelas e retornam agregados por segmento

### 002 — Support Triage
- Input de texto → classificação automática (categoria + confiança) via Anthropic API
- Painel operacional: gargalos por canal, prioridade, tipo, estimativa de custo
- Proposta de automação inline com dados de suporte
- API route `/api/support/classify` chama Claude para classificar ticket

### 003 — Lead Scorer
- Tabela com todos os 8.800 deals, score de prioridade, filtros em tempo real
- Filtros por vendedor, manager, região, produto, stage
- Card de explicação: por que este deal tem score X
- Visão por vendedor: pipeline ranqueado
- API route retorna todos os deals com score (DuckDB server-side); TanStack Table filtra client-side

### 004 — Social Dashboard
- Performance por plataforma, tipo de conteúdo, creator size
- Comparativo orgânico vs. patrocinado (controlado por contexto)
- Perfil de audiência que mais engaja
- Página de estratégia com recomendações priorizadas e evidências

---

## Ordem de execução

1. **Setup do monorepo** — pnpm workspace, Next.js base, packages/ui
2. **003 — Lead Scorer** — mais "puro build", valida toda a stack
3. **002 — Support Triage** — dashboard + AI feature real
4. **001 — Churn Dashboard** — análise profunda, 5 tabelas relacionadas
5. **004 — Social Dashboard** — estratégia + visualizações
6. **Process log + submission README** — consolidar evidências

---

## Riscos e decisões abertas

| Risco | Decisão |
|-------|---------|
| CSVs no container Railway | Usar Railway Volume montado em `/data`; CSVs são copiados uma vez e persistem entre deploys |
| API key Anthropic (002) | Variável de ambiente no Railway; fallback com classificação por keywords se ausente |
| Deploy dos 4 apps | 4 serviços Railway no mesmo projeto (um por app Next.js) — cada um com sua URL pública |
| Process log convincente | Documentar desde o início, não reconstituir no final |

---

## Plans individuais

| Arquivo | Status |
|---------|--------|
| [001-churn.md](./001-churn.md) | pendente |
| [002-support.md](./002-support.md) | pendente |
| [003-lead-scorer.md](./003-lead-scorer.md) | pendente |
| [004-social.md](./004-social.md) | pendente |

**Prioridade:** 003 → 002 → 001 → 004
