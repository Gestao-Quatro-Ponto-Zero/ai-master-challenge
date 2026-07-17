# Lead Scorer — working agreement

Guilherme is the Architect (decides what/why), Claude is the Builder (proposes how, implements, verifies). Advisory style: direct, opinionated, small verified steps.

## Ground rules

- Plan in writing before building; ROADMAP.md is the source of truth for scope.
- Every step must end runnable. No half-wired code left on the branch.
- Rebuild the lake with `python src/build_datalake.py` — never hand-edit `data/lake/`.
- `data/raw/` is immutable source data (CC0 Kaggle dataset). All fixes happen in ETL code.
- Snapshot date is 2017-12-31 (historical dataset) — never use the real clock for deal ages.
- Explainability beats sophistication: every score must decompose into named factors a seller understands.
- Append significant prompts/decisions to docs/process-log.md as we go (challenge requires AI-process evidence).

## Layout

- `src/build_datalake.py` — ETL: raw CSVs → data/lake (CSVs + crm.db SQLite)
- `src/scorer.py` — scoring engine (Phase 2)
- `app.py` — Streamlit seller UI (Phase 3)
- `docs/DATA_DICTIONARY.md` — schema + cleaning rules + profiling facts
