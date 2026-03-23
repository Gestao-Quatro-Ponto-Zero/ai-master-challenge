# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What Is This Project?

**G4 AI Master Challenge — Challenge 002: Redesign de Suporte**

A business process optimizer that analyzes customer support operations, maps processes, identifies bottlenecks, classifies tickets with LLM, and proposes AI-powered automation — all through an interactive dashboard.

The project serves dual purpose:
1. **Deliverable for G4:** Diagnostic report + automation proposal + working prototype
2. **Reusable tool:** A "Business Optimizer Consultant" that can be applied to any operations dataset

---

## Tech Stack

- **Framework:** Next.js 14+ (App Router, TypeScript, Tailwind CSS)
- **UI:** shadcn/ui components
- **Database:** Supabase (Postgres + Storage + RLS) — local-first development
- **Charts:** Recharts + Mermaid (process diagrams)
- **Analytics:** PostHog (server + client events)
- **Validation:** Zod schemas for all inputs
- **Hosting:** Vercel
- **AI Classification:** Claude API (Sonnet for complex classification, Haiku for simple edits) + Gemini (text classification benchmark)
- **Data Processing:** Python scripts for initial EDA, then API routes for live queries

---

## Commands Quick Reference

```bash
# Development
npm run dev                    # Start Next.js dev server (localhost:3000)
supabase start                 # Start local Supabase (requires Docker)

# Type generation (run after any DB schema change)
supabase gen types typescript --local > src/types/supabase.ts

# Build & check
npm run build                  # Production build
npx tsc --noEmit               # Type check without emitting
npm run lint                   # ESLint

# Database
supabase db push               # Push migrations to production
supabase db reset              # Reset local DB to clean state
supabase migration new NAME    # Create new migration file

# Data loading
npm run seed                   # Load CSV datasets into Supabase
npm run classify               # Run LLM classification on tickets

# Deployment
vercel deploy --prod           # Deploy to Vercel production

# Analysis Notebooks (Claude Code executes these — human does NOT code in them)
./analysis/run.sh 01_data_exploration                # Run notebook headlessly
analysis/.venv/bin/python3 -m papermill analysis/01_data_exploration.ipynb analysis/output/01_output.ipynb --kernel optiflow --log-output
```

---

## Project Structure

```
g4-challenge/
├── CLAUDE.md                  # This file — agent instructions
├── PRD.md                     # Product spec, architecture, data model
├── BACKLOG.md                 # Task tracking, sprint progress
├── DECISIONS.md               # Technical decision log
├── CHAT_LOG.md                # Conversation log (process evidence for G4)
├── process-log/               # Screenshots, exports, evidence for G4 submission
│   ├── screenshots/
│   ├── chat-exports/
│   └── decisions/
├── data/                      # Raw CSV datasets (gitignored)
│   ├── customer_support_tickets.csv    # Dataset 1: ~30K tickets
│   └── it_service_tickets.csv          # Dataset 2: ~48K IT tickets
├── analysis/                  # EDA notebooks and scripts
│   └── eda.py                 # Initial data exploration
├── src/
│   ├── app/
│   │   ├── page.tsx           # Dashboard home — KPI cards + nav
│   │   ├── explorer/          # Data explorer — tables with filters
│   │   ├── process/           # As-is process map (Mermaid/BPMN)
│   │   ├── bottlenecks/       # Time/cost analysis
│   │   ├── classification/    # LLM ticket classification results
│   │   ├── automation/        # To-be process + automation proposal
│   │   └── roadmap/           # Implementation roadmap
│   ├── components/
│   │   ├── ui/                # shadcn/ui
│   │   ├── charts/            # Recharts wrappers
│   │   ├── process/           # Mermaid diagram components
│   │   └── filters/           # Reusable filter components
│   ├── lib/
│   │   ├── supabase/          # client.ts, server.ts, admin.ts
│   │   ├── classification/    # LLM classification logic
│   │   ├── analysis/          # Data analysis helpers
│   │   └── utils.ts
│   └── types/
│       ├── index.ts           # Shared types
│       └── supabase.ts        # Generated DB types
├── supabase/
│   └── migrations/            # SQL migration files
└── submissions/               # Final G4 submission package
    └── README.md              # Follows G4 template
```

