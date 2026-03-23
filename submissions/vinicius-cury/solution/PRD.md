# PRD: Business Optimizer — Support Operations

## Project Codename: **OptiFlow**

> AI-powered support operations analyzer: diagnose bottlenecks, classify tickets, propose automation, deliver actionable roadmap.

---

## 1. Executive Summary

OptiFlow is a diagnostic and optimization tool for customer support operations. It ingests ticket data, maps the current process, identifies bottlenecks and waste, classifies tickets using LLM, and proposes an optimized process with AI automation — all through an interactive dashboard.

**Built for:** G4 AI Master Challenge — Challenge 002 (Redesign de Suporte)
**Context:** A tech company with ~30K tickets/year across email, chat, phone, and social media. Team is overloaded, resolution time is up, satisfaction is down.

**The Diretor de Operações wants:**
1. Where are we losing time?
2. What can be automated with AI?
3. Show me it works — not a PowerPoint, something running.

---

## 2. Problem Statement

The support operation has these symptoms:
- **Rising resolution times** — tickets taking longer to close
- **Declining satisfaction** — customer ratings dropping
- **Team overload** — agents overwhelmed, no clear prioritization
- **No visibility** — leadership can't see where the process breaks

Root causes are unknown. The data exists but hasn't been analyzed systematically.

---

## 3. Goals & Success Criteria

### Primary Goals
1. **Diagnose** — Find where the process breaks, quantified with data
2. **Classify** — Demonstrate LLM can categorize tickets accurately
3. **Propose** — Design an optimized process with clear automation boundaries
4. **Demonstrate** — Working prototype that proves the proposal works

### Success Criteria (from G4 evaluation)
- Used both datasets (metrics + text — power is in the cross)
- Diagnosis has concrete numbers, not generic statements
- Automation proposal is realistic (100% automation is a red flag)
- Knows where AI helps vs where humans are irreplaceable
- Prototype works with real data, not cherry-picked examples

---

## 4. Data Sources

### Dataset 1 — Customer Support Tickets (~30K records)
**Source:** [Kaggle - Customer Support Ticket Dataset](https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset) (CC0)

| Column | Type | Description |
|--------|------|-------------|
| `ticket_id` | string | Unique identifier |
| `customer_name` | string | Customer name |
| `customer_email` | string | Customer email |
| `customer_age` | int | Customer age |
| `customer_gender` | string | Customer gender |
| `product_purchased` | string | Related product |
| `ticket_type` | string | Technical issue / Billing inquiry / Product inquiry |
| `ticket_subject` | string | Short subject line |
| `ticket_description` | text | **Full text** of customer complaint/request |
| `ticket_status` | string | Open / Closed / Pending customer response |
| `resolution` | text | **Full text** of agent resolution |
| `ticket_priority` | string | Low / Medium / High / Critical |
| `ticket_channel` | string | Email / Phone / Chat / Social media |
| `first_response_time` | string | Time to first response |
| `time_to_resolution` | string | Total time to resolution |
| `customer_satisfaction_rating` | int | 1-5 satisfaction score |

**Key value:** Has both operational metrics AND full text (description + resolution). Enables NLP analysis + operational diagnosis.

