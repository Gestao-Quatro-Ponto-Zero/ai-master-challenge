# DASHBOARD_SPEC.md — Pipeline Coach AI

## META
Full specification for all dashboard views. Block order = priority order. Do not reorder.

---

## VIEW-01: Rep Dashboard (Primary View)

### Layout Hierarchy
```
ABOVE FOLD (always visible without scroll):
┌─────────────────────────────────┐
│  BLOCK-1: Prioridades do Dia    │  ← Primary action space
│  [5 items max, action buttons]  │
├─────────────────────────────────┤
│  BLOCK-2: Contas em Risco       │  ← Urgency signal
│  [3 items, expand link]         │
├─────────────────────────────────┤
│  BLOCK-3: Ranking Sem Contato   │  ← Cold pipeline alert
│  [3 items, expand link]         │
├─────────────────────────────────┤
│  BLOCK-4: Execution Score       │  ← Behavioral feedback
│  [Number + bar + daily goal]    │
└─────────────────────────────────┘

BELOW FOLD (secondary — requires scroll or tab):
- Benchmark (rep vs team vs company)
- Full pipeline view
- Conversion by product
- Historical trends
```

---

## BLOCK-1: Prioridades do Dia

### Data Requirements
- Source: `daily_priorities` table, filtered by `rep_id` and `date = today`
- Max items: 5
- Sort: by `score DESC` (pre-sorted at generation time)

### Item Schema
```json
{
  "deal_id": "uuid",
  "account_name": "string",
  "product": "string",
  "score": 0-100,
  "score_label": "Crítico|Alto|Médio|Baixo",
  "context_reason": "string (max 60 chars)",
  "stage": "Prospecting|Engaging",
  "est_value": "number",
  "days_without_contact": "number",
  "action_status": "pending|executed|rescheduled|ignored"
}
```

### Action Buttons
| Button | Label | Score Impact | System Action |
|--------|-------|-------------|---------------|
| Primary | Executado ✓ | +execution_point | Opens registration bottom sheet |
| Secondary | Reagendar | 0 | Opens date picker (tomorrow default) |
| Tertiary | Ignorar | -0.5 points | Marks ignored, removes from view |

### Execution Registration Bottom Sheet
```
Step 1 (required):
  [📞 Liguei]  [✉️ Email]  [🤝 Reunião]  [🔄 Follow-up]

Step 2 (required, appears after step 1):
  [✓ Avançou de stage]
  [⏳ Aguardando resposta]
  [📅 Reagendado]
  [✗ Perdido]

→ Auto-submit after step 2
→ Show toast: "Ação registrada ✓"
→ Update execution score
→ Mark item as done (visual strike-through + fade)
```

### Empty State
```
"Todas as prioridades de hoje foram tratadas 🎉
Execution Score: {score}% — Continue amanhã!"
```

---

## BLOCK-2: Contas em Risco

### Trigger Condition
`days_in_stage > team_avg_days_in_stage_for_stage × 1.2`

### Item Schema
```json
{
  "account_name": "string",
  "product": "string",
  "stage": "string",
  "days_in_stage": "number",
  "team_avg": "number",
  "days_over_avg": "number",
  "deal_value": "number"
}
```

### Display
- Main view: 3 items max, sorted by `days_over_avg DESC`
- Each item shows: account name | product | "{N} dias acima da média"
- CTA: "Ver todas ({total}) →"
- Full list: same sort, all items

---

## BLOCK-3: Ranking Sem Contato

### Trigger Condition
`days_since_last_interaction > 0` (all open deals, sorted)

### Item Schema
```json
{
  "account_name": "string",
  "product": "string",
  "deal_value": "number",
  "last_contact_date": "date|null",
  "days_without_contact": "number"
}
```

### Display
- Main view: 3 items max, sorted by `days_without_contact DESC`
- Each item: account name | "{N} dias sem contato"
- Tap → open deal detail with quick-action buttons
- CTA: "Ver todas ({total}) →"

---

## BLOCK-4: Execution Score

