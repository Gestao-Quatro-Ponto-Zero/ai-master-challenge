# PRD — Protótipo: Sistema de Suporte Inteligente

> Control document for prototype development. All agents working on the prototype MUST read this before starting.

**Version:** 1.0
**Date:** 2026-03-22
**Status:** Draft — awaiting human review before development

---

## 1. Product Overview

### 1.1 What This Is
A working prototype of the AI-powered support system proposed in the OptiFlow diagnostic. Lives inside the existing OptiFlow dashboard as a new "Protótipo" section. Simulates the complete ticket lifecycle: customer contact → auto-classification → scenario routing → operator handling → resolution.

Not a mock — uses the fine-tuned classifier (84.6%), the 6-scenario routing matrix, and real ticket data from the analysis phase.

### 1.2 Why It Matters for G4
- G4 requires "algo rodando" — this proves the analysis translates into a working system
- Connects all prior work: diagnostic framework, classifier, automation proposal, roadmap
- Three audiences see three things: customer sees a chatbot, operator sees a queue, manager sees metrics

### 1.3 Goals
- Demonstrate end-to-end ticket lifecycle in real time
- Show the classifier making routing decisions visible to the operator
- Prove the 6-scenario framework works as an operational tool
- Provide a simulation mode for evaluators to test with custom scenarios
- All UI in pt-BR

### 1.4 Non-Goals
- Not a production system (no auth, no multi-tenant, no billing)
- Not connected to real email/phone/social channels
- Voice via ElevenLabs documented as future feature (see §11)
- Sandbox mode — single-user demo

---

## 2. User Personas

### 2.1 Customer (Cliente)
- Arrives via chat widget
- Describes their problem in natural language
- Gets 3-4 turns of automated response (RAG-powered)
- If unresolved, escalated with channel recommendation
- Sees their conversation summarized into a ticket upon escalation

### 2.2 Operator (Atendente)
- Views operator dashboard with queues organized by scenario priority
- Sees tickets arriving in real-time, already classified and routed
- For each ticket: scenario badge, recommended action, confidence score, conversation history
- Can accept/reassign/escalate tickets
- Sees SLA timers per ticket

### 2.3 Manager (Gestor)
- Views aggregate metrics: throughput, avg resolution time, CSAT, scenario distribution
- Sees operator capacity and queue health
- Can run simulations (inject N tickets with specific characteristics)
- Guided walkthrough mode explains each component

---

## 3. System Architecture

### 3.1 Classification Pipeline

```
Customer message (text) + channel
    ↓
Stage 1: OpenAI fine-tuned (gpt-4o-mini) → 8 D2 categories (84.6%)
    ↓
Stage 2: Zero-shot (restricted options per category + "Other")
    ↓
Taxonomy mapping → D1 subject (16 subjects)
    ↓
Channel × Subject pair → Routing matrix (64 pairs)
    ↓
Scenario assignment (acelerar/desacelerar/redirecionar/quarentena/manter/liberar)
    ↓
Confidence check: ≥85% → auto-route | <85% → operator review queue
    ↓
Output: scenario, action, confidence, explanation
```

**Key decision:** The routing matrix is deterministic (lookup table). Only classification uses LLM. If OpenAI is down, fall back to random assignment with "classificador indisponível" badge.

### 3.2 RAG System (Synthetic KB)

- Each of the 16 D1 subjects gets 3-5 KB articles
- Generated from D1 resolution text patterns (clustered by subject)
- Storage: Supabase `kb_articles` table
- Retrieval: classifier already identifies the subject → serve top KB article for that subject directly (no embedding search needed for demo)
- Response: synthesized answer from KB, never "I found this article"
- Ask if it helped → escalate if not

### 3.3 Routing Engine

- Extract existing `buildRoutingMatrix()` logic from `/api/tickets/diagnostic/route.ts` into shared module: `src/lib/routing/engine.ts`
- Routing decision is deterministic — ML is only for classification
- Escalation logic: after 3-4 turns without resolution → generate conversation summary → route to operator queue

### 3.4 Real-Time Layer

