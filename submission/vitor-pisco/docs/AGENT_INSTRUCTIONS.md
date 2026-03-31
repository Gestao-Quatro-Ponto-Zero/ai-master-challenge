# AGENT_INSTRUCTIONS.md — Pipeline Coach AI
# Operating manual for AI agents. Read this file first. Always.

---

## 0. WHAT YOU ARE WORKING WITH

You have access to two types of files:

**Knowledge files** (in this directory — `agent-context/`):
Structured specs, logic, flows, and constraints for the Pipeline Coach AI product.
These are pre-processed and agent-optimized. No need to re-derive anything in them.

**Data files** (CSV — raw CRM data):
Live source data. Always read directly from CSV when you need numbers, records, or analysis.
Never use pre-computed summaries as a substitute for reading the CSV when precision matters.

```
agent-context/
├── AGENT_INSTRUCTIONS.md   ← YOU ARE HERE. Read fully before anything else.
├── INDEX.md                ← File map + quick reference
├── PRODUCT_SPEC.md         ← What the product does and for whom
├── USER_JOURNEYS.md        ← All user flows as state machines
├── SCORING_ENGINE.md       ← Priority score formula + weights
├── UX_RISKS.md             ← 7 adoption risks + mitigations
├── DASHBOARD_SPEC.md       ← All dashboard blocks + hierarchy
├── DATA_SCHEMA.md          ← Data model + known issues + queries
└── DIAGRAMS.md             ← 10 Mermaid diagrams by ID

data/ (CSV files — raw source)
├── sales_pipeline.csv      ← 8,800 deals — CENTRAL TABLE
├── sales_teams.csv         ← 35 reps with manager + office
├── products.csv            ← 7 products with series + price
├── accounts.csv            ← 85 customer accounts
└── metadata.csv            ← Field descriptions for all tables
```

---

## 1. STARTUP PROTOCOL

Run this sequence at the start of every task:

```
STEP 1 → Read AGENT_INSTRUCTIONS.md (this file) fully
STEP 2 → Read INDEX.md for quick orientation
STEP 3 → Identify task type (see Section 2)
STEP 4 → Load only the context files listed for that task type
STEP 5 → Load CSV files only if the task requires data access (see Section 3)
STEP 6 → Execute task
STEP 7 → Validate output against constraints in Section 6
```

Do not load all files at once. Load selectively. Context window is finite.

---

## 2. TASK-TO-FILE ROUTING

Look up your task type. Load only the listed files.

### TASK: Feature design / product spec work
```
LOAD: PRODUCT_SPEC.md
LOAD: USER_JOURNEYS.md
LOAD: UX_RISKS.md (check constraints before designing)
CSV:  Not required unless validating against real data
```

### TASK: Frontend / UI / dashboard implementation
```
LOAD: DASHBOARD_SPEC.md
LOAD: UX_RISKS.md (RISK-01 and RISK-02 are P0 — must not violate)
LOAD: PRODUCT_SPEC.md → Section 3 (features F-01 through F-04)
CSV:  Not required
```

### TASK: Backend / API / database work
```
LOAD: DATA_SCHEMA.md
LOAD: SCORING_ENGINE.md
CSV:  sales_pipeline.csv (primary), then join as needed
WARN: See Section 3 — critical data issues
```

### TASK: Scoring engine / ML / priority algorithm
```
LOAD: SCORING_ENGINE.md (all of it)
LOAD: DATA_SCHEMA.md → sections on sales_pipeline and products
CSV:  sales_pipeline.csv + products.csv + sales_teams.csv
```

### TASK: UX audit / design review / QA
```
LOAD: UX_RISKS.md (all 7 risks)
LOAD: USER_JOURNEYS.md → failure paths
LOAD: DASHBOARD_SPEC.md → validation criteria
CSV:  Not required
```

### TASK: Data analysis / reporting / insights
```
LOAD: DATA_SCHEMA.md
CSV:  Start with metadata.csv to understand fields
CSV:  Then sales_pipeline.csv as primary
CSV:  Join sales_teams.csv, products.csv, accounts.csv as needed
WARN: See Section 3 — critical data issues
```

### TASK: Documentation / diagrams
```
LOAD: DIAGRAMS.md (reference existing diagrams by ID before creating new ones)
LOAD: whichever spec file the diagram topic belongs to
CSV:  Not required unless diagram shows real data
```

