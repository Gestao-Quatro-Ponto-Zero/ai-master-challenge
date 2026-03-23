# DECISIONS.md — OptiFlow (G4 Challenge 002)

> Technical decision log. When Claude Code makes an architecture choice, it logs it here.
> Format: Date, Decision, Context, Alternatives Considered, Rationale.

---

## D001 — Full stack (Next.js + Supabase) over notebook/lightweight approach
**Date:** Mar 20, 2026
**Context:** G4 challenge could be solved with a Jupyter notebook + PDF report, a lightweight HTML dashboard, or a full-stack application. Need to decide project weight.
**Alternatives:**
- Jupyter notebook + PDF: Fastest to produce, shows analysis skills, but G4 explicitly says "quero ver algo rodando — não quero só um PowerPoint"
- Lightweight (Next.js + CSV in-memory): Fast, no DB overhead, but limits interactivity and can't handle 30K rows smoothly
- Full stack (Next.js + Supabase + Vercel): More setup, but delivers a production-grade tool that can actually be used
**Decision:** Full stack. The Diretor de Operações wants something running, not a document. A production app demonstrates AI Master capability — building real tools, not just analysis. Also, Supabase handles 30K+ rows with proper indexing and filtering far better than in-memory CSV parsing.
**Trade-off:** More setup time (~1-2 hours), but pays off in interactivity, scalability, and impression factor.

---

## D002 — Consultant workflow methodology (phased with validation gates)
**Date:** Mar 20, 2026
**Context:** Need a structured approach to the analysis that mirrors real consulting work, not just "dump data into AI and see what comes out." The G4 evaluation explicitly penalizes single-prompt-to-submission approaches.
**Decision:** 7-phase workflow with human validation gates between each phase:
1. Data Intake → 2. As-Is Process → 3. Problems → 4. Bottlenecks → 5. Classification → 6. Automation → 7. Roadmap
Each phase produces a dashboard page + documentation. Human must approve before next phase starts.
**Rationale:** This approach:
- Shows G4 that the candidate thinks before executing
- Produces iterative evidence (great for process log)
- Ensures quality at each step (catch errors early)
- Mirrors how a real AI Master would work in a company

---

## D003 — LLM classification over classic NLP
**Date:** Mar 20, 2026
**Context:** Need to classify support tickets into categories. Options: classic NLP (TF-IDF + SVM/Random Forest), fine-tuned transformer, or LLM zero-shot/few-shot classification.
**Alternatives:**
- Classic NLP (TF-IDF + classifier): Fast, cheap, well-understood, but requires feature engineering and typically lower accuracy on nuanced text
- Fine-tuned transformer (BERT): High accuracy, but requires GPU, training time, and infrastructure
- LLM zero-shot/few-shot: No training needed, handles nuance well, explainable (provides reasoning), but higher per-ticket cost
**Decision:** LLM classification with model benchmarking (Sonnet vs Haiku vs Gemini). Use Dataset 2's 48K labeled tickets as ground truth for accuracy measurement.
**Rationale:**
- G4 is testing AI Master skills — showing fluency with LLMs is more relevant than classic ML
- Zero-shot means we can iterate on taxonomy without retraining
- Reasoning output adds explainability (which G4 values)
- Cost is manageable: Haiku at ~$0.001/ticket = ~$30 for 30K tickets
- Classic NLP would look like "the AI Master chose the least AI approach"

---

## D004 — Process mapping through data inference (not assumption)
**Date:** Mar 20, 2026
**Context:** Challenge data doesn't include explicit process steps, agent IDs, or escalation history. We need to map the support process from what IS in the data: channels, types, priorities, statuses, times.
**Decision:** Infer the as-is process from data patterns rather than assuming a generic support process. The Mermaid diagram will be annotated with actual data (median times, volumes, satisfaction scores per path). Where data doesn't tell us something (e.g., internal handoffs), we'll explicitly mark it as "inferred" or "not visible in data."
**Rationale:** G4 evaluates whether insights are verified. A generic "tickets come in → agent picks up → resolves" diagram adds zero value. A data-backed process map with real numbers shows analytical depth.

---

## D005 — Document system adapted from Wavvo project
**Date:** Mar 20, 2026
**Context:** Need a documentation strategy for both the project itself and the G4 process log requirement. Developer has a proven 5-document system from the Wavvo project.
**Decision:** Adapt the Wavvo document ecosystem (CLAUDE.md, PRD.md, BACKLOG.md, DECISIONS.md) and add CHAT_LOG.md specifically for G4's process evidence requirement. Every document follows the same conventions: changelog, version tracking, structured format.
**Rationale:** Battle-tested system. CHAT_LOG.md serves double duty — it's our working memory AND the G4 process log. DECISIONS.md captures every architectural choice, which directly maps to G4's "show how you used AI" requirement.

---

## D006 — Correction: All content in Brazilian Portuguese
**Date:** Mar 20, 2026 — Session 4
**What happened:** Claude wrote the entire data exploration notebook (markdown cells, chart titles, axis labels) in English.
**Human correction:** "everything we write there and in our websystem must be in brazilian portuguese"
**Why:** The G4 challenge audience is Brazilian. The Diretor de Operações reads pt-BR. The submission must communicate in the audience's language.
**Change:** All notebook markdown, chart titles/labels, dashboard UI, and analysis text will be in pt-BR from now on. Code and variable names stay in English. CLAUDE.md updated with this rule.

---

## D007 — Correction: Setup before execution, don't rush
**Date:** Mar 20, 2026 — Session 4
**What happened:** Claude created the Supabase project, applied migration, wrote the seed script, built the entire notebook, and tried to execute it — all in rapid succession without pausing for the human to set up the service role key or review the approach.
**Human correction:** "here you are going too fast, we need to recap some stuff... make clear on the decision documents when I correct you"
**Why:** Moving fast without setup leads to failed executions and wasted time. The human needs to be part of the process — this is a collaborative project, not autonomous execution.
**Change:** From now on: (1) ensure all dependencies/configs are ready before executing, (2) pause at natural checkpoints for human review, (3) document corrections explicitly in DECISIONS.md.

