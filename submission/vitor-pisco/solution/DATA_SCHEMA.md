# DATA_SCHEMA.md — Pipeline Coach AI

## META
Data model derived from CRM Sales Pipeline dataset. 8,800 opportunities across 35 reps, 7 products, 3 offices.

---

## ENTITY RELATIONSHIP OVERVIEW

```
sales_teams ──┐
              ├──► sales_pipeline ◄── products
accounts ─────┘
```

---

## TABLE: sales_pipeline (Central Table)
**8,800 rows — one row per opportunity**

| Column | Type | Values | Notes |
|--------|------|--------|-------|
| opportunity_id | VARCHAR(8) | e.g. "1C1I7A6R" | Primary key, unique |
| sales_agent | VARCHAR | FK → sales_teams.sales_agent | Rep name |
| product | VARCHAR | FK → products.product | Product name |
| account | VARCHAR | FK → accounts.account | May be empty string |
| deal_stage | ENUM | Prospecting, Engaging, Won, Lost | Current state |
| engage_date | DATE | YYYY-MM-DD | When rep first engaged |
| close_date | DATE | YYYY-MM-DD or NULL | Only set on Won/Lost |
| close_value | DECIMAL | 0.00 or actual value | 0 if Lost or open |

### Derived Fields (compute at query time)
```sql
-- Days in current stage (open deals)
days_in_stage = CURRENT_DATE - engage_date  -- approximation

-- Days without contact (requires interactions table)
days_without_contact = CURRENT_DATE - MAX(interaction_date)

-- Estimated value (for open deals)
est_value = products.sales_price  -- use list price when no close_value

-- Cycle time (closed deals)
cycle_days = close_date - engage_date
```

### Key Aggregates (from dataset analysis)
```
Total deals:          8,800
Won:                  4,238 (48.2% of total)
Lost:                 2,473 (28.1% of total)
Open (Prospecting):     500  (5.7%)
Open (Engaging):      1,589 (18.1%)

Total won revenue:    $10,005,534
Open pipeline est:    $4,966,215
Overall win rate:     63.2% (Won / Won+Lost)
Avg cycle time:       51.8 days
Median cycle time:    57 days
```

---

## TABLE: sales_teams
**35 rows — one row per sales agent**

| Column | Type | Notes |
|--------|------|-------|
| sales_agent | VARCHAR | Primary key, matches sales_pipeline.sales_agent |
| manager | VARCHAR | Manager name (6 unique managers) |
| regional_office | ENUM | Central, East, West |

### Teams Summary
```
Offices: Central | East | West
Managers (6):
  - Dustin Brinkmann → Central
  - Melvin Marxen → Central
  - Cara Losch → East
  - Rocco Neubert → East
  - Celia Rouche → West
  - Summer Sewald → West

Active reps (with deals): 30
Reps with zero activity:  5 (Mei-Mei Johns, Elizabeth Anderson, 
                             Natalya Ivanova, Carol Thompson, Carl Lin)
```

---

## TABLE: products
**7 rows — one row per product**

| Column | Type | Notes |
|--------|------|-------|
| product | VARCHAR | Primary key (NOTE: "GTX Pro" in products table = "GTXPro" in pipeline) |
| series | ENUM | GTX, GTK, MG |
| sales_price | DECIMAL | List price |

### Products Data
```
product          series  price      won   lost   open   won_val      win_rate
GTXPro           GTX     $4,821     729   418    333    $3,510,578   63.6%
GTX Plus Pro     GTX     $5,482     479   266    223    $2,629,651   64.3%
MG Advanced      MG      $3,393     654   430    328    $2,216,387   60.3%
GTX Plus Basic   GTX     $1,096     653   398    332    $705,275     62.1%
GTX Basic        GTX     $550       915   521    430    $499,263     63.7%
GTK 500          GTK     $26,768    15    10     15     $400,612     60.0%
MG Special       MG      $55        793   430    428    $43,768      64.8%
```

**⚠️ KNOWN DATA ISSUE**: Product name mismatch between tables:
- `products.product` = "GTX Pro"
- `sales_pipeline.product` = "GTXPro"
- Always normalize to "GTXPro" when joining.

---

## TABLE: accounts
**85 rows — one row per customer account**

| Column | Type | Notes |
|--------|------|-------|
| account | VARCHAR | Primary key |
| sector | VARCHAR | technology, medical, retail, software, etc. |
| year_established | INTEGER | |
| revenue | DECIMAL | in millions |
| employees | INTEGER | |
| office_location | VARCHAR | Country |
| subsidiary_of | VARCHAR | Parent company, if applicable |

