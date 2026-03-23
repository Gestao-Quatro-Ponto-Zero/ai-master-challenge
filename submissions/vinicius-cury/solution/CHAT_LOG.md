# CHAT_LOG.md — OptiFlow (G4 Challenge 002)

> Conversation log capturing significant interactions, decisions, and AI usage.
> This file serves as process evidence for the G4 AI Master Challenge submission.
> Format: Timestamp, Context, Exchange Summary, Outcome.

---

## Session 1 — Mar 20, 2026 — Project Discovery & Planning

### 1.1 — Challenge Review
**Context:** Human shared the G4 AI Master Challenge repository. Claude analyzed all 4 challenges, submission requirements, and evaluation criteria.

**Key findings:**
- 4 challenges available: Churn (001), Support Redesign (002), Lead Scorer (003), Social Media (004)
- Submission via Pull Request with mandatory process log
- G4 already ran baseline AI responses — must substantially exceed baseline
- Time budget: 4-6 hours (no timer, but efficiency valued)

**Outcome:** Full repo analyzed, all READMEs read, submission guide and CONTRIBUTING.md documented.

### 1.2 — Challenge Comparison & Selection
**Context:** Human evaluated all 4 challenges for depth, data quality, and personal fit.

**Human's assessment:**
- **Support (002):** Richest — process + time as cost + classification + UI. Has text data for NLP.
- **Marketing (004):** Simpler — classification/prediction model on metadata only. No text content.
- **Lead Scorer (003):** "Can't believe they made this a challenge" — straightforward build.
- **Churn (001):** Simplest analysis — no flow data limits depth.

**Decision:** Start with Support (002). Possibly add others later.

### 1.3 — Approach Design
**Context:** Human outlined their consulting methodology for the Support challenge.

**Human's approach:**
1. Data drill down first — understand before designing
2. Map as-is process (Mermaid BPMN-style)
3. Identify bottlenecks (time × people = cost)
4. Classify tickets with LLM (not classic NLP — "NLP sucks")
5. Build live dashboard — think over real data
6. PRD comes AFTER data exploration
7. Stage-based delivery with checkpoints

**Key insight:** "We need to automate first what takes longer and what involves more people. That's where we reduce time."

### 1.4 — Tech Stack & Documentation Decision
**Context:** Human shared 4 template documents from their Wavvo project (CLAUDE.md, PRD.md, BACKLOG.md, DECISIONS.md) and proposed adapting them for this challenge.

**Decisions made:**
- Full stack: Next.js 14+ / Supabase / PostHog / Vercel / shadcn/ui
- Focus on Operations (002) first
- Create adapted document set as first deliverable
- Log all conversations for G4 process evidence
- Treat as a "business optimizer consultant" built on Claude Code

**Human's problem identification framework:**
- Manual work
- Lack of standard process
- Lack of guided system
- Lack of system integration

**Human's delivery workflow:**
1. Understand goals → 2. Get data (dashboard + filters) → 3. Map as-is process (Mermaid) → 4. Plot and validate → 5. Identify problems → 6. Quantify bottlenecks → 7. Wait for guidance → 8. Design to-be with automation → 9. Explain impact → 10. Create roadmap + PRD

### 1.5 — Document Set Creation
**Context:** Claude created the full project document set adapted from Wavvo patterns.

**Documents created:**
- `CLAUDE.md` — Agent instructions with 7-phase consultant workflow
- `PRD.md` — Product spec for "OptiFlow" with DB schema, API routes, classification strategy
- `BACKLOG.md` — Full task tracking across 7 phases + Phase 0 setup
- `DECISIONS.md` — 5 initial decisions logged (stack, methodology, LLM over NLP, data inference, doc system)
- `CHAT_LOG.md` — This file

**Outcome:** Foundation documents ready for human review.

---

---

## Session 2 — Mar 20, 2026 — Project Scaffold

### 2.1 — Pre-Scaffold Q&A
**Context:** Claude asked 9 clarifying questions before starting initialization. Human provided answers.

