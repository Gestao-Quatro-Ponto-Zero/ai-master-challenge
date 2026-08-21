# Claude.md — Lead Scorer Challenge (003)

**Project:** AI Master Challenge — Build a sales pipeline prioritizer.

**Owner:** Gabriel Moreira

**Date:** 2026-08-19 (formula revised same day — see decisions-log.md); RBAC removed 2026-08-20; SCORE/CONFIANÇA/ESTADO redesigned 2026-08-20 (same day, second pass — see decisions-log.md); `score_fatores` + ESTÁGIO in listing added 2026-08-20 (same day, third pass); 200-day reclassification + workload/fit analysis added 2026-08-21 (see decisions-log.md); `mult_setor` (product×sector adjustment) + `K_PRODUTO` removal added 2026-08-21 (same day, second pass — see decisions-log.md)

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

**1.436 open deals, every one scoreable — including the 987 without an account and the 500 in Prospecting.** (Was 2.089 before 2026-08-21: 653 opportunities open ≥200 days were reclassified to `Lost` — see "200-day reclassification" below.)

**Formula (revised 2026-08-19, see decisions-log.md for the full reasoning):**

```
p̂_produto = (n_produto × taxa_produto + k × 0,5755) / (n_produto + k)    ← hierarchical shrinkage, k DERIVED from the data (k≈0,6966 in this calibration, not a frozen K_PRODUTO constant — see decisions-log.md 2026-08-21)

  se Prospecting:  p̂(idade) = p̂_produto (no age adjustment)
  se idade > 138:   p̂(idade) = 0,632                                     ← censoring: revert to the ORGANIC prior (curves never see reclassified deals), never extrapolate
  senão:            p̂(idade) = p̂_produto × p_ganho(min(idade,120)) / 0,632

p̂ = p̂(idade) × mult_setor(produto, setor)                          ← ±15% product×sector performance adjustment (K_SETOR=25, policy constant), neutral (1,0) when sector unknown — see "mult_setor" below

VALOR = preço_tabela(produto) × mult_porte(porte, default 1,00)   ← default 1.00 makes no-account scoreable

  se Prospecting:  URGÊNCIA = 0,47
  se idade > 138:   URGÊNCIA = 0,15
  senão:            URGÊNCIA = risco_isotônico(min(idade,120))    ← P(resolves in 30 days), isotonic-smoothed

PRIORIDADE = p̂ × VALOR × URGÊNCIA                                  ← in dollars, "value at stake right now"
SCORE      = percentil(PRIORIDADE) × 100                           ← percentile against historical WON deals, not the open funnel
```

**SCORE's reference population is the 4,238 historically won deals** (PRIORIDADE computed for each using its real age-at-close), not the current open funnel. That population is fixed/historical — it only updates on the quarterly recalibration cycle. So SCORE = 82 literally means "this opportunity is worth more, at stake right now, than 82% of deals that historically became revenue" — and unlike a percentile against the open funnel, it never moves because some other deal entered or left the pipeline.

