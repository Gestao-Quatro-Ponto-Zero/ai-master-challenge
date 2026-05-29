# README.md
# Lead Scorer — Challenge 003 (v3)

Streamlit app that prioritizes ~8.8k CRM opportunities. A rep opens the tool, sees their pipeline ranked, knows where to focus, and can read off *why* any given deal scored what it did.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Drop the four CSVs into `data/`:

```
.
├── app.py
├── scoring.py
├── requirements.txt
└── data/
    ├── accounts.csv
    ├── products.csv
    ├── sales_teams.csv
    └── sales_pipeline.csv
```

Run:

```bash
streamlit run app.py
```

## Two numbers per deal — kept separate on purpose

- **Score (0–100)** — priority signal. Weighted sum of subscores. Used for ranking the worklist.
- **Close probability (0–1)** — cohort-derived empirical close rate (see below). Used in the "Probability-weighted $" KPI.

Mixing the two (e.g. `score/100 × value`) would be wrong — score is not a probability.

## Scoring features

| Feature | Weight | What it captures |
|---|---:|---|
| Stage | 28% | Cohort close-rate for current stage (see below). |
| Freshness | 18% | Monotone decay over days since `engage_date`. **Omitted, with remaining weights renormalized, when `engage_date` is null** — so Prospecting deals aren't silently penalized for a missing time signal. |
| Account size | 15% | Avg of revenue percentile + employees percentile across the **85 unique accounts** (not 8.8k pipeline rows). |
| Deal value | 16% | Percentile of expected $ across open deals (the universe reps choose from). |
| Product win rate | 15% | Bayesian-smoothed historical close rate per product. |
| Sector win rate | 8% | Bayesian-smoothed historical close rate per sector. |

### Expected $ calibration

Open deals: `sales_price × (1 − typical_discount)`, where `typical_discount` is the median `(close_value / sales_price)` ratio on Won deals.

### Stage close rate — cohort-derived, not hardcoded

The "Probability-weighted $" KPI multiplies value by a **real conditional probability**:

- **Engaging**: `Won / (Won + Lost)` among closed deals with `engage_date` set — i.e. deals that actually reached Engaging.
- **Prospecting**: overall historical `Won / Closed`. Every closed deal was once a prospect, so the full closed cohort is the right denominator.

v2 hardcoded these (20% / 55%) as a fallback. v3 derives them from your data.

### Freshness handling for Prospecting

Prospecting deals typically have no `engage_date` → no time signal. v2 silently neutralized freshness to 50, leaving the score quietly biased. v3 drops freshness from the score for those deals and renormalizes the other weights so they sum to 100%. The breakdown panel shows this explicitly.

### Reference "today"

`max(today, max(engage_date), max(close_date))`. Snaps to the most recent data point so historical dumps don't get freshness measured against a calendar date far past the data.

### Account-level context

The table includes an **Other open** column — how many other open opportunities exist at the same account. The inspect panel surfaces a note when there are siblings. Reps can batch outreach instead of calling the same buyer six times.

### Sort & filters

- Sidebar filters: manager, rep, region, stage, sector, **account**, min score, stalled-only.
- Sort by: score, expected $, days (most stale / freshest), close probability.
- Stalled-only covers both Engaging >60d **and** Prospecting >90d.
- Inspect panel limits its selectbox to the top 200 visible deals, labeled by account/product/score/rep — opportunity IDs are not human-readable.

### Recommended actions

Per-deal one-liner from `(stage, days, score)`. Prospecting now considers age (`Old prospect (Xd) — qualify hard or drop.`, `Stale prospect — disqualify.`), not just stage. Engaging keeps the v2 stalled/top-focus logic.

## Limitations

- **Rule-based, not learned.** Weights are reasoned, not fit. A logistic regression could improve calibration at the cost of explainability — which the brief explicitly rewards.
- **No stage-transition history.** We can identify "ever reached Engaging" via `engage_date`, but can't see *when* it entered Engaging, dwell times, regressions, etc.
- **No external signals.** No email opens, web visits, intent — not in source CSVs.
- **Win rates are global**, not stratified (e.g. agent × sector). Conditional rates risk small-cell noise on this dataset.
- **`typical_discount` is a single median**, not per-product/segment.
- **Read-only.** No write-back to the CRM.
- **No agent-quality feature.** Including rep win-rate would systematically deprioritize struggling reps' deals — the opposite of what a rep-facing prioritizer should do.