- **Primary:** Supabase Realtime subscriptions on `conversations` and `messages` tables
- **Fallback:** polling every 2s via SWR (indistinguishable from real-time for human watching)
- Decision: start with Supabase Realtime since it's already in the stack and free tier

### 3.5 Chat → Ticket Handoff

When escalation triggers:
1. LLM generates a summary of the conversation (standard gpt-4o-mini, not fine-tuned)
2. Summary becomes the ticket description
3. Ticket appears in operator queue with full conversation history attached
4. Operator sees: summary + classification + scenario + conversation thread

---

## 4. Feature Specifications

### 4.1 Chat Widget

- **Position:** split-screen layout on Atendimento page (left: chat, right: classification panel)
- **Components:** message list (scrollable), text input, send button, typing indicator
- **Flow:**
  1. Welcome message with greeting
  2. Customer types problem description
  3. System classifies in background (shows "Analisando..." spinner)
  4. Returns KB-based synthesized response
  5. Customer responds (turn 2)
  6. System refines or asks clarifying question (turn 3) — clarifying questions improve zero-shot accuracy
  7. If unresolved by turn 3-4, escalation message with channel recommendation ("Recomendamos ligar para...")
  8. Conversation saved as ticket, appears in operator dashboard
- **Backend classification panel** (right side): shows classification steps in real-time as the customer types — scenario, confidence, routing decision, animated steps. This is what makes it a G4-worthy demo.

### 4.2 Operator Dashboard

- **Layout:** 3 columns
  - Left (30%): queue list, filterable by scenario, sortable by priority/time
  - Center (50%): active ticket detail (conversation, classification info, KB suggestions, action buttons)
  - Right (20%): operator stats (tickets handled today, avg time)
- **Queue items:** ticket ID, subject, scenario badge (color-coded), channel icon, time in queue, SLA indicator
- **Ticket detail:** full conversation thread, classification result (category, confidence, scenario), recommended action, KB articles tried, escalation history
- **Actions:** accept ticket, transfer to specialist, mark resolved, add internal note
- **Real-time:** new tickets animate into the queue, SLA timers tick live

### 4.3 Simulation Tool

- **Controls:**
  - Number of tickets (1, 5, 10, 20, 50)
  - Channel distribution (sliders or presets)
  - Subject focus (specific subjects or realistic distribution)
  - Arrival pattern (all at once, steady stream N/min, burst)
- Start/Stop/Pause buttons
- Progress indicator: tickets generated, classified, routed
- **Data reset button** with confirmation dialog — clears all prototype data, never touches analysis data

### 4.4 Metrics Dashboard

- **KPI cards:** tickets in queue, avg wait time, avg resolution time, auto-resolution rate, deflection rate
- **Charts:**
  - Scenario distribution pie/donut (live updating)
  - Channel distribution bar chart
  - Throughput over time (tickets resolved per window)
  - SLA compliance gauge
- **Capacity panel:** tickets per scenario queue vs capacity

### 4.5 Guided Walkthrough

- Overlay tooltips highlighting each component with pt-BR explanation
- Sequential steps:
  1. Open chat widget, pre-filled message "Meu notebook Dell não liga desde ontem"
  2. See classification panel light up: Hardware → Hardware issue → Acelerar → 91%
  3. Chat responds with KB troubleshooting article
  4. Customer responds "Já tentei, não funcionou"
  5. Escalation message appears with channel recommendation
  6. Switch to Operador — ticket appears in queue with "Acelerar" badge
  7. Accept ticket, see full details
  8. Switch to Simulador, inject 20 tickets, watch metrics update
- 3 pre-loaded scenarios:
  - "Hardware notebook" → Acelerar (speed priority)
  - "Cancelar assinatura" → Redirecionar (channel switch)
  - "Dados sumindo do sistema" → Quarentena (investigation flag)

---

## 5. Data Model (New Tables)

All prototype tables are separate from analysis tables. Reset button truncates only these.