**Redesigned 2026-08-20 (second pass, same day as the RBAC removal): PRIORIDADE in dollars is no longer displayed or used to sort the queue.** The variance decomposition of `log(PRIORIDADE)` attributed 87.3% to VALOR and 0.1% to `p̂` in that calibration — sorting by it was, in practice, sorting by table price (products range 486.7× vs. `p̂_produto`'s old 1.074×). Note: the 2026-08-21 recalibration widened `p̂_produto`'s range considerably (GTK 500 alone moved ~17pp) — this decomposition has not been rerun since, and the exact split is due for a refresh at the next quarterly recalibration; VALOR still dominates by a wide margin regardless. **SCORE (0-100) is now the only priority number exposed** — in the UI, as the API's default sort, and as ESTADO's input. PRIORIDADE stays calculated and CSV-exported as an auditable intermediate value. See the CONFIANÇA/ESTADO redesign below and `docs/decisions-log.md` (2026-08-20 entry) for the full reasoning, including three refinement hypotheses that were tested and rejected: conditioning `p̂` on product×sector, per-product aging curves, and per-product URGÊNCIA — all three made out-of-sample prediction *worse* (5-fold cross-validation, reproducible in `validation/backtest.py` section 6). **Unlike the other two, the first of these three was implemented anyway, in a distinct and heavily-constrained form** — see "mult_setor" below and the 2026-08-21 decisions-log entry: direct product×sector conditioning (`logloss` 0,66974 vs. 0,66795 for the flat product prior, 70 cells, median 86 deals) is still confirmed worse every run, but `mult_setor` is a different mechanism — shrunk toward `p̂_produto` (not the global rate) with `K_SETOR=25` and capped at ±15% — applied by product decision despite that negative result, not because it stopped being true.

**Counter-intuitive finding baked into the formula:** `p_ganho(t)` **rises** with age (0.632 at day 0 → 0.751 at day 120) — it does not decay. What age consumes is the **window**: by day 57, half of all historical wins have already happened; by day 88, only 25% remain. That's why URGÊNCIA uses `risco(t)` (P of resolving in 30 days, isotonic-smoothed) instead of an age-decay proxy.

**Censoring:** nothing in the 6.711 closed deals took more than 138 days. Above that, revert to the prior instead of extrapolating — forward-filling would give `p̂ = 0.751` (the curve's highest value) to a 377-day-old deal, rewarding abandonment.

**CONFIANÇA (0-100, redesigned 2026-08-20)** — separate from SCORE, never combined into one number: how much of what the score claims rests on observed data and historical precedent, not how much is known "about the deal" loosely. `CONFIANÇA = min(completude, suporte)`:

- **completude** — % of 5 registration fields observed (`engage_date`, account, employees, sector, assigned team) vs. defaulted to a prior.
- **suporte** — how much history backs the numbers actually used, from three terms, each saturating at `min(1, n/50)`: `s_idade` (deals near this age), `s_produto` (deals of this product), and `s_célula` (deals in this exact product×sector cell, added 2026-08-21 alongside `mult_setor`). `suporte = 100 × Σ(peso_i × termo_i) / Σ(peso_i)` over the *present* terms, weights `0,65 idade / 0,20 produto / 0,15 célula`. Without a known age (Prospecting) or a known sector, the corresponding term is OMITTED — never zeroed — and the remaining weights renormalize: with only age missing, weights become 0,20/0,15 (produto/célula); with only sector missing, 0,65/0,20 (idade/produto, same ratio as before 2026-08-21); with both missing, only `s_produto` remains. The missing input is already charged once in completude and can't be charged twice.
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

Distribution on the current funnel (1,436 open deals): `Priorizar` 54, `Acompanhar` 283, `Qualificar` 656, `Revisão em lote` 443 (workable queue: 993 — unchanged, because all 653 reclassified deals were already ≥200 days old and therefore already inside `Revisão em lote` before reclassification removed them from the open funnel entirely). `Revisão em lote`'s age range is now 154–199 days — the ≥200-day tail moved to `Lost` — never containing a Prospecting deal (unknown age is never read as "no precedent").

Each opportunity gets a deterministic-template explanation + action plan, not just a number. The CONFIANÇA reason names which half (completude or suporte) governed the minimum and, when it's completude, which specific fields are missing. The detail panel's "Por que este score" section also shows `score_fatores` — 4 template-generated, jargon-free sentences that decompose `p̂`/VALOR/URGÊNCIA and the account porte effect into plain business language (e.g. "Dados da conta indicam porte Enterprise — isso eleva o valor considerado"), including the counter-intuitive aging finding when it applies, plus a 5th sentence when the sector is known (added 2026-08-21) naming the `mult_setor` direction (above/within/below the product's average) and the cell's sample size — omitted entirely, not hedged, when the sector is unknown. Same auditability guarantee as the action plan — never an LLM summary. Detail-only, same as `plano_de_acao_passos` and `prioridade`. ESTÁGIO (`deal_stage`) is now also a listing column, not detail-only.

**Access control:** none. Removed 2026-08-20 (see decisions-log.md) — every data endpoint is open, no `Authorization` header. Sales agent, manager and regional office (the real hierarchy in `sales_teams.csv`: 35 `sales_agent` → 6 `manager` → 3 `regional_office`) are ordinary filters over the whole funnel, not identities with scope. Acceptable only because the dataset is public demo data with no real customer information; documented as an assumed limitation, not hidden.

**CSV export:** every data load writes a full processed dataset (all 1,436 open opportunities + every derived field, including PRIORIDADE as an auditable value even though it is not displayed) to disk for offline consultation. Separate from the "export filtered IDs" mechanism, which also drives the Revisão em lote view's batch export. The same load also (re)writes `analysis_by_product_detailed.csv` and `analysis_by_sector_detailed.csv` (vendor×product / vendor×setor win rate, `Won / (Won + Lost)`) from the identical code path the API uses — see "200-day reclassification" below for why the earlier hand-built versions of those two files were wrong.

**Validation:** standalone Python script (13 sections) runs on the closed deals — permutation tests, reproduces the `k` derivation for all four hierarchy levels (product no longer uses a frozen constant, see below) and the account×product/product×sector collapse, checks `risco(t)` monotonicity, confirms no organically-closed deal exceeds 138 days, reports PRIORIDADE concentration, 5-fold cross-validates three rejected refinements (product×sector conditioning — still negative every run, now a permanent warning instead of a gate, see "mult_setor" below — per-product aging, per-product URGÊNCIA) plus a direct reproduction of `mult_setor` itself (clip behavior, small-vs-large-cell shrinkage, funnel/reference consistency), the CONFIANÇA/completude/suporte distribution, the before/after impact of the 200-day reclassification, the 138-day circularity audit, the vendor-fit permutation test, and the analysis-CSV denominator audit.

### 200-day reclassification + workload/fit analysis (added 2026-08-21)

**Data hygiene finding:** 653 open opportunities (31.3% of the old 2,089-deal funnel) had been sitting in `Engaging` for ≥200 days, while the oldest *organically closed* deal ever took 138 days. Counting those 653 as live workload inflated whoever owned them and made any carteira-vs-carteira comparison meaningless. They are now reclassified to `Lost` at load time, in memory (`scoring/repository.py`) — the raw `sales_pipeline.csv` is never touched.

**Two calibration populations, not one** (`scoring/pipeline.py`): `fechados_organicos` (6,711, unchanged) feeds the age curves (`p_ganho`, `risco`) and the 138-day censoring boundary — age is the input there, so the 653 age-based reclassifications can never enter it without circularity. `fechados_calibracao` (7,364 = 6,711 + 653) feeds the per-product win rate and `p̂`'s global shrinkage prior — those don't take age as input, so learning from the reclassified deals there is legitimate. Consequence: base rate `0.632` (`GLOBAL_WIN_RATE_ORGANICO`, used for censoring) and `0.5755` (`GLOBAL_WIN_RATE_CALIBRACAO`, the new p̂-shrinkage prior) are now two different constants, not one. Funnel: 2,089 → 1,436 open. Base rate: 63.15% → 57.55%. **BREAKING** — p̂_produto, PRIORIDADE and SCORE all shifted; the backtest was regenerated in full.

**Honest surprise:** the product-level shrinkage (`K_PRODUTO = 4.0`, frozen by policy at the time) was previously believed to collapse (`k=∞`) under strict recomputation, same as account×product/product×sector. It no longer does — `GTK 500` alone swings from 60.0% (n=25) to 42.86% (n=35), and a fresh derivation now gives `k≈0.6966` (finite). **Resolved 2026-08-21, same day as `mult_setor` (below): `K_PRODUTO` is removed entirely.** The product level now calls the same `shrinkage.level_stats` derivation the other three levels already used, at load time (`pipeline.build_scoring_context`) — no frozen constant left to go stale. `p̂_produto` moves by ≤0.01pp for the six higher-volume products and by −1.22pp for `GTK 500` (n=35, the lowest-volume product) versus the old frozen value. `validation/backtest.py` section 3 now reports the derived `k` for all levels every run instead of comparing against a constant that no longer exists.

**mult_setor (added 2026-08-21):** product asked for a product×sector performance signal in `p̂`, capped at 10-15%, despite `validation/backtest.py` section 6 confirming — before and after this change — that conditioning `p̂` directly on product×sector is worse than not conditioning (`logloss` 0,66974 vs. 0,66795 for the flat product prior; 70 cells, median 86 deals; the level collapses, `k=∞`, under strict recomputation). The compromise, matching the pattern already used for vendor fit (`scoring/fit.py`, `K_FIT=25`): `mult_setor(produto, setor)` shrinks each cell's raw win rate toward `p̂_produto` (not the global rate) with a policy constant `K_SETOR=25` (reused from `K_FIT`, same role), then clips to `[0,85, 1,15]`. Unknown sector (68.7% of the open funnel) → `mult_setor=1,0`, neutral. `p̂ = p̂(idade) × mult_setor`, applied identically to the open funnel and to the Won reference population (asymmetric application would skew SCORE's numerator against an unadjusted denominator). Measured on the real funnel: SCORE shifts median 0,30pp / max 4,4pp, CONFIANÇA shifts median 0,00 / max 12,6 — **zero** opportunities cross either the SCORE≥95 or CONFIANÇA<50 cut, and the ESTADO distribution is unchanged (54/283/656/443). Side effect: the Won reference population's median PRIORIDADE rises 6,75% (351,52 → 375,26) — a structural artifact (higher-win-rate cells contribute proportionally more Won rows to the very population the multiplier is measured against), not a market change; accepted rather than corrected because PRIORIDADE in dollars isn't displayed and the effect on SCORE ordering is already measured as negligible. `validation/backtest.py` section 6 no longer fails the suite if the negative cross-validation result were to reverse — it's a permanent printed warning now, not a gate, so the decision to proceed despite the result stays visible every run instead of silently blocking it.

**Workload (`scoring/carga.py`):** for each (vendor, ESTADO) pair — `revisao_lote` excluded — compares the vendor's open count against their own regional office's average in that ESTADO. Overloaded = `count ≥ 1.5× office average` **and** `count ≥ 5` (the floor kills false alarms in low-average states). Currently: 12 overloaded pairs, 8 vendors, 227 opportunities.

**Fit (`scoring/fit.py`):** vendor's historical win rate by product and by sector, over `fechados_calibracao` only (`Won + Lost` denominator), two-level shrinkage (vendor → office → global, `K_FIT = 25`, frozen by policy). A permutation test that shuffles vendor labels while holding product/sector fixed per row finds vendor×sector indistinguishable from chance (p≈0.20) but vendor×product borderline (p≈0.047 across 178 uncorrected cells) — weak, not robust evidence of real vendor skill. Every fit number ships with its supporting sample size and a statistical caveat glued to it in the same UI section; fit never enters `p̂`, VALOR, URGÊNCIA, PRIORIDADE, SCORE, CONFIANÇA or ESTADO.

**Redistribution suggestion:** for an overloaded vendor's deal, rank same-office non-overloaded colleagues with history (`rank = 0.5×slack + 0.5×normalized_fit`) and surface the top one. Informative only — nothing is reassigned, and the suggested vendor is shown **only** in the Sobrecarga tab and the detail panel, never in the general Oportunidades listing (which gets just a boolean flag, gold `#B9915B`, distinct from `revisao_lote`'s alert red).

---

## Stack

- **Backend:** FastAPI, Python 3.10+, no authentication
- **Frontend:** React 18+, TypeScript
- **Data:** Pandas in-memory, behind a clean repository module
- **Scoring:** Pure Python package in `scoring/`, imported by API, export, and validation script
- **No authentication at all** (documented limitation) — every endpoint is open; sales agent/manager/office are plain filters
- **Theme:** G4 Business palette (navy #001F35, gold #B9915B, light bg #FAFBFC, alert #AF4332 exclusive to Revisão em lote)

**Testing (part of Definition of Done, not optional):**
- Unit: scoring engine (shrinkage incl. `k=∞` collapse, aging curves, censoring, CONFIANÇA branches, ESTADO assignment, explanation generation, action-plan steps, workload detection, fit shrinkage, redistribution ranking)
- API: contract tests for pagination (page union has no dup/gap, sort over the whole slice, stable tie-break), deal detail, filter options, filtered-id export, carga/sobrecarga endpoints — none of it gated behind identification

---

## Files and their roles

**Key decision documents:**
- [`docs/decisions-log.md`](docs/decisions-log.md) — all decisions and the reasoning, including the 2026-08-19 formula revision and the 2026-08-21 reclassification/workload/fit entry. See this first.
- [`docs/architecture.md`](docs/architecture.md) — technical blueprint, data flow, component layout.
- [`analise-lead-scoring.md`](analise-lead-scoring.md) — full statistical analysis. Answers "why is AUC 0.50?" with evidence, plus the 2026-08-21 reclassification numbers and the analysis-CSV audit.
- [`../../openspec/changes/add-lead-scorer/`](../../openspec/changes/add-lead-scorer/) — formal proposal/design/specs for the original scoring engine.
- [`../../openspec/changes/add-analise-carga-fit/`](../../openspec/changes/add-analise-carga-fit/) — formal proposal/design/specs for the 200-day reclassification, workload analysis and fit.
- [`../../openspec/changes/add-mult-setor/`](../../openspec/changes/add-mult-setor/) — formal proposal/design/specs for `mult_setor` and the `K_PRODUTO` removal.

**Submission structure:**
- `solution/` — code: `scoring/` (core, now includes `carga.py` and `fit.py`), `api/` (now includes `routes/carga.py`), `web/` (now includes `SobrecargaView.tsx`), `validation/`
- `process-log/` — chat exports and screenshots showing Claude Code usage
- `data/` — CSVs (accounts, products, sales_pipeline, sales_teams, metadata)

---

## Decisions

**Design decisions made via grilling session (32 questions) + a 2026-08-19 formula revision pass. Full reasoning in `docs/decisions-log.md`.**

Still holding from the original session:
1. Score on value/timing, not a win-probability classifier — AUC evidence killed the predictive path
2. Rank open deals (not score new leads) — 1.436 open (2.089 before the 2026-08-21 reclassification) is the real problem
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
