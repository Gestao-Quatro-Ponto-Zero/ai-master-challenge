# Process Log — AI-assisted build evidence

Challenge 003 (Lead Scorer). Built with Claude Code under an Architect (Guilherme) / Builder (Claude) workflow.

## 2026-07-16 — Session 1: Data foundation

**Prompt (Guilherme):** Act as CTO/Builder; develop a roadmap and first centralize the spread CRM data (ZIP with 4 CSVs + metadata) into a single datalake before anything else.

**What the AI did:**
1. Extracted the ZIP into `data/raw/` and read `metadata.csv` as the field-definition source of truth.
2. Profiled all 4 tables with pandas: shapes, nulls by stage, referential integrity, duplicates, date ranges, value distributions.
3. Found real issues before writing any product code:
   - `GTXPro` vs `GTX Pro` naming mismatch (would have silently dropped ~1,480 deals from product joins)
   - `technolgy` / `Philipines` typos in accounts
   - 1,425 open deals with no account → kept + flagged, not dropped
   - Won deals close at ~100% of list price → list price adopted as expected value for open deals
   - Lost deals die fast (median 14d) vs Won (57d) → staleness confirmed as scoring signal
   - Dataset is historical → snapshot date anchored at 2017-12-31
4. Wrote `src/build_datalake.py` (ETL with inline validation gate), ran it, verified with SQL queries against the SQLite output.
5. Documented: `docs/DATA_DICTIONARY.md`, `ROADMAP.md`, `CLAUDE.md` (working agreement).

**Human decisions:** fork/branch strategy, Architect/Builder method, datalake-first sequencing.

## 2026-07-16 — Session 2: Hypothesis validation (Architect-driven)

**Prompt (Guilherme):** Before setting scoring rules, validate 3 hypotheses: (1) won-deal profile → refine ICP; (2) mid-funnel 2-week convert-or-close rule; (3) triage/enrich prospecting deals against refined ICP.

**AI analysis & verdicts:**
1. H1 partial: price confirmed not an objection (68% of won deals at >=95% list, median 1.00) — but firmographic ICP is FLAT: win rate varies only 61-65% across sectors, 61-66% across size quartiles, 63-64% across regions. The real spread is per-agent (55-70%) and per-deal momentum.
2. H2 REFUTED/INVERTED: P(win | survived >= t) RISES with age: 63% @ 0d -> 69% @ 14d -> 75% @ 120d. Losses die early (median 14d). Killing deals at 2 weeks would kill 69%-odds deals. Real kill line: no deal in history ever won after 138 days — and 1,291 of 1,589 open Engaging deals (81%) are past it (zombie pipeline).
3. H3 partial: all 500 Prospecting deals can be ranked by product value x product win rate + agent track record; only 163/500 have an account for ICP checks; 337 need external enrichment; no buying-signal fields exist in the dataset.

**Human decision pending:** sign off amended rule set before scorer build.

## 2026-07-16 — Session 3: Playbook forensics (Architect-driven)

**Prompt (Guilherme):** Analyze top-quartile agent practices; model deal momentum as a distribution over the 14-138d window; confirm the 138d close rule; identify mid-funnel buying signals and missing metrics; enrich the 500 Prospecting deals; produce funnel KPIs by agent quartile.

**AI analysis & outputs:**
1. Quartiled 30 agents by win rate AND by revenue — the two disagree. Win rate is flat (~63%) across revenue quartiles; top-revenue agents win BIGGER (premium mix 53% vs 33%, avg deal $2,728 vs $1,646), not more often.
2. Won-cycle 14-138d ≈ bell curve, mean 76d / σ 30d, plus fast-close spike <28d. Win rate never dips below 65% inside the window (rises to 80% at 126-139d) → age inside window is not a negative signal. 138d hard close rule confirmed (0 wins ever past it).
3. Mid-funnel buying signals in-data: survival past 14d (69% odds). No activity/contact/objection fields exist — instrumentation gap list written to PLAYBOOK.md.
4. Enriched all 500 Prospecting deals with agent quartiles, product win rates, blended win prob, priority_value → data/lake/prospecting_enriched.csv; 337 flagged enrichment_needed (no account attached; no internal key can recover it).
5. Hygiene check: account fill rate anti-correlates with win rate (-0.55) — hygiene matters for visibility, not winning.
6. Wrote docs/PLAYBOOK.md incl. "tested and rejected" section.