### Notes
- Many pipeline records have `account = ""` (empty) — account not always recorded
- Account is informational only for scoring; deal-level fields drive priority score

---

## INTERACTIONS TABLE (to be built — not in source data)

The source CRM data does not include interaction history. This table must be created:

```sql
CREATE TABLE interactions (
  interaction_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  opportunity_id  VARCHAR(8) REFERENCES sales_pipeline(opportunity_id),
  rep_id          VARCHAR REFERENCES sales_teams(sales_agent),
  interaction_type ENUM('call', 'email', 'meeting', 'follow_up'),
  result          ENUM('advanced', 'waiting', 'rescheduled', 'lost'),
  interaction_date TIMESTAMP DEFAULT NOW(),
  notes           TEXT  -- optional, not required in MVP
);

-- Index for scoring queries
CREATE INDEX idx_interactions_opportunity ON interactions(opportunity_id, interaction_date DESC);
CREATE INDEX idx_interactions_rep_date ON interactions(rep_id, interaction_date DESC);
```

---

## DAILY_PRIORITIES TABLE (computed — not source data)

```sql
CREATE TABLE daily_priorities (
  priority_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  rep_id            VARCHAR REFERENCES sales_teams(sales_agent),
  date              DATE,
  opportunity_id    VARCHAR(8) REFERENCES sales_pipeline(opportunity_id),
  rank              INTEGER CHECK (rank BETWEEN 1 AND 5),
  score             DECIMAL(5,2),
  score_breakdown   JSONB,  -- {d1: n, d2: n, d3: n, d4: n, d5: n}
  context_reason    VARCHAR(100),
  status            ENUM('pending', 'executed', 'rescheduled', 'ignored') DEFAULT 'pending',
  updated_at        TIMESTAMP,
  
  UNIQUE (rep_id, date, rank)
);
```

---

## KEY QUERIES FOR SCORING ENGINE

### Fetch team averages for D2 (aging benchmark)
```sql
SELECT 
  regional_office,
  deal_stage,
  AVG(close_date - engage_date) as avg_cycle_days
FROM sales_pipeline sp
JOIN sales_teams st ON sp.sales_agent = st.sales_agent
WHERE close_date > CURRENT_DATE - INTERVAL '90 days'
  AND deal_stage IN ('Won', 'Lost')
GROUP BY regional_office, deal_stage;
```

### Fetch open deals with last contact
```sql
SELECT 
  sp.opportunity_id,
  sp.sales_agent,
  sp.product,
  sp.account,
  sp.deal_stage,
  sp.engage_date,
  p.sales_price as est_value,
  COALESCE(
    CURRENT_DATE - MAX(i.interaction_date)::date,
    CURRENT_DATE - sp.engage_date
  ) as days_without_contact
FROM sales_pipeline sp
JOIN products p ON sp.product = REPLACE(p.product, ' ', '') -- normalize GTX Pro
LEFT JOIN interactions i ON sp.opportunity_id = i.opportunity_id
WHERE sp.deal_stage IN ('Prospecting', 'Engaging')
GROUP BY sp.opportunity_id, sp.sales_agent, sp.product, sp.account, 
         sp.deal_stage, sp.engage_date, p.sales_price;
```

---

## REP PERFORMANCE SUMMARY (pre-computed for agent reference)

Top 5 reps by won revenue:
```
1. Darcel Schlecht    Central  $1,153,214  WR: 63.1%  349 won  Avg cycle: 49.4d
2. Vicki Laflamme     West     $478,396    WR: 63.7%  221 won  Avg cycle: 53.6d
3. Kary Hendrixson    West     $454,298    WR: 62.4%  209 won  Avg cycle: 53.0d
4. Cassey Cress       East     $450,489    WR: 62.5%  163 won  Avg cycle: 48.8d
5. Donn Cantrell      East     $445,860    WR: 57.5%  158 won  Avg cycle: 53.3d
```

At-risk reps (win rate <60% or cycle time >60d):
```
Lajuana Vencill   WR: 55.0%  Cycle: 62.9d  → Both metrics at-risk
Moses Frase       WR: 66.2%  Cycle: 64.7d  → Cycle only
Donn Cantrell     WR: 57.5%  Cycle: 53.3d  → Win rate only
Gladys Colclough  WR: 58.2%  Cycle: 53.0d  → Win rate only
Markita Hansen    WR: 57.3%  Cycle: 55.9d  → Win rate only
```

Inactive reps (0 deals in CRM):
```
Mei-Mei Johns, Elizabeth Anderson, Natalya Ivanova, Carol Thompson, Carl Lin
```