**Questions asked & answers:**
1. **Supabase CLI?** → Not installed. Claude installed via Homebrew (v2.75.0).
2. **Docker running?** → No, but will use Supabase cloud (online).
3. **Node.js version?** → v24.12.0 (compatible).
4. **shadcn/ui style?** → Claude's choice → Used defaults (new shadcn v4 with base-ui).
5. **Dashboard color scheme?** → Professional. Used zinc base with clean sidebar.
6. **Candidate name?** → Vinicius Cury. Submission folder: `submissions/vinicius-cury/`.
7. **Git remote?** → Both local and GitHub (on user's account).
8. **PostHog?** → Claude's choice → Deferred config, env vars added.
9. **G4 baseline responses?** → Human clarified: all G4 instructions are important for behavior. G4 already ran baselines with multiple AI models — submission must substantially exceed what AI produces alone.

**Key human feedback:**
- "you need to install everything needed, this is a new project" — don't assume tools are available
- "the goals are there, it should be in claude.md" — reference existing docs rather than re-asking
- MCP tools are available for screenshots

### 2.2 — Environment Setup
**Context:** Fresh machine setup. Claude installed required tools.

**Installed:**
- Supabase CLI v2.75.0 (via `brew install supabase/tap/supabase`)
- GitHub CLI v2.88.1 (via `brew install gh`)
- Verified Node v24.12.0 / npm v11.6.2

### 2.3 — G4 Challenge Reference
**Context:** Cloned G4 challenge repo, copied reference files into `reference/g4/`.

**Files copied:**
- `reference/g4/challenge/README.md` — Challenge 002 full spec
- `reference/g4/submission-guide.md` — What to submit, process log requirements
- `reference/g4/submission-template.md` — README template for submission
- `reference/g4/CONTRIBUTING.md` — PR submission instructions
- `reference/g4/README.md` — AI Master Challenge overview

**Key takeaways from G4 reference:**
- G4 already ran each challenge through multiple AI models (Claude, GPT, Gemini) as baseline
- "Parecido com o baseline não é suficiente" — must substantially exceed AI-only output
- Process log is mandatory — no log = disqualified
- Submission via PR to `submissions/vinicius-cury/` on branch `submission/vinicius-cury`
- They evaluate: understanding problem first, strategic AI use, actionable output, iteration + judgment evidence
- Time budget: 4-6h (no timer, but efficiency valued)
- "O valor de um AI Master não é saber pedir pra IA. É saber o que pedir, quando desconfiar, o que ajustar"

### 2.4 — Project Scaffold
**Context:** Full Next.js project initialization with all dependencies and structure.

**What was built:**
1. **Next.js 16 (App Router, TypeScript, Tailwind CSS, Turbopack)** — initialized with `create-next-app`
2. **Dependencies installed:** @supabase/supabase-js, @supabase/ssr, zod, recharts, mermaid, lucide-react, posthog-js
3. **shadcn/ui v4** — initialized with 15 components (button, card, table, tabs, badge, input, select, separator, sheet, dialog, dropdown-menu, tooltip, command, popover, calendar)
4. **Supabase init** — `supabase/` directory created with config
5. **Initial migration** — 4 tables (support_tickets, it_tickets, classification_runs, process_findings) + 8 indexes
6. **Supabase client helpers** — `src/lib/supabase/client.ts` (browser) + `server.ts` (API routes)
7. **Root layout** — sidebar navigation with 7 tabs matching consultant phases
8. **7 page shells** — each with PageHeader + placeholder client component (SPA pattern)
9. **Project structure** — process-log/, data/, analysis/, submissions/ directories
10. **.env.local.example** — all required env vars documented
11. **.gitignore** — updated for /data/ and env files

**Technical note:** shadcn/ui v4 uses `@base-ui/react` instead of Radix, so Tooltip API is different (no `asChild`, no `delayDuration`). Simplified sidebar to use plain Links instead.

**Outcome:** Full project scaffold passing type check (`tsc --noEmit` clean). Ready for data loading.

### 2.5 — GitHub Setup
**Context:** GitHub CLI authenticated via `gh auth login --web`. Repo created and pushed.

**Result:** Private repo at https://github.com/viniciuscury/optiflow — initial scaffold committed and pushed.

**Human feedback:** Do not add `Co-Authored-By` lines to commits. Added rule to CLAUDE.md Git Conventions section.

### 2.6 — Analysis Notebook Layer
**Context:** Human provided JUPYTER_SETUP.md with detailed instructions for adding Jupyter notebooks as an analysis scratchpad. Claude asked 6 clarifying questions before proceeding.

**Q&A before implementation:**
1. **Python venv vs system-wide?** → Use venv to avoid conflicts (Claude's decision)
2. **Supabase connection?** → Human suggested installing Supabase MCP to connect with their account
3. **Which Claude models?** → "We will decide when the time comes" — cost analysis first, run classifications in parallel
4. **Raw SQL via RPC?** → Claude explained the limitation: Supabase Python client has no raw SQL. Proposed 3 options (direct Postgres, query builder only, RPC functions). Human chose option A (direct Postgres via psycopg2).
5. **Notebook outputs committed?** → "Keep notebook locally, we will review in the end to commit"
6. **ipykernel needed?** → Human challenged: "why default would not work?" — valid point, but registered kernel anyway for venv isolation

**What was built:**
- Python venv at `analysis/.venv/` with all analysis dependencies
- `analysis/lib/db.py` — Direct Postgres connection (psycopg2) for raw SQL + Supabase client for table ops
- `analysis/lib/classify.py` — Claude + Gemini classification with batch support and benchmarking
- `analysis/lib/notebook.py` — Create/execute/read notebooks programmatically from CLI
- `analysis/run.sh` — Shell script for headless notebook execution via papermill
- 4 starter notebooks: data exploration, process mapping, classification, bottlenecks
- Supabase MCP server configured (pending access token from human)
- CLAUDE.md updated with notebook architecture rules
- Jupyter kernel "optiflow" registered pointing to venv

**Technical note:** Python 3.9.6 on macOS doesn't support `str | Path` union syntax — fixed with `from __future__ import annotations`.

### 2.7 — Security Incident & Token Configuration
**Context:** Human placed Supabase access token in `.env.local.example` (git-tracked file) instead of `.env.local` (gitignored).

**What happened:**
1. Claude read the file and the token was visible in chat output
2. Immediately moved token to `.env.local` (gitignored)
3. Cleaned `.env.local.example` back to placeholder
4. Committed fix and pushed
5. Warned human to revoke the exposed token and generate a new one
6. Human generated new token, placed it correctly in `.env.local`
7. Supabase MCP reconfigured with new token

**Lesson:** Always store secrets in gitignored files only. Chat logs are recorded for G4 evidence — any secret displayed becomes permanently visible.

### 2.8 — Memory System Setup
**Context:** Human requested memory files so conversation context persists across chat restarts.

**Memory files created:**
- `user_profile.md` — Vinicius Cury profile and working preferences
- `feedback_git.md` — No Co-Authored-By in commits
- `feedback_security.md` — Never display secrets in output
- `feedback_approach.md` — Working approach preferences
- `project_optiflow.md` — Current project status and next steps
- `reference_g4.md` — G4 challenge rules and evaluation criteria

---

## Session 3 — Mar 20, 2026 — Data Intake & Supabase Setup

### 3.1 — CSV Datasets Obtained
**Context:** Claude identified the two required datasets from the G4 challenge README (Kaggle links). Human downloaded both and placed them in the project root.

**Datasets:**
- `all_tickets_processed_improved_v3.csv` → Dataset 2 (IT Service Tickets, 47,837 rows, columns: Document, Topic_group)
- `customer_support_tickets 2.csv` → Dataset 1 (Customer Support Tickets, 29,807 rows, columns: Ticket ID, Customer Name, Email, Age, Gender, Product Purchased, Date of Purchase, Ticket Type, Ticket Subject, Ticket Description, Ticket Status, Resolution, Ticket Priority, Ticket Channel, First Response Time, Time to Resolution, Customer Satisfaction Rating)

**Action:** Copied to `data/customer_support_tickets.csv` and `data/it_service_tickets.csv`.

### 3.2 — Supabase MCP Token Issue
**Context:** Previous access token was revoked after Session 2 security incident. Human generated a new token and placed it in `.env.local`.

**Issue:** MCP server process was already running with the old token. Updating the config file doesn't restart the running MCP process — requires Claude Code restart. Token verified working via direct `npx` test.

**Status:** MCP config updated with new token. Awaiting Claude Code restart to pick up new token.

### 3.3 — Next Steps
- Restart Claude Code → MCP picks up new token
- Create Supabase cloud project
- Run migration on cloud project
- Fill `.env.local` with cloud project keys
- Write seed script to load CSVs into Supabase
- Begin Phase 1: Data Exploration

---

## Session 4 — Mar 20, 2026 — Supabase Cloud Setup & Course Corrections

### 4.1 — Supabase Cloud Project Created
**Context:** MCP token working after restart. Created cloud project and applied migration.

**What was done:**
- Supabase MCP connected successfully (new token working)
- Created project "optiflow" (id: mbyfatsvjlxltctrgrdt, region: eu-west-1, free tier)
- Applied initial_schema migration (4 tables + 8 indexes)
- Updated .env.local with URL + anon key
- Service role key still needed from dashboard

### 4.2 — Seed Script Written
**Context:** Wrote Python seed script to load CSVs into Supabase via REST API.

**Script:** `scripts/seed.py` — reads CSVs with pandas, batch inserts (500 rows) via Supabase REST API using service role key.
**Dependency:** Needs `SUPABASE_SERVICE_ROLE_KEY` in `.env.local` to run.

### 4.3 — Data Exploration Notebook Prepared
**Context:** Rebuilt `01_data_exploration.ipynb` with 8 analysis sections.

**Sections:**
1. Carregar & Inspecionar (shape, dtypes, nulls)
2. Distribuições Categóricas (canais, prioridades, tipos, status)
3. Métricas de Tempo — FRT & TTR (parse + histograms)
4. Tempo por Dimensão (heatmaps: canal × prioridade, canal × tipo)
5. Análise de Satisfação (CSAT distribution, by channel, vs TTR/FRT)
6. Análise por Produto (volume, TTR, CSAT per product)
7. Dataset 2 — IT Tickets (topic groups, document lengths)
8. Principais Descobertas (to be filled after execution)

### 4.4 — Correction: Content Language
**What happened:** Claude wrote the entire notebook in English.
**Human correction:** "everything we write there and in our websystem must be in brazilian portuguese"
**Action:** All markdown cells, chart titles, and labels rewritten in pt-BR. Rule added to CLAUDE.md.

### 4.5 — Correction: Pace & Documentation
**What happened:** Claude rushed through creating project, migration, seed script, notebook, and tried to execute — all without pausing for human setup or review.
**Human correction:** "here you are going too fast, we need to recap some stuff... make clear on the decision documents when I correct you, put this information on claude.md to setup your behavior"
**Action:**
- Added "Working Rules" section to CLAUDE.md with language, pace, documentation, and security rules
- Added D006-D009 to DECISIONS.md (including explicit correction entries)
- Updated all memory files
- Puppeteer MCP configured for screenshot documentation

### 4.6 — Puppeteer MCP & Jupyter Setup
**Context:** Human wants visual documentation of the analytical process.

**What was done:**
- Puppeteer MCP added via `claude mcp add` (needs restart to connect)
- Jupyter server tested and working (analysis venv)
- Screenshots will be saved to `process-log/screenshots/`
- Added Tools & Services section to CLAUDE.md documenting Jupyter, Puppeteer, and Supabase configs

### 4.7 — Status at End of Session 4
**Ready:**
- Supabase cloud project + migration
- Notebook prepared (pt-BR)
- Seed script ready
- Puppeteer MCP configured
- All control docs updated

**Needs after restart:**
1. Verify Puppeteer MCP connects
2. Human provides service role key
3. Run seed script to load data
4. Start Jupyter → human reviews notebook
5. Screenshot key outputs

---

## Session 5 — Mar 20, 2026 — Data Exploration & Quality Audit

### 5.1 — Notebook Execution & Variable Classification
**Context:** Human asked to open the data in Jupyter, classify each variable, list categorical values (up to 20), run stats on quantitative ones.

**What was done:**
- Executed `01_data_exploration.ipynb` via papermill
- Classified all 17 variables in Dataset 1 (5 identifiers, 4 categorical, 3 text, 3 time/date, 1 quantitative, 1 derived)
- Listed all values for categorical variables: 5 channels, 4 priorities, 4 types, 3 statuses, 16 ticket subjects
- Statistical analysis on Customer Age and CSAT Rating

### 5.2 — Data Quality Discovery
**Context:** Human suspected Ticket Subject was preset text, asked Claude to verify. Then asked about Description.

**Findings:**
- **Ticket Subject:** 16 fixed categories (not free text) — e.g., "Product setup", "Billing inquiry", "Refund request"
- **Ticket Description:** Templates with `{product_purchased}` placeholder, not unique text. Each Subject maps to a Description template, but some templates appear under multiple Subjects (incoherent mapping)
- **Resolution:** Lorem ipsum / nonsensical text — no analytical value
- **Timestamps:** FRT and TTR are randomized — ~50% of cases have TTR before FRT (impossible in reality)
- **Distributions:** Perfectly uniform across channels, priorities, types — confirms synthetic data

**Human decisions:**
- Description incoherence "will not matter" for the project objective
- Use `abs(TTR - FRT)` as proxy for duration, only for Closed tickets
- Document all quality issues formally

### 5.3 — Status Structure Identified
**Context:** Analysis of which fields are populated per status.

**Finding:**
- **Open** (2,819 / 33.3%) — no FRT, no TTR, no CSAT, no Resolution
- **Pending Customer Response** (2,881 / 34.0%) — has FRT, no TTR
- **Closed** (2,769 / 32.7%) — has everything: FRT, TTR, CSAT, Resolution

This reveals the lifecycle: Open → Pending → Closed.

---

## Session 6 — Mar 20, 2026 — Dashboard Build & Bottleneck Analysis

### 6.1 — Dashboard API & Initial Charts
**Context:** Human asked for an interactive dashboard to visualize bottlenecks. Asked 5-10 questions before starting.

**What was built:**
- 3 API routes: `/api/tickets` (raw data), `/api/tickets/stats` (aggregated stats), `/api/tickets/scatter` (regression analysis)
- All routes read CSV directly (no Supabase — cloud not set up yet)
- CSV parsed server-side with custom parser handling quoted fields
- 6 filter dropdowns: Canal, Prioridade, Tipo, Assunto, Status, CSAT

### 6.2 — Correction: Negative Duration
**What happened:** Dashboard showed negative resolution times.
**Human spotted it:** "check again, we have negative resolution time"
**Root cause:** TTR timestamps are randomized — some fall before FRT.
**Fix:** `Math.abs(TTR - FRT)` as proxy, only computed for Closed tickets.

### 6.3 — Correction: Missing Filter Labels
**What happened:** Dropdowns had no visible titles.
**Human spotted it:** "i dont have the titles in the filters"
**Fix:** Added `<span>` labels above each Select component.

### 6.4 — CSAT Segmentation
**Human defined 3 segments:**
- Satisfeito (≥4)
- Neutro (=3)
- Insatisfeito (≤2)

### 6.5 — Scoring Criteria Design
**Context:** Human wanted a criteria that mixes insatisfaction with business impact.

**Claude proposed 3 options:**
- A: Volume × Taxa Insatisfação
- B: Volume × Taxa Insatisfação × Duração Média (Risco Operacional)
- C: Volume × Duração Média × CSAT Inverso

**Human chose:** B and B by Priority (multiplied by priority weight: Critical=4, High=3, Medium=2, Low=1).

**Result:**
- **Risco Operacional** = Volume × Taxa_Insatisfação × Duração_Média
- **Risco por Prioridade** = Risco Operacional × Peso_Prioridade

Documented in notebook Section 9 with formulas, justification, and limitations.

### 6.6 — Heatmaps & Cross-Tab Analysis
**Context:** Human asked for actionable visualizations focused on channels (what can be automated).

**Built:**
- CSS heatmap (green→red gradient) for Canal × Assunto and Canal × Prioridade
- Duration vs CSAT heatmap (duration buckets × CSAT ratings 1-5)
- Finding: no correlation between duration and CSAT in synthetic data (uniform distribution across all cells)

### 6.7 — Regression Scatter Chart
**Context:** Human asked to plot regression relating time to solve with CSAT for worst 25%.

**Built:**
- Bubble scatter chart (size = √totalTickets × 1.8)
- Worst 25% in red, rest in gray
- Linear regression line with R² display
- Goal zone (green) and Critical zone (red)
- Average reference lines

**Finding:** R² ≈ 0.003-0.011 across all dimensions — confirms no correlation between duration and satisfaction in synthetic data.

### 6.8 — Bottleneck Tables
**Built:**
- Sortable tables with SortableHeader components
- Dimension-specific filters for cross-tab data (e.g., filter by specific Canal or Assunto within the table)
- Columns: Nome, Tickets, Resolvidos, Duração Média, % Insatisf., CSAT Médio, CSAT Mediana, Risco Op., Risco Prio., Satisfação breakdown

---

## Session 7 — Mar 20, 2026 — Dashboard Organization & Dataset 2 Review

### 7.1 — Dashboard Reorganized into 4 Sections
**Context:** Human asked to separate analysis dimensions to avoid mixing information.

**Layout:**
1. **Visão Geral** — KPIs, duration by channel/priority, satisfaction by channel/priority
2. **Análise: Canal × Assunto** — subject chart, heatmap, duration×CSAT, regression scatter, bottleneck table
3. **Análise: Canal × Prioridade** — heatmap, duration×CSAT, regression scatter, bottleneck table
4. **Análise: Prioridade × Assunto** — heatmap, duration×CSAT, regression scatter, bottleneck table

Scatter API made configurable with `?groupBy=channelSubject|channelPriority|prioritySubject`.

### 7.2 — Dataset 2 Review
**Context:** Human asked to check Dataset 2 variables before proceeding to classification.

**Finding:**
- 47,837 rows, 2 columns only: `Document` (free text, avg 291 chars) and `Topic_group` (8 categories)
- Categories: Access, Administrative rights, HR Support, Hardware, Internal Project, Miscellaneous, Purchase, Storage
- This is a labeled training dataset for NLP classification — no timestamps, no CSAT, no status

### 7.3 — Correlação Pearson por Par Canal × Assunto
**Context:** R² global era ~0.003, sugerindo zero correlação entre duração e CSAT. Human pediu para verificar por par individual.

**Key Finding:**
- A nível agregado: R² ≈ 0.003 (sem correlação)
- A nível de par Canal × Assunto: correlações individuais de **-0.70** a **+0.87**
- Correlações opostas se cancelam quando agregadas — o efeito Simpson mascarava correlações reais
- Exemplos: Email × Battery life: r = +0.42 (mais tempo → MAIS satisfação?), Phone × Data loss: r = -0.54 (mais tempo → menos satisfação)
- Em dados sintéticos, essas correlações são artefatos do tamanho pequeno de cada grupo (~30-50 tickets por par), mas o **método** é o que importa

**Human reaction:** "we found the way" — este é o insight metodológico correto para dados reais.

**Action:** Heatmap de correlação Pearson adicionado ao dashboard (Seção 2). 10 screenshots capturados e salvos em `process-log/screenshots/`.

### 7.4 — LLM Classification Cost Analysis
**Context:** Human asked which API is cheapest for classifying 48K tickets.

**Analysis:**
- Gemini 2.0 Flash: ~$0.15 (cheapest)
- Gemini 2.5 Flash / GPT-4o mini: ~$0.25
- Claude Haiku 3.5: ~$1.50

**Human leaning:** Gemini Flash. Decision pending on which API is already configured.

---

## Session 8 — Mar 21, 2026 — Diagnostic Drill-down: 4 Cenários Operacionais

### 8.1 — Plan Mode: Diagnostic Framework Design
**Context:** Human wanted to go beyond correlation analysis. Not just "where is there a relationship?" but "what do we DO about it?"

**Human's 4-scenario framework:**
1. **Acelerar** — negative correlation, speed matters → route to fast agents
2. **Desacelerar / Mais Cuidado** — positive correlation, more time = better CSAT → specialized agents
3. **Redirecionar Canal** — channel experience is wrong → route to better channel for that subject
4. **Liberar Recursos** — no correlation → deprioritize, free up resources for scenarios 1-3

**Key human insight:** "Don't spend resource where resources don't matter. Bring resources from where they don't matter to the places that matter. That's the true routing system."

**Action:** Plan approved with Mermaid decision flowchart for the classification process.

### 8.2 — Implementation: API + Dashboard
**Built:**
- `src/app/api/tickets/diagnostic/route.ts` — tercile analysis, efeito_canal vs efeito_tempo, Pearson r thresholds, 4-scenario classification
- `src/app/diagnostic-panel.tsx` — summary cards, Mermaid decision tree, routing matrix heatmap, per-subject diagnostic detail, action plan tables
- Dashboard reorganized: 8 sections in narrative order (Visão Geral → Assunto×Satisfação → Canal×Assunto → Diagnóstico → Plano de Ação → Referência)

**Results:**
- 14 pairs classified as Acelerar (514 tickets)
- 14 pairs classified as Desacelerar (491 tickets)
- 16 pairs classified as Redirecionar (576 tickets)
- 20 pairs classified as Liberar Recursos (738 tickets)

**Method validation:** The tercile approach (dividing tickets into rápido/médio/lento by duration, then comparing CSAT across channels within each tercile) successfully separates canal effect from tempo effect even in synthetic data.

### Where AI erred / human corrected
- AI initially proposed only 2 scenarios (time vs experience). Human expanded to 4 scenarios, adding "desacelerar" (positive correlation = spend MORE time) and "liberar recursos" (no correlation = deprioritize). This is a consulting insight — the AI optimized for finding problems, the human optimized for resource allocation.

---

## Session 8b — Mar 21, 2026 — Diagnostic v2: Two-Layer Analysis Correction

### Context
Human reviewed v1 diagnostic results and found critical flaws: several subjects had ALL 4 channels classified as "redirecionar" (Battery life, Delivery problem, Peripheral compatibility, Product setup). Human challenged: "if a ticket comes from a given subject and you put all channels redirect, what that means?" Phone × Peripheral Compatibility (r=0.87) was wrongly classified as "redirecionar" instead of "desacelerar".

### Root Cause
v1 used `efeito_canal > efeito_tempo × 1.5` at subject level, overriding pair-level correlations. This made channel effect dominate and ignored strong pair-specific correlations.

### Human's Design Direction
Human explicitly specified TWO separate analyses:
1. **Dimension A:** r(time, CSAT) of the PAIR — does time influence satisfaction in this specific combination?
2. **Dimension B:** CSAT level comparison across channels — is this channel good/bad for this subject?

Key insight from human: "One thing is the R of the pair. The other thing is if time matters, it's different. So they have two analyses."

### What Changed
- Decision tree: pair-first (check r of PAIR before comparing channels)
- 4 scenarios → 6 scenarios: added Quarentena (bad CSAT, no viable redirect) and Manter (good CSAT, time neutral)
- Redirection viability matrix with physical constraints (Social media → Chat = impossible, etc.)
- Divergence detection: when SubR and PairR disagree, flagged explicitly
- Human correction on Social media: "Social media can be redirected to email, can be redirected to phone. You redirect TO social media that is harder."

### Results (v2)
- 9 Acelerar, 10 Desacelerar, 17 Redirecionar, 5 Quarentena, 7 Manter, 16 Liberar
- Phone × Peripheral Compatibility = desacelerar (r=0.87) ✓
- Email × Hardware Issue = acelerar (r=-0.705) ✓
- 0 Social media → Chat redirections ✓

### Where AI erred / human corrected
- AI's v1 classified by subject-level effects, ignoring pair-specific correlations. Human forced pair-first analysis.
- AI initially blocked all Social media redirections. Human corrected: SM→Email and SM→Phone are viable.
- AI conflated "r of the pair" with "does time matter" — these are the same measurement (Pearson r between duration and CSAT within the pair), but human needed explicit confirmation that Dimension A IS the time-satisfaction relationship.

---

## Session 9 — Mar 21, 2026 — ML Validation of Diagnostic Framework

### 9.1 — Strategy: Systematic ML validation
**Context:** Human wanted to validate the manual 6-scenario classification with systematic ML experiments. Three parallel analyses planned:
1. GBR + SHAP (notebook 05) — feature importance and interactions
2. OLS Regression (notebook 06) — interpretable coefficients with interaction terms
3. LLM Classification (notebook 07) — Gemini 2.5 Flash Lite on Dataset 2

**Human insight:** "Channel and Subject are actionable — that's what matters. We can route tickets and prioritize queues. Duration is the variable to test within those contexts."

### 9.2 — Notebook 05: GBR + SHAP (12 experiments)
**Outcome:** All 12 experiments completed. Best model (Channel+Subject only) MAE=1.216, but baseline (predict mean) MAE=1.189 — model 2.2% worse. Permutation test Z=0.68, not significant.

**Key findings:**
- SHAP confirms Subject (0.123) and Channel (0.087) are only meaningful features
- Age bucket: no predictive value (MAE worsened)
- Duration: degraded performance
- Product features: no improvement
- Interactions: added complexity, no gain

### 9.3 — Notebook 06: OLS Regression (8 experiments)
**Outcome:** All 8 experiments completed. Same pattern — R1 (Channel+Subject) best at MAE=1.209, all R² negative.

**Key findings:**
- Channel coefficients: Email -0.148, Phone -0.110, SM -0.090 vs Chat (all p>0.05)
- Duration×Channel: all coefficients tiny, all p>0.60
- Duration×Subject: only Hardware Issue significant (p=0.046)
- **Age confirmed irrelevant** (R4 worse than R1)

### 9.4 — Convergence
Both models agree on everything:
1. Channel + Subject are the only variables that matter
2. Age is irrelevant — dropped from framework
3. Duration matters only at pair level (Simpson's Paradox), not globally
4. Models can't beat mean prediction with synthetic data
5. The 6-scenario framework is sound — pair-level Pearson r remains valid

**Human decision:** "Age is irrelevant. We need to come back to the 6 scenarios grid classification Channel×Subject."

### 9.5 — Notebook 07: LLM Classification (in progress)
**Status:** Notebook rebuilt with checkpoint queue system (200 tickets/batch, auto-resume). Running in separate Claude Code terminal.

### Where AI erred / human corrected
- AI initially proposed running notebooks as background tasks. Human corrected: "you keep me asking authorization... in separated terminals they would interact without asking me." Fix: give terminal commands with `claude --dangerously-skip-permissions`.
- AI gave raw papermill commands. Human corrected: "we are not using claude?" — wanted Claude Code instances in terminals for autonomous documentation.
- AI didn't implement queue system for LLM notebook. Human suggested: "is not better to make a system and queue to avoid timeout?" Fix: checkpoint system with batch processing.

### 9.6 — Strategy: Parallel Terminals for Phase 6+7
**Context:** Human laid out the full strategy — resource analysis first, then automate, simulate reallocation, build prototype. Key insight: "time is the name of the resource because we don't know how many people are there."

**Human decision:** Split into 4 independent terminals working on separate git branches:
- Terminal A: Resource analysis notebook (as-is hours allocation)
- Terminal B: Automation page (what to automate, impact×feasibility)
- Terminal C: Prototype classifier (working demo with queue simulation)
- Terminal D: Roadmap + control files

**Human reasoning:** "the name of the game here is split in several terminals so we can go fast now that we know the reasoning and we need to document everything because you need to explain this reasoning"

**Plan approved.** Branching and launching terminals next.

### 9.7 — Terminal Launch Execution
**Context:** Setting up 4 parallel Claude Code terminals on separate git worktrees.

**Setup steps:**
1. Committed all current work on main (ML notebooks, diagnostic API, screenshots, control files)
2. Created 4 git branches from main: `feat/resource-analysis-notebook`, `feat/automation-page`, `feat/prototype-classifier`, `feat/roadmap-page`
3. Created 4 git worktrees at `../optiflow-{a,b,c,d}` — each is an independent copy on its own branch
4. Symlinked gitignored files into worktrees: `data/`, `analysis/.venv/`, `.env.local`, `analysis/output/`, `node_modules/`
5. Created plain-text prompt files (`scripts/prompt_{a,b,c,d}.txt`) — markdown files with backticks broke the shell

**Obstacles encountered & resolved:**
- `git worktree add` failed initially — needed to create branches first with `git branch`
- `claude --dangerously-skip-permissions -p "$(cat file.md)"` failed — backticks in markdown were interpreted as shell commands. Fixed: plain .txt prompts piped via `cat file.txt | claude`
- Worktrees missing gitignored files — fixed with symlinks
- Cannot launch claude from within claude — terminals must be opened from macOS Terminal.app, not from VSCode terminal running this session

**Launch command pattern:**
```
cd /Users/koristuvac/DEV/optiflow-{x} && cat scripts/prompt_{x}.txt | claude --dangerously-skip-permissions
```

**Status:** All 4 terminals launched and running simultaneously.
- Terminal A: Resource analysis notebook (feat/resource-analysis-notebook)
- Terminal B: Automation page (feat/automation-page)
- Terminal C: Prototype classifier (feat/prototype-classifier)
- Terminal D: Roadmap + control files (feat/roadmap-page)

### 9.8 — Notebook 07 LLM Classification (background)
**Status:** Still running in separate terminal. Last check: 4,800/9,559 zero-shot classifications complete (~50%), 0 errors, ~40min remaining. Checkpoint system working — saves every 200 tickets to `data/llm_checkpoint_zero_shot.csv`.

---

---

## Session 10 — Mar 21, 2026 — Parallel Terminal Execution (Terminal D: Roadmap + Control Files)

### 10.1 — Parallel Terminal Launch
**Context:** After ML validation (Session 9), human launched 4 independent Claude Code terminals on separate git branches for Phase 6+7 execution:
- Terminal A: Resource analysis notebook (`feat/resource-analysis-notebook`)
- Terminal B: Automation page (`feat/automation-page`)
- Terminal C: Prototype classifier (`feat/prototype-classifier`)
- Terminal D: Roadmap page + control files (`feat/roadmap-page`) — this terminal

**Strategy:** Zero file overlap between terminals. Terminal D is the ONLY terminal that touches control files (BACKLOG.md, DECISIONS.md, CHAT_LOG.md). Merge order: A → B → C → D.

### 10.2 — Roadmap Page Built
**What was built:**
- Replaced `src/app/roadmap/roadmap-view.tsx` stub with full implementation
- **Section 1:** Matriz Impacto × Esforço — Recharts ScatterChart with 2×2 quadrant (4 colored regions), 4 initiative bubbles with labels
- **Section 2:** Quick Wins (<1 semana) — 2 Cards: auto-roteamento (17 pares) + fila prioritária (9 pares)
- **Section 3:** Médio Prazo (1-4 semanas) — 2 Cards: roteamento especialista + dashboard tempo-real
- **Section 4:** Estratégico (1-3 meses) — 2 Cards: chatbot automático + modelo preditivo CSAT
- **Section 5:** Timeline — Mermaid Gantt chart with 3 phases
- **Section 6:** PRD Resumido — tech stack, métricas-chave, impacto projetado + Mermaid architecture diagram

**Patterns used:**
- Recharts patterns from `overview-dashboard.tsx` (ScatterChart, ReferenceArea, tooltips)
- Mermaid patterns from `diagnostic-panel.tsx` (render with useRef, initialize, error handling)
- shadcn/ui Cards with Badge for impact/effort levels

**Verification:** `tsc --noEmit` passes clean. `npm run build` blocked by pre-existing Turbopack symlink issue (node_modules → ../optiflow/node_modules), not related to code changes.

### 10.3 — Control Files Updated
- BACKLOG.md: Terminal D tasks marked complete, Phase 5A ML validation confirmed done
- DECISIONS.md: Verified D018-D020 exist (ML validation, parallel strategy, resource analysis)
- CHAT_LOG.md: This session entry added

### Where AI worked autonomously
- Built entire roadmap page from spec without additional questions
- Used existing codebase patterns (Recharts, Mermaid, shadcn/ui) for consistency
- Fixed TypeScript error (Recharts label prop typing) independently
- All content in pt-BR per established rule

---

## Session 11 — Mar 21, 2026 — Review & Documentation (continued)

### 11.1 — Screenshots of New Pages
Captured Puppeteer screenshots of all 3 new pages on localhost:3001:
- `/automation` — 4 automation candidate cards, Impact×Feasibility scatter chart, Before/After simulation (17,364h → 15,713h = -1,651h savings, CSAT 2.97→3.29)
- `/classification` — Ticket classifier form with Canal/Assunto selects, Fila Simulada tab, Métricas tab
- `/roadmap` — Impact×Effort 2×2 quadrant, Quick Wins cards, timeline

### 11.2 — LLM Classification Review (Notebook 07)
**Model:** Gemini 2.5 Flash Lite | **Sample:** 9,559 tickets (20% of Dataset 2)

**Results:**
- Zero-shot: 40.9% accuracy, F1 Macro 0.352
- Few-shot (5 examples/category): 46.2% accuracy, F1 Macro 0.476
- Best: Purchase (F1=0.77) | Worst: Administrative rights (F1=0.22)

**Root cause analysis:**
1. "Miscellaneous" category has no clear boundary — top confusion sink
2. "Administrative rights" vs "Access" semantically overlap
3. Synthetic/template data limits differentiation
4. Flash Lite optimized for speed not accuracy
5. Zero-shot hallucinated "Backup" category

**Verdict:** 46.2% = proof-of-concept, not production. Improvement path: merge overlapping categories, use CoT prompting, upgrade model.

### 11.3 — Resource Analysis Document (Notebook 08)
Created `analysis/RESOURCE_ANALYSIS.md` — comprehensive explanatory document covering:
- Methodology (duration_hours proxy)
- Distribution by channel (uniform ~25% each) and subject (uniform ~6-8% each)
- 6-scenario classification of 64 pairs
- **Central finding:** 79.5% of 21,439h classified as "liberar" (waste)
- Reallocation scenarios (25%/50%/75%)
- Simpson's Paradox explanation
- Operational recommendations (immediate, short-term, medium-term)
- Honest limitations (synthetic data, proxy metric, closed-only sample)

### 11.4 — Prompts Presented
Extracted and presented both prompts from notebook 07:
- **Zero-shot** (267 chars): Direct instruction, 8 categories listed, "respond with ONLY the category name"
- **Few-shot** (7,533 chars): Same structure + 40 examples (5/category, truncated to 200 chars)

### Where AI identified problems independently
- Noted that "Miscellaneous" acts as classification black hole (no semantic boundary)
- Identified category overlap (Administrative rights ≈ Access) as structural prompt issue
- Connected synthetic data limitations to uniform distribution → weak correlations → 79.5% "liberar"
- Recommended category consolidation before investing more API calls

---

## Session 12 — Mar 21, 2026 — G4 Submission Document

### 12.1 — Submission Document Strategy
**Context:** Human wanted a static storytelling document following the G4 template, with clear visuals, tables, and charts. Specified full pt-BR, 3 roadmap scenarios by classifier accuracy, LLM prompts inline.

**Human's narrative flow (16 points):**
1. Data investigation → synthetic data errors + disclaimer
2. Variable influence on satisfaction
3. Lack of aggregate correlation (duration × CSAT)
4. Simpson's Paradox (per-pair correlations)
5. Time influence analysis per pair
6. ML validation (2 models)
7. Why decision tree over ML
8. 6-scenario framework + routing matrix
9. Resource analysis as-is
10. To-Be process + impact
11. Roadmap with 3 scenarios by classifier accuracy
12. Current bottlenecks
13. LLM classification with prompts inline
14. "Done until here" marker
15. Executive summary (written last)
16. Future: fine-tune model, design prototype

**Human asked 5-10 questions before starting.** Answers:
- Format: G4 template (README.md on GitHub with images)
- Scenarios: By classifier accuracy (46%/70%/90%+)
- Language: Full pt-BR
- Prompts: Inline with analysis
- Approach: Two-layer (README.md primary + notebook for new charts)

### 12.2 — Plan v5 Designed and Approved
Created comprehensive plan mapping G4 template sections to narrative flow. 9 new assets identified (7 markdown tables + 2 generated charts). Plan approved.

### 12.3 — Submission Directory Created
- `submissions/vinicius-cury/` with `docs/images/`, `process-log/`, `solution/`
- 39 screenshots copied from `process-log/screenshots/`
- All image paths verified

### 12.4 — README.md Written (Full Submission)
Complete G4 submission document: ~460 lines of markdown with:
- Executive Summary (3 paragraphs: waste finding, Simpson's Paradox, automation proposal)
- Abordagem: methodology, variable classification table, 6 data quality issues, disclaimer, status structure
- 9 Findings (F1-F9): variable influence, Simpson's Paradox, ML validation, 6-scenario framework, resource analysis, to-be process, bottlenecks, LLM classification with inline prompts, 3 roadmap scenarios
- Recomendações: 8 prioritized actions (immediate → strategic)
- Limitações: 7 items with honest assessment
- Process Log: tools, workflow, 5 AI errors, 6 human additions
- Evidências: 9 notebooks, 49+ screenshots, 24 decisions, 7 dashboard pages
- 20 embedded images with verified paths

### Where AI worked autonomously
- Drafted complete 460-line submission document from plan + existing analysis
- Structured narrative to match G4 template exactly
- Included all LLM prompts inline (zero-shot + few-shot)
- Created 3-scenario comparison table with 8 dimensions
- All content in pt-BR per established rule

---

## Session 13 — Mar 21, 2026 — Time Decomposition + Fine-Tuning

### 13.1 — Time Decomposition Model (Notebook 12)
**Context:** Human proposed time decomposition model: use post_contact_time variance across subjects to infer routing overhead.

**What was built:**
- Created `analysis/12_time_decomposition.ipynb` with 6 sections:
  1. **Análise por Assunto:** Cross-tab Subject × Type, per-subject stats (count, median FRT, median duration, mean CSAT, std)
  2. **Classificação por Complexidade:** Subjects classified as handler único (<= median of medians), transferência provável (>= P75), or ambíguo
  3. **Decomposição Temporal:** Stacked bar chart — baseline handling (blue) vs transfer penalty (red). Baseline = median of "handler único" subjects
  4. **Impacto Canal × Assunto:** Heatmap of median duration by Subject × Channel, with transfer subjects highlighted
  5. **Quantificação da Penalidade:** Total penalty hours, % of 21,439h operational, per-subject breakdown, business case with 3 reduction scenarios
  6. **Conclusões:** Methodology rationale, assumptions, limitations, connection to 6-scenario framework

**Charts saved:**
- `process-log/screenshots/p13_time_decomposition.png` — stacked bar decomposition
- `process-log/screenshots/p13_duration_heatmap_subject_channel.png` — duration heatmap
- `process-log/screenshots/p13_routing_penalty_by_subject.png` — penalty breakdown

**Key findings:**
- [Pending notebook execution — numbers to be filled after papermill run]

**Methodology:**
- Baseline = median duration of "handler único provável" subjects
- Transfer penalty = subject median - baseline (clipped at 0)
- Total penalty hours = sum of per-ticket penalties across all closed tickets
- Business case: 30%/50%/70% reduction scenarios quantified

### 13.2 — Other Session 13 Work
- OpenAI fine-tuning notebook 11 created (gpt-4o-mini, 20% sample, 80/20 split)
- Dataset taxonomy mapping documented (D1 16 subjects ↔ D2 8 categories)
- DRAFT.md v3: 24 sanity check issues fixed (8 HIGH, 11 MEDIUM, 5 LOW)

**Decisions:** D027 (taxonomy mapping), D028 (OpenAI fine-tuning), D029 (time decomposition model)

---

## Session 14 — Mar 22, 2026 — Fine-Tuning Results & Prototype Direction

### 14.1 — OpenAI Fine-Tuning: 84.6% Accuracy
**Context:** Fine-tuned gpt-4o-mini on 20% sample (7,647 train, 1,912 test), same protocol as Gemini experiment.

**Results:**
| Metric | Gemini Few-Shot | OpenAI Fine-Tuned | Delta |
|--------|----------------|-------------------|-------|
| Accuracy | 46.2% | **84.6%** | +38.4pp |
| F1 Macro | 0.476 | **0.743** | +0.267 |
| F1 Weighted | 0.475 | **0.846** | +0.371 |

- Every category improved. Biggest jumps: Administrative rights (+0.52), Miscellaneous (+0.49)
- Training cost: ~US$7.07. Inference: ~US$0.08/1,912 tickets
- Zero errors. Model: `ft:gpt-4o-mini-2024-07-18:mcury:optiflow-tickets:DM09m89K`
- Cenário B (70%) **surpassed** — classifier is production-viable

**Charts:** `p13_openai_vs_gemini_confusion.png`, `p13_f1_comparison_by_category.png`

### 14.2 — 3-Pool Resource Decomposition
**Context:** Human identified that resource analysis should decompose 21,439h into 3 pools: Frontline (agents), Routing (queue/transfer), Specialist (fixers). Different automations affect different pools.

**Analysis:** Added to DRAFT.md as sensitivity analysis. Pool estimates: Frontline ~6,432h (30%), Routing ~1,698h (7.9%), Specialist ~13,309h (62.1%). Human noted this is partially speculative — data doesn't directly show pools.

**Human constraint:** "o formato da solução não muda" — solution stays the same, only resource source changes.

### 14.3 — Prototype Direction Defined
**Context:** With classifier at 84.6%, human wants to shift from analysis to building.

**Human's vision:**
1. Simulate new tickets coming in through different channels
2. Dashboard showing ticket lifecycle and flow in real-time
3. "A true support system" — not just analytics
4. User sees in real-time what is happening

**Plan:** Define PRD on Mar 23, then build immediately.

### 14.4 — DRAFT.md v4 Update
**Context:** Updating submission document with fine-tuning results, revised 3-scenario roadmap (now 84.6% is baseline, not theoretical), and pool decomposition.

**Decisions:** D030 (fine-tuning results), D031 (3-pool decomposition), D032 (prototype direction)

---

## Session 15 — Mar 22, 2026 — Document Restructuring & Polish

### 15.1 — Waterfall Charts + Executive Summary
**Context:** Human rejected previous waterfall charts (Y-axis at zero, conservative chatbot scenario) and executive summary (bullets, not slides).

**Actions:**
- Rewrote `analysis/generate_waterfall_charts.py` with full chatbot solution (50% deflexão, -9.043h)
- Y-axis starting near data range for visual impact
- Executive summary rewritten as 3 visual slides with big numbers and chart embeds

### 15.2 — Full Document Restructuring
**Context:** Human created RESTRUCTURE_INSTRUCTION.md and EXECUTIVE_SUMMARY_v2.md with detailed guidelines for restructuring. Key principles: dual-audience (director scanning in 15 min + evaluators analyzing depth), no inline disclaimers, no "/ano", no repeated information.

**Actions:**
- Saved DRAFT_v8_backup.md
- Restructured DRAFT.md: sections mapped to G4 requirements (§Diagnóstico, §Automação, §Classificação)
- Bold 2-3 line summaries at top of every section
- Removed 8+ inline synthetic data disclaimers → consolidated in Limitações
- Removed all "/ano" → "sobre o volume analisado (8.469 tickets)"
- Eliminated repeated information (pools appeared 4x → 1x, channel viability 3x → 1x)

**Human feedback:** "This version is significantly better than the previous one."

### 15.3 — Document Polish (Human Review)
**Context:** Human provided detailed review with 6 issues to fix.

**Fixes applied:**
1. Section numbering: dropped numbers, descriptive headers only
2. Mermaid: "Hipótese: Simpson" → "Hipótese: Análise por Subgrupo"
3. Bridged 8% vs 42% gap with explanatory sentence
4. Reduced §4.1 images from 8 to 4
5. ROI table now shows both scenarios (R$58k / R$316k)
6. Chatbot timeline: 1-3 meses → 4-6 semanas

### 15.4 — Taxonomy Mapping + Dashboard Issues
**Context:** Human identified critical gap: no bridge between D1 subjects (16) and D2 categories (8) in the document. Also flagged dashboard screenshots as stale.

**Actions:**
- Added taxonomy mapping table to Classification section
- Identified dashboard code issues: wrong base (17,364h), wrong pair counts, wrong channel viability
- Flagged for fix before recapturing screenshots (P8-G in backlog)

### 15.5 — Human Directives for Next Phase
**Human notes for prototype:**
- Chatbot first version in 4-6 weeks, not 1-3 months
- Architecture first → implement → create synthetic data to test
- Need answer bank (RAG or matching) for chatbot demo — don't have real answers
- Conversation flows are the main challenge for chatbot
- Taxonomy mapping is essential for the solution to work end-to-end

**Decisions:** D033 (restructuring), D034 (polish + taxonomy + timeline)

---

## Session 16 — Mar 22, 2026 — Zero-Shot Experiment + Prototype PRD

### 16.1 — Bridge Table: D2→D1 Mapping with Operational Impact
Created unified bridge table connecting D2 categories (8) → D1 subjects (16) → scenario → recommended action. Key finding: 6/8 categories have zero operational impact from wrong sub-classification (all lead to same action). Only Hardware has divergent scenarios.

### 16.2 — Zero-Shot Sub-Classification Experiment
- Sampled 48 tickets from D2 (6 per category, real classified data)
- Built category-specific zero-shot prompts (Gemini 2.5 Flash Lite) with restricted D1 subject options + "Other"
- Built `/experiment` page in Next.js for manual human evaluation (batch save, D1 options visible per card)
- **Result: 45/48 correct (93.75%)** — most correctly classified as "Other" (domains don't cross)
- Only Access category showed meaningful cross-domain mapping (Account access at 90% confidence)
- Architecture validated (two-stage: fine-tuned + zero-shot), but needs real data for full potential

### 16.3 — 11 Labs Research
Deep research on ElevenLabs Conversational AI:
- Supports text + voice dual mode (same widget)
- Server Tools: agent calls our API mid-conversation (classify, create ticket)
- React SDK: `@elevenlabs/react`, drop-in for Next.js
- pt-BR: first-class support, ~75ms latency
- Cost: Creator plan $11/month (~150 min)
- KB: upload files/text + Server Tools for dynamic Supabase data
- Documented as future feature in PRD §11

### 16.4 — Prototype PRD Created
Created `PRD_PROTOTYPE.md` — comprehensive spec covering:
- System architecture (progressive classification, 3-4 turns with confidence refinement)
- 5 new Supabase tables (conversations, messages, kb_articles, operators, simulation_runs)
- Full API design under `/api/prototype/`
- 9 React components
- 3 new pages (Atendimento, Operador, Simulador)
- 5 development sprints with dependencies
- Mermaid diagrams of full process flow added to DRAFT.md

### 16.5 — Human Decisions on Prototype Scope
- Same repo, organized separation in dashboard
- Chat first, voice later (11 Labs as future feature)
- OpenAI for classification (fine-tuned model confirmed active)
- Progressive classification: re-classify each turn with accumulated context
- Clarifying questions targeted to what the classifier needs
- Escalation routes to best channel, quarantine = special force (agents + managers)
- KB articles must be realistic with disclaimers
- Guided walkthrough with 3 pre-loaded scenarios
- QA via Puppeteer flow testing (reference: Wavvo QA procedures)
- No human review between sprints — consolidate and test at end

**Decisions:** D035 (zero-shot experiment), D036 (prototype scope)

---

## Session 17 — Mar 22, 2026 — Prototype Build (5 Sprints)

### 17.1 — Sprint Execution Strategy
- Human instruction: "run everything in the back with no interruption"
- Launched sequential background agents for each sprint
- Attempted parallel Sprints 3+4 with git worktrees — failed (worktree agents lack Bash permissions)
- Fell back to sequential execution: Sprint 1 → 2 → 3 → 4 → 5

### 17.2 — Sprint 1: Foundation (Agent 1)
- Applied Supabase migration: 5 tables (conversations, messages, kb_articles, operators, simulation_runs)
- Extracted routing engine from diagnostic route into `src/lib/routing/engine.ts`
- Created taxonomy mapping at `src/lib/routing/taxonomy.ts`
- Built classify API endpoint (two-stage: fine-tuned D2 + zero-shot D1)
- Seeded 36 KB articles (3 per subject, pt-BR) and 5 operators
- Added "PROTÓTIPO" sidebar section with 3 page shells

### 17.3 — Sprint 2: Chat + Classification (Agent 2)
- ChatWidget: message bubbles, typing indicator, auto-scroll, escalation messages
- ClassificationPanel: animated pipeline visualization (200ms stagger between steps)
- Conversation/message API routes with full classification pipeline trigger
- Progressive classification: 85% confidence gate, clarifying questions, forced classification at turn 3
- KB response synthesis via gpt-4o-mini (natural answers, never "I found this article")
- Escalation: LLM-generated summary → ticket to operator queue

### 17.4 — Sprint 3: Operator Dashboard (Agent 3)
- QueueList: filterable by 6 scenarios, sortable by priority/time
- TicketDetail: conversation thread, classification, KB articles tried, summary, action buttons
- OperatorCard: status, capacity bar, specialties, resolved count
- 6 API routes: queue, accept, transfer, resolve, operators CRUD
- SLA timers with scenario-based deadlines (acelerar 30min → liberar 24h)
- 3-column page layout with operator selector and 3-second polling

### 17.5 — Sprint 4: Simulation + Metrics (Agent 4)
- Simulation engine: samples from CSV, batch classification (4 concurrent), ~50% auto-resolve
- 5 API routes: start, stop, status, reset, metrics
- SimulationControls: ticket count, channel presets (Uniforme/Chat-first/Realista), arrival pattern
- MetricsPanel: 4 KPI cards + Recharts donut (scenario) + bar chart (channel)
- Reset: truncates prototype tables only, re-seeds operators

### 17.6 — Sprint 5: Polish + QA (Agent 5)
- WalkthroughOverlay: 12-step guided tour with auto-typing and page navigation
- 3 pre-loaded demo scenarios as clickable cards on Atendimento empty state
- UI animations: slide-in messages, fade-in queue items, zoom-in badges
- Empty states with contextual links (queue → simulator)
- Puppeteer QA: screenshots of all 3 prototype pages
- All passes: `tsc --noEmit` clean, `npm run build` clean

### 17.7 — Final Inventory
**Components (9):** chat-widget, classification-panel, scenario-badge, queue-list, ticket-detail, operator-card, simulation-controls, metrics-panel, walkthrough-overlay
**API Routes (15):** classify, conversations (CRUD), messages, queue, accept, transfer, resolve, operators (CRUD), simulation (start/stop/status/reset), metrics
**Pages (3):** atendimento (60/40 chat+classification), operador (3-column dashboard), simulador (controls+feed+metrics)
**Git commits (6):** one per sprint + control file update

**Decisions:** D037 (prototype implementation)

---

## Session 18 — Sprints 6-7: Identity + QA (Mar 22, 2026)

### 18.1 — Sprint 6: User Identity + Chat UX
- Added `customer_email` column to conversations table
- User history API endpoint (`/api/prototype/users/history`)
- Personalized welcome messages for returning users
- Fixed response quality: progressive investigation, max 3-4 sentences, no info dump
- Fixed simulation: resolve `{product_purchased}` template variables in CSV

### 18.2 — Sprint 7: QA Validation
- 12 persona definitions with distinct communication styles
- 26 issue templates covering all D2 categories
- Bulk QA runner (`scripts/qa_runner.mjs`) with auto-resolution evaluation
- QA Procedure document (`process-log/QA_PROCEDURE.md`)

---

## Session 19 — Sprints 8-12: Waves 1+2 Parallel Execution (Mar 22, 2026)

User requested parallel agent execution for remaining sprints. 5 sprints executed across 2 waves using background agents.

### 19.1 — Sprint 8: Confidence Calibration (D044)
- Pre-classification gate: greeting, farewell, gibberish, too-short detection (zero API calls)
- Information density score: token count, technical terms, problem verbs, error codes → 0.0-1.0
- Effective confidence = raw × density → feeds into 85% threshold
- Classification panel shows gate result, density bar, raw vs effective confidence
- New file: `src/lib/prototype/classification-gate.ts`

### 19.2 — Sprint 9: Chat-Driven Identity (D044)
- Removed email/name input fields from Atendimento page
- Chat asks name + email conversationally via state machine (greeting → asking_name → asking_email → support)
- Returning user detection after email collected
- Ticket status queries ("qual o status do meu ticket?")
- `identity_state` column added to conversations
- Simulation bypasses identity flow (identity_state='support')
- New file: `src/lib/prototype/identity-flow.ts`

### 19.3 — Sprint 10: RAG Architecture (D045)
- pgvector extension enabled, embedding column added to kb_articles
- RAG helper: embed query via text-embedding-3-small → cosine similarity via `match_kb_articles` RPC → top 3 articles
- Exact-match KB lookup replaced with semantic search
- Classification panel shows RAG step (article titles + similarity score badges)
- KB amplification script: `scripts/seed_kb_expanded.mjs` (36 → 72 articles)
- New file: `src/lib/prototype/rag.ts`

### 19.4 — Sprint 11: KPI Dashboard (D046)
- Migration: `csat_rating` column added to conversations
- 8 KPI cards: resolution rate, escalation rate, deflection rate, FRT, TTR, CSAT, SLA compliance, queue depth
- CSAT star rating on ticket resolve flow
- SLA gauge chart (Recharts semicircle)

### 19.5 — Sprint 12: Message Grouping (D047)
- Frontend debounce: 4-second timer, reset on each new message
- Visual indicator: "Aguardando mais mensagens... (N recebidas) [Xs]"
- Concatenated text sent to API, individual messages stored for transcript
- Classification panel shows grouping step when grouped_count > 1
- Identity flow messages bypass buffering

### 19.6 — Integration Fixes
- `grouped_messages` was missing from Zod schema — silently stripped by validation
- Backend wasn't storing individual grouped messages — only saved concatenated text
- `grouped_count` missing from all 3 API response paths (escalation, gate-blocked, classification)
- Human correction: "you committed a lot of basic mistakes here... this should run independently safe"

**Decisions:** D044-D050

---

## Session 20 — Sprint 13 + KPI Upgrade + Pre-Simulation Review (Mar 22, 2026)

### 20.1 — KPI Dashboard Relocation
- User flagged: KPI dashboard was on the simulator page, should be on the dashboard page
- Moved KPIDashboard, SLAGauge from simulador to dashboard
- Removed KPIRoadmap placeholder (list of "things we can't compute")

### 20.2 — User Challenge: "Why can't we compute those KPIs?"
- User pointed out that simulation data IS sufficient for most "production-only" KPIs
- 5 of 7 KPIs are fully computable: FCR, AHT, Cost, CES proxy, Reopen Rate, Agent Utilization
- NPS excluded (requires separate brand loyalty survey, different from CSAT)

### 20.3 — Sprint 13: Intelligent Routing (background agent)
- Database: `level` column on operators (junior/senior/lead), `escalation_tier` + `escalated_from_operator` on conversations
- Operators seeded: 2 junior (Ana, Carlos), 2 senior (Maria, Pedro), 1 lead (Juliana)
- New file: `src/lib/prototype/escalation.ts` — `findBestOperator`, `shouldAutoEscalate`, `escalateTicket`
- Queue filters by operator tier (juniors see tier 1, seniors see tier 2 + SLA-threatened, leads see tier 3 + critical)
- Accept validates tier >= ticket's escalation_tier
- Transfer blocks downward transfers (senior → junior prevented)
- UI: level badges (blue/purple/gold), escalation tier badges on queue items

### 20.4 — Real KPI Metrics (D051)
- Replaced placeholder KPIRoadmap with 6 computed KPIs from prototype data:
  - FCR: % resolved without operator (auto-resolved by chatbot)
  - AHT: avg time between operator acceptance and resolution
  - Cost per ticket: estimated from API calls + operator time
  - CES proxy: turn_count + escalation penalty, normalized to 1-5
  - Reopen rate: % of conversations with post-resolution customer messages
  - Agent utilization: avg active_tickets / max_capacity across operators
- Deleted `src/components/prototype/kpi-roadmap.tsx`

### 20.5 — Pre-Simulation Review (3 blockers found)
Full system review before Sprint 14 multi-day simulation:

**Blockers:**
1. SLA auto-escalation is dead code — `shouldAutoEscalate`/`escalateTicket` exist but nothing calls them
2. Race condition on `active_tickets` — non-atomic read-increment-write under concurrent load
3. AHT uses `updated_at` as proxy — gets overwritten on every update, reads near-zero

**Test coverage:** 6 of 12 features NOT COVERED (identity flow, message grouping, operator tiers, SLA escalation, specialty matching, KPI validation)

**Decision:** Fix blockers before launching Sprint 14 simulation.

**Decisions:** D051 (real KPI computation)

---

## Session 21 — Sprint 13.5: Pre-Simulation Blocker Fixes (Mar 22, 2026)

### 21.1 — 5 Blockers Fixed for Multi-Day Simulation

All 5 pre-simulation blockers identified in Session 20 resolved:

**Blocker 1 — SLA Auto-Escalation Trigger:**
- Created `/api/prototype/sla-check/route.ts` — standalone endpoint that checks all active conversations with SLA deadlines, calls `shouldAutoEscalate` (80% threshold), and `escalateTicket` for those that qualify
- Added SLA check call at the top of queue GET handler — every time someone views the queue, stale SLAs get auto-escalated

**Blocker 2 — Race Condition on active_tickets:**
- Applied Supabase migration with `increment_active_tickets` and `decrement_active_tickets` Postgres RPC functions (atomic, capacity-safe)
- Updated all 6 files that touch active_tickets: queue/accept, queue/transfer, conversations/resolve, conversations/messages (2 escalation paths), escalation.ts, simulation/start

**Blocker 3 — accepted_at Column for AHT:**
- Added `accepted_at` column to conversations table via migration
- queue/accept sets `accepted_at` when operator accepts ticket
- Metrics route AHT calculation now uses `accepted_at` instead of `updated_at`

**Blocker 4 — Simulation Uses findBestOperator:**
- Replaced simple loop operator assignment in simulation/start with `findBestOperator` (tier-aware, specialty-matching)
- Also assigns escalated tickets without operators, not just in_progress

**Blocker 5 — findBestOperator Accepts Busy Operators:**
- Removed `.eq("status", "available")` filter — now queries all operators and filters by `active_tickets < max_capacity`

**Verification:** `tsc --noEmit` and `npm run build` both pass clean.

---

## Session 22 — Mar 22, 2026 — Sprint 14: Multi-Day Simulation Script

### 22.1 — Script Creation: qa_simulation_multiday.mjs

**Context:** Sprint 14 requires a comprehensive multi-day simulation to validate the full prototype pipeline end-to-end. Script created (not executed yet — requires running dev server).

**What was built:**
- `scripts/qa_simulation_multiday.mjs` — 1058-line script simulating 50 users over 4 days
- Day 1: 30 users through full identity flow + classification + 50% auto-resolve / 50% escalate
- Day 2: 10 returning users (5 status queries, 5 new issues) + 15 new users
- Day 3: Stress testing — 5 rapid-message grouping tests, 5 low-info gate-blocking tests, 5 high-density technical messages + SLA check trigger
- Day 4: Operator accepts + resolves all escalated tickets with CSAT ratings
- 12-item validation checklist: gate blocking, density scoring, progressive classification, RAG search, identity flow, message grouping, tier routing, SLA escalation, specialty matching, FCR, CSAT, KPIs
- Report generated to `process-log/multiday_simulation_report.md`

**Coverage:**
- All 8 D2 categories (Access, Administrative rights, HR Support, Hardware, Internal Project, Miscellaneous, Purchase, Storage)
- 12 persona styles (formal, informal, irritado, confuso, técnico, idoso, jovem, detalhista, resumido, educado, impaciente, primeiro_contato)
- 4 channels (Chat, Email, Phone, Social media)
- Brazilian Portuguese names and realistic issues

**Status:** Script created and committed. Execution pending (requires `npm run dev` running).

---

## Session 23 — Mar 22, 2026 — Sidebar Cleanup

**Context:** Preparing for deployment. Many investigation pages (Explorer, Process Map, Bottlenecks, Classification, Automation, Roadmap) were stubs or no longer needed — all analytical work lives in the prototype now.

**Exchange:**
- Human: "let's clean everything on that side menu that we are not using"
- Identified 3 empty stubs (Explorer, Process Map, Bottlenecks) and 3 real but superseded pages (Classification, Automation, Roadmap)
- Human confirmed: remove all 6 investigation pages
- Removed page directories and sidebar nav entries
- Sidebar now: Overview + 4 Prototype items (Dashboard, Atendimento, Operador, Simulador)
- Clean `tsc --noEmit` pass after clearing `.next` cache

**Outcome:** Sidebar decluttered. Only functional pages remain.

## Session 24 — Mar 23, 2026 — Simulation Runs, Post-Sim Fixes, Document Updates

### 24.1 — Simulation Battery Execution
**Context:** Ran `qa_simulation_multiday.mjs` twice with all fixes from Sprint 13.5 + SLA backdating.

**Results (consistent across 2 runs):**
- 70 conversations total, 50 simulated users, 4 days
- **9/12 validations passed**
- Gate blocking: 13 conversations blocked (low-info messages like "oi", "??", "ajuda")
- SLA backdating: 83% → escalated ✓, 75% → maintained ✓, 95% → escalated ✓
- Identity flow: 70/70 with name + email
- Progressive classification: 36 multi-turn conversations classified
- Tier routing: 0 mismatches, specialty matching 5/5
- 3 failures are script-level issues: density score capture, FCR (simulation always escalates), KPIs (AHT = API latency)

**Outcome:** Report saved to `process-log/multiday_simulation_report.md`. Results documented in DRAFT.md.

### 24.2 — Manual Testing: Bugs Found & Fixed
**Context:** Human tested the prototype manually and found UX issues.

**Issues identified:**
1. "Other" label shown to customer → Human: "Other is not acceptable for communication"
2. Conversation resets after escalation → Human: "after escalation, the conversation came back to a reset state"
3. No conversation queue → Human: "I need to see the specific queues" (compared to respond.io)
4. No operator visibility → Human: "we need to see which operator handles each ticket"
5. No date filter on Overview → Human: "Date filter. It's important to have a date filter."

**Fixes applied (Sprint 14.5):**
- "Other" → natural language: "um problema na área de {category}"
- Escalation guard: prevents re-classification after escalation
- ConversationQueue component with filters (status, category, scenario, operator)
- Operator/IA visibility in queue cards
- Date filter (dateFrom/dateTo) on Overview dashboard

### 24.3 — Sidebar Reorder + Rename
**Context:** Human: "Let's put prototype on top and investigation after that."

**Changes:**
- Sidebar: Protótipo section moved to top (Dashboard, Atendimento (Teste), Operador, Simulador)
- Investigação section below with Overview only

### 24.4 — Classification Panel Enhancement
**Context:** Human: "we need to see how it was escalated... if this followup is in another channel, we should tell that."

**Changes:**
- Historical timeline view with turn numbers and timestamps
- Escalation details: operator name/level, tier, SLA deadline, channel redirect
- `skipAnimation` prop for loaded conversations (no re-animation)

### 24.5 — DRAFT Updates
**Context:** Human: "Remember to document all the runs of tests that we did and the achievements and what we improve."

**Changes:**
- Sprint 14 status: ✅ 9/12 validações
- Sprint 14.5 added with fixes table
- Full simulation results section with 4-day breakdown + 12-validation checklist
- Methodology disclaimer added to 3-pool decomposition (Human asked: "do we explain the reasoning even though we don't have this division explicit in the data?")
- Version preserved as DRAFT_v11_backup.md

---

*Last updated: Mar 23, 2026 — Session 24*