### 5.1 conversations
```sql
id UUID PK DEFAULT gen_random_uuid()
channel TEXT NOT NULL (email/chat/phone/social_media)
status TEXT NOT NULL DEFAULT 'active' (active/waiting_operator/in_progress/resolved/escalated)
customer_name TEXT
subject_classified TEXT          -- D1 subject (set after classification)
category_classified TEXT         -- D2 category
scenario TEXT                    -- 6-scenario result
confidence FLOAT
assigned_operator_id UUID        -- FK to operators
escalation_channel TEXT          -- recommended channel for escalation
summary TEXT                     -- auto-generated on escalation
turn_count INT DEFAULT 0
sla_deadline TIMESTAMPTZ
created_at TIMESTAMPTZ DEFAULT now()
updated_at TIMESTAMPTZ DEFAULT now()
resolved_at TIMESTAMPTZ
```

### 5.2 messages
```sql
id UUID PK DEFAULT gen_random_uuid()
conversation_id UUID FK conversations(id) ON DELETE CASCADE
role TEXT NOT NULL (customer/assistant/operator/system)
content TEXT NOT NULL
metadata JSONB                   -- classification results, KB article used, etc.
created_at TIMESTAMPTZ DEFAULT now()
```

### 5.3 kb_articles
```sql
id UUID PK DEFAULT gen_random_uuid()
subject TEXT NOT NULL             -- D1 subject
category TEXT NOT NULL            -- D2 category
title TEXT NOT NULL
content TEXT NOT NULL
created_at TIMESTAMPTZ DEFAULT now()
```

### 5.4 operators (simulated)
```sql
id UUID PK DEFAULT gen_random_uuid()
name TEXT NOT NULL
status TEXT DEFAULT 'available' (available/busy/offline)
active_tickets INT DEFAULT 0
max_capacity INT DEFAULT 5
specialties TEXT[]                -- subjects they handle best
total_resolved INT DEFAULT 0
created_at TIMESTAMPTZ DEFAULT now()
```

### 5.5 simulation_runs
```sql
id UUID PK DEFAULT gen_random_uuid()
config JSONB NOT NULL            -- channel dist, subject focus, arrival pattern, count
status TEXT DEFAULT 'running' (running/paused/completed/cancelled)
tickets_generated INT DEFAULT 0
tickets_classified INT DEFAULT 0
tickets_resolved INT DEFAULT 0
started_at TIMESTAMPTZ DEFAULT now()
completed_at TIMESTAMPTZ
```

---

## 6. API Design

All prototype APIs under `/api/prototype/` — separate from analysis APIs under `/api/tickets/`.

### 6.1 Chat / Conversations
```
POST   /api/prototype/conversations                    -- Create new conversation
GET    /api/prototype/conversations/[id]               -- Get conversation + messages
POST   /api/prototype/conversations/[id]/messages      -- Send message (triggers classify + respond)
PATCH  /api/prototype/conversations/[id]               -- Update status (escalate, resolve, assign)
```

### 6.2 Classification
```
POST   /api/prototype/classify
  Input:  { text: string, channel: string }
  Output: { category, subject, scenario, confidence, action, explanation, kb_suggestion }
  Pipeline: OpenAI classify → taxonomy map → routing matrix → KB lookup
```

### 6.3 Operator / Queue
```
GET    /api/prototype/queue                            -- Queue list (filterable by scenario)
GET    /api/prototype/operators                        -- List operators with status
PATCH  /api/prototype/operators/[id]                   -- Update operator status
POST   /api/prototype/queue/accept                     -- Accept a ticket
POST   /api/prototype/queue/transfer                   -- Transfer ticket
```

### 6.4 Simulation
```
POST   /api/prototype/simulation/start                 -- Start simulation run
POST   /api/prototype/simulation/stop                  -- Stop simulation
GET    /api/prototype/simulation/status                 -- Current state
POST   /api/prototype/simulation/reset                 -- Reset all prototype data
```

### 6.5 Metrics
```
GET    /api/prototype/metrics
  Output: { queue_depth, avg_wait, avg_resolution, auto_resolution_rate,
            scenario_distribution, channel_distribution, throughput_history }
```

