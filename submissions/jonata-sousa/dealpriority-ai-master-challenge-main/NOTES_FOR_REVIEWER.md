# Notes for Reviewer

This package includes the files required to address the review blockers:

1. Reproducible scoring:
   - `scripts/generate_scores.py`
   - `docs/scoring-methodology.md`
   - original CSVs in `data/raw/`

2. App evaluation:
   - public demo URL in `README.md`
   - local setup instructions in `README.md`
   - Supabase seed in `supabase/seed.sql`
   - seed generator in `scripts/seed_from_csv.py`

If testing the public demo, use the credentials documented in `README.md`.
Replace `[INSERIR_SENHA_DE_TESTE_AQUI]` with a temporary test password before committing if you want reviewers to log in directly.