### Dataset 2 — IT Service Ticket Classification (~48K records)
**Source:** [Kaggle - IT Service Ticket Classification](https://www.kaggle.com/datasets/adisongoh/it-service-ticket-classification-dataset) (CC0)

| Column | Type | Description |
|--------|------|-------------|
| `document` | text | **Full text** of IT support ticket |
| `topic_group` | string | Classification label (8 categories) |

**Categories:** Hardware, HR Support, Access/Login, Storage, Purchase, Internal Project, Administrative rights, Miscellaneous

**Key value:** 48K pre-labeled tickets = training/benchmarking data for classification models.

### Cross-Dataset Strategy
- Dataset 1 → operational diagnosis (time, cost, satisfaction, process)
- Dataset 2 → classification model training/benchmarking
- Classification model trained on Dataset 2 → applied to Dataset 1 tickets
- Result: Dataset 1 tickets get enriched with LLM classification → deeper analysis

---

## 5. User Flow (Dashboard)

```
┌─────────────────────────────────────────────────────┐
│                    OptiFlow                          │
│             Support Operations Optimizer             │
├─────────────────────────────────────────────────────┤
│                                                     │
│  [1. Overview]  [2. Explorer]  [3. Process Map]     │
│  [4. Bottlenecks]  [5. Classification]              │
│  [6. Automation]  [7. Roadmap]                      │
│                                                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. OVERVIEW (Home)                                 │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐      │
│  │ Total  │ │ Avg    │ │ Avg    │ │ Avg    │      │
│  │Tickets │ │ FRT    │ │ TTR    │ │ CSAT   │      │
│  │ 30,142 │ │ 4.2h   │ │ 18.6h  │ │ 3.4/5  │      │
│  └────────┘ └────────┘ └────────┘ └────────┘      │
│                                                     │
│  [Distribution by Channel]  [By Priority]           │
│  [By Type]  [Satisfaction Trend]                    │
│                                                     │
│  2. EXPLORER                                        │
│  ┌─────────────────────────────────────────────┐   │
│  │ Filters: Channel | Priority | Type | Status │   │
│  │          Date Range | Product | Search       │   │
│  ├─────────────────────────────────────────────┤   │
│  │ Ticket | Subject | Type | Priority | Channel│   │
│  │ FRT | TTR | CSAT | Status                   │   │
│  │ ──────────────────────────────────────────── │   │
│  │ TK-001 | Login issue | Tech | High | Email  │   │
│  │ 2.1h | 14.3h | 4/5 | Closed                │   │
│  │ ...                                          │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  3. PROCESS MAP                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │ Mermaid BPMN-style diagram                  │   │
│  │ Swim lanes: Customer | System | Agent        │   │
│  │ Decision points highlighted                  │   │
│  │ Time annotations per step                    │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  4. BOTTLENECKS                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │ Problem categories:                          │   │
│  │ 🔴 Manual work | 🟡 No standard process     │   │
│  │ 🟠 No guided system | 🔵 No integration     │   │
│  │                                              │   │
│  │ Ranked by: time × frequency × cost           │   │
│  │ Cross-filtered by channel, type, priority    │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  5. CLASSIFICATION                                  │
│  ┌─────────────────────────────────────────────┐   │
│  │ LLM classification results                   │   │
│  │ Accuracy benchmarks (Sonnet vs Haiku vs      │   │
│  │ Gemini)                                      │   │
│  │ Confusion matrix | Confidence distribution   │   │
│  │ Sample review panel                          │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  6. AUTOMATION PROPOSAL                             │
│  ┌─────────────────────────────────────────────┐   │
│  │ To-Be process map (Mermaid)                  │   │
│  │ What to automate ✅ vs What stays human 🧑   │   │
│  │ Impact estimates per automation              │   │
│  │ Before/After comparison                      │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  7. ROADMAP                                         │
│  ┌─────────────────────────────────────────────┐   │
│  │ Impact × Effort matrix                       │   │
│  │ Quick wins → Strategic improvements          │   │
│  │ Timeline with milestones                     │   │
│  │ PRD for software solution                    │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 6. Tech Stack

### Core Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Framework** | Next.js 14+ (App Router) | SSR capability, API routes, single deploy |
| **Database** | Supabase (Postgres) | Powerful queries on 30K+ rows, full-text search, RLS |
| **UI** | shadcn/ui + Tailwind | Fast, professional, consistent |
| **Charts** | Recharts | React-native, composable, interactive |
| **Process Diagrams** | Mermaid.js | BPMN-style, data-driven, embeddable |
| **Analytics** | PostHog | Track user interactions with dashboard |
| **Validation** | Zod | All inputs validated |
| **Hosting** | Vercel | Native Next.js, instant deploys |
| **AI — Classification** | Claude API (Sonnet/Haiku) | Primary classifier |
| **AI — Benchmark** | Gemini API | Comparison benchmark for classification |

### Why Full Stack (Not Just a Notebook)
The G4 challenge explicitly says: *"Quero ver algo rodando — não quero só um PowerPoint."*

A notebook shows analysis. A running application shows:
- You can build production software
- The analysis is interactive and explorable
- The classification actually works at scale
- The proposal is concrete, not theoretical

---

## 7. Database Schema

```sql
-- Dataset 1: Customer Support Tickets
CREATE TABLE support_tickets (
  id SERIAL PRIMARY KEY,
  ticket_id TEXT UNIQUE NOT NULL,
  customer_name TEXT,
  customer_email TEXT,
  customer_age INT,
  customer_gender TEXT,
  product_purchased TEXT,
  ticket_type TEXT,          -- Technical issue, Billing inquiry, Product inquiry
  ticket_subject TEXT,
  ticket_description TEXT,   -- Full text
  ticket_status TEXT,        -- Open, Closed, Pending customer response
  resolution TEXT,           -- Full text
  ticket_priority TEXT,      -- Low, Medium, High, Critical
  ticket_channel TEXT,       -- Email, Phone, Chat, Social media
  first_response_time TEXT,  -- Will parse to interval
  time_to_resolution TEXT,   -- Will parse to interval
  customer_satisfaction_rating INT,
  -- Enrichment columns (added by our analysis)
  frt_minutes INT,           -- Parsed first response time in minutes
  ttr_minutes INT,           -- Parsed time to resolution in minutes
  llm_category TEXT,         -- LLM classification result
  llm_confidence FLOAT,      -- Classification confidence 0-1
  llm_model TEXT,            -- Which model classified it
  llm_reasoning TEXT,        -- Model's explanation
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Dataset 2: IT Service Tickets (classification training)
CREATE TABLE it_tickets (
  id SERIAL PRIMARY KEY,
  document TEXT NOT NULL,     -- Full ticket text
  topic_group TEXT NOT NULL,  -- Human-labeled category (8 classes)
  -- Enrichment
  llm_category TEXT,          -- LLM classification for benchmarking
  llm_confidence FLOAT,
  llm_model TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Classification runs (track experiments)
CREATE TABLE classification_runs (
  id SERIAL PRIMARY KEY,
  model TEXT NOT NULL,        -- claude-sonnet, claude-haiku, gemini
  dataset TEXT NOT NULL,      -- support_tickets, it_tickets
  total_records INT,
  classified INT,
  accuracy FLOAT,             -- Only for it_tickets (has ground truth)
  avg_confidence FLOAT,
  taxonomy JSONB,             -- Classification categories used
  config JSONB,               -- Prompt, temperature, etc.
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Process analysis results
CREATE TABLE process_findings (
  id SERIAL PRIMARY KEY,
  phase TEXT NOT NULL,        -- as_is, bottleneck, to_be
  category TEXT,              -- manual_work, no_standard, no_guide, no_integration
  title TEXT NOT NULL,
  description TEXT,
  evidence JSONB,             -- Data points supporting the finding
  impact_hours_month FLOAT,   -- Estimated hours wasted per month
  impact_cost_month FLOAT,    -- Estimated cost per month
  priority TEXT,              -- critical, high, medium, low
  recommendation TEXT,        -- What to do about it
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes
CREATE INDEX idx_support_tickets_channel ON support_tickets(ticket_channel);
CREATE INDEX idx_support_tickets_type ON support_tickets(ticket_type);
CREATE INDEX idx_support_tickets_priority ON support_tickets(ticket_priority);
CREATE INDEX idx_support_tickets_status ON support_tickets(ticket_status);
CREATE INDEX idx_support_tickets_product ON support_tickets(product_purchased);
CREATE INDEX idx_support_tickets_csat ON support_tickets(customer_satisfaction_rating);
CREATE INDEX idx_it_tickets_topic ON it_tickets(topic_group);
CREATE INDEX idx_classification_runs_model ON classification_runs(model);
```

---

## 8. API Routes

```
/api/
├── tickets/
│   ├── GET    /                    # List support tickets (paginated, filtered)
│   ├── GET    /stats               # Aggregate stats (KPIs, distributions)
│   └── GET    /[id]                # Single ticket detail
├── it-tickets/
│   ├── GET    /                    # List IT tickets (paginated)
│   └── GET    /stats               # Category distribution
├── classification/
│   ├── POST   /run                 # Start classification batch
│   ├── GET    /runs                # List past runs
│   ├── GET    /runs/[id]           # Run details + results
│   ├── POST   /test                # Classify a single ticket (live test)
│   └── GET    /benchmark           # Accuracy comparison across models
├── analysis/
│   ├── GET    /process             # As-is process data
│   ├── GET    /bottlenecks         # Ranked bottleneck list
│   ├── GET    /impact              # Time/cost impact estimates
│   └── GET    /recommendations     # Automation recommendations
└── export/
    ├── GET    /report              # Generate PDF/MD report
    └── GET    /csv                 # Export filtered data as CSV
```

---

## 9. Classification Strategy

### Phase 1: Understand the Space (Clustering)
- Sample 500 tickets from Dataset 1
- Ask LLM to cluster into natural categories (unsupervised)
- Compare with Dataset 2's 8 categories
- Design final taxonomy that covers both datasets

### Phase 2: Benchmark on Dataset 2 (Ground Truth)
- Dataset 2 has 48K labeled tickets → perfect benchmark
- Run classification with:
  - Claude Sonnet (high accuracy, higher cost)
  - Claude Haiku (fast, cheaper)
  - Gemini (alternative benchmark)
- Measure: accuracy, precision, recall, F1 per category
- Measure: avg confidence, cost per ticket, latency

### Phase 3: Apply to Dataset 1 (Production)
- Use winning model to classify all 30K support tickets
- Store results in `support_tickets.llm_*` columns
- Enable drill-down by LLM category in all dashboards

### Classification Prompt Design
```
System: You are a support ticket classifier for a technology company.
Classify the following ticket into exactly one category.

Categories:
[taxonomy from Phase 1]

Respond in JSON:
{
  "category": "...",
  "confidence": 0.0-1.0,
  "reasoning": "one sentence explaining why"
}

Ticket:
{ticket_text}
```

### Cost Estimate (Classification)
| Model | Cost/ticket | 30K tickets | 48K tickets |
|-------|-------------|-------------|-------------|
| Sonnet | ~$0.01 | ~$300 | ~$480 |
| Haiku | ~$0.001 | ~$30 | ~$48 |
| Gemini Flash | ~$0.001 | ~$30 | ~$48 |

**Strategy:** Benchmark with small sample (500) on all models → pick best quality/cost ratio → run full batch.

---

## 10. Bottleneck Analysis Framework

### Problem Categories
| Category | Description | Data Signal |
|----------|-------------|-------------|
| **Manual work** | Tasks that could be automated | High TTR + repetitive resolution patterns |
| **No standard process** | Same ticket type handled differently | High variance in TTR for same type/priority |
| **No guided system** | Agents lack decision support | Misclassified priority, wrong channel routing |
| **No system integration** | Disconnected tools/channels | Channel-specific delays, information gaps |

### Quantification Method
```
Impact = Time_per_occurrence × Frequency × (Agent_cost_per_hour)

Where:
- Time_per_occurrence = Median TTR for affected tickets
- Frequency = Count of affected tickets per month
- Agent_cost_per_hour = Assumed $25/hr (configurable)
```

---

## 10b. Resource Analysis & Allocation

### As-Is Resource Map
Duration (hours) = `abs(TTR - FRT)` is the resource proxy. We don't have headcount, but we know how much time goes where.

Analysis dimensions:
- Total hours per channel (~5,100-5,700 each — nearly uniform with synthetic data)
- Total hours per subject
- Total hours per Channel×Subject pair (64 pairs)
- **Total hours per scenario** — the key insight:
  - Hours on "liberar" pairs = waste (low-impact, time doesn't matter)
  - Hours on "acelerar" pairs = under-resourced (need speed)
  - Hours on "quarentena" pairs = need investigation, not more resources

### Reallocation Strategy
Move resources FROM low-impact scenarios TO high-impact:
1. Reduce liberar hours by 50% (chatbot/automation)
2. Reallocate to acelerar (faster agents) and quarentena (root cause investigation)
3. Preserve desacelerar hours (these need MORE time, not less)
4. Redirect redirecionar tickets to better channels (no extra hours needed, just routing)

---

## 10c. Automation Proposal

### 4 Automation Candidates (ordered by Impact × Feasibility)

| # | Candidate | Scenario | Pairs | Feasibility | Impact | Timeline |
|---|-----------|----------|-------|-------------|--------|----------|
| 1 | Fila Prioritária | acelerar | ~9 | 1 (trivial) | 4 (direct CSAT) | < 1 semana |
| 2 | Auto-roteamento | redirecionar | ~17 | 1 (lookup table) | 3 (channel CSAT gap) | < 1 semana |
| 3 | Roteamento Especialista | desacelerar | ~10 | 2 (agent skills) | 3 (quality improvement) | 2-3 semanas |
| 4 | Chatbot Automático | liberar | ~50 | 4 (NLP/chatbot) | 2 (free resources) | 2-3 meses |

### What NOT to Automate
- **Quarentena pairs** — root cause unknown, need human investigation first
- **Desacelerar resolution** — these need human expertise and time, not speed
- **Complex ticket triage** — when Channel×Subject doesn't match known pairs

### Before/After Simulation
- Before: equal resource distribution across all pairs
- After: prioritized queue (acelerar first), auto-redirects (redirecionar), chatbot (liberar)
- Projected: CSAT improvement via faster resolution on acelerar pairs + better channel match on redirecionar pairs

---

## 10d. Functional Prototype Design

### Ticket Classifier
POST `/api/tickets/classify` — accepts `{ channel, subject, description }`, returns scenario + action + explanation.

Logic: lookup (channel, subject) in the 64-pair routing matrix. No ML needed — the matrix IS the model, validated by GBR+SHAP and OLS regression (notebooks 05+06).

### Simulated Queue
GET `/api/tickets/queue` — returns 20 tickets sorted by scenario priority:
1. Acelerar (needs speed NOW)
2. Quarentena (needs investigation)
3. Redirecionar (needs channel switch)
4. Desacelerar (needs careful handling)
5. Manter (working fine)
6. Liberar (low priority)

### Dashboard Pages
- `/classification` — Interactive classifier + simulated queue
- `/automation` — Impact×Feasibility analysis + Before/After simulation
- `/roadmap` — Implementation roadmap with timeline

### New API Routes
```
/api/tickets/
├── GET    /diagnostic         # 6-scenario routing matrix (existing)
├── POST   /classify           # Classify a single ticket
├── GET    /queue              # Simulated priority queue
└── GET    /automation         # Automation analysis + simulation
```

---

## 10e. Parallel Development Strategy

### Lane Division (4 independent terminals)
```
Terminal A ──── analysis/08_resource_analysis.ipynb ──── feat/resource-analysis-notebook
Terminal B ──── /automation page + API ──────────────── feat/automation-page
Terminal C ──── /classification prototype + APIs ────── feat/prototype-classifier
Terminal D ──── /roadmap page + control files ───────── feat/roadmap-page
```

Zero file overlap. Merge order: A → B → C → D.

Each terminal runs `claude --dangerously-skip-permissions` with task-specific prompt from `scripts/terminal_{a,b,c,d}.md`.

**Rationale:** Demonstrates AI Master capability — parallel AI-assisted development with proper branch management. Documented as process evidence for G4.

---

## 11. Deliverable Format (G4 Submission)

### README.md (follows G4 template)
- Executive Summary (3-5 sentences)
- Approach (how we attacked the problem)
- Results / Findings (data, screenshots, links)
- Recommendations (prioritized)
- Limitations

### Solution Folder
```
submissions/candidate-name/
├── README.md                 # G4 template
├── solution/
│   ├── app/                  # Full Next.js application
│   ├── setup.md              # How to run
│   └── analysis-summary.md   # Key findings document
├── process-log/
│   ├── CHAT_LOG.md           # Full conversation log
│   ├── DECISIONS.md          # Decision log
│   ├── screenshots/          # Key moments captured
│   └── chat-exports/         # AI conversation exports
└── docs/
    ├── as-is-process.md      # Process map documentation
    ├── bottleneck-analysis.md
    ├── automation-proposal.md
    └── roadmap.md
```

---

## 12. Cost Estimate

| Service | Free Tier | Notes |
|---------|----------|-------|
| Vercel | Free (hobby) | Sufficient for demo |
| Supabase | Free (500MB) | 30K + 48K rows fits easily |
| Claude API | Pay per use | ~$30-80 for full classification |
| Gemini API | Free tier available | Benchmark only |
| PostHog | Free (1M events) | Dashboard analytics |
| **TOTAL** | **~$30-80** | Mainly classification cost |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | Mar 20, 2026 | Initial PRD — G4 Challenge 002 OptiFlow |
| v1.1 | Mar 21, 2026 | Added: Resource analysis (10b), Automation proposal (10c), Prototype design (10d), Parallel strategy (10e) |

*Current version: 1.1 — March 2026*
*Built for Claude Code agent execution*
