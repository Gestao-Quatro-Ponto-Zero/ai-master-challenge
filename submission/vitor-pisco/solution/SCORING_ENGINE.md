# SCORING_ENGINE.md — Pipeline Coach AI

## META
This file fully specifies the AI priority scoring system. All weights, formulas, and edge cases are defined here. Do not deviate from these specs without product approval.

---

## SCORING OVERVIEW

Each open deal receives a **Priority Score** (0–100) calculated from 5 dimensions. The top 5 deals per rep per day become the daily priority list.

```
Priority Score = W1×tempo_sem_contato + W2×aging + W3×valor + W4×stage + W5×benchmark
```

---

## DIMENSION DEFINITIONS

### D1: Tempo Sem Contato (Days Without Contact)
- **Definition**: Days since last registered interaction on this deal
- **Weight**: 25 points max
- **Formula**: `min(25, days_without_contact / threshold × 25)`
- **Threshold**: 14 days (configurable per product category)
- **Edge cases**:
  - No interactions ever recorded → use days since engage_date
  - Interaction recorded today → score = 0
  - Days > threshold → capped at max weight (25)

### D2: Aging da Oportunidade (Deal Age in Stage)
- **Definition**: Days the deal has been in current stage
- **Weight**: 25 points max
- **Formula**: `min(25, days_in_stage / stage_avg × 25)`
- **stage_avg**: Rolling 90-day average for that stage, per rep's office/team
- **Edge cases**:
  - New deal (<3 days in stage) → score = 0
  - No stage_avg available → use global average
  - days_in_stage > 2× stage_avg → capped at max (25)

### D3: Valor da Oportunidade (Deal Value)
- **Definition**: Estimated deal value vs portfolio maximum
- **Weight**: 20 points max
- **Formula**: `deal_value / portfolio_max_value × 20`
- **portfolio_max_value**: 90th percentile of all open deals for that rep
- **Edge cases**:
  - deal_value = 0 or null → use product list price as proxy
  - deal_value > portfolio_max → capped at max (20)
  - Prospecting stage → value = product list price (no close_value yet)

### D4: Stage Atual (Current Pipeline Stage)
- **Definition**: Fixed weight per stage
- **Weight**: 20 points max
- **Stage weights**:

| Stage | Points | Rationale |
|-------|--------|-----------|
| Engaging | 20 | Active negotiation, highest close probability |
| Prospecting | 10 | Early stage, lower urgency |
| Won | 0 | Removed from scoring |
| Lost | 0 | Removed from scoring |

### D5: Benchmark da Equipe (Team Comparison)
- **Definition**: How this deal compares to team averages
- **Weight**: 10 points max
- **Formula**: `clamp(0, 10, (days_above_team_avg / 7) × 10)`
- **days_above_team_avg**: `deal_aging - team_avg_aging_for_stage`
- **Edge cases**:
  - Deal is below team average → score = 0 (no penalty)
  - days_above_team_avg > 7 → capped at 10

---

## SCORE RANGES AND LABELS

| Score | Label | Color | Action |
|-------|-------|-------|--------|
| 85–100 | 🔴 Crítico | Red | Must act today |
| 70–84 | 🟠 Alto | Orange | Act within 24h |
| 55–69 | 🟡 Médio | Yellow | Act this week |
| 0–54 | ⚪ Baixo | Gray | Monitor only |

---

## TIEBREAKER RULES

When two deals have the same score:
1. Higher deal value wins
2. If still tied: older deal (earlier engage_date) wins
3. If still tied: alphabetical by account name (deterministic)

---

## CONTEXT GENERATION (Explainability)

For each scored deal, generate a human-readable reason string:

```
Template: "{primary_driver} · {secondary_driver} · {value_context}"

Examples:
- "14 dias sem contato · Engaging · $5.4K"
- "Acima da média da equipe em 8 dias · Alto valor · $26K"
- "Novo Engaging hoje · Maior deal do portfólio"
```

### Primary Driver Selection
Use the dimension with the highest individual score contribution:
- D1 wins → "N dias sem contato"
- D2 wins → "N dias acima da média no stage"
- D3 wins → "Maior valor no portfólio"
- D4 wins → "Engaging em andamento"
- D5 wins → "N dias acima da média da equipe"

---

## BATCH JOB SPECIFICATION

```yaml
job_name: daily_priority_scoring
schedule: "0 7 * * 1-5"  # 07:00, Mon-Fri
timeout: 10 minutes
retry_on_failure: 2

steps:
  1. fetch_open_deals:
     query: "SELECT * FROM deals WHERE stage IN ('Prospecting', 'Engaging')"
     
  2. fetch_team_averages:
     query: "SELECT stage, office, AVG(days_in_stage) FROM deals WHERE close_date > NOW()-90d GROUP BY stage, office"
     
  3. calculate_scores:
     for_each: deal
     output: {deal_id, rep_id, score, score_breakdown, context_reason}
     
  4. rank_per_rep:
     partition_by: rep_id
     order_by: score DESC
     take: 5
     
  5. persist:
     table: daily_priorities
     upsert_key: (rep_id, date)
     
  6. mark_ready:
     update: daily_priorities SET status='ready' WHERE date=TODAY()
```

---

## INTRADAY SCORE REFRESH

Triggered by:
- Rep registers an action → re-score affected deal
- Deal stage changes → re-score deal, update daily_priorities
- New deal added → run scoring, insert into daily_priorities if top-5

Do NOT:
- Re-send the 08:00 email
- Reshuffle confirmed priorities (items already marked Executado stay done)

---

## SCORE CALIBRATION (Ongoing)

Track these signals to recalibrate weights over time:
- Execution rate by score range (do high-score items get executed more?)
- Win rate of items that appear in Top 5 vs those that don't
- Rep feedback: "This recommendation was useful" (implicit: executed it)

Recalibrate weights quarterly or when execution rate drops >10% vs baseline.