---

## Consultant Workflow (Phase-Based)

This project follows a structured consulting methodology. Each phase has clear deliverables and validation gates.

### Phase 1: Data Intake & Exploration
- Load both datasets into Supabase
- Build data explorer dashboard (tables + filters)
- Initial EDA: distributions, nulls, outliers, data quality
- **Gate:** Human validates data understanding before proceeding

### Phase 2: As-Is Process Mapping
- Infer current support process from data patterns
- Build Mermaid/BPMN process diagram
- Identify decision points, handoffs, channels
- Plot on dashboard
- **Gate:** Human validates process map accuracy

### Phase 3: Problem Identification
- Categorize problems into 4 buckets:
  - Manual work (high time, low automation)
  - Lack of standard process (high variance in handling)
  - Lack of guided system (no decision support)
  - Lack of system integration (disconnected channels/tools)
- Cross-reference with data evidence
- **Gate:** Human validates problem categories

### Phase 4: Bottleneck Analysis
- Quantify time and cost per bottleneck
- Cross datasets to find patterns
- Rank by impact (time × frequency × cost)
- **Gate:** Human validates bottleneck ranking

### Phase 5: LLM Classification
- Design classification taxonomy
- Test with sample tickets (clustering first)
- Benchmark models (Claude Sonnet vs Haiku vs Gemini)
- Run full classification on datasets
- Validate accuracy with human review
- **Gate:** Human validates classification quality

### Phase 6: To-Be Process Design
- Design automated process with AI intervention points
- Define what to automate vs what stays human
- Estimate impact (time/cost reduction per improvement)
- **Gate:** Human validates automation proposal

### Phase 7: Roadmap & PRD
- Build implementation roadmap (impact × effort matrix)
- Quick wins first, then strategic improvements
- Generate PRD for the software solution
- **Gate:** Human validates roadmap priorities

---

## Architecture Rules

### Data Handling
- Raw CSVs stored in `/data/` (gitignored)
- All data loaded into Supabase tables for querying
- API routes serve data to frontend — no direct CSV reading in components
- All queries support filtering by: channel, priority, type, status, date range

### Dashboard Pages
- Each page is a phase deliverable (explorer, process, bottlenecks, etc.)
- Pages use client-side data fetching (SPA pattern, same as Wavvo)
- Filters are persistent across pages via URL params
- Charts are interactive (click to drill down)

### LLM Classification
- Classification runs server-side via API routes
- Results stored in Supabase (not recomputed on every page load)
- Each classification stores: input text, model used, category, confidence, reasoning
- Support batch processing with progress tracking

### Process Diagrams
- Mermaid.js for process flows (rendered client-side)
- BPMN-style notation: tasks, gateways, events, swim lanes
- Diagrams are data-driven (generated from analysis, not hardcoded)

### Analysis Notebooks (Side Helper)
- Notebooks in `analysis/` are Claude Code's analysis scratchpad
- Human gives instructions in natural language → Claude Code writes cells, executes, reports back
- Claude Code creates and executes notebooks headlessly via papermill — no manual Jupyter server needed
- Results that matter get saved to Supabase via `analysis/lib/db.py` → the dashboard app displays them
- Notebooks themselves are reasoning logs — they show the analytical process for G4 evidence
- Each notebook should have markdown cells explaining WHY each analysis was done, not just code
- When human asks "what's the X by Y?", the workflow is:
  1. Write the analysis cells in the appropriate notebook
  2. Execute with papermill
  3. Read the output
  4. Report findings to human in plain language
  5. If the finding is significant → save to process_findings table
