# Scoring Engine V3 — decision-support policy

## What is implemented

- **Commercial attractiveness:** V2 40% stage + 35% catalog-price percentile-like log scale + 25% account scale. Existing `priority_score` and ranking remain unchanged pending evidence-based recalibration.
- **Qualification evidence:** decision maker, timeline, budget (`yes` / `no` / `unknown`), assessed separately from attractiveness.
- **Buying readiness:** `UNASSESSED`, `PARTIAL`, `QUALIFIED`, or `BLOCKED`. These are operational classifications, not conversion probabilities.
- **Data confidence:** presence of account and count of known qualification answers. A missing account is neutral in attractiveness but triggers a data-quality action.
- **Deal health:** explicit qualification blockers and missing evidence are reported as flags, not silently subtracted from the commercial score.
- **Job priority hint:** triage hint `P1` for explicit qualification blocker, `P2` for missing account, otherwise `P3`. This is **not** a due-date scheduler or a complete Job Queue engine.
- **Next best action:** identify missing account, resolve explicit blocker, qualify incomplete evidence, or review engagement.
- **Policy version:** `3.0.0-decision-support`, exposed per opportunity and via `/api/dashboard`.

## Deliberate limits

1. **No empirically validated close probability.** Prior explorations found no useful predictive discrimination with available static CRM features.
2. **No fabricated current recency.** CRM `engage_date` is historical; it is not compared to the current clock.
3. **No automatic bonus for sectors.** Previous sector association analysis did not support the proposed large sector weights.
4. **No deal-value claim.** Product `sales_price` is a catalog reference, not negotiated revenue or contribution margin.
5. **No dynamic recalibration of commercial attractiveness from qualification yet.** Without outcome evidence or an approved decision policy, doing so would be arbitrary. Qualification changes readiness, risk flags and next action immediately.
6. **No claim of authenticated multi-user access.** The MVP is a local single-user prototype.

## Validation and use

Run `python -m unittest discover -s tests -v` and `python app.py`, then open `http://127.0.0.1:8050`.

For each opportunity, the API now returns `policy_version`, `score_basis`, `buying_readiness`, `qualification_evidence`, `qualification_evidence_summary`, `data_confidence_detail`, `deal_health_flags`, `job_priority_hint`, `job_priority_explanation`, alongside the original fields.

### Acceptance checks

- V1 regression tests all pass.
- V3 behavior tests pass.
- Saving qualification updates readiness and action without fabricating a change in conversion probability.
- Repeated reads of the same data produce the same score.
- Missing account, unknown evidence and old CRM dates are handled explicitly.

### Next milestone

Integrate the evidence and action outputs into the seller cockpit and implement persisted, deduplicated jobs with verified transitions and history. Calibrate commercial weights only when supported by appropriate historical or prospective evidence.
