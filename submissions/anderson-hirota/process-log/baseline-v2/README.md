# README.md
# Lead Scorer — Challenge 003 (v2)

Streamlit app that prioritizes ~8.800 CRM opportunities so a rep opens the tool, sees their pipeline ranked, and knows where to focus.

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

## Run

```bash
streamlit run app.py
```

Sidebar filters: **manager, rep, region, stage, sector, minimum score, stalled-only**. The right panel shows the full score breakdown plus a recommended action for any selected deal.

## Two numbers per deal — kept separate on purpose

- **Score (0–100)** — a *priority* signal. Weighted average of 6 subscores. Used for ranking the worklist.
- **Close probability (0–1)** — the *empirical* Won/(Won+Lost) ratio for that deal's stage in your historical data. Used in the "Probability-weighted $" KPI so that number actually means something.

Mixing the two (e.g. `score/100 × value`) is wrong — score is not a probability.

## Scoring features

| Feature | Weight | What it captures |
|---|---|---|
| Stage | 30% | Empirical Won/(Won+Lost) per stage, derived from your own closed deals (not hardcoded). |
| Freshness | 20% | Bell shape over `days_since engage_date`: peak 7–30d, decays after 60d. Penalizes both "just engaged, no traction" and stalled deals. |
| Account size | 15% | Avg of revenue percentile + employees percentile. **Percentiles are computed over the 85 unique accounts**, not over the 8.800 pipeline rows — otherwise high-volume accounts dilute their own percentile. |
| Deal value | 15% | Percentile of expected $ across *open* deals (the universe reps are choosing from). |
| Product win rate | 12% | Bayesian-smoothed historical close rate per product. |
| Sector win rate | 8% | Bayesian-smoothed historical close rate per sector. |

**Removed from v1:** agent win rate. It systematically deprioritized struggling reps' deals, which is the opposite of what a rep-facing prioritizer should do.

### Expected $ calibration

Open deals use `sales_price × (1 − typical_discount)`, where `typical_discount` is the median `(close_value / sales_price)` ratio on Won deals — so the forecasted value matches what these deals historically actually close at.

### Reference "today"

`max(today, max(engage_date), max(close_date))`. For historical CSV dumps this snaps to the most recent activity so freshness isn't measured against a calendar date years in the future of the data.

### Recommended actions

Each deal gets a one-line next action based on stage + days + score (e.g. "Stalled 87d — re-engage with new angle.", "Top focus — close this week.", "Likely dead — disqualify or escalate."). Surfaced in the table and the inspect panel.

### Stalled-deal alert

Engaging deals older than 60 days are surfaced as a top-of-page warning with total $ at risk, plus a sidebar toggle to filter to them.

## Limitations

- **Rule-based, not learned.** Weights are reasoned, not fit. A logistic regression could improve calibration but at the cost of explainability — which the brief explicitly rewards.
- **Stage probability comes from closed deals only.** Prospecting and Engaging never appear in closed data, so their probabilities use the fallback table (Prospecting 20%, Engaging 55%). A proper version would need stage-transition history.
- **No external signals.** No email opens, web visits, intent — not in the source CSVs.
- **Win rates are global**, not stratified (e.g. agent × sector). With more data, conditional rates would be more accurate but risk small-cell noise.
- **`typical_discount` is a single median.** Doesn't vary by product or segment.
- **Read-only.** No write-back to the CRM.
