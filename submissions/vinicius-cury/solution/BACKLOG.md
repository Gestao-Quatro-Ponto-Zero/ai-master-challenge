# BACKLOG.md — OptiFlow (G4 Challenge 002)

> Task tracking for Claude Code. Read this before starting work. Update after every completed task.

---

## ACTIVE: Phase 9 — Prototype: Sistema de Suporte Inteligente

**Goal:** Build a working prototype demonstrating the full support pipeline: chatbot → progressive classification → scenario routing → operator dashboard → simulation.

**Control document:** `PRD_PROTOTYPE.md` — all specs, data model, API design, component inventory.

**Branch strategy:** Sequential sprints on separate branches, merge to main after each sprint passes.

### Sprint 1 — Foundation (`feat/proto-foundation`) ✓
- [x] Supabase migration: 5 new tables (conversations, messages, kb_articles, operators, simulation_runs)
- [x] Extract routing engine into `src/lib/routing/engine.ts` (from diagnostic route)
- [x] Create `/api/prototype/classify` endpoint (OpenAI fine-tuned → taxonomy map → routing matrix → KB lookup)
- [x] Generate and seed KB articles (36 articles across 12 subjects, pt-BR)
- [x] Seed simulated operators (5 with specialties)
- [x] Add "Protótipo" section to sidebar (3 items: Atendimento, Operador, Simulador)
- [x] Taxonomy mapping at `src/lib/routing/taxonomy.ts` (D2→D1, scenario labels/colors)

### Sprint 2 — Chat + Classification (`feat/proto-chat`) ✓
- [x] ChatWidget component (message bubbles, typing indicator, auto-scroll, escalation messages)
- [x] ClassificationPanel component (animated pipeline steps with 200ms stagger)
- [x] ScenarioBadge component (color-coded by scenario)
- [x] Conversation/message API routes (CRUD + message triggers classification pipeline)
- [x] Progressive classification (re-classify each turn, 85% confidence gate)
- [x] Clarifying question generation via gpt-4o-mini
- [x] KB response synthesis (natural language, never "I found this article")
- [x] Escalation logic: 3-4 turns → LLM summary → ticket to operator queue
- [x] Atendimento page: 60/40 split layout with channel selector

### Sprint 3 — Operator Dashboard (`feat/proto-operator`) ✓
- [x] QueueList component (filterable by scenario, sortable by priority/SLA)
- [x] TicketDetail component (conversation thread + classification + KB tried + summary)
- [x] OperatorCard component (status, capacity bar, specialties, resolved count)
- [x] Operator/queue API routes (queue, accept, transfer, resolve, operators CRUD)
- [x] SLA timers (ticking live, color-coded: green/yellow/red/flashing)
- [x] SLA deadlines by scenario (acelerar 30min → liberar 24h)
- [x] Accept/transfer/resolve ticket actions with operator validation
- [x] Operador page: 3-column layout with operator selector, 3s polling

### Sprint 4 — Simulation + Metrics (`feat/proto-simulator`) ✓
- [x] SimulationControls component (ticket count, channel presets, arrival pattern)
- [x] MetricsPanel component (4 KPI cards + Recharts donut/bar charts)
- [x] Simulation API routes (start/stop/status/reset)
- [x] Ticket generation engine (CSV sampling, batch classification, ~50% auto-resolve)
- [x] Reset functionality (truncate prototype tables, re-seed operators, confirm dialog)
- [x] Metrics API (queue depth, resolution rate, scenario/channel distribution)
- [x] Simulador page: controls top, live feed middle, metrics bottom, 3s polling

### Sprint 5 — Polish + QA (`feat/proto-polish`) ✓
- [x] WalkthroughOverlay component (12-step guided tour with auto-typing, auto-navigation)
- [x] 3 pre-loaded scenarios (Hardware→Acelerar, Cancelamento→Redirecionar, Dados→Quarentena)
- [x] UI polish: animations (slide-in, fade-in, zoom), empty states, error handling
- [x] Puppeteer screenshots of all 3 prototype pages
- [x] Final build verification (`tsc --noEmit` + `npm run build` pass)

### Sprint 6 — User Identity + Chat UX (`feat/proto-identity`) ✓
- [x] Add `customer_email` column to conversations table (migration applied)
- [x] User history API endpoint (`/api/prototype/users/history`)
- [x] Conversation creation accepts email, detects returning users
- [x] Personalized welcome messages for returning users
- [x] Fix response quality: progressive investigation, max 3-4 sentences, no info dump
- [x] Fix simulation: resolve `{product_purchased}` template variables in CSV

