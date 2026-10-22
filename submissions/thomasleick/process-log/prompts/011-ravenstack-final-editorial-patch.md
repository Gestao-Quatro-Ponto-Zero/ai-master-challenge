# Prompt 011 — RavenStack Final Editorial Patch

## User objective

Apply only three scoped editorial corrections to the existing seven-page RavenStack paper, regenerate its official PDF from the Markdown/source generator, verify the cited numbers and rendered pages, and record an additive checkpoint. The instruction explicitly prohibited a new analysis, a conceptual rewrite, changes to the React application, or Git/remote effects.

## Work performed

1. Reworked the page 2 Q1 diagnosis to lead with the 62 date-reconstructed account–plan-tier losses, note that 54 had another plan relation active, state the top declared reason-code counts (features 114/600, support 104/600, budget 104/600), and distinguish declared reasons from demonstrated causes.
2. Kept all 24 monthly observations and zero-denominator January 2023 behavior, reduced x-axis label density to quarter starts, and added separate October 2024 and December 2024 callouts. The October callout uses opening-cohort loss (9/1,073); the December callout distinguishes 11 gross events from 5 opening-cohort losses (5/1,279).
3. Added the requested qualification immediately below the page 6 scenario table: the 60 accounts are historical investigation cases, not verified current eligibility; scenario eligibility and values are assumed, not observed revenue or causal ROI.

## Evidence and validation

The edited claims were checked against the existing daily-ledger and reason-code outputs. The paper generator regenerated the official PDF and both evidence manifests. The paper evidence suite passed 7/7 tests. `pdfinfo` reports seven A4 pages; the generated artifact hash is `aa812c97358fce560168594e6777bb0da66f623af3a237931fe92f55cb3c36c0`. The seven page renders and contact sheet are stored at `docs/paper/qa-render-v11/`; the full-resolution revised pages 2, 3 and 6 were inspected after rendering, as were the other four pages.

## Correction during validation

An auxiliary manifest-check snippet initially looked for a nonexistent top-level `outputs` JSON key. Inspection showed the generator's actual schema stores the hash under `paper.pdf_sha256`; the check was corrected to match that schema. This did not modify business inputs or calculations. The final corrected hash check passed.

## Decision provenance

The three requested content changes and their wording priorities were specified by the user. The implementation details (quarter-start tick cadence, the local output hash check, and checkpoint numbering) were routine execution choices. No additional human decision or approval is claimed.

## Scope and effects

Only the paper source, its existing generator/tests/manifests, paper reproduction README, and additive process records were changed. Historical reports and datasets were preserved. No Git initialization, commit, push, PR, deployment, or remote effect occurred.