---

## 7. UI/UX Specs

### 7.1 Navigation
Add sidebar section separator: **"Protótipo"** header, with 3 items:
- "Atendimento" (HeadsetIcon) — chat + classification panel
- "Operador" (UsersIcon) — operator dashboard
- "Simulador" (PlayIcon) — simulation + metrics

### 7.2 Pages

| Route | Layout | Purpose |
|-------|--------|---------|
| `/prototype/atendimento` | Split: 60% chat, 40% classification panel | Customer + AI interaction with visible pipeline |
| `/prototype/operador` | 3-column: queue, detail, stats | Operator workflow |
| `/prototype/simulador` | Top: controls, Middle: live feed, Bottom: metrics | Simulation + dashboard |

### 7.3 Component Inventory

| Component | File | Purpose |
|-----------|------|---------|
| ChatWidget | `components/prototype/chat-widget.tsx` | Message list + input |
| ClassificationPanel | `components/prototype/classification-panel.tsx` | Real-time pipeline vis |
| QueueList | `components/prototype/queue-list.tsx` | Filterable ticket queue |
| TicketDetail | `components/prototype/ticket-detail.tsx` | Conversation + classification |
| OperatorCard | `components/prototype/operator-card.tsx` | Operator status + stats |
| SimulationControls | `components/prototype/simulation-controls.tsx` | Config form |
| MetricsPanel | `components/prototype/metrics-panel.tsx` | KPI cards + charts |
| WalkthroughOverlay | `components/prototype/walkthrough-overlay.tsx` | Guided tour |
| ScenarioBadge | `components/prototype/scenario-badge.tsx` | Reusable badge (extract from classification-view) |

---

## 8. Integration Points

### 8.1 OpenAI API
- **Fine-tuned model:** `ft:gpt-4o-mini-2024-07-18:mcury:optiflow-tickets:DM09m89K`
- **Used for:** ticket classification (Stage 1), conversation summary on escalation
- **Cost:** ~$0.04 per classification call
- **Env vars:** `OPENAI_API_KEY`, `OPENAI_FINETUNE_MODEL_ID`

### 8.2 Supabase
- Database: PostgreSQL for all prototype tables
- Realtime: subscribe to `conversations` and `messages` for live updates
- RLS: disabled for prototype (single-user demo)
- Existing connection already configured

### 8.3 Routing Matrix
- Extract from `/api/tickets/diagnostic/route.ts` into `src/lib/routing/engine.ts`
- Compute once, cache in memory
- Eliminates CSV parsing duplication across 3 existing API routes

---

## 9. Demo Flow

### 9.1 Evaluator Journey (~5 minutes)
1. Land on Protótipo section, see overview card
2. Click "Iniciar Tour Guiado"
3. Chat widget opens with pre-filled message
4. Classification panel shows pipeline steps in real-time
5. Chat responds, customer responds, escalation triggers
6. Switch to Operador — ticket in queue with scenario badge
7. Accept ticket, see full details
8. Switch to Simulador, inject 20 tickets, watch metrics update

### 9.2 Free Exploration
- After tour, evaluator types any problem and sees full pipeline
- Simulation tool for stress testing
- Reset button to start fresh

---

## 10. Development Phases

### Phase A: Foundation (Agent 1)
- [ ] Supabase migration for 5 new prototype tables
- [ ] Extract routing engine into `src/lib/routing/engine.ts`
- [ ] Create `/api/prototype/classify` endpoint
- [ ] Generate and seed KB articles (script)
- [ ] Seed simulated operators (3-5)
- [ ] Add "Protótipo" section to sidebar

### Phase B: Chat + Classification (Agent 2)
- [ ] ChatWidget component
- [ ] ClassificationPanel component
- [ ] Conversation/message API routes
- [ ] Wire chat to classification pipeline
- [ ] Atendimento page with dual-panel layout
- [ ] 3-4 turn logic with escalation + summary generation

### Phase C: Operator Dashboard (Agent 3)
- [ ] QueueList, TicketDetail, OperatorCard components
- [ ] Operator/queue API routes
- [ ] Operador page with 3-column layout
- [ ] Supabase Realtime subscriptions (new tickets appear live)

