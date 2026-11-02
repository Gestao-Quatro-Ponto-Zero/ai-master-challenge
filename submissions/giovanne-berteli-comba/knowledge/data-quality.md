---
type: Data Audit
title: Version-one dataset quality and measurement boundaries
description: Audited dimensions, temporal limitations, duplicate groups and implications for D02.
status: draft
generated:
  by: codex
  at: 2026-11-02T17:29:24Z
sources:
  - id: manifest
    resource: ../data/manifest.json
  - id: audit
    resource: ../data/audit.json
  - id: report
    resource: ../docs/data-audit.md
---

# Audited inputs

D01 acquired the two official Kaggle version-1 archives. The manifest owns source
versions, publisher-declared licenses, member names, sizes and hashes. The audit
JSON owns computed counts; the Portuguese report explains their populations and
limitations. Raw files remain local and ignored. Reproduce using `data/README.md`.

Customer support: 8,469 rows, 17 columns; IT classification: 47,837 rows, 2 columns,
8 labels. No common entity key is available. No dataset-use or stack decision is
made by this audit.

# Measurement boundaries

- The first dataset's time fields are timezone-unspecified timestamps. Ticket
  creation time is absent. Purchase date cannot substitute for ticket creation.
- Of 2,769 response/resolution pairs, 1,365 have resolution before first response.
  Nonnegative post-response intervals are not full ticket lifetimes or active
  effort. Do not repair the chronology silently or claim measured labor savings.
- Satisfaction is observed for 2,769/8,469 rows, exactly the closed population;
  5,700 nonclosed tickets have no satisfaction or resolution observations.
- All 8,469 descriptions have unfilled brace placeholders. Template-like content
  and reserved example email domains do not independently establish data origin
  or prove that every field is de-identified.
- Customer descriptions form 54 repeated normalized-text groups (457 rows),
  including 49 groups with conflicting Ticket Type labels (446 rows). Preserve
  raw rows and prevent duplicate leakage when defining evaluation membership.
- IT texts have no exact/normalized duplicates or blanks in this audit. This
  does not establish absence of near-duplicates or common source entities.

# Next decisions

D02 must define complementary roles, trustworthy metrics and treatment of label
conflicts. V00 must reserve evaluation groups before model/prompt/threshold
selection. No model has been trained or evaluated. Acquisition/audit reproduced
from a clean temporary directory; this was an automated check, not human review.
The D01 receipt is `docs/review-evidence/data-audit-current.json`; stale hashes
require regenerating affected outputs before explicitly recording new evidence.
