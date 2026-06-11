# DealPriority — Scoring Methodology

This document makes the scoring logic reproducible and auditable for the Challenge 003 — Lead Scorer submission.

## 1. Input data

The scoring pipeline starts from the four original challenge files:

| File | Role |
|---|---|
| `sales_pipeline.csv` | Central fact table. One row per opportunity. |
| `accounts.csv` | Account dimension. Joined by `account`. |
| `products.csv` | Product dimension. Joined by `product`. |
| `sales_teams.csv` | Sales team dimension. Joined by `sales_agent`. |

The files are stored in:

```text
data/raw/
```

## 2. Join strategy

`sales_pipeline` is the anchor table.

Joins:

```text
sales_pipeline.account     -> accounts.account
sales_pipeline.product     -> products.product
sales_pipeline.sales_agent -> sales_teams.sales_agent
```

Before the product join, product names are normalized. The known mismatch `GTXPro` vs. `GTX Pro` is resolved by compact alphanumeric matching and by an explicit fallback rule.

Validation guards:

- `opportunity_id` must remain unique after joins.
- row count after joins must remain equal to the original `sales_pipeline` row count.
- missing `account` values are preserved because they exist in the source data.

## 3. Derived variables

| Variable | Purpose |
|---|---|
| `deal_status_group` | Groups deals into `open`, `won` or `lost`. |
| `deal_age_days` | Measures how long an open deal has been in the pipeline. |
| `days_to_close` | Historical days between engage date and close date. |
| `seller_win_rate` | Historical win rate by seller. |
| `product_win_rate` | Historical win rate by product. |
| `regional_win_rate` | Historical win rate by regional office. |
| `manager_win_rate` | Historical win rate by manager. |
| `stage_weight` | Converts funnel stage into an operational maturity signal. |
| `aging_risk_flag` | Flags deals older than the historical 75th percentile of days to close. |

Historical win rates are calculated only from closed deals: `Won` and `Lost`.

## 4. Stage weights

| Stage | Weight |
|---|---:|
| Prospecting | 0.10 |
| Engaging | 0.25 |
| Won | 1.00 |
| Lost | 0.00 |

Only open deals are exported to the final ranked file.

## 5. Score formula

```text
priority_score = 100 × (
    0.45 × stage_weight +
    0.20 × seller_win_rate +
    0.15 × product_win_rate +
    0.10 × regional_win_rate +
    0.10 × manager_win_rate
) − aging_penalty
```

Aging penalty:

```text
-10 points when aging_risk_flag = true
```

The result is clipped to the interval 0–100.

## 6. Weight rationale

| Component | Weight | Reason |
|---|---:|---|
| Stage weight | 45% | Funnel maturity is the strongest direct signal of commercial priority. |
| Seller win rate | 20% | Seller-level performance is the most granular historical execution signal. |
| Product win rate | 15% | Some products have better historical conversion patterns. |
| Regional win rate | 10% | Regional context influences conversion. |
| Manager win rate | 10% | Manager portfolio history adds operational context. |

This is intentionally an explainable heuristic, not a black-box predictive model.

## 7. Percentile recalibration

The raw score distribution was not operationally useful with fixed thresholds. To create a practical priority queue, labels are assigned by percentiles across open deals:

| Rule | Label |
|---|---|
| `priority_score >= p85` | `Foco Agora` |
| `p50 <= priority_score < p85` | `Nutrir` |
| `priority_score < p50` | `Baixa Prioridade` |

This creates a focused top segment for immediate action, a middle segment for nurturing, and a low-priority segment for review or automation.

## 8. Explanation fields

For each open opportunity, the pipeline generates:

| Field | Meaning |
|---|---|
| `top_positive_reason_1` | Main factor increasing priority. |
| `top_positive_reason_2` | Secondary positive factor. |
| `top_risk_reason_1` | Main risk or warning factor. |
| `top_risk_reason_2` | Secondary risk factor. |
| `recommended_action` | Practical next step for the seller. |

Examples:

- `estágio avançado no funil`
- `bom histórico do vendedor`
- `produto com bom desempenho histórico`
- `deal envelhecendo acima do ideal`
- `região com baixa conversão histórica`
- `avançar para o próximo passo hoje`

## 9. How to reproduce

From the project root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install pandas numpy

python scripts/generate_scores.py
```

Expected output:

```text
data/output/ranked_open_deals_final.csv
```
