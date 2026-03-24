# Chat Export — Claude Code Session
**Projeto:** Challenge 003 — Lead Scorer
**Candidata:** Mariana Peixoto Coelho
**Ferramenta:** Claude Code (Anthropic) + Antigravity Kit
**Data:** 2026-03-23 / 2026-03-24

---

## Sessão 1 — Setup e Exploração dos Dados

**Mariana:** Irei fazer um projeto para uma vaga de emprego. Crie uma pasta e de acordo com o processo, vou pedir para você incluir os dados nesse arquivo. Quais opções/formato você me dá para organizar isso tudo?

**Claude Code:** Apresentei 3 opções de estrutura. Recomendei a Opção B — pasta dedicada com seções separadas:
```
submission/
├── SUBMISSION.md
├── evidence/screenshots/
├── evidence/recordings/
├── evidence/chat_exports/
├── analysis/
└── assets/
```

**Mariana:** Vamos de opção B. Meu nome é Mariana Peixoto Coelho, LinkedIn: https://www.linkedin.com/in/maripeixotoc/, Challenge 003 — Lead Scorer.

**Claude Code:** Criei a estrutura de pastas completa. Aguardei os CSVs.

---

## Sessão 2 — Análise dos Dados

**Mariana:** [Colocou os 4 CSVs + metadata.csv na pasta data/]

**Claude Code:** Li todos os arquivos e mapeei a estrutura:

```
Exploração executada via Node.js (Python não disponível no ambiente):

sales_pipeline.csv — 8.800 registros
Distribuição de stages:
  Won:         4.238 (histórico positivo)
  Lost:        2.473 (histórico negativo)
  Engaging:    1.589 (ATIVO — foco principal)
  Prospecting:   500 (ATIVO — foco secundário)

Total de deals ATIVOS para scoring: 2.089

accounts.csv — campos: sector, revenue, employees, office_location
products.csv — 7 produtos, preço entre $55 e $4.821
sales_teams.csv — 35 vendedores, 6 managers, 3 regiões
metadata.csv — dicionário de dados
```

**Decisão tomada pela Mariana (não pela IA):** Usar `2017-12-31` como data de referência para cálculo de dias no pipeline, pois o dataset é de 2016-2017. A IA teria calculado com a data atual (2026), gerando valores absurdos de 3.000+ dias.

---

## Sessão 3 — Design com Stitch

**Mariana:** A interface eu quero que faça um prompt para eu incluir no Stitch para termos um design moderno, mas totalmente intuitivo!

**Claude Code:** Criei um prompt detalhado para o Stitch em `submission/assets/stitch_prompt.md` especificando:
- Tema dark com neon (inspiração: Linear, Vercel, Stripe)
- 4 telas: Main Dashboard, Empty State, Manager View, Deal Breakdown
- Sistema de score visual com badges coloridos (verde/amarelo/vermelho)
- Painel de explicabilidade do score
- Filtros por região/manager/vendedor

**Mariana:** [Enviou os 4 screenshots gerados pelo Stitch]

Resultado: design neon cyberpunk com tema dark, badges circulares de score, tabela ordenável, painel de breakdown lateral, manager view com leaderboard.

**Decisão curatorial da Mariana:** Escolheu o estilo neon/cyberpunk entre as variações geradas — direção visual que eu (IA) não teria tomado sozinha sem o input de gosto e contexto de público (vendedores B2B).

---

## Sessão 4 — Construção da Lógica de Scoring

**Claude Code:** Implementei o scoring engine em TypeScript (`web/src/lib/lead-scorer.ts`):

```typescript
// Lógica de scoring com 5 componentes — 0 a 100 pontos

// 1. Deal Stage (25 pts)
Engaging:    25 pts  // Deal ativo e avançando
Prospecting: 15 pts  // Deal inicial

// 2. Product Value (20 pts)
// Normalizado pelo preço máximo do portfólio ($4.821 - GTX Pro)
pts = (product.sales_price / maxPrice) * 20

// 3. Account Profile (20 pts)
// Revenue normalizado (10 pts) + Employees normalizado (10 pts)
revenueScore = Math.min(account.revenue / 1100, 1) * 10
employeeScore = Math.min(account.employees / 2822, 1) * 10

// 4. Pipeline Velocity (20 pts)
// Penaliza deals parados — referência: 2017-12-31
daysInPipeline = diff(engageDate, "2017-12-31")
pts = daysInPipeline <= 30  ? 20
    : daysInPipeline <= 60  ? 15
    : daysInPipeline <= 90  ? 10
    : daysInPipeline <= 150 ? 5
    : 0  // Deal parado há mais de 150 dias = sem pontos

// 5. Rep Performance (15 pts)
// Win rate histórico calculado dos dados Won/Lost por vendedor
winRate = wonDeals / (wonDeals + lostDeals)
pts = winRate * 15
```