### Phase D: Simulation + Metrics (Agent 4)
- [ ] SimulationControls and MetricsPanel components
- [ ] Simulation API routes
- [ ] Simulador page
- [ ] Ticket generation engine (random sampling from D1)
- [ ] Reset functionality with confirmation dialog

### Phase E: Polish + Walkthrough (Agent 5)
- [ ] WalkthroughOverlay component
- [ ] 3 pre-loaded scenarios
- [ ] ScenarioBadge as reusable component
- [ ] UI polish: animations, loading states, error handling
- [ ] Screenshot all states with Puppeteer

### Phase F: QA Audit (After all sprints)

**Phase A — Static Analysis (automated)**
1. `npx tsc --noEmit` — must be zero errors
2. `npm run lint` — report all errors/warnings with file:line
3. `npm run build` — must succeed (catches SSR issues, missing imports)

**Phase B — Code Review (read every prototype file)**
- Check each file for: missing null checks, wrong types, dead code, unused variables
- API routes: Zod validation on all inputs, proper error responses
- No hardcoded credentials or leaked internals
- Prototype tables isolated from analysis tables (reset only affects prototype)

**Phase C — Visual QA with Puppeteer**
- Navigate every prototype page — screenshot, check console errors
- Test flows:
  1. Open chat → type problem → see classification → get KB response → escalation
  2. Switch to Operador → ticket appears in queue → accept → see details
  3. Open Simulador → configure → run → watch metrics update
  4. Data reset → verify clean state
- Verify each of the 3 pre-loaded scenarios works end-to-end
- Check responsive behavior (desktop viewport sufficient for demo)

**Phase D — Report**
Produce report with: Errors (must fix), Warnings (should fix), UX Issues (nice to fix).
Each item: severity, file:line, description, suggested fix.

**Dependencies:**
- A must complete before B (classify API needed for chat)
- B must complete before C (operator needs conversations)
- D can run parallel with C
- E depends on all others

---

## 11. Future: Voice Channel (ElevenLabs)

Documented here for the submission roadmap. Not implemented in v1.

### 11.1 Architecture
- **ElevenLabs Conversational AI** — supports text + voice dual mode in same widget
- **React SDK:** `@elevenlabs/react` with `useConversation` hook
- **Server Tools:** agent calls our API mid-conversation (classify, create ticket, fetch KB)
- **pt-BR:** first-class support, ~75ms latency, multiple Brazilian voices

### 11.2 Integration Pattern
```
Customer speaks → ElevenLabs ASR → text → our classify API (Server Tool) →
ElevenLabs LLM generates response using KB → ElevenLabs TTS → customer hears answer
```

### 11.3 Cost
- Creator plan: $11/month (~150 min conversations, 5 concurrent)
- Demo cost: ~$5-11 for full evaluation session
- Twilio for phone: ~$1/month for BR number

### 11.4 KB Access
- Static: upload articles as PDF/text (20MB limit)
- Dynamic: Server Tools call our Supabase API for live data
- Recommended: combine both — static KB for common answers, Server Tools for ticket-specific queries

### 11.5 Implementation Estimate
- Widget integration: ~2-4 hours (React SDK is drop-in)
- Server Tools setup: ~2-4 hours (point to our existing APIs)
- Voice selection + prompt tuning: ~2-4 hours
- **Total: ~1 day** (user confirmed from prior experience)

---

## 12. Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| OpenAI API down | Classification fails | Routing matrix is deterministic; fall back to random assignment with warning badge |
| Supabase Realtime issues | No live updates | Polling fallback at 2s intervals |
| LLM generates wrong classification | Wrong routing | 85% confidence gate + operator review queue |
| Evaluator confused by prototype | Poor impression | Guided walkthrough with pre-loaded scenarios |
| Demo data looks fake | Credibility loss | Use D1 resolution patterns for KB, D2 real ticket text for simulation |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | 2026-03-22 | Initial PRD — full prototype spec |