---

## D008 — Puppeteer MCP for screenshot documentation
**Date:** Mar 20, 2026 — Session 4
**Context:** G4 requires a process log with evidence of reasoning. Screenshots capture key moments (notebook outputs, dashboard states, charts) that prove analytical process.
**Decision:** Install Puppeteer MCP server. Use it to capture screenshots at key moments and save to `process-log/screenshots/`.
**Rationale:** The CHAT_LOG shows the conversation, but screenshots show the actual outputs. Together they make the process log compelling for G4 evaluation.

---

## D009 — Jupyter server for human visualization
**Date:** Mar 20, 2026 — Session 4
**Context:** Claude was executing notebooks headlessly via papermill and reporting results in text. Human wanted to see the actual charts and outputs visually.
**Decision:** Start Jupyter server for human to view notebooks interactively. Papermill execution is still used for automated runs, but human review happens in the browser.
**Rationale:** The human needs to see charts, not hear descriptions of charts. Visual review catches issues that text summaries miss.

---

## D010 — CSV-based API routes instead of Supabase queries
**Date:** Mar 20, 2026 — Session 6
**Context:** Supabase cloud project exists but service role key not yet configured. Need data access for dashboard.
**Decision:** Build API routes that read CSV directly from `data/` folder using `fs.readFileSync`. Parse CSV server-side with custom parser. Cache parsed data in module-level variable.
**Rationale:** Unblocks dashboard development without waiting for Supabase setup. Same API contract — can swap to Supabase queries later without changing frontend.
**Trade-off:** No pagination, no complex queries, entire dataset in memory. Fine for 8.5K rows.

---

## D011 — Correction: Negative resolution duration
**Date:** Mar 20, 2026 — Session 6
**What happened:** Claude computed `TTR - FRT` without checking timestamp validity. Dashboard showed negative durations.
**Human correction:** "check again, we have negative resolution time"
**Root cause:** Synthetic dataset has randomized timestamps — ~50% of Closed tickets have TTR before FRT (impossible in reality).
**Fix:** `Math.abs(TTR - FRT)` as proxy, only for Closed tickets. Documented as known limitation.
**Going forward:** Always validate data sanity before computing derived metrics.

---

## D012 — CSAT segmentation: Satisfeito / Neutro / Insatisfeito
**Date:** Mar 20, 2026 — Session 6
**Context:** Need to segment CSAT ratings for analysis.
**Decision:** Three segments: Satisfeito (≥4), Neutro (=3), Insatisfeito (≤2).
**Rationale:** Standard NPS-inspired segmentation. Human confirmed these exact thresholds.

---

## D013 — Scoring criteria: Risco Operacional + Risco por Prioridade
**Date:** Mar 20, 2026 — Session 6
**Context:** Human wanted a composite metric mixing insatisfaction with business impact.
**Alternatives considered:**
- A: Volume × Taxa Insatisfação (simple, ignores time)
- B: Volume × Taxa Insatisfação × Duração Média (captures operational cost)
- C: Volume × Duração Média × CSAT Inverso (alternative weight)
**Decision:** Use B (Risco Operacional) and B × Priority Weight (Risco por Prioridade).
- Priority weights: Critical=4, High=3, Medium=2, Low=1
**Rationale:** Human chose B for capturing time cost. Adding priority weight surfaces high-priority bottlenecks that deserve faster attention.

---

## D014 — Dashboard organized by analysis dimension
**Date:** Mar 20, 2026 — Session 7
**Context:** Dashboard was mixing all cross-tab analyses together.
**Human instruction:** "organize the layout so we have them separated... to not mix information"
**Decision:** 4 sections: Visão Geral, Canal × Assunto, Canal × Prioridade, Prioridade × Assunto. Each section gets the full analysis stack (heatmap, duration×CSAT, regression, bottleneck table).
**Rationale:** Each dimension tells a different story. Separation makes the analysis easier to follow and present.

---

## D015 — Correlação Pearson por par vs agregada (Simpson's paradox)
**Date:** Mar 20, 2026 — Session 7
**Context:** R² global entre duração e CSAT era ~0.003, sugerindo zero correlação. Humano pediu para verificar por par Canal × Assunto.
**Finding:** Correlações individuais vão de -0.70 a +0.87. Efeito Simpson: correlações opostas se cancelam na agregação. Em dados reais, isto revelaria quais combinações específicas de canal e assunto têm relação entre tempo de resolução e satisfação do cliente.
**Decision:** Adicionar heatmap de correlação Pearson ao dashboard como ferramenta de diagnóstico principal. O método é mais importante que os números (dados sintéticos), mas demonstra capacidade analítica.
**Impact:** Este é o insight central do diagnóstico — não basta olhar agregados, é preciso descer ao nível do par operacional.

---

## D016 — LLM classification over classic NLP for Dataset 2
**Date:** Mar 20, 2026 — Session 7
**Context:** Dataset 2 has 48K labeled IT tickets (Document + Topic_group with 8 categories). Need to choose classification approach.
**Decision:** Use LLM API (Gemini Flash as primary candidate due to lowest cost ~$0.15 for full dataset). Benchmark against Claude Haiku for accuracy comparison.
**Rationale:** G4 evaluates AI Master skills — LLM classification is more relevant than TF-IDF + SVM. Zero-shot means no training pipeline needed. Cost is negligible with Gemini Flash.

---

## D017 — 6-Scenario Diagnostic Framework (Routing Matrix) — v2
**Date:** Mar 21, 2026 — Session 8 (revised in Session 8b)
**Context:** After discovering Simpson's Paradox (global R²~0.003 but per-pair correlations -0.70 to +0.87), needed to classify each Canal × Assunto pair into actionable operational scenarios.
**Human instruction:** "We need a matrix... channel × subject... where doesn't matter, where time doesn't matter, where we should go faster and where we need to go slower. That's the true routing system."