### TASK: Onboarding flow / email / user communications
```
LOAD: USER_JOURNEYS.md → JOURNEY-01 and JOURNEY-05
LOAD: PRODUCT_SPEC.md → Feature F-06 (email)
LOAD: UX_RISKS.md → RISK-06 (benchmark framing rules)
CSV:  Not required
```

---

## 3. CSV FILE GUIDE

### 3.1 File Locations and Sizes

| File | Rows | Columns | Primary Key | Central join? |
|------|------|---------|-------------|---------------|
| `sales_pipeline.csv` | 8,800 | 8 | `opportunity_id` | YES — join everything here |
| `sales_teams.csv` | 35 | 3 | `sales_agent` | Via `sales_agent` |
| `products.csv` | 7 | 3 | `product` | Via `product` (see WARNING) |
| `accounts.csv` | 85 | 7 | `account` | Via `account` (see WARNING) |
| `metadata.csv` | 21 | 3 | `Table`+`Field` | Reference only |

### 3.2 Column Reference

**sales_pipeline.csv**
```
opportunity_id  → VARCHAR(8), unique, e.g. "1C1I7A6R"
sales_agent     → rep name, joins to sales_teams.sales_agent
product         → product name, joins to products.product (⚠ see 3.4)
account         → company name, joins to accounts.account (⚠ see 3.5)
deal_stage      → ENUM: "Prospecting" | "Engaging" | "Won" | "Lost"
engage_date     → DATE "YYYY-MM-DD", always present
close_date      → DATE "YYYY-MM-DD", EMPTY STRING if deal is open
close_value     → number if Won, "0" if Lost, EMPTY STRING if open
```

**sales_teams.csv**
```
sales_agent     → rep full name (joins to sales_pipeline.sales_agent)
manager         → manager full name
regional_office → "Central" | "East" | "West"
```

**products.csv**
```
product         → product name (⚠ "GTX Pro" ≠ "GTXPro" in pipeline — see 3.4)
series          → "GTX" | "GTK" | "MG"
sales_price     → integer, suggested retail price in USD
```

**accounts.csv**
```
account         → company name (may not match pipeline — see 3.5)
sector          → industry string (note: "technolgy" typo in source data)
year_established → integer
revenue         → float, annual revenue in millions USD
employees       → integer
office_location → country string
subsidiary_of   → parent company name, often empty
```

**metadata.csv**
```
Table  → table name
Field  → column name
Description → human-readable field description
```
Use metadata.csv when you are unsure what a field means. Always check it before assuming.

### 3.3 How to Read CSV Files (Python)

```python
import csv

# Standard read pattern
with open('sales_pipeline.csv', newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    deals = list(reader)

# Filter open deals
open_deals = [r for r in deals if r['deal_stage'] in ('Prospecting', 'Engaging')]

# Filter won deals
won_deals = [r for r in deals if r['deal_stage'] == 'Won']

# Safe numeric conversion (close_value is empty string for open deals)
def safe_float(val, default=0.0):
    try:
        return float(val) if val.strip() else default
    except (ValueError, AttributeError):
        return default

# Join with products (normalize product name — see 3.4)
with open('products.csv', newline='', encoding='utf-8') as f:
    products = {r['product']: r for r in csv.DictReader(f)}

# Normalize join key
def normalize_product(name):
    return name.replace(' ', '')  # "GTX Pro" → "GTXPro"

# Join
for deal in deals:
    key = normalize_product(deal['product'])
    product_info = products.get(key) or products.get(deal['product'])
```

### 3.4 ⚠️ CRITICAL: Product Name Mismatch

The pipeline and products tables use different names for the same product:

| In `sales_pipeline.csv` | In `products.csv` | Series | Price |
|-------------------------|-------------------|--------|-------|
| `GTXPro` | `GTX Pro` | GTX | $4,821 |
| `GTX Plus Pro` | `GTX Plus Pro` | GTX | $5,482 ✓ |
| `GTX Plus Basic` | `GTX Plus Basic` | GTX | $1,096 ✓ |
| `GTX Basic` | `GTX Basic` | GTX | $550 ✓ |
| `MG Advanced` | `MG Advanced` | MG | $3,393 ✓ |
| `MG Special` | `MG Special` | MG | $55 ✓ |
| `GTK 500` | `GTK 500` | GTK | $26,768 ✓ |