### Calculation
```
score = (actions_executed / actions_recommended) × 100
window = rolling 7 days
```

### Display Components
```
Large number: "72%"
Subtitle: "Esta semana"
Progress bar: filled to score%
Daily goal: "Meta de hoje: registre 3 ações"
Delta: "+8% vs semana passada ↑" (green if positive)
```

### Score Thresholds and Messages
| Score | Color | Message |
|-------|-------|---------|
| ≥80% | Green | "Excelente consistência! 🏆" |
| 60–79% | Blue | "Boa semana, continue!" |
| 40–59% | Amber | "Registre mais ações para subir o score" |
| <40% | Red | "Score baixo — tente registrar hoje" |

---

## BLOCK-5: Benchmark (Secondary View)

### Comparison Dimensions
```
Lead Time Médio:
  [Você: 58d] ──────────────────
  [Empresa: 52d] ────────────
  [Equipe: 46d] ────────

Tempo Sem Contato (avg):
  [Você: N] vs [Equipe: M]

Conversão por Produto:
  [Produto A: 68%] vs [Empresa: 63%]
```

### Framing Rule (enforced in UI copy)
Every below-average metric MUST be followed by a suggestion chip:
```
"Você está 6 dias acima da média da equipe"
[💡 Priorize follow-ups em Engaging > 14 dias]
```

---

## VIEW-02: Manager Dashboard

### Default State
- Period: Last 7 days
- Scope: All reps in manager's team
- Primary sort: Execution Score DESC

### Block Order (fixed)
```
BLOCK-M1: Execution Score Ranking
  - Table: rep_name | score | score_trend | deals_executed | deals_pending
  - Sort: score DESC
  - Highlight: reps <40% in red

BLOCK-M2: Aging Médio por Vendedor
  - Bar chart or table: rep_name | avg_days | vs_team_avg | delta
  - Sort: avg_days DESC (worst first)
  - Outlier: >20% above team avg → red badge

BLOCK-M3: Ranking Sem Contato
  - Table: rep_name | accounts_cold | avg_days_cold
  - Sort: accounts_cold DESC

BLOCK-M4: Pipeline Coverage
  - Per rep: open_pipeline_value | quota | coverage_ratio
  - Coverage = open_pipeline / quota
  - Green: >150% | Amber: 100–150% | Red: <100%

BLOCK-M5: Conversão por Produto
  - Matrix: reps (rows) × products (columns) × win_rate (cells)
  - Color scale: red → green by win rate
```

### Filters (all blocks respond to filters simultaneously)
```
Filter: office       → dropdown [All | Central | East | West]
Filter: product      → dropdown [All | GTXPro | GTX Plus Pro | ...]
Filter: period       → tabs [7d | 30d | 90d | Custom]
Filter: rep          → search autocomplete
```

### Rep Detail Drill-Down
Accessible from any manager block by clicking rep name:
```
Rep Detail:
  - Header: name | office | manager | tenure
  - Execution score trend (last 30 days)
  - Daily priority completion rate
  - Aging trend
  - Top 3 products by conversion rate
  - Open deals list (sortable)
```

---

## NAVIGATION STRUCTURE

```
Rep App:
  / (home)          → View-01: Rep Dashboard
  /pipeline         → Full open deals list (sortable/filterable)
  /accounts         → Account list with contact history
  /performance      → Benchmark + trends (View-01 Block-5 expanded)
  /history          → All registered actions

Manager App:
  / (home)          → View-02: Manager Dashboard
  /rep/:id          → Rep detail drill-down
  /pipeline         → Team pipeline overview
  /reports          → Export + deeper analytics (RevOps use case)
```

---

## RESPONSIVE / DEVICE REQUIREMENTS

| View | Primary Device | Secondary |
|------|---------------|-----------|
| Rep Dashboard | Mobile (iOS/Android) | Desktop |
| Email CTA landing | Mobile | — |
| Manager Dashboard | Desktop | Mobile (read-only) |
| Rep Detail (from manager) | Desktop | — |