- DO NOT put analysis logic in the Next.js app — the app only reads results from Supabase
- Notebooks can be re-run anytime — they should be idempotent
- Python venv at `analysis/.venv/` — use `analysis/.venv/bin/python3` for execution
- Direct Postgres connection (`psycopg2`) for complex SQL queries in notebooks

---

## G4 Submission Requirements

### Deliverables (Challenge 002)
1. **Diagnóstico operacional** — Where does the flow get stuck? What impacts satisfaction? How much time/cost is wasted?
2. **Proposta de automação com IA** — What to automate, what NOT to automate, practical flow description
3. **Protótipo funcional** — Working classifier, suggested responses, auto-router, or dashboard
4. **Process log** — Evidence of AI usage (MANDATORY — no log = disqualified)

### Process Log Protocol
- `CHAT_LOG.md` — Append every significant interaction (prompts, decisions, corrections)
- `process-log/screenshots/` — Capture key moments (dashboard states, classification results, errors found)
- `DECISIONS.md` — Every technical choice logged with context and rationale
- Git history — Meaningful commits showing evolution

### What Makes a Strong Submission (from G4)
- Candidate clearly understood the problem before executing
- AI was used strategically, not as "glorified Google"
- Output is actionable — someone could use it tomorrow
- Process log shows iteration and judgment, not single-prompt-to-submission
- Communication is clear — technical and non-technical audiences understand

### What Gets You Disqualified
- Output generic enough to be about any company
- Zero evidence of verification (AI said it, candidate believed it)
- Process log shows 1 prompt → 1 response → submission
- 40-page document where 5 would solve it

---

## Document Management

### Project Documents
| File | Purpose | Updated by |
|------|---------|------------|
| `CLAUDE.md` | Architecture rules, conventions, commands | Human + Claude Code when conventions change |
| `PRD.md` | Product spec, data model, architecture | Human + Claude Code on major changes |
| `BACKLOG.md` | Task tracking, sprint progress, blockers | Claude Code after every completed task |
| `DECISIONS.md` | Technical decision log | Claude Code when making architecture choices |
| `CHAT_LOG.md` | Conversation log for G4 process evidence | Claude Code after every significant exchange |

### Before Starting Work
1. Read `BACKLOG.md` — know what's done, what's next, what's blocked
2. Check `DECISIONS.md` — understand recent technical choices
3. Follow `CLAUDE.md` — architecture rules and conventions

### After Completing a Task
1. Update `BACKLOG.md` — check off completed tasks, note any blockers
2. If a technical decision was made → add entry to `DECISIONS.md`
3. Append significant interactions to `CHAT_LOG.md`
4. Commit code + doc updates together (same commit)

### Change Protocol
1. **DECISIONS.md** — log WHAT changed, WHY, and WHAT it replaces
2. **PRD.md** — modify affected section(s), bump version in changelog
3. **BACKLOG.md** — add new tasks, remove obsolete ones
4. **CLAUDE.md** — update ONLY if architecture rules changed
5. **Implement** the change in code
6. **Commit** all changes together

---

## Working Rules (from human corrections)

These rules come from direct corrections during work. They override defaults.