**Rule**: When joining pipeline → products, apply `replace(' ', '')` to the products key, OR handle `GTX Pro` → `GTXPro` explicitly. Only this one product is affected.

### 3.5 ⚠️ CRITICAL: Account Field is Unreliable for Joins

- **16.2% of pipeline rows (1,425 of 8,800) have an empty `account` field.**
- These rows still have valid deal data — only the account link is missing.
- When joining pipeline → accounts, always use a LEFT JOIN pattern.
- Do not filter out empty-account rows unless account data is specifically required.
- Account data (revenue, employees, sector) is supplementary — the scoring engine does not use it.

```python
# Correct pattern — never drop empty-account rows
with open('accounts.csv', newline='', encoding='utf-8') as f:
    accounts = {r['account']: r for r in csv.DictReader(f)}

for deal in deals:
    account_info = accounts.get(deal['account'])  # None if empty or not found — OK
```

### 3.6 ⚠️ CRITICAL: close_value and close_date are Empty for Open Deals

| deal_stage | close_date | close_value |
|------------|------------|-------------|
| Won | YYYY-MM-DD | numeric string e.g. "4514" |
| Lost | YYYY-MM-DD | "0" |
| Engaging | "" (empty string) | "" (empty string) |
| Prospecting | "" (empty string) | "" (empty string) |

**Rule**: Never call `float(r['close_value'])` directly. Always use `safe_float()` or check for empty string first. Same for `close_date`.

For open deals, use `products.csv` → `sales_price` as estimated deal value.

### 3.7 Dataset Date Range

All data spans: **2016-10-20 → 2017-12-27**

This is historical data. Do not compute "days since today" relative to the current real-world date when doing analysis — use relative comparisons within the dataset instead (e.g., cycle time = close_date − engage_date).

When the scoring engine is deployed live, CURRENT_DATE will be the actual run date. In analysis/testing against this dataset, use a reference date of `2017-12-27` (latest record) or the specific analysis window you define.

---

## 4. NAVIGATION DECISION TREE

Use this to find the right file in ≤3 steps:

```
What do you need?
│
├── "What does the product do?"
│     → PRODUCT_SPEC.md § 1-2
│
├── "How does the scoring work?"
│     → SCORING_ENGINE.md (full)
│     → Then: DATA_SCHEMA.md for query patterns
│
├── "What should the dashboard show?"
│     → DASHBOARD_SPEC.md § VIEW-01
│     → PRODUCT_SPEC.md § F-01 through F-04 for feature logic
│
├── "What are the users' flows?"
│     → USER_JOURNEYS.md
│     → JOURNEY-01 = daily rep cycle
│     → JOURNEY-03 = registration flow (P0 UX constraint)
│     → JOURNEY-05 = onboarding
│
├── "What can break adoption?"
│     → UX_RISKS.md
│     → RISK-01 = overload (P0)
│     → RISK-02 = friction (P0)
│     → RISK-03 to 07 = degraded retention
│
├── "What's in the data?"
│     → metadata.csv first (field meanings)
│     → DATA_SCHEMA.md for structure + known issues
│     → Then open the relevant CSV
│
├── "Is there a diagram for this?"
│     → DIAGRAMS.md — check by topic:
│         DIAG-01 = daily cycle flow
│         DIAG-02 = deal state machine
│         DIAG-03 = scoring calculation
│         DIAG-04 = user roles
│         DIAG-05 = registration UX flow
│         DIAG-06 = dashboard hierarchy
│         DIAG-07 = entity relationship
│         DIAG-08 = system architecture
│         DIAG-09 = UX risk quadrant
│         DIAG-10 = benchmark framing
│
└── "Who are the users?"
      → PRODUCT_SPEC.md § 2 (user profiles)
      → USER_JOURNEYS.md § 2.1-2.3 (per-role mental models)
```

---

## 5. COMMON ANALYSIS PATTERNS

These patterns cover the most frequent agent tasks. Copy and adapt.

### Pattern A: Win Rate by Rep
```python
import csv
from collections import defaultdict

with open('sales_pipeline.csv', newline='') as f:
    deals = list(csv.DictReader(f))

rep_stats = defaultdict(lambda: {'won': 0, 'lost': 0})
for d in deals:
    if d['deal_stage'] == 'Won':
        rep_stats[d['sales_agent']]['won'] += 1
    elif d['deal_stage'] == 'Lost':
        rep_stats[d['sales_agent']]['lost'] += 1

for rep, s in sorted(rep_stats.items(), key=lambda x: -x[1]['won']):
    total = s['won'] + s['lost']
    wr = s['won'] / total * 100 if total else 0
    print(f"{rep}: {wr:.1f}% ({s['won']}W / {s['lost']}L)")
```

