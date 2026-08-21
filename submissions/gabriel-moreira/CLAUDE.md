# Claude.md — Lead Scorer Challenge (003)

**Project:** AI Master Challenge — Build a sales pipeline prioritizer.

**Owner:** Gabriel Moreira

**Date:** 2026-08-19 (formula revised same day — see decisions-log.md); RBAC removed 2026-08-20; SCORE/CONFIANÇA/ESTADO redesigned 2026-08-20 (same day, second pass — see decisions-log.md); `score_fatores` + ESTÁGIO in listing added 2026-08-20 (same day, third pass)

---

## The problem

Sales team of 35 people, 8.800 open opportunities (~60 per person, but highly skewed). No prioritization logic — each rep guesses. RevOps Head: "Vendedor abre a ferramenta, vê o pipeline, sabe onde focar."

Budget: 4–6 hours. Deliverable must **run**. Explainability wins.

---

## The data finding (critical)

**8.800 deals closed (2016–2017), analyzed:**

- **Firmographic attributes: no signal.** AUC ≈ 0.50 on holdout. Permutation tests on agent/product/sector/account: p between 0.26–0.98 — all noise. Confirmed a second way: the hierarchical shrinkage levels account×product and product×sector have zero excess variance and collapse to weight zero automatically (`k = ∞`).
- **Value: strong signal.** Product alone explains 98.3% of closed-value variance. Products range $55–$26,768 (487×).
- **Conclusion:** don't build a categorical win-probability classifier. Build a **priority-in-dollars** score: `PRIORIDADE = p̂ × VALOR × URGÊNCIA`, where `p̂` barely moves (0.60–0.75) and the real differentiation comes from value and timing.

This is still the entire design decision tree — the formula got more rigorous, the conclusion didn't change.

---

## Solution shape

**2.089 open deals, every one scoreable — including the 1.425 without an account and the 500 in Prospecting.**

**Formula (revised 2026-08-19, see decisions-log.md for the full reasoning):**

```
p̂ = (n_produto × taxa_produto + k × 0,632) / (n_produto + k)     ← hierarchical shrinkage, k derived not chosen

  se Prospecting:  p̂ = p̂_produto (no age adjustment)
  se idade > 138:   p̂ = 0,632                                     ← censoring: revert to prior, never extrapolate
  senão:            p̂ = p̂_produto × p_ganho(min(idade,120)) / 0,632

VALOR = preço_tabela(produto) × mult_porte(porte, default 1,00)   ← default 1.00 makes no-account scoreable

  se Prospecting:  URGÊNCIA = 0,47
  se idade > 138:   URGÊNCIA = 0,15
  senão:            URGÊNCIA = risco_isotônico(min(idade,120))    ← P(resolves in 30 days), isotonic-smoothed

PRIORIDADE = p̂ × VALOR × URGÊNCIA                                  ← in dollars, "value at stake right now"
SCORE      = percentil(PRIORIDADE) × 100                           ← percentile against historical WON deals, not the open funnel
```

**SCORE's reference population is the 4,238 historically won deals** (PRIORIDADE computed for each using its real age-at-close), not the current open funnel. That population is fixed/historical — it only updates on the quarterly recalibration cycle. So SCORE = 82 literally means "this opportunity is worth more, at stake right now, than 82% of deals that historically became revenue" — and unlike a percentile against the open funnel, it never moves because some other deal entered or left the pipeline.

