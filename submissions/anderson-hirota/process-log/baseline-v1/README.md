# Lead Scorer — Challenge 003

A Streamlit app that scores ~8.800 CRM opportunities so sales reps can focus on the deals most likely to close with the biggest impact, instead of prioritizing by gut feel.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Put the four CSV files inside a `data/` folder next to `app.py`:

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

The app opens in the browser. Use the sidebar to filter by **manager, sales rep, region, stage, sector, and minimum score**. Pick any deal in the right-hand panel to see the full score breakdown.

## Scoring logic

Each **open** opportunity (Prospecting or Engaging) gets a **0–100 score** computed as a weighted average of seven subscores. Closed deals (Won / Lost) are excluded from the priority list but still feed the historical win-rate features.

| Feature | Weight | What it captures |
|---|---|---|
| Stage | 25% | Engaging (80) is much closer to closing than Prospecting (35). |
| Agent win rate | 18% | Closed-deal win rate of the rep, Bayesian-smoothed with a global prior so reps with thin history don't dominate. |
| Product win rate | 12% | Some product lines close more reliably. |
| Sector win rate | 10% | Some industries convert better than others. |
| Freshness | 15% | Step function on days since `engage_date`: ≤14d = 100, ≤30d = 85, ≤60d = 65, ≤90d = 45, ≤180d = 25, else 10. Stale deals decay fast. |
| Account size | 10% | Percentile of `revenue` + percentile of `employees` (averaged). Bigger accounts → more budget. |
| Deal value | 10% | Percentile of expected $ (product price for open deals). Bigger deals get a modest bump — focus matters more there. |

Final score = `Σ (subscore × weight)`, rounded.

### Why these features
- **Stage** and **freshness** dominate close probability in any CRM — they're cheap signals with strong predictive value.
- **Agent / product / sector win rates** add a learned prior from your own historical closed deals, so the score gets smarter as more deals close. Win rates are smoothed (prior weight = 5) to avoid penalizing a rep with only 3 closed deals.
- **Account size + deal value** answer "what's at stake?" — two equally-likely-to-close deals aren't equal if one is worth 5×.
- All subscores are **on the same 0–100 scale**, so the breakdown table is directly readable: a rep sees exactly which feature pushed the score up or down.

### Explainability
The right-hand panel shows the full breakdown per deal: raw value, subscore, weight, points contributed, and a plain-English reason. That's the "why score 85" question answered without staring at code.

## Limitations

- **Rule-based, not learned.** Weights are reasoned, not optimized against held-out labels. A logistic regression on the closed deals could improve calibration — but at the cost of explainability, which the brief explicitly rewards.
- **No external signals.** No email opens, web visits, intent data, or contact-level engagement — the CRM tables don't have it.
- **Stage is binary-ish.** With only Prospecting / Engaging / Won / Lost, there's no early/mid/late distinction inside Engaging.
- **Freshness uses `engage_date`** as the start of the clock. If a deal was created but not engaged, days_in_pipeline is undefined and gets a neutral 50 — could be improved with a `created_date`.
- **Reference "today"** defaults to the max `engage_date` in the dataset (since the data is historical). For a live CRM, swap to actual `datetime.now()`.
- **Win rates are global**, not stratified (e.g., agent × sector). With more data, conditional rates would be more accurate but risk small-cell noise.
- **Expected value** for open deals = list price; doesn't account for typical discounting on Won deals.
- **No write-back.** This is a read-only prioritizer; it doesn't push scores back to the CRM.