### Sprint 7 — QA Validation (`feat/proto-qa`) ✓
- [x] 12 persona definitions with distinct communication styles
- [x] 26 issue templates covering all D2 categories
- [x] Bulk QA runner with auto-resolution evaluation
- [x] QA Procedure document (`process-log/QA_PROCEDURE.md`)

### Sprint 8 — Confidence Calibration (`feat/proto-confidence-gate`) ✓
- [x] Pre-classification gate: greeting detection, farewell, gibberish, too-short
- [x] Information density score: technical terms, problem verbs, error codes
- [x] Effective confidence = raw × density → feeds into 85% threshold
- [x] Classification panel shows gate result, density, raw vs effective confidence
- [x] QA runner updated with low-information test cases + auto-resolution eval

### Sprint 9 — Chat-Driven Identity (`feat/proto-chat-identity`) ✓
- [x] Remove email/name input fields from Atendimento page
- [x] Chat asks name + email conversationally (state machine)
- [x] Returning user detection after email collected
- [x] Ticket status queries ("qual o status do meu ticket?")
- [x] identity_state column added to conversations
- [x] Simulation bypasses identity flow (identity_state='support')

### Sprint 10 — RAG Architecture + KB Amplification (`feat/proto-rag`) ✓
- [x] pgvector extension enabled, embedding column added to kb_articles
- [x] RAG helper (searchKB with cosine similarity, top 3 articles)
- [x] Exact-match KB lookup replaced with semantic search
- [x] Classification panel shows RAG step (articles + similarity scores)
- [x] KB amplification script (seed_kb_expanded.mjs — run manually to generate 72 articles)
- [ ] **Manual step:** Run `node scripts/seed_kb_expanded.mjs` to populate new articles + embeddings

### Sprint 11 — KPI Dashboard (`feat/proto-kpi`) ✓
- [x] Migration: csat_rating column added to conversations
- [x] Expanded metrics API (12 KPIs: resolution rate, FRT, TTR, CSAT, SLA compliance, etc.)
- [x] 8 KPI cards with color-coded thresholds
- [x] CSAT star rating on ticket resolve flow
- [x] SLA gauge chart (Recharts semicircle)
- [x] ~~Production KPI roadmap section~~ (replaced by real computed KPIs in Sprint 13)

### Sprint 12 — Message Grouping ✓
- [x] Frontend debounce: 4-second timer, reset on each new message
- [x] Visual indicator: "Aguardando mais mensagens... (N recebidas) [Xs]"
- [x] Send concatenated text to API, store individual messages for transcript
- [x] Classification panel shows grouping step when grouped_count > 1
- [x] Identity flow messages bypass buffering

### Parallel Execution Plan (remaining)

```
WAVE 3 (sequential — needs Waves 1+2 features)
└── Sprint 13: Intelligent Routing + Operator Hierarchy

WAVE 4 (integration test — needs everything above)
└── Sprint 14: Multi-Day Simulation (50 users, 4 days, full pipeline validation)

WAVE 5 (final)
└── Sprint 15: Deployment
```

### Sprint 13 — Intelligent Routing + Operator Hierarchy + Real KPIs ✓
- [x] Operator levels: junior, senior, lead (new column + seeded operators)
- [x] Tier-based queue filtering (juniors see tier 1, seniors see tier 2 + SLA-threatened, leads see tier 3)
- [x] Accept validates operator tier >= ticket's escalation_tier
- [x] Transfer blocks downward escalation (senior → junior prevented)
- [x] Specialty-based routing via `findBestOperator` in escalation flow
- [x] Real KPI dashboard: FCR, AHT, Cost per Ticket, CES, Reopen Rate, Agent Utilization
- [x] Removed KPIRoadmap placeholder — all 6 KPIs computed from live prototype data
- [x] KPI components relocated from simulator page to dashboard page

### Sprint 13.5 — Pre-Simulation Blockers (before Sprint 14) ✓
- [x] SLA auto-escalation trigger — new `/api/prototype/sla-check` route + queue GET calls it on every load
- [x] Atomic `active_tickets` increment — Postgres RPC functions `increment_active_tickets`/`decrement_active_tickets`, all 6 files updated
- [x] `accepted_at` column — migration applied, queue/accept sets it, metrics uses it for AHT
- [x] Simulation start route uses `findBestOperator` instead of simple operator assignment
- [x] `findBestOperator` queries all operators with `active_tickets < max_capacity` regardless of status

### Sprint 14 — Multi-Day Simulation (50 users, 4 days) ✓
- [x] Script: `scripts/qa_simulation_multiday.mjs`
- [x] 50 simulated users with emails, names, and behavioral profiles
- [x] Day 1-4 simulation with returning users, SLA breaches, message grouping tests
- [x] Low-information testing scattered across days
- [x] Final report: `process-log/multiday_simulation_report.md`
- [x] Simulation executed 2x with consistent results: 9/12 validations passed
- [x] SLA backdating test endpoint (`/api/prototype/test/backdate`)
- [x] Density score capture during simulation
- [x] Results documented in DRAFT.md

