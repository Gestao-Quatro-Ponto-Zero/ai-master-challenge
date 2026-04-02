# PRODUCT_SPEC.md — Pipeline Coach AI

## META
- **Product**: Pipeline Coach AI
- **Type**: B2B SaaS, Sales Operations
- **Version**: 1.0
- **Audience**: AI agents building/extending this product

---

## 1. OBJECTIVE

Transform CRM data into daily executable actions for B2B sales reps.

### Problems Solved
| Problem | Solution |
|---------|----------|
| Reps prioritize by intuition | AI scores and ranks all open deals daily |
| Good deals go cold | Aging + last-contact alerts surface at-risk accounts |
| No visibility on execution | Execution Score tracks what reps actually do |
| Reps don't open dashboards | Email at 08:00 pushes context to rep |
| No benchmark | Automatic comparison vs team vs company |
| Managers lack execution data | Real-time team dashboard with scores |

---

## 2. USERS

### 2.1 Primary — Vendedor (B2B Sales Rep)
- **Mental model**: "What do I do right now?"
- **Pain**: Too many open deals, no clear priority, no time for analysis
- **Behavior**: Checks phone/email in the morning, wants clarity fast
- **Friction threshold**: Any task >5 seconds will be skipped
- **Motivation levers**: Daily rank improvement, benchmark vs peers, visible progress

### 2.2 Secondary — Gestor (Sales Manager)
- **Mental model**: "Who needs coaching? Who is performing?"
- **Pain**: No visibility on rep activity between meetings
- **Behavior**: Reviews team data weekly, acts on outliers
- **Risk**: If product feels like surveillance → reps avoid using it

### 2.3 Tertiary — RevOps
- **Mental model**: "Is the pipeline healthy? Will we hit forecast?"
- **Pain**: Inaccurate forecasting, unknown pipeline coverage
- **Behavior**: Analytical, tolerates complex views, exports data
- **Value**: Pipeline coverage, conversion rates, cycle time trends

---

## 3. CORE FEATURES

### F-01: Daily Priority List
- **Output**: Top 5 actions per rep, generated at 07:00 for 08:00 delivery
- **Format**: Ordered list, each item has 3 action buttons
- **Action buttons**: `[Executado]` | `[Reagendar]` | `[Ignorar]`
- **Score impact**: Executado = +points | Reagendar = neutral | Ignorar = -points (small)
- **Explainability**: Each item shows context: stage + value + aging reason

### F-02: At-Risk Accounts
- **Trigger**: Aging > team average for that deal stage
- **Display**: Account name, product, days over average, stage
- **Sort**: Worst first (most days over average)
- **Max visible**: Top 3 in main view, link to full list

### F-03: No-Contact Ranking
- **Trigger**: Days since last registered interaction
- **Display**: Account name, deal value, days without contact
- **Sort**: Most days first
- **Max visible**: Top 3 in main view, link to full list

### F-04: Execution Score
- **Definition**: (actions executed / actions recommended) × 100, rolling 7-day window
- **Display**: Percentage + daily goal indicator
- **Impact**: Feeds team ranking, affects email content, visible to manager
- **Without impact**: Becomes decorative number — do not ship without downstream effects

### F-05: Benchmark Module
- **Dimensions**: Lead time, days-without-contact, conversion-by-product
- **Comparisons**: Rep vs Team vs Company
- **Framing rule**: Always pair comparison with an action suggestion
- **NEVER**: "You are worse than the team" → **ALWAYS**: "You are 6 days above team average. Suggestion: prioritize Engaging follow-ups >14 days"

### F-06: Email Daily (08:00)
- **Trigger**: Automated, daily, business days
- **Content sections** (in order):
  1. Top 5 priorities
  2. At-risk accounts (max 3)
  3. No-contact ranking (max 3)
  4. Current Execution Score
  5. Main AI suggestion (1 sentence)
- **CTA**: Single deep-link to dashboard, pre-filtered to today's priorities

### F-07: Manager Dashboard
- **Blocks** (in order): Execution Score ranking | Avg aging by rep | No-contact ranking | Pipeline coverage | Conversion by product/rep
- **Filters** (required): office | product | period | rep
- **Framing**: Acceleration tool, NOT surveillance tool

---

## 4. KPIs

| KPI | Direction | Definition |
|-----|-----------|------------|
| Lead Time Médio | ↓ Reduce | Avg days from engage_date to close_date |
| Execution Score Médio | ↑ Increase | Team avg of individual execution scores |
| Taxa de Contato Semanal | ↑ Increase | Registered interactions per rep per week |
| Conversão por Produto | ↑ Increase | Won / (Won + Lost) per product category |
| Pipeline Coverage | ↑ Increase | Open pipeline value / revenue quota |

---

## 5. CONSTRAINTS

- Registration flow: ≤5 seconds end-to-end (1-click + 1-select)
- Main screen: maximum 4 primary blocks visible above fold
- AI recommendations: always include ≥1 context reason
- Benchmark framing: always includes actionable suggestion
- Manager view: language must emphasize team acceleration, not individual surveillance
