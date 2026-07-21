# Watchlist Validation

## Result

`PASS_WITH_WARNINGS` with zero unexplained reconciliation differences and zero operational actions.

## Passed controls

- anonymous account keys only;
- cutoff-safe evidence;
- no behavioral P1 with LOW confidence;
- no UNSTABLE, HIGH-order, or small-sample graph evidence;
- quality-only quarantine policy;
- de-duplicated MRR reconciliation;
- aggregate JSON privacy;
- deterministic explanations without unsafe causal language.

## Warnings

Quality and broad-rule flags are retained for human review, not hidden by the gate.