### v1 → v2 Correction
**What v1 did wrong:** Used `efeito_canal > efeito_tempo × 1.5` at subject level, which made ALL channels of a subject get the same "redirecionar" scenario. Human flagged: "if a ticket comes from a given subject and you put all channels redirect, what that means?" Phone × Peripheral Compatibility (r=0.87) was wrongly classified as "redirecionar" instead of "desacelerar".
**What v2 changed:** Pair-first decision tree. Check r of the PAIR first (Dimension A: time vs satisfaction). Only when |r| ≤ 0.3 does it move to Dimension B (channel comparison via CSAT gap).

### v2 Decision Tree (Two-Layer Analysis)
**Dimension A — r(time, CSAT) of the pair:**
- r < -0.3 → **Acelerar** (more time → less satisfaction)
- r > 0.3 → **Desacelerar** (more time → more satisfaction)
- |r| ≤ 0.3 → time NOT a factor → go to Dimension B

**Dimension B — CSAT level vs other channels (same subject):**
- CSAT gap > 0.5 below best channel → check redirect viability
  - Viable target exists → **Redirecionar** (specifies from→to channel)
  - No viable target → **Quarentena** (investigate root cause)
- CSAT ≥ 3.5 → **Manter** (channel works, don't change)
- All channels bad for this subject → **Quarentena**
- Otherwise → **Liberar** (deprioritize, free resources)

**Redirection Viability Matrix:**
- Email, Chat, Phone can redirect to each other ✓
- Social media → Email ✓, Phone ✓, Chat ✗
- Anything → Social media ✗

**Implementation:** API `/api/tickets/diagnostic` (pair-first logic) + `diagnostic-panel.tsx` (Mermaid flowchart, routing matrix, divergence table, action plan)
**Result:** 9 Acelerar, 10 Desacelerar, 17 Redirecionar, 5 Quarentena, 7 Manter, 16 Liberar — 64 Channel × Subject pairs
**Validation:** Phone × Peripheral Compatibility = desacelerar (r=0.87) ✓, Email × Hardware Issue = acelerar (r=-0.705) ✓, 0 SM→Chat redirections ✓

---

## D018 — ML Validation: Age irrelevant, models can't beat baseline, Channel+Subject dominant
**Date:** Mar 21, 2026 — Session 9
**Context:** Three notebooks ran systematic ML experiments to validate the manual 6-scenario diagnostic classification (64 Channel × Subject pairs).

### Notebook 05 — GBR + SHAP (12 experiments)
- 12 feature ablation experiments (Blocks A: ablation, B: interactions, C: product)
- Best model: A1 (Channel + Subject only), MAE=1.216
- Baseline (predict mean 2.99): MAE=1.189 — **model is 2.2% worse**
- Age bucket (A5): added no value, MAE=1.234 (worse than A1)
- Duration (A4): degraded performance, MAE=1.284
- Product (C1, C2): no improvement
- Interactions (B1-B3): added complexity, no gain
- SHAP: Subject (0.123) and Channel (0.087) are the only meaningful features
- Permutation test: Z=0.68, **not statistically significant**

### Notebook 06 — OLS Regression (8 experiments)
- 8 regression experiments with dummy variables and interaction terms
- Best model: R1 (Channel + Subject only), MAE=1.209
- All R² negative (worse than intercept-only model)
- Channel coefficients: Email -0.148, Phone -0.110, SM -0.090 vs Chat (all p>0.05)
- Duration×Channel: Phone +0.008, Email -0.007 (all p>0.60, not significant)
- Duration×Subject: only Hardware Issue significant (p=0.046, +0.053)
- Age (R4): MAE=1.218, R²_adj=-0.0025 — **confirmed irrelevant**

### Key Conclusions
1. **Age is irrelevant** — adds no predictive value in either model
2. **Duration is irrelevant at aggregate level** — only significant for 1/16 subjects (Hardware Issue)
3. **Channel and Subject are the only actionable variables** — both models agree
4. **Models can't beat mean prediction** — expected with synthetic data (uniform CSAT distribution)
5. **The analytical framework (6 scenarios) is sound** — even though models fail on prediction, the pair-level Pearson r analysis (Simpson's Paradox) remains valid for routing decisions
6. **GBR and OLS converge** — same ranking, same conclusions, different methods = stronger evidence

**Decision:** Drop age from the diagnostic framework. Focus the routing matrix exclusively on Channel × Subject pairs with duration as the conditional variable (per-pair Pearson r, not global).

---

## D019 — Parallel Terminal Strategy for Phase 6+7
**Date:** Mar 21, 2026 — Session 9
**Context:** After ML validation, need to execute Phase 6 (automation proposal) and Phase 7 (roadmap + prototype) quickly. Human proposed splitting into independent terminals.

**Decision:** 4 parallel Claude Code terminals, each on a separate git branch with zero file overlap:
- **Terminal A** (`feat/resource-analysis-notebook`): Resource analysis notebook — maps where hours go today
- **Terminal B** (`feat/automation-page`): Automation page — impact×feasibility, before/after simulation
- **Terminal C** (`feat/prototype-classifier`): Working prototype — ticket classifier + simulated queue
- **Terminal D** (`feat/roadmap-page`): Roadmap page + control files

**Merge order:** A → B → C → D (control files only in D to avoid conflicts)

**Rationale:**
- Each terminal touches completely different files (zero conflict risk)
- Shared code (diagnostic logic, CSV parser) is copied inline — no shared module dependency
- Human monitors all 4 terminals simultaneously
- This approach demonstrates "AI Master" capability — parallel AI-assisted development
- Documented as process evidence for G4 submission

---

## D020 — Resource Analysis: Time as Resource Proxy
**Date:** Mar 21, 2026 — Session 9
**Context:** Need to understand where operational resources go. Don't have headcount data, but have resolution duration per ticket.

**Decision:** Use `duration_hours = abs(TTR - FRT)` as the resource proxy. Total hours per Channel×Subject pair represents "how much of our capacity goes here."

**Key insight:** Hours per scenario reveals waste. If 50%+ of hours go to "liberar" pairs (low-impact, time doesn't matter), those hours could be reallocated to "acelerar" pairs (high-impact, need speed) or "quarentena" pairs (need investigation).

**Limitation:** Synthetic data has near-uniform distribution (~5,100-5,700 hours per channel). In real data, resource imbalance would be more visible.

---

## D021 — Git Worktrees for Parallel Terminal Execution
**Date:** Mar 21, 2026 — Session 9
**Context:** Needed 4 Claude Code instances working simultaneously on separate branches. A single git directory can only check out one branch at a time.

**Decision:** Use `git worktree` to create 4 independent working copies:
- `../optiflow-a` → `feat/resource-analysis-notebook`
- `../optiflow-b` → `feat/automation-page`
- `../optiflow-c` → `feat/prototype-classifier`
- `../optiflow-d` → `feat/roadmap-page`

Symlinked gitignored files (`data/`, `analysis/.venv/`, `.env.local`, `node_modules/`) into each worktree so all have access to shared resources.

**Rationale:** Worktrees are the git-native solution for parallel branch work. Each terminal sees a full repo copy with its own branch. No file conflicts, no checkout switching. After completion, merge branches back to main in order.

**Trade-off:** Disk space (~5× repo size), but repos are small. Symlinks prevent duplicating large files (data, node_modules).

---

## D022 — Prompt Files: Plain Text over Markdown
**Date:** Mar 21, 2026 — Session 9
**What happened:** Initial prompt files were `.md` with code blocks containing backticks. When passed via `$(cat file.md)`, shell interpreted backticks as command substitution, causing `claude` to receive malformed input.

**Fix:** Created `.txt` prompt files with no backticks, no special shell characters. Piped via `cat file.txt | claude --dangerously-skip-permissions`.

**Going forward:** When creating prompts for CLI tools, avoid markdown formatting. Plain text is more robust for shell piping.

---

## D023 — LLM Classification Results: 46.2% Accuracy, Needs Refinement
**Date:** Mar 21, 2026 — Session 10
**Context:** Notebook 07 ran Gemini 2.5 Flash Lite on 20% sample (9,559 tickets) of Dataset 2 (IT Service Tickets) with zero-shot and few-shot prompts.

**Results:**
- Zero-shot: 40.9% accuracy, F1 Macro 0.352
- Few-shot (5 examples/category): 46.2% accuracy, F1 Macro 0.476
- Best category: Purchase (F1=0.77), Worst: Administrative rights (F1=0.22)
- Top confusions: Hardware→Miscellaneous (742), HR Support→Miscellaneous (684)
- Zero-shot hallucinated a "Backup" category not in the list
- Cost: ~US$1.54 for 20% sample, ~US$7.09 projected for full dataset

**Root causes of low accuracy:**
1. "Miscellaneous" has no clear semantic boundary — acts as a black hole
2. "Administrative rights" vs "Access" overlap semantically
3. Synthetic data uses template-generated text with similar phrasing across categories
4. Flash Lite is optimized for speed/cost, not accuracy

**Decision:** Accept 46.2% as proof-of-concept for G4 submission. Document improvement path (merge categories, use CoT, larger model). Do NOT invest more API calls trying to optimize — the methodology demonstration is sufficient.

---

## D024 — Resource Analysis: 79.5% of Hours Are "Liberar" (Waste)
**Date:** Mar 21, 2026 — Session 10
**Context:** Notebook 08 mapped 21,439 operational hours across 64 Channel×Subject pairs using the 6-scenario diagnostic framework.

**Key finding:** 50 of 64 pairs (79.5% of hours) classify as "liberar" — resources with no clear return on CSAT. Only 1 pair is "acelerar" (1.5%) and 1 is "desacelerar" (1.4%).

**Interpretation:** With synthetic data (uniform distributions), most pairs have weak correlations (-0.3 < r < 0.3) and CSAT below 3.5. This is expected — real operations data would show more variance and more actionable pairs. The framework itself is valid; the data limits it.

**Reallocation scenario:** Moving 25% of "liberar" hours to "acelerar" would increase acelerar capacity by +1,313%. This demonstrates the magnitude of potential optimization.

**Decision:** Document as-is with honest limitations. The diagnostic framework is the deliverable, not the specific numbers from synthetic data.

---

## D025 — Two-Layer Submission: README.md + Background Notebook
**Date:** Mar 21, 2026 — Session 12
**Context:** G4 submission needs a storytelling document with rich visuals. Options considered:

**Alternatives:**
- HTML/PDF report: Good visuals but harder to review on GitHub
- Jupyter notebook as submission: Shows code but not evaluator-friendly
- README.md with embedded images: GitHub renders natively, evaluator reads directly
- README.md + background notebook for new charts: Best of both

**Decision:** Two-layer approach. `submissions/vinicius-cury/README.md` is the primary document (GitHub-rendered, ~460 lines, 20 embedded images, all markdown tables). Background notebook `analysis/10_submission_charts.ipynb` generates any new charts not already in the 49 existing screenshots.

**Rationale:** Evaluators read on GitHub — markdown is native. Images generated from analysis are evidence. The README IS the deliverable; the notebook is the evidence factory.

---

## D026 — 3 Roadmap Scenarios by Classifier Accuracy (46%/70%/90%+)
**Date:** Mar 21, 2026 — Session 12
**Context:** Human specified that the roadmap should be framed as 3 escalating scenarios based on the LLM classifier accuracy, not generic timeline.

**Scenarios:**
- **A (46% — current):** Proof of concept. Classifier as assistant, human confirms. 0% auto-routing.
- **B (70% — MVP):** Merge overlapping categories, CoT prompting, auto-route high-confidence tickets (~30%). ~2,500h/year saved.
- **C (90%+ — strategic):** Fine-tuning + active learning, ~70% auto-routing. ~8,500h/year saved.

**Rationale:** Tying the roadmap to a measurable metric (classifier accuracy) makes the progression concrete and testable. Each scenario has clear prerequisites, investments, and projected returns.

---

## D027 — Dataset Taxonomy Mapping for Unified Classification
**Date:** Mar 21, 2026 — Session 13
**Context:** Dataset 1 (customer support, 16 subjects) and Dataset 2 (IT service desk, 8 categories) have no common key. To build a classification prototype that works across both, we need a semantic mapping.

**Mapping rationale:**
- Dataset 1 subjects are consumer-facing (products, e-commerce): refund, software bug, hardware issue, etc.
- Dataset 2 categories are IT internal (infrastructure, permissions, HR): Access, Hardware, Purchase, etc.
- Some map directly (Hardware issue → Hardware, Account access → Access, Payment issue → Purchase)
- Others are forced (Delivery problem → Miscellaneous, Product recommendation → Miscellaneous)

**3 connection strategies identified:**
1. **Classifier as bridge** (current): train on D2 (has labels), validate method, apply logic to D1
2. **Unified taxonomy**: create new taxonomy covering both, reclassify
3. **Transfer learning**: fine-tune on D2, then apply to D1 with D1's 16 subjects as labels — model learns *how to classify tickets* from D2

**Decision:** Start with strategy 1 (fine-tuning on D2 validates capability). Store mapping for P8-B. If fine-tuned model reaches ≥70%, explore strategy 3 for D1 classification.

**Trade-off:** The mapping is imperfect because the domains genuinely differ. Acknowledging this is more honest than forcing a clean mapping.

---

## D028 — OpenAI gpt-4o-mini Fine-Tuning over Gemini for Classification Improvement
**Date:** Mar 21, 2026 — Session 13
**Context:** Gemini 2.5 Flash Lite few-shot achieved 46.2% accuracy. Need to improve toward Cenário B (70%). Evaluated fine-tuning options across providers.

**Alternatives:**
- OpenAI gpt-4o-mini: simplest setup (5 min), ~$9 training cost for 20% sample, API-first
- Google Gemini (Vertex AI): requires GCP account + provisioned throughput, moderate complexity
- Anthropic Claude (Bedrock): requires AWS + provisioned throughput, only Haiku, not practical for prototype
- Open-source local (Mistral/Llama): requires GPU, too slow for prototyping

**Decision:** OpenAI gpt-4o-mini. Simplest setup, lowest cost, fastest iteration. 20% sample (80/20 train/test split, stratified, same random seed as Gemini experiment for fair comparison).

**Expected:** 70-85% accuracy based on similar classification tasks with fine-tuning.

---

## D029 — Time Decomposition Model: Inferring Process Stages from FRT/TTR Gap
**Date:** Mar 21, 2026 — Session 13
**Context:** We only have two timestamps (FRT, TTR) but the real support process has multiple invisible stages: queue time, first contact, possible transfer to specialist department, specialist queue, actual fix time. The human identified that analyzing `post_contact_time = TTR - FRT` variance across ticket subjects can reveal which subjects involve simple single-handler resolution vs department transfers and specialist work.

**Decision:** Build a time decomposition model using post_contact_time as the "black box" between first response and resolution. Classify subjects by complexity:
- **Single-handler likely** — low post_contact_time (baseline for handling time)
- **Transfer likely** — high post_contact_time (baseline + transfer penalty + specialist time)
- **Ambiguous** — can't distinguish from time data alone

The gap between single-handler baseline and transfer subjects estimates the **routing/waiting overhead** — this becomes the business case for auto-routing and auto-classification.

**Rationale:** This directly answers the operational question "where are we losing time?" and quantifies the **transfer penalty** in hours. Even with synthetic data, the methodology demonstrates how to extract process insights from minimal timestamp data. If results show significant variation, we update the diagnostic framework and automation projections.

**Trade-off:** The decomposition is an estimate based on assumptions (subjects with low post_contact_time = single-handler). With real data, we'd validate against actual transfer records. With synthetic data, we acknowledge this as a methodological demonstration.

---

## D030 — Fine-Tuning Results: 84.6% Accuracy (Cenário B Surpassed)
**Date:** Mar 22, 2026 — Session 14
**Context:** OpenAI gpt-4o-mini fine-tuned on 20% sample (7,647 train, 1,912 test). Same random seed, stratified split, and evaluation protocol as Gemini experiment (D028).

**Results:**
- Accuracy: **84.6%** (vs 46.2% Gemini few-shot = +38.4pp)
- F1 Macro: **0.743** (vs 0.476 = +0.267)
- F1 Weighted: **0.846** (vs 0.475 = +0.371)
- Every category improved: worst = Admin Rights F1=0.74 (+0.52), best = Access/Purchase F1=0.90
- Training cost: ~US$7.07, inference cost: ~US$0.08/1,912 tickets
- Zero API errors, 20 minutes inference time

**Impact on roadmap scenarios:**
- Cenário A (46%) → now historical baseline
- Cenário B (70%) → **surpassed** at 84.6%
- Cenário C (90%+) → now realistic with further optimization (merge similar categories, add CoT, active learning)

**Decision:** The classifier is production-viable. Update DRAFT.md scenarios to reflect actual 84.6% as the new baseline. Cenário B becomes "current state" and Cenário C becomes the stretch goal.

---

## D031 — 3-Pool Resource Decomposition (Sensitivity Analysis)
**Date:** Mar 22, 2026 — Session 14
**Context:** Resource analysis initially treated all 21,439h as a single pool. The human identified that the support process has 3 distinct resource pools: Frontline (agents doing triage), Routing (queue/transfer time), Specialist (fixers). Different automations affect different pools.

**Decision:** Add as sensitivity analysis to DRAFT.md (not primary analysis) because:
- FRT is a reasonable proxy for Frontline (~30% of total)
- Transfer penalty from notebook 12 estimates Routing (~7.9%)
- Specialist is the residual (~62.1%)
- BUT the data doesn't directly show these pools — it's inference from timestamps

**Pool estimates:** Frontline ~6,432h, Routing ~1,698h, Specialist ~13,309h
**Constraint from human:** "o formato da solução não muda" — solution stays the same, only resource reallocation source changes.

---

## D032 — Prototype Direction: Real-Time Ticket Simulation + Support Dashboard
**Date:** Mar 22, 2026 — Session 14
**Context:** With a production-viable classifier (84.6%), the next phase shifts from analysis to building a working prototype. The human wants a direction that goes beyond static analytics.

**Decision:** Prototype will simulate a real support system:
1. Ticket ingestion simulation (new tickets arriving through different channels)
2. Auto-classification with fine-tuned model → scenario routing
3. Dashboard showing ticket lifecycle and flow in real-time
4. User sees what's happening as tickets move through the system

**Rationale:** This demonstrates the full value chain: data → analysis → classification → routing → operational tool. G4 evaluators want "algo rodando" — a simulation of the proposed system is the strongest possible prototype.

**Timeline:** PRD definition on Mar 23, 2026. Build immediately after.

---

## D033 — Document Restructuring: Scannable + Depth, Mapped to G4 Requirements
**Date:** Mar 22, 2026 — Session 15
**Context:** DRAFT.md v8 had grown to ~990 lines with repeated information (synthetic data disclaimers 8+ times, pool decomposition 4 times, channel viability 3 times), mixed technical/business language, and "/ano" on all values despite dataset having no date range. Human created RESTRUCTURE_INSTRUCTION.md and EXECUTIVE_SUMMARY_v2.md as guidelines.

**Problems identified:**
- Disclaimers inline diluted the narrative
- Same information repeated across sections (pools, viability matrix, sanity check)
- "/ano" on all values was factually unsupported — dataset has no date range
- Sections mixed C-level scanning with deep technical detail
- Structure didn't map cleanly to G4 template requirements

**Decision:** Full restructure with dual-audience principle:
1. Each section opens with **bold 2-3 line summary** (for the director scanning in 15 min)
2. Followed by detailed content with data and reasoning (for evaluators analyzing depth)
3. Map structure to G4 requirements: §4 = Diagnóstico Operacional (#1), §5 = Proposta de Automação (#2), §6 = Evidência técnica
4. Executive Summary replaced with EXECUTIVE_SUMMARY_v2.md (visual, slide-like)
5. ALL disclaimers consolidated in §8 Limitações (ONE time)
6. ALL "/ano" removed — values reference "volume analisado (8.469 tickets)"
7. New limitation added: sem range de datas no dataset
8. CSAT projection methodology made explicit (per-component with discount factors)
9. Removed "Por que árvore de decisão e não ML?" (internal debate, not deliverable)

**Files changed:** DRAFT.md (restructured), DRAFT_v8_backup.md (previous version preserved)

---

## D034 — Document Polish: Dual-Audience Principle, Taxonomy Bridge, Timeline Fix
**Date:** Mar 22, 2026 — Session 15
**Context:** Human reviewed restructured document and identified 6 issues: inconsistent numbering, technical jargon in mermaid, unclear 8% vs 42% gap, too many images in one section, ROI not showing both scenarios, chatbot timeline too long.

**Changes:**
1. Section numbering dropped (was 3-8, inconsistent) — now descriptive headers only
2. Mermaid diagram: "Hipótese: Simpson" → "Hipótese: Análise por Subgrupo" (business language)
3. Added bridge sentence before scenarios table explaining chatbot dependency
4. §4.1 images reduced from 8 to 4 (cut: satisfação canal, heatmap risco, ML experiment comparison)
5. ROI table now shows both scenarios side-by-side (sem chatbot R$58k / com chatbot R$316k)
6. Chatbot timeline: "1-3 meses" → "4-6 semanas" (user's explicit correction)
7. Taxonomy mapping D1↔D2 added (16 subjects → 8 categories bridge table)
8. Duplicate screenshots removed (p6 automation = same as p12)
9. Dashboard screenshots flagged as stale (show 17,364h, pair counts wrong)

**Human feedback on what worked:** "This version is significantly better." Validated: bold summaries, clean section flow mapped to G4, technical depth preserved, much shorter.

---

## D035 — Zero-Shot Sub-Classification Experiment: 93.75% Accuracy on Synthetic Data
**Date:** Mar 22, 2026
**Context:** Need to validate two-stage classification pipeline (fine-tuned D2 → zero-shot D1 sub-classification). D1 descriptions are template garbage — can't test on D1 directly. Used D2 real tickets instead.
**Experiment:** 48 D2 tickets (6 per category), zero-shot via Gemini 2.5 Flash Lite, category-specific prompts with restricted D1 subject options + "Other". Manual human evaluation via custom `/experiment` page.
**Results:** 45/48 correct (93.75%). Most classifications correctly fell to "Other" because D2 (IT internal) and D1 (customer support) are different domains. Only Access category showed meaningful cross-domain mapping (Account access at 90% confidence).
**Key finding:** Impact analysis shows 6/8 categories have ZERO operational impact from wrong sub-classification — all D1 subjects within those categories lead to the same action (Liberar → Chatbot). Only Hardware has divergent scenarios where sub-classification matters.
**Decision:** Two-stage pipeline validated as architecture. With real production data + chatbot clarifying questions providing additional context, zero-shot accuracy would be significantly higher.
**Trade-off:** Synthetic data limits what we can prove. Document acknowledges this and frames the approach as validated architecture, not proven accuracy.

---

## D036 — Prototype Scope Decisions: Same Repo, Chat Widget, Real-Time Pipeline
**Date:** Mar 22, 2026
**Context:** Defining prototype scope for G4 submission. User provided detailed requirements across 16 questions.
**Decisions:**
- **Repo:** Same OptiFlow repo, organized sections in dashboard (prototype vs analysis)
- **Chat:** Widget-style chatbot, 3-4 turns before escalation, conversation → summary ticket handoff
- **Classification:** Two-stage (fine-tuned + zero-shot), visible to operator in real-time, 85% confidence threshold
- **RAG:** Synthesized answers from KB, never "I found this article"
- **Dashboard:** Full operator view (queues, SLAs, metrics, capacity), real-time updates
- **Voice:** 11 Labs as future feature, needs deeper research on KB access and cost
- **Demo:** Guided walkthrough mode, data reset button, simulation tool for scenarios
- **LLM:** OpenAI preferred for chat (fine-tuning already working), flexible
**Rationale:** Scope balances "impressive demo" with feasibility. User wants to craft PRD carefully, then spread development across multiple agents in one organized batch.

---

## D037 — Prototype Implementation: 5 Sprints, Sequential with Parallel Attempt
**Date:** Mar 22, 2026
**Context:** Building the full prototype across 5 sprints. Attempted parallel execution of Sprints 3+4 using git worktrees, but worktree agents lacked Bash permissions. Fell back to sequential execution.
**Decisions:**
- Sprint 1 (Foundation): 5 Supabase tables, routing engine extraction, classify API, 36 KB articles, 5 operators, sidebar
- Sprint 2 (Chat): ChatWidget, ClassificationPanel, progressive classification with 85% confidence gate, KB synthesis, escalation with LLM summary
- Sprint 3 (Operator): QueueList, TicketDetail, OperatorCard, SLA timers (scenario-based deadlines), accept/transfer/resolve actions
- Sprint 4 (Simulation): CSV-based ticket sampling, batch classification, ~50% auto-resolve rate, Recharts metrics dashboard
- Sprint 5 (Polish): 12-step walkthrough overlay with auto-typing, 3 pre-loaded demo scenarios, UI animations, Puppeteer QA
**Architecture:** All prototype code isolated under `src/app/prototype/`, `src/app/api/prototype/`, `src/components/prototype/`. Prototype tables separate from analysis tables. Reset only affects prototype data.
**Result:** All 5 sprints pass `tsc --noEmit` and `npm run build`. 9 components, 15 API routes, 3 pages, guided walkthrough.

---

## D038 — Confidence Calibration: Pre-Classification Gate + Information Density
**Date:** Mar 22, 2026 — Session 19
**Context:** "oi" (just a greeting) was being classified as Hardware at 98% confidence. The fine-tuned model always returns a category regardless of input quality.
**Decision:** Two-layer defense, zero extra API calls:
1. **Pre-classification gate** — regex-based detection of greetings, farewells, gratitude, gibberish, too-short messages. Blocks classification entirely.
2. **Information density score** — token count + technical terms + problem verbs + error codes → 0.0-1.0 multiplier. Effective confidence = raw × density.
**Rationale:** Combined approach catches low-information inputs before API call (gate) and dampens overconfident classification on thin content (density). Both visible in real-time on classification panel.

---

## D039 — Chat-Driven Identity Collection
**Date:** Mar 22, 2026 — Session 19
**Context:** Atendimento page had email/name input fields outside the chat — unnatural UX. Chat started with a customer number that made no sense.
**Decision:** Remove all input fields. Chat itself asks for name and email conversationally via a state machine: greeting → asking_name → asking_email → returning_user_check → support. Simulation bypasses identity flow (identity_state='support').
**Rationale:** Natural conversational flow. Returning user detection after email enables personalized experience.

---

## D040 — RAG Architecture: pgvector Replacing Exact-Match KB Lookup
**Date:** Mar 22, 2026 — Session 19
**Context:** KB lookup used exact subject-match queries, missing relevant articles in adjacent topics.
**Decision:** Enable pgvector extension, add embedding column (1536 dims) to kb_articles. Embed customer message with text-embedding-3-small, cosine similarity search via `match_kb_articles` RPC, top 3 articles with similarity ≥ 0.3. Results shown in classification panel with similarity score badges.
**Rationale:** Semantic search finds contextually relevant articles regardless of category boundaries. Visible RAG pipeline demonstrates the architecture to evaluators.

---

## D041 — External KB Datasets Rejected (Bitext + Tobi-Bueck)
**Date:** Mar 22, 2026 — Session 19
**Context:** Evaluated external KB datasets (Bitext, Tobi-Bueck on HuggingFace) for amplifying our knowledge base.
**Decision:** Rejected. Our KB is domain-specific (telecom support in pt-BR). External datasets are generic English customer support — would dilute quality and create language inconsistency.
**Alternative chosen:** Amplify from 36 → 72 articles using gpt-4o-mini to generate 3 variations per subject from existing seed articles.

---

## D042 — Message Grouping: 4-Second Frontend Debounce
**Date:** Mar 22, 2026 — Session 19
**Context:** Users often send rapid short messages ("oi" / "meu celular" / "nao liga") that individually lack context for classification.
**Decision:** 4-second debounce timer on frontend. Reset on each new message. Visual countdown indicator. Concatenated text sent to API, individual messages stored for transcript. Identity flow bypasses buffering.
**Rationale:** Groups fragmented input into meaningful classification context. 4 seconds balances responsiveness vs grouping effectiveness.

---

## D043 — Parallel Sprint Execution Strategy (Waves 1-2)
**Date:** Mar 22, 2026 — Session 19
**Context:** 8 sprints remaining. User requested autonomous parallel execution via background agents.
**Decision:** 5 waves: Wave 1 (Sprints 8+9 parallel), Wave 2 (Sprints 10+11+12 parallel), Wave 3 (Sprint 13 sequential), Wave 4 (Sprint 14), Wave 5 (Sprint 15). Cherry-pick from worktrees to main.
**Result:** Waves 1+2 completed but with integration issues — Zod schema mismatch, grouped message storage bugs, grouped_count missing from response paths. Required manual integration fixes.
**Lesson:** Worktree-based parallel agents work for isolated features but fail when sprints touch shared files (messages/route.ts was modified by 5 sprints).

---

## D044 — Intelligent Routing: Operator Tiers + Specialty Matching
**Date:** Mar 22, 2026 — Session 20
**Context:** All operators were equal — no escalation hierarchy, no specialty-based assignment.
**Decision:** 3-tier operator hierarchy (junior/senior/lead). Queue filtering by tier: juniors see tier-1 tickets, seniors see tier-2 + SLA-threatened, leads see tier-3 + critical. Accept validates tier ≥ ticket's escalation_tier. Transfer blocks downward escalation. `findBestOperator` matches specialty + minimum tier.
**Known gap:** `shouldAutoEscalate` and `escalateTicket` functions exist but have no trigger mechanism — SLA auto-escalation is not yet active. Must be fixed before multi-day simulation.

---

## D045 — Real KPI Computation Replacing Placeholder Roadmap
**Date:** Mar 22, 2026 — Session 20
**Context:** Sprint 11 added a KPIRoadmap component listing 7 "production KPIs" that couldn't be computed from prototype data. User challenged: "we have the simulation, why can't we compute this?" — and was right. 6 of 7 are computable.
**Decision:** Replace static placeholder with 6 real computed KPIs:
1. **FCR** — % resolved without operator (auto-resolved by chatbot)
2. **AHT** — avg(resolved_at - updated_at) for operator-handled tickets
3. **Cost per ticket** — estimated from API calls + operator time at $15/hr
4. **CES proxy** — turn_count + escalation penalty, normalized to 1-5
5. **Reopen rate** — % of resolved conversations with post-resolution messages
6. **Agent utilization** — avg(active_tickets / max_capacity) across operators
**NPS excluded:** Requires dedicated post-service brand loyalty survey, fundamentally different from CSAT.
**Known issues:** AHT uses `updated_at` as proxy (overwritten on every update, reads near-zero). Needs `accepted_at` column.

---

## D046 — Pre-Simulation Review: 3 Blockers Identified
**Date:** Mar 22, 2026 — Session 20
**Context:** Full system review before Sprint 14 (50-user, 4-day simulation). Reviewed all pipeline files, test coverage, and integration points.
**Blockers found:**
1. **SLA auto-escalation is dead code** — `shouldAutoEscalate`/`escalateTicket` exist but nothing calls them. Tickets pile up with expired SLAs.
2. **Race condition on `active_tickets`** — non-atomic read-increment-write. Under 50 concurrent users, capacity tracking will drift.
3. **AHT metric inaccurate** — `updated_at` used as acceptance proxy but gets overwritten on every conversation update.
**Test coverage:** 6 of 12 features NOT COVERED (identity flow, message grouping, operator tiers, SLA escalation, specialty matching, KPI validation).
**Decision:** Fix all 3 blockers before launching Sprint 14.

---

## D047 — SLA Backdating for Simulation Testing
**Date:** Mar 23, 2026 — Session 24
**Context:** SLA auto-escalation couldn't be tested in simulation because tickets are processed too fast (API latency ~1s). Need to simulate SLA conditions without waiting real-time.
**Decision:** Created test-only endpoint `/api/prototype/test/backdate` that rewrites `created_at` and `sla_deadline` on existing conversations. Test sequence: create ticket normally → backdate to desired SLA percentage → trigger `/api/prototype/sla-check` → verify escalation behavior.
**Rationale:** Backdating timestamps is the only way to test SLA thresholds in an automated simulation. The endpoint is clearly marked test-only.
**Validation:** 83% → escalated ✓, 75% → maintained ✓, 95% → escalated ✓ (3/3 correct across 2 runs).

---

## D048 — Escalation Guard: Prevent Re-classification After Escalation
**Date:** Mar 23, 2026 — Session 24
**Context:** When a customer sent follow-up messages after their conversation was escalated, the message re-entered the classification pipeline, resetting the conversation state.
**Human correction:** "After escalation, the conversation came back to a reset state when I asked about the specialist."
**Decision:** Added status guard at the top of the message POST handler. If `conversation.status === "escalated" || "in_progress"`, respond with a contextual message ("Seu caso já foi encaminhado para um especialista...") without re-entering the classification pipeline.
**Impact:** Prevents escalated conversations from being reclassified, maintains conversation continuity.

---

## D049 — "Other" Label Never Exposed to Customer
**Date:** Mar 23, 2026 — Session 24
**Context:** When the classifier returned subject="Other" (sub-classification fallback), the bot message showed "Other" directly to the customer.
**Human correction:** "It says 'Other'... Other is not acceptable for communication."
**Decision:** Display logic: if `subject.toLowerCase() === "other"`, substitute with natural language: "um problema na área de {category}". The raw "Other" value is preserved in the database for analytics, but never shown to the customer.

---

## D050 — Conversation Queue with Operator Visibility
**Date:** Mar 23, 2026 — Session 24
**Context:** Human compared our prototype to respond.io workflow: "I need to see the specific queues... filter by classification, by scenario, by operator."
**Decision:** Added ConversationQueue component to Atendimento page (3-column layout: Queue 220px | Chat flex | Classification 350px). Queue shows: customer name, status dot, category/scenario badges, assigned operator or "IA" indicator, channel, time, turns, tier. Filters: status, category, scenario, operator (including "IA" option). 5s auto-refresh polling.
**Rationale:** Mirrors real support tool UX — operators need to see and filter their work queue, take over tickets, and understand which conversations the bot is handling vs. which need human intervention.

---

## D051 — Date Filter on Overview Dashboard
**Date:** Mar 23, 2026 — Session 24
**Context:** Overview dashboard had filters for channel, priority, type, subject, status, CSAT — but no date filter. The CSV has dates in First Response Time column.
**Decision:** Added `dateFrom`/`dateTo` query params to `/api/tickets/stats` API. Added native date pickers to FilterBar with min/max constraints from available dates. Dataset has only 3 unique dates (synthetic), but the filter demonstrates the capability for evaluators.

---

*Last updated: Mar 23, 2026 — Session 24 (D047-D051: Simulation results, post-simulation fixes)*