### Sprint 14.5 — Post-Simulation Fixes ✓
- [x] Fix "Other" label exposed to customer → natural language substitute
- [x] Fix conversation reset after escalation → escalated guard in message handler
- [x] Add date filter (dateFrom/dateTo) to Overview dashboard stats API + FilterBar UI
- [x] Add ConversationQueue component with filters (status, category, scenario, operator)
- [x] Add operator/IA visibility in queue cards
- [x] Reorder sidebar: Prototype section on top, Investigation below
- [x] Rename "Atendimento" → "Atendimento (Teste)"
- [x] Classification panel: historical timeline with turn numbers + escalation details
- [x] Add methodology disclaimer for 3-pool decomposition in DRAFT.md

### Sidebar Cleanup ✓
- [x] Removed 6 unused investigation pages (Explorer, Process Map, Bottlenecks, Classification, Automation, Roadmap)
- [x] Sidebar: Overview + 4 Prototype items only
- [x] Clean `tsc --noEmit` pass

### Sprint 15 — Deployment
- [ ] Vercel deployment configuration
- [ ] Environment variables for production (API keys NOT in repo — public branches)
- [ ] Rate limiting / token protection for public access
- [ ] Verify prototype works on deployed URL
- [ ] Share URL with evaluator instructions

---

## COMPLETED: Phase 8 — Document & Classification

### P8-A — OpenAI Fine-Tuning ✓
- [x] Fine-tuned gpt-4o-mini: 84.6% accuracy (D030)
- [x] 3-pool resource decomposition (D031)

### P8-B — Taxonomy Mapping ✓
- [x] Semantic mapping D1 (16 subjects) ↔ D2 (8 categories)
- [x] Bridge table created (`submissions/vinicius-cury/docs/BRIDGE_TABLE.md`)
- [x] Zero-shot experiment: 48 tickets, 93.75% accuracy, human-evaluated via `/experiment` page
- [x] Impact analysis: 6/8 categories have zero impact from wrong sub-classification

### P8-E — Document Restructuring ✓
- [x] DRAFT.md restructured: scannable + depth, mapped to G4 requirements
- [x] Executive Summary, taxonomy bridge, experiment results added

### P8-F — Document Polish ✓
- [x] Section numbering, images reduced, ROI clarity, chatbot timeline fixed

### P8-G — Dashboard Code Fixes (TODO — deferred until after prototype)
- [ ] Fix automation route: 17,364h → 21,439h
- [ ] Fix REDIRECT_VIABLE matrix
- [ ] Fix pair counts to match framework
- [ ] Recapture screenshots

---

## COMPLETED: Phases 0-7

### Phase 0 — Project Setup ✓
- [x] Next.js + Supabase + shadcn/ui scaffold
- [x] CLAUDE.md, PRD.md, BACKLOG.md, DECISIONS.md, CHAT_LOG.md
- [x] Analysis notebook setup (Python venv, papermill, helpers)

### Phase 1 — Data Intake & Exploration ✓
- [x] Overview dashboard with KPIs, distribution charts, 6 interactive filters
- [x] EDA: 5 data quality issues, variable classification, CSAT segmentation

### Phase 3+4 — Bottleneck Analysis ✓
- [x] Scoring criteria, heatmaps, regression scatters, bottleneck tables
- [x] Simpson's Paradox discovered: per-pair correlations -0.70 to +0.87
- [x] 6-scenario diagnostic framework (Acelerar/Desacelerar/Redirecionar/Quarentena/Manter/Liberar)

### Phase 5A — ML Validation ✓
- [x] GBR+SHAP (12 experiments) + OLS (8 experiments)
- [x] Channel+Subject dominant, Age irrelevant, models can't beat baseline

### Phase 5B — LLM Classification ✓
- [x] Zero-shot 40.9%, Few-shot 46.2%, Fine-tuned 84.6%

### Phase 6+7 — Parallel Execution ✓
- [x] Resource analysis, automation page, classifier prototype, roadmap
- [x] 4 branches merged, build passes, all 7 pages functional

---

## Parking Lot
- [ ] Voice channel (ElevenLabs integration — documented in PRD_PROTOTYPE.md §11)
- [ ] Active learning pipeline (operator corrections → model improvement)
- [ ] PostHog analytics
- [ ] Multi-language support

---

*Last updated: Mar 22, 2026 — Session 22 (Sprint 14 script created — execution pending. Sprint 15 remaining)*