**Redesigned 2026-08-20 (second pass, same day as the RBAC removal): PRIORIDADE in dollars is no longer displayed or used to sort the queue.** The variance decomposition of `log(PRIORIDADE)` attributes 87.3% to VALOR and 0.1% to `p̂` — sorting by it was, in practice, sorting by table price (products range 486.7× vs. `p̂_produto`'s 1.074×). **SCORE (0-100) is now the only priority number exposed** — in the UI, as the API's default sort, and as ESTADO's input. PRIORIDADE stays calculated and CSV-exported as an auditable intermediate value. See the CONFIANÇA/ESTADO redesign below and `docs/decisions-log.md` (2026-08-20 entry) for the full reasoning, including three refinement hypotheses that were tested and rejected: conditioning `p̂` on product×sector, per-product aging curves, and per-product URGÊNCIA — all three made out-of-sample prediction *worse* (5-fold cross-validation, reproducible in `validation/backtest.py` sections 6-8).

**Counter-intuitive finding baked into the formula:** `p_ganho(t)` **rises** with age (0.632 at day 0 → 0.751 at day 120) — it does not decay. What age consumes is the **window**: by day 57, half of all historical wins have already happened; by day 88, only 25% remain. That's why URGÊNCIA uses `risco(t)` (P of resolving in 30 days, isotonic-smoothed) instead of an age-decay proxy.

**Censoring:** nothing in the 6.711 closed deals took more than 138 days. Above that, revert to the prior instead of extrapolating — forward-filling would give `p̂ = 0.751` (the curve's highest value) to a 377-day-old deal, rewarding abandonment.

**CONFIANÇA (0-100, redesigned 2026-08-20)** — separate from SCORE, never combined into one number: how much of what the score claims rests on observed data and historical precedent, not how much is known "about the deal" loosely. `CONFIANÇA = min(completude, suporte)`:

- **completude** — % of 5 registration fields observed (`engage_date`, account, employees, sector, assigned team) vs. defaulted to a prior.
- **suporte** — how much history backs the numbers actually used: `0.75 × s_idade + 0.25 × s_produto`, each saturating at `min(1, n/50)`. Without a known age (Prospecting), only the product term is used — the missing `engage_date` is already charged once in completude and can't be charged twice.
- `min`, not average: knowing every field about a deal with no historical precedent doesn't make it trustworthy.
- **Age dropped out of CONFIANÇA entirely.** The original A–D scale used age>138 days as level D, which then force-routed 61.8% of the funnel to "give up" — confusing CONFIANÇA (how much is known) with URGÊNCIA (how stale is it). Age now only enters through the density of historical precedent in `suporte`.
- **`sem_precedente` marker** (`s_idade == 0` with known age) is what routes ESTADO to batch review — never a cutoff on the combined CONFIANÇA number, because fresh-but-unregistered deals and old-but-unprecedented deals cluster at adjacent CONFIANÇA values (20 and 25) in *inverted* order; no single threshold separates the two populations.

**ESTADO** — 4 values (down from 5), a decision tree instead of a 4×2 table:

```
1. sem_precedente        -> Revisão em lote
2. SCORE >= 95            -> Priorizar
3. CONFIANÇA < 50          -> Qualificar
4. otherwise               -> Acompanhar
```

`Qualificar` absorbs the old `Engajar` — the two states converged on the same action ("keep following up" / "go get information"), and the distinction that would separate them (missing information vs. missing maturity) is exactly what the completude half already measures as an exposed number, not a state. `Desistir` becomes `Revisão em lote`: same population (no historical precedent), but explicitly named as a data-hygiene backlog routed *out* of the ranked queue — not a per-deal recommendation to give up, which is what "Desistir" implied and what made 61.8%+ of the funnel read as "abandon this."

Distribution on the current funnel (2,089 open deals): `Priorizar` 54, `Acompanhar` 283, `Qualificar` 656, `Revisão em lote` 1,096 (workable queue: 993). `Revisão em lote`'s minimum age is 154 days — genuinely past the 138-day historical boundary, never containing a Prospecting deal (unknown age is never read as "no precedent").

Each opportunity gets a deterministic-template explanation + action plan, not just a number. The CONFIANÇA reason names which half (completude or suporte) governed the minimum and, when it's completude, which specific fields are missing. The detail panel's "Por que este score" section also shows `score_fatores` — 4 template-generated, jargon-free sentences that decompose `p̂`/VALOR/URGÊNCIA and the account porte effect into plain business language (e.g. "Dados da conta indicam porte Enterprise — isso eleva o valor considerado"), including the counter-intuitive aging finding when it applies. Same auditability guarantee as the action plan — never an LLM summary. Detail-only, same as `plano_de_acao_passos` and `prioridade`. ESTÁGIO (`deal_stage`) is now also a listing column, not detail-only.

**Access control:** none. Removed 2026-08-20 (see decisions-log.md) — every data endpoint is open, no `Authorization` header. Sales agent, manager and regional office (the real hierarchy in `sales_teams.csv`: 35 `sales_agent` → 6 `manager` → 3 `regional_office`) are ordinary filters over the whole funnel, not identities with scope. Acceptable only because the dataset is public demo data with no real customer information; documented as an assumed limitation, not hidden.

**CSV export:** every data load writes a full processed dataset (all 2,089 open opportunities + every derived field, including PRIORIDADE as an auditable value even though it is not displayed) to disk for offline consultation. Separate from the "export filtered IDs" mechanism, which also drives the Revisão em lote view's batch export.

**Validation:** standalone Python script (9 sections) runs on the 6,711 closed deals — permutation tests, reproduces the `k` derivation and the account×product/product×sector/product collapse, checks `risco(t)` monotonicity, confirms no closed deal exceeds 138 days, reports PRIORIDADE concentration (top 10% ≈ 49% of total), and 5-fold cross-validates three rejected refinements (product×sector conditioning, per-product aging, per-product URGÊNCIA) plus the CONFIANÇA/completude/suporte distribution.

---

## Stack

- **Backend:** FastAPI, Python 3.10+, no authentication
- **Frontend:** React 18+, TypeScript
- **Data:** Pandas in-memory, behind a clean repository module
- **Scoring:** Pure Python package in `scoring/`, imported by API, export, and validation script
- **No authentication at all** (documented limitation) — every endpoint is open; sales agent/manager/office are plain filters
- **Theme:** G4 Business palette (navy #001F35, gold #B9915B, light bg #FAFBFC, alert #AF4332 exclusive to Revisão em lote)

**Testing (part of Definition of Done, not optional):**
- Unit: scoring engine (shrinkage incl. `k=∞` collapse, aging curves, censoring, CONFIANÇA branches, ESTADO assignment, explanation generation, action-plan steps)
- API: contract tests for pagination (page union has no dup/gap, sort over the whole slice, stable tie-break), deal detail, filter options, filtered-id export — none of it gated behind identification

---

## Files and their roles

**Key decision documents:**
- [`docs/decisions-log.md`](docs/decisions-log.md) — all decisions and the reasoning, including the 2026-08-19 formula revision. See this first.
- [`docs/architecture.md`](docs/architecture.md) — technical blueprint, data flow, component layout.
- [`analise-lead-scoring.md`](analise-lead-scoring.md) — full statistical analysis. Answers "why is AUC 0.50?" with evidence.
- [`../../openspec/changes/add-lead-scorer/`](../../openspec/changes/add-lead-scorer/) — formal proposal/design/specs; source of truth for exact requirement wording.

**Submission structure:**
- `solution/` — code (will have `scoring/`, `api/`, `web/`, `validation/`)
- `process-log/` — chat exports and screenshots showing Claude Code usage
- `data/` — CSVs (accounts, products, sales_pipeline, sales_teams, metadata)

---

## Decisions

**Design decisions made via grilling session (32 questions) + a 2026-08-19 formula revision pass. Full reasoning in `docs/decisions-log.md`.**

Still holding from the original session:
1. Score on value/timing, not a win-probability classifier — AUC evidence killed the predictive path
2. Rank open deals (not score new leads) — 2.089 open is the real problem
3. Product coverage as account potential, not deal signal — 39.6% effort on 5.4% revenue
4. FastAPI + React (not Streamlit) — a clean API/UI split, needed regardless of auth
5. Validate with permutation tests, ship the evidence

**Revised 2026-08-19 (reversing earlier calls, with the new evidence that justified it):**
- `MULT_PORTE` is **back in** VALOR — variance decomposition shows product+porte explains 98.7% vs. 98.3% product-alone, a real 0.4pp gain I hadn't measured before. Default 1.00 when account unknown is what makes "score even without account" literal.
- Percentile normalization is **back** for the display SCORE — matching the new spec's `SCORE = percentil(PRIORIDADE) × 100` — but against the fixed historical population of won deals, not the live open funnel. That's strictly more stable than the original percentile-scoring rejection was worried about: the reference never depends on what's currently in the pipeline.
- Tiers (Diamante/Ouro/Prata/Bronze) + lanes (Prioridades/Novos/Zumbis) collapsed into 5 ESTADO values on 2026-08-19 — a 4×2 decision table crossing CONFIANÇA (A-D) with SCORE (≥50 or not). **Redesigned again 2026-08-20**: CONFIANÇA became a 0-100 `min(completude, suporte)` measurement (age dropped out entirely), and the 4×2 table became a 4-value decision tree — see the CONFIANÇA/ESTADO section above.
- Auth is no longer fully out of scope — identity-based RBAC with server-enforced isolation is now required (still no password). **Reversed 2026-08-20** — the RBAC built here was removed entirely (deletion, not a feature flag); see the 2026-08-20 entry in `decisions-log.md` for why.

Still true / unchanged:
- Win-rate by agent/product/sector: no signal (confirmed twice now — permutation tests AND the hierarchical `k=∞` collapse).
- Smooth exponential decay on age: still wrong, and now more clearly wrong — `p_ganho(t)` actually *rises* with age, doesn't just plateau.

---

## Known limitations and evolution path

**Doesn't do:**
- Categorical win-probability forecasting (`p̂` varies only 0.60–0.75; real differentiation is value+timing).
- Any authentication or authorization — every endpoint is open, not even the identity-selection scoping from the earlier design. Not SSO, not RBAC.
- Behavioral intent (no email opens, call logs, page visits).
- Automatic portfolio rebalancing — insight surfaces in Gestão, policy stays off-system.
- Real persistence. All in-memory; CSV export is the closest thing to a durable artifact.
- Write-back to CRM.

**Evolution (MVP → production):**
1. **Database** (Supabase) + auto-score + auto-regenerate the processed CSV on new deal
2. **Real auth** (SSO/OIDC) plus server-enforced scope over sales agent/manager/office, both absent today
3. **Behavioral signal** (CRM webhook + speed-to-lead model) to recalibrate `p̂`
4. **A/B test:** half the reps on score, half on gut; track revenue
5. **Mobile** (React Native)

---

## To run the solution

```bash
# Backend
cd solution/api
pip install -r requirements.txt
python -m uvicorn main:app --reload

# Frontend (another terminal)
cd solution/web
npm install && npm run dev

# Validation
cd solution/validation
python backtest.py

# Tests
cd solution/scoring && pytest            # unit
cd solution/api && pytest                # contract/pagination/e2e — no auth to exercise
```

Or via Docker:
```bash
docker compose up
```

---

## For the next person

- **Start here:** [`decisions-log.md`](docs/decisions-log.md), especially the 2026-08-19 entry — it explains every reversal from the earlier design.
- **Then:** [`architecture.md`](docs/architecture.md) for the implementation blueprint.
- **Then:** [`analise-lead-scoring.md`](analise-lead-scoring.md) for the evidence behind every number.
- **Code:** `scoring/` is the core; `api/`, `web/`, `validation/`, and the CSV export are all consumers. Keep that separation — it's what makes "the number shown = the number validated = the number exported" true.
- **Watch for:** PRIORIDADE is deterministic and auditable; SCORE (the percentile) is only stable between dataset generations, not between requests — that distinction is load-bearing, don't collapse it back into a single always-live percentile.
- **No auth:** every endpoint is open by design (see the 2026-08-20 decisions-log entry). If you're extending an endpoint, don't reintroduce a scope check — sales agent/manager/office stay plain filters, same as product.

---

## Questions?

- **Why not ML?** AUC ≈ 0.50 on the best available attributes. Permutation tests and the hierarchical `k=∞` collapse both say the same thing two different ways.
- **Why does age *raise* `p̂` instead of lowering it?** That's what the data shows (`p_ganho(0)=0.632` → `p_ganho(120)=0.751`). What age actually costs is the decision window (`janela(t)`), which is what URGÊNCIA tracks.
- **Why revert to the prior above 138 days instead of extrapolating?** Forward-filling would reward the most abandoned deal in the funnel with the curve's highest score. No closed deal in the data ever took that long — there's no precedent to extrapolate from.
- **Why 4 estados (Priorizar/Acompanhar/Qualificar/Revisão em lote) instead of tiers or the original 5?** They aren't a relabeling — ESTADO is a decision tree over SCORE and CONFIANÇA, not a lookup table. CONFIANÇA answers "how much should I trust this number"; ESTADO answers "what do I do about it." The original 5-value table crossed CONFIANÇA (A-D, driven mostly by age) with SCORE, which meant a single rule — CONFIANÇA D — force-routed 61.8% of the funnel to "give up." The redesign separates measurement (CONFIANÇA, now completude/suporte) from routing (a named `sem_precedente` condition checked first in the tree), and merges `Engajar` into `Acompanhar` because they gave the same advice.
- **Why no login at all?** The dataset is public demo data, no real customer information — so the friction of an identity gate cost more than the isolation demo was worth. An earlier version of this solution did have identity-based RBAC with server-enforced scope; it was removed by deletion, not a flag, on 2026-08-20 (see decisions-log.md). Documented explicitly as a limitation, not hidden.