## 2026-07-16 — Session 4: Winners/zombies segmentation, repo restructure, scorer v1 + eval

**Prompt (Guilherme):** Client is not price-sensitive — focus on customer segmentation. Analyze factors behind winners and zombies. Move all work to submissions folder for PR from branch guilherme-cleffe. Run the model without missing metrics and evaluate. Are guardrails/evals necessary now?

**AI work:**
1. Restructured to repo convention (CONTRIBUTING.md): submissions/guilherme-cleffe/{solution,docs,process-log}; challenge folder restored pristine; ETL re-verified from new paths.
2. Zombie forensics with vintage control (deals engaged <= 2017-08-15): 22% became zombies. Factors: missing account (closed deals are 100% account-attached vs 32% of zombies), manager process gap (West 25-28% vs 17-18%), GTK 500 at 44%, top win-rate agents have the worst abandon rates.
3. Winner segmentation: account-level win rates spread 53-75% in-sample — but see #5.
4. Built src/scorer.py (rules engine, factor explanations, actions) + time-split backtest (train < 2017-09-01, test after).
5. **Eval caught a designed-in mistake:** win-prob factor (account x agent x product history) scored AUC 0.487 out-of-time; account win rates correlate -0.17 across periods. The "segment signal" was noise. Removed win-prob from the score; final policy = expected value (65%) + momentum window (35%) + hard rules (138d close, attach-account). PLAYBOOK.md updated with the rejection — this is thecore evidence of iteration/judgment the submission guide asks for.
6. Scored live pipeline: 2,089 deals -> scored_pipeline.csv. Actions: 1,291 CLOSE/RECYCLE, 546 ATTACH ACCOUNT, 163 TRIAGE, 43 PUSH NOW, 29 FOCUS, 17 NURTURE.

**Human decisions:** segmentation focus, PR structure, eval-before-trust.

## 2026-07-17 — Session 5: Monday Morning brief (design pass)

**Prompt (Guilherme):** With designer support, draft the "Monday Morning" email — this week's priorities segregated by top/mid/bottom funnel plus main bottlenecks. Comprehensive but straight to the point.

**AI work:**
1. Pulled the week's real numbers from scored_pipeline.csv (no placeholder data): $3.14M open EV of which $2.02M zombie; workable book $1.12M/798 deals; actions 43 PUSH / 29 FOCUS / 546 FIX / 163 TRIAGE / 1,291 PURGE.
2. Drafted two versions: docs/monday-morning-email.md (plain-text, paste-into-mail-client) and docs/monday-morning-email.html (designed: memo/ledger aesthetic, funnel-ordered sections, bottleneck list ranked by money, light+dark themes).
3. Published preview artifact for review.

**Design decisions:** subject line leads with the honest thesis ("your $3.1M pipeline is really $1.1M"); five-verb summary strip; severity tags separate from accent color; per-deal FOCUS table with real opportunity IDs so reps can act without opening the tool.

## 2026-07-17 — Session 6: pt-BR, conformidade e submissão

**Prompt (Guilherme):** Relatório em português (Brasil); checagem final contra as instruções dos arquivos MD do repo; README.md da pasta guilherme-cleffe conforme submission-guide + template, com instruções de execução; process log completo para a audiência.

**Trabalho da IA:**
1. Boletim "Segunda de Manhã" traduzido para pt-BR (versões .md e .html; artifact republicado na mesma URL).
2. Checklist de conformidade (challenge README, submission-guide, CONTRIBUTING, template): solução roda end-to-end (ETL -> score -> backtest reverificados), dados reais, lógica de scoring explicável, docs de setup/lógica/limitações, process log, nada modificado fora de submissions/guilherme-cleffe/.
3. **Armadilha encontrada na checagem final:** o .gitignore do repo upstream ignora submissions/ inteiro — um `git add` normal geraria PR vazio. Solução conforme as regras (sem tocar arquivos fora da pasta): `git add -f submissions/guilherme-cleffe/`. Artefatos regeneráveis (crm.db, dim_*/fact_* do lake) ficam fora do commit; deliverables (scored_pipeline.csv, prospecting_enriched.csv) entram.
4. README.md da submissão criado seguindo templates/submission-template.md, em pt-BR, com instruções de execução, findings, recomendações, limitações e process log resumido.
