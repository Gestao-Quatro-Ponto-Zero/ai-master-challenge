# Prompt 012 — Monthly Business Lab & Key Moments

## User objective

Consolidate the existing RavenStack monthly view and simulator into a useful management laboratory. Preserve the paper and daily engine, make Key Moments deterministic and explorable, connect a selected month to the existing scenario lab, and validate the local application.

## Work performed

- Reused the account × plan-tier daily ledger and monthly periods. Added `key_moments` to the existing API response rather than introducing a second engine or endpoint.
- Implemented descriptive selectors for valid rate peaks, gross loss-volume peaks, acquisition changes, recovery counts, portfolio contraction/candidate downgrade, rate/count divergence, and event/date lifecycle discrepancy.
- Added selectable monthly moments with numerator/denominator, comparison, criterion, linked segments/accounts and same-month lab navigation.
- Added typed contracts/tests and an evaluator sequence in README.
- Preserved the paper and existing observed/scenario laboratory behavior.

## Revalidated examples

October 2024: 9 / 1,073 = 0.83877% opening-cohort plan-proxy loss, the highest monthly valid rate. December 2024: 11 gross plan-proxy loss events (largest count), separately 5 / 1,279 = 0.39093% opening-cohort losses. All five source CSV hashes match the daily-ledger metadata.

## Validation and limitations

API/analytics suite 45 passed; Ruff passed; frontend 9 passed; Vite build passed; Compose config and project build/runtime passed; API, frontend proxy, and scenario HTTP smoke checks passed; invalid scenario input returned 422. In-app browser access was denied by the browser security policy. No workaround was attempted and visual browser QA remains UNKNOWN. No Git or remote effects occurred.

## Decision provenance

The user specified the required selectors, constraints and evaluator flow. Component reuse, deterministic tie handling, typed response extension and the choice to classify browser verification as UNKNOWN were implementation decisions based on the existing code and permission result. No unverified commercial conclusion was added.