### Pattern B: Cycle Time by Rep (Won Deals Only)
```python
from datetime import datetime

def parse_date(s):
    return datetime.strptime(s, '%Y-%m-%d') if s.strip() else None

rep_cycles = defaultdict(list)
for d in deals:
    if d['deal_stage'] == 'Won':
        ed, cd = parse_date(d['engage_date']), parse_date(d['close_date'])
        if ed and cd:
            rep_cycles[d['sales_agent']].append((cd - ed).days)

for rep, cycles in sorted(rep_cycles.items(), key=lambda x: -len(x[1])):
    avg = sum(cycles) / len(cycles)
    print(f"{rep}: avg {avg:.1f}d over {len(cycles)} deals")
```

### Pattern C: Open Deals with Estimated Value (Scoring Input)
```python
with open('products.csv', newline='') as f:
    products_raw = list(csv.DictReader(f))

# Build lookup with normalization
products = {}
for p in products_raw:
    products[p['product']] = p
    products[p['product'].replace(' ', '')] = p  # GTX Pro → GTXPro alias

open_deals = []
for d in deals:
    if d['deal_stage'] in ('Prospecting', 'Engaging'):
        product_key = d['product']
        prod = products.get(product_key) or products.get(product_key.replace(' ', ''))
        est_value = float(prod['sales_price']) if prod else 0.0
        open_deals.append({**d, 'est_value': est_value})
```

### Pattern D: Rep → Manager → Office Enrichment
```python
with open('sales_teams.csv', newline='') as f:
    teams = {r['sales_agent']: r for r in csv.DictReader(f)}

for d in open_deals:
    team_info = teams.get(d['sales_agent'], {})
    d['manager'] = team_info.get('manager', 'Unknown')
    d['office'] = team_info.get('regional_office', 'Unknown')
```

### Pattern E: Team Average Cycle Time (for Scoring D2/D5)
```python
from collections import defaultdict

office_stage_avg = defaultdict(list)
for d in deals:
    if d['deal_stage'] in ('Won', 'Lost'):
        ed, cd = parse_date(d['engage_date']), parse_date(d['close_date'])
        if ed and cd:
            team_info = teams.get(d['sales_agent'], {})
            key = (team_info.get('regional_office', ''), d['deal_stage'])
            office_stage_avg[key].append((cd - ed).days)

# Compute averages
avg_by_office_stage = {
    k: sum(v) / len(v)
    for k, v in office_stage_avg.items()
}
```

### Pattern F: Priority Score Calculation (Full)
*See SCORING_ENGINE.md for weight definitions.*

```python
def calc_priority_score(deal, est_value, days_in_stage, days_without_contact,
                         team_avg_days, portfolio_max_value):
    """Returns score 0-100 and breakdown dict."""
    
    # D1: Time without contact (25 pts max)
    THRESHOLD_DAYS = 14
    d1 = min(25, days_without_contact / THRESHOLD_DAYS * 25)
    
    # D2: Aging in stage (25 pts max)
    avg = team_avg_days if team_avg_days else days_in_stage
    d2 = min(25, days_in_stage / avg * 25) if avg > 0 else 0
    
    # D3: Deal value (20 pts max)
    p90 = portfolio_max_value if portfolio_max_value else est_value
    d3 = min(20, est_value / p90 * 20) if p90 > 0 else 0
    
    # D4: Stage weight
    d4 = 20 if deal['deal_stage'] == 'Engaging' else 10
    
    # D5: Team benchmark (10 pts max)
    days_over = days_in_stage - team_avg_days if team_avg_days else 0
    d5 = max(0, min(10, days_over / 7 * 10))
    
    score = round(d1 + d2 + d3 + d4 + d5, 2)
    return score, {'d1': d1, 'd2': d2, 'd3': d3, 'd4': d4, 'd5': d5}
```

---

## 6. OUTPUT VALIDATION CHECKLIST

Before returning any output, validate against these constraints:

### Data outputs
- [ ] Did not call `float()` on `close_value` without empty-string check
- [ ] Did not drop rows with empty `account` field unless account data is required
- [ ] Used `normalize_product()` or equivalent when joining pipeline → products
- [ ] Used `2017-12-27` as reference date for dataset-relative analysis (not today's real date)
- [ ] Cited which CSV file(s) were read

### Feature / design outputs
- [ ] Dashboard main screen has ≤4 blocks (RISK-01 constraint)
- [ ] Registration flow is ≤5 seconds / 2 taps maximum (RISK-02 constraint)
- [ ] Every AI recommendation includes at least 1 context reason (RISK-05)
- [ ] Benchmark copy never uses "você está pior que" framing (RISK-06)
- [ ] Scoring weights match SCORING_ENGINE.md exactly — not approximated
- [ ] Dashboard block order matches DASHBOARD_SPEC.md — not reordered

### Diagram outputs
- [ ] Checked DIAGRAMS.md first — does this diagram already exist?
- [ ] If new diagram, it is consistent with existing diagrams in the same system
- [ ] Mermaid syntax is valid

---

## 7. THINGS AGENTS MUST NOT DO

These are errors seen in previous outputs. Do not repeat them.

| ❌ Wrong | ✅ Correct |
|----------|-----------|
| Compute `float(r['close_value'])` directly | Use `safe_float(r['close_value'])` |
| Drop open deals because they have no `close_value` | Open deals have empty `close_value` — this is expected |
| Join products on `product` field without normalization | Apply `replace(' ', '')` to handle `GTX Pro` / `GTXPro` |
| Ignore 16% of pipeline rows due to empty `account` | Empty account is normal — do not filter these rows |
| Use `CURRENT_DATE` for date math in analysis mode | Use `2017-12-27` as reference date for this dataset |
| Invent scoring weights not in SCORING_ENGINE.md | Load SCORING_ENGINE.md and use exact weights |
| Show more than 4 blocks above fold in rep dashboard | Max 4 blocks — this is a P0 UX constraint |
| Show benchmark without an action suggestion | Comparison + action suggestion is mandatory |
| Use "monitoramento" in manager dashboard copy | Use "apoio" / "aceleração" framing |
| Load all context files at once | Load only files relevant to the task (Section 2) |

---

## 8. QUICK STATS (pre-computed — do not re-derive for trivial queries)

Use these when exact numbers are needed without running analysis:

```
DATASET RANGE:    2016-10-20 → 2017-12-27

PIPELINE TOTALS:
  Total deals:    8,800
  Won:            4,238   (48.2% of all)
  Lost:           2,473   (28.1% of all)
  Engaging:       1,589   (18.1% of all)
  Prospecting:      500    (5.7% of all)
  Win rate:       63.2%   (Won / Won+Lost)
  Avg cycle:      51.8 days
  Median cycle:   57 days
  Won revenue:    $10,005,534
  Open pipeline:  $4,966,215 (estimated at list price)

TEAM:
  Total reps:     35
  Active reps:    30  (with at least 1 deal)
  Inactive reps:   5  (Mei-Mei Johns, Elizabeth Anderson,
                        Natalya Ivanova, Carol Thompson, Carl Lin)
  Managers:        6  (2 per office)
  Offices:         3  (Central, East, West)

PRODUCTS (7 total):
  Highest price:  GTK 500     — $26,768
  Most revenue:   GTXPro      — $3,510,578
  Highest WR:     MG Special  — 64.8%
  Lowest WR:      MG Advanced — 60.3%
  Most deals:     GTX Basic   — 1,866

DATA ISSUES:
  Empty account:  1,425 rows (16.2%)
  Product alias:  "GTX Pro" (products.csv) = "GTXPro" (pipeline)
  Open close_val: empty string (not zero, not null)
  Open close_dt:  empty string (not null)
```

---

## 9. ESCALATION — WHEN CONTEXT FILES ARE INSUFFICIENT

If a task requires information not covered by these files:

1. **Missing business logic** → State assumption explicitly, flag for human review
2. **Ambiguous spec** → Default to the most conservative interpretation, document it
3. **Data anomaly not listed** → Run analysis on CSV, document finding in output
4. **Conflicting specs** → `SCORING_ENGINE.md` > `PRODUCT_SPEC.md` > `INDEX.md` for scoring; `UX_RISKS.md` > `DASHBOARD_SPEC.md` for UI constraints
5. **New feature not documented** → Load `PRODUCT_SPEC.md` for patterns, follow same structure

---

*End of AGENT_INSTRUCTIONS.md*