### Language
- **All written content must be in Brazilian Portuguese (pt-BR)** — notebooks, dashboard UI, chart titles/labels, analysis text, findings, markdown cells
- Code comments and variable names stay in English
- CLAUDE.md and control files (BACKLOG, DECISIONS, CHAT_LOG) stay in English (they're for Claude Code, not the submission audience)

### Pace & Process
- **Setup before execution** — don't rush into running things. Ensure dependencies, configs, and environment are ready before executing scripts or notebooks
- **Document before moving on** — after completing a phase or making a decision, update DECISIONS.md, BACKLOG.md, and CHAT_LOG.md before starting the next task
- **Screenshot evidence** — use Puppeteer MCP to capture key moments (notebook outputs, dashboard states, charts) and save to `process-log/screenshots/`

### Decision Documentation
- When the human corrects Claude's approach, log it explicitly in DECISIONS.md as a correction (not just as a new decision)
- Format: what Claude did wrong → what the human corrected → why → what changes going forward

### Git Conventions
- **Never** add `Co-Authored-By` lines to commits
- Commit messages should be concise and descriptive
- Use conventional commits format: `feat:`, `fix:`, `refactor:`, `docs:`, etc.

### Security
- **Never** display tokens, API keys, or secrets in chat output
- Always store secrets in `.env.local` (gitignored), never in tracked files
- When reading `.env.local`, do not echo contents

### Communication
- Before big tasks: ask 5-10 focused questions
- During execution: be autonomous, don't ask for every small decision
- After completion: update control files, report findings in plain language
- Reference existing project docs (CLAUDE.md, PRD.md) instead of re-asking questions that are already answered there

---

## Tools & Services

### Jupyter Notebooks
- Server: `analysis/.venv/bin/jupyter notebook` from `analysis/` directory
- Kernel: `optiflow` (registered, points to `analysis/.venv/`)
- Execute headlessly: `analysis/.venv/bin/python3 -m papermill <input.ipynb> <output.ipynb> --kernel optiflow --log-output`
- Start server for human review: `analysis/.venv/bin/jupyter notebook analysis/ --no-browser`

### Puppeteer MCP
- Configured for screenshots of notebooks and dashboard
- Save screenshots to `process-log/screenshots/` with descriptive names
- Naming convention: `{phase}_{description}_{date}.png` (e.g., `p1_categorical_distributions_20260320.png`)

### Supabase
- Project: `optiflow` (id: `mbyfatsvjlxltctrgrdt`, region: eu-west-1)
- URL: `https://mbyfatsvjlxltctrgrdt.supabase.co`
- MCP configured with access token for schema management
- Migration applied: `initial_schema` (support_tickets, it_tickets, classification_runs, process_findings)

---

## Changelog

## Prototype Development Rules

### Control Document
- `PRD_PROTOTYPE.md` is the control document for all prototype work
- Read it before starting any prototype sprint — it has specs, data model, API design, component inventory

### Code Organization
- All prototype pages under `src/app/prototype/` (atendimento, operador, simulador)
- All prototype API routes under `src/app/api/prototype/`
- All prototype components under `src/components/prototype/`
- Shared routing engine at `src/lib/routing/engine.ts`
- Prototype tables are SEPARATE from analysis tables — never mix them

### Branch Strategy
- Each sprint gets its own branch: `feat/proto-foundation`, `feat/proto-chat`, etc.
- Merge to main after each sprint passes `npx tsc --noEmit` + `npm run build`
- Sprints 3 and 4 can run in parallel (separate branches)

### Classification Pipeline
- Stage 1: OpenAI fine-tuned model (env: `OPENAI_API_KEY`, `OPENAI_FINETUNE_MODEL_ID`)
- Stage 2: Zero-shot sub-classification with restricted options per category + "Other"
- Progressive: re-classify each turn with accumulated conversation context
- Confidence threshold: ≥85% → auto-route, <85% → ask clarifying question
- After 3 turns below threshold → force best option with low-confidence flag

### KB Articles
- Must be realistic (not template garbage)
- Disclaimer in conversation: never claim it WILL work for the customer
- Guide the customer, ask if it helped, escalate if not
- Some tickets go directly to senior support (quarantine scenario)

### QA Procedure (Sprint 5)
- Phase A: `tsc --noEmit`, `npm run lint`, `npm run build`
- Phase B: Code review (all prototype files)
- Phase C: Puppeteer visual QA (3 scenarios end-to-end)
- Phase D: Report with severity levels

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | Mar 20, 2026 | Initial CLAUDE.md — G4 Challenge 002 Business Optimizer |
| v1.1 | Mar 20, 2026 | Added: Working Rules (language, pace, corrections), Tools & Services (Jupyter, Puppeteer, Supabase) |
| v1.2 | Mar 22, 2026 | Added: Prototype Development Rules (code organization, branch strategy, classification pipeline, QA) |
