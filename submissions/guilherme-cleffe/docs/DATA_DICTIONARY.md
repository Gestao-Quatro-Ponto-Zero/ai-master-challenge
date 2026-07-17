# Data Dictionary — Lead Scorer Datalake

Source: [CRM Sales Predictive Analytics](https://www.kaggle.com/datasets/agungpambudi/crm-sales-predictive-analytics) (CC0), delivered as 4 CSV extracts + metadata.
The lake is rebuilt from `data/raw/` by `python src/build_datalake.py` and written to `data/lake/` (CSVs + `crm.db` SQLite — same content, pick whichever is convenient).

**Snapshot date: 2017-12-31.** The dataset is historical, so every "age" metric is computed against the max date found in the data, not the real clock.

## Cleaning rules applied (raw → lake)

| Issue found in raw data | Fix | Rows affected |
|---|---|---|
| Product named `GTXPro` in pipeline but `GTX Pro` in catalog | Normalized to `GTX Pro` | ~1,480 |
| Sector typo `technolgy` in accounts | → `technology` | 12 accounts |
| Location typo `Philipines` | → `Philippines` | 2 accounts |
| Open deals with no account (1,088 Engaging + 337 Prospecting) | Kept, flagged with `account_known = False` | 1,425 |
| Dates stored as strings | Parsed to dates; missing dates stay null | — |

## Tables

### `fact_deals` (8,800 rows — one per opportunity)

| Column | Type | Description |
|---|---|---|
| `opportunity_id` | str | Unique deal ID (primary key) |
| `sales_agent`, `manager`, `regional_office` | str | From sales_teams join |
| `product`, `series`, `sales_price` | str/num | From products join; `sales_price` = list price USD |
| `account`, `sector`, `year_established`, `revenue_musd`, `employees`, `office_location`, `subsidiary_of` | mixed | From accounts join; null when `account_known = False` |
| `deal_stage` | str | Prospecting → Engaging → Won / Lost |
| `engage_date`, `close_date` | date | Null for stages that haven't happened (all Prospecting deals have no dates) |
| `close_value` | num | Actual revenue; 0 for Lost, null for open deals |
| `account_known` | bool | False for the 1,425 open deals with no account |
| `is_open`, `is_won` | bool | Convenience flags |
| `cycle_days` | int | close − engage, closed deals only |
| `age_days` | int | snapshot − engage, open deals only |
| `expected_value` | num | `close_value` for closed deals; **list price for open deals** (justified below) |

### `dim_accounts` (85) · `dim_products` (7) · `dim_sales_teams` (35)

Cleaned copies of the raw dimensions. `dim_sales_teams` includes 5 agents with zero deals in the pipeline (likely new hires).

## Facts worth knowing (from profiling)

- Historical win rate on closed deals: **63%** (4,238 Won / 2,473 Lost).
- Won deals close at **~100% of list price** (mean ratio 0.99–1.00 per product) → list price is a sound expected-value proxy for open deals.
- **Lost deals die fast** (median cycle 14 days) vs Won (median 57 days) — deal age relative to typical cycle is a real signal.
- All 500 Prospecting deals sit in the **Central** region and have no dates — they are untriaged leads, not tracked deals.
- Open pipeline at snapshot: **2,089 deals ≈ $4.97M** expected value.