**Erro da IA corrigido pela Mariana:** Claude Code inicialmente usou formatação europeia nos números (ponto como separador de milhar). Mariana identificou e corrigiu para `toLocaleString('en-US')`.

---

## Sessão 5 — Construção da Interface

**Claude Code:** Construí o dashboard completo em Next.js + React + Tailwind seguindo os designs do Stitch:

Arquivos criados:
- `web/src/app/lead-scorer/page.tsx` — página principal
- `web/src/app/lead-scorer/dashboard.tsx` — componente principal com estado
- `web/src/app/api/leads/route.ts` — API route que lê os CSVs e aplica o scoring
- `web/data/` — CSVs copiados para a pasta da aplicação

Componentes implementados:
- Sidebar com métricas (Active Deals, Avg Score, Quick Filters)
- Tabela com ordenação por score/dias
- Badges circulares com gradiente por faixa de score
- Painel de breakdown do score (Score Factors)
- Agente de IA estratégico com recomendação personalizada por deal
- Dropdowns customizados (substituindo `<select>` nativo para manter o tema dark)
- Filtros por Região, Manager e Vendedor
- Busca livre por conta/produto/vendedor
- Manager View com leaderboard de equipe

---

## Sessão 6 — Ajustes e Refinamentos

**Mariana:** Está tudo em inglês. Coloque em português e seja minucioso.

**Claude Code:** Traduzi todos os textos da interface:
- Labels da tabela: Score, Conta, Produto, Estágio, Dias, Vendedor, Região
- Filtros: "Todas as Regiões", "Todos os Managers", "Todos os Vendedores"
- Quick filters: "Todos os Ativos", "Em Engajamento", "Em Prospecção"
- Botão: "Visão do Manager"
- Regiões: East → Leste, West → Oeste, Central → Central
- Stage badges: Engaging → Em Engajamento, Prospecting → Em Prospecção
- Score factors: traduzidos com contexto de negócio

**Mariana:** Os dropdowns quando abertos ainda estão com o estilo do browser (fundo branco).

**Claude Code:** Substituí os `<select>` nativos por componentes React customizados com estado controlado, matching exato do tema dark (#0d1424, bordas neon cyan, hover states).

**Mariana:** "Maureen Marcano" aparece fora do container do dropdown de Managers.

**Claude Code:** Corrigi o overflow — o container usava `position: absolute` relativo ao nav com `maxHeight: 280px` insuficiente para 8 itens. Migrei para `position: fixed` com `zIndex: 9999` e `maxHeight: 340px` com `overflowY: auto`.

---

## Resumo das Decisões Humanas vs. IA

| Decisão | Quem tomou | Por quê importa |
|---|---|---|
| Data de referência 2017-12-31 | Mariana | Sem isso, todos os scores de velocity seriam 0 |
| Priorizar explicabilidade vs. ML complexo | Mariana | Vendedor entende regras, não XGBoost |
| Estética neon/cyberpunk | Mariana | Curadoria entre variações do Stitch |
| Threshold ≥70 como critério de prioridade | Mariana | Interpretação de negócio, não técnica |
| Agente de IA estratégico no painel | Mariana | Insight de UX: score sem contexto não ajuda |
| Correção do locale de números | Mariana | Identificou bug visual no output |
| Refinamento do prompt do Stitch | Mariana | Adicionou referências visuais específicas |

---

## Tecnologias utilizadas

- **Runtime:** Node.js 24 + Next.js 15 + React 19
- **Styling:** Tailwind CSS + CSS-in-JS inline para efeitos neon
- **Data processing:** TypeScript puro (sem pandas/numpy — ambiente Windows sem Python)
- **Design:** Stitch (Google AI) para geração de mockups
- **Agentes:** Antigravity Kit (https://github.com/vudovn/antigravity-kit.git)
- **IA de desenvolvimento:** Claude Code (Anthropic)

---

*Log exportado em: 2026-03-24*
