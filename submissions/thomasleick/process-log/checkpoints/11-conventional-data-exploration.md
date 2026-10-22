CHECKPOINT: 11 — Conventional data exploration
STATUS: PASS
OBJECTIVE: Independently profile the five source tables and verify source integrity before interpreting outcomes.
WORK COMPLETED:
- Re-read all five original CSVs without modifying them; confirmed row counts, field names, nulls, duplicate keys, distributions, date spans and entity relationships.
- Generated source hashes and table profiles in the new conventional-analysis module.
- Audited one-to-many relationships and orphan rows. Every child FK checked had zero orphans; 500 accounts map to 5,000 subscription rows, and usage maps to subscriptions.
- Quantified repeated event and usage IDs without deleting rows.
FILES CREATED: `solution/analysis/conventional/README.md`; `run.py`; `outputs/data-profile.json`; initial output inventory and report.
FILES MODIFIED: NONE. Original source CSVs and previous evidence remain unchanged.
COMMANDS EXECUTED:
- `python3 solution/analysis/conventional/run.py --data-dir solution/data/raw --output-dir solution/analysis/conventional/outputs` (absolute paths were used in this workspace; exact standalone command is in README).
- Read-only Python CSV/hash/schema profiling.
TESTS EXECUTED: Source table/hash/cardinality assertions within `python3 -m unittest discover -s solution/analysis/conventional/tests -v`.
TEST RESULTS: 500 accounts; 5,000 subscriptions; 25,000 usage rows; 2,000 tickets; 600 churn-event rows. No orphan rows across the four checked relationships. Usage has 21 duplicate IDs, 42 rows in their groups, 21 excess rows. Event rows repeat across 175 accounts (423 rows in repeated groups; 248 excess beyond one per account). Missing satisfaction: 825/2,000.
EVIDENCE LEVEL: LOCAL_RUNTIME — current CSVs were read and deterministic outputs generated locally.
BUSINESS FINDINGS: These tables have different grains and require separate aggregation. Dataset README identifies values as synthetic; these observations do not establish real-company performance.
UNKNOWN: Production lifecycle meaning, historical eligible-account denominators, causal drivers, valid recurring revenue.
BLOCKERS: None for descriptive source profiling.
RISKS: Repeated events and inconsistent source indicators can materially change label selection; cross-table fan-out would inflate metrics.
NEXT STEP: Compare explicit account and event churn labels, then build segment-specific descriptive tables.

## Provenance

CSV SHA-256 hashes are persisted in `outputs/data-profile.json` and `outputs/analysis-summary.json`; source files were not copied, altered, or deduplicated.
