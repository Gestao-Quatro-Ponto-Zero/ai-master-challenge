# Process Evidence Validation

**Gate: PASS.**

## Summary

- PASS: 45
- PASS_WITH_WARNINGS: 0
- BLOCKED: 0

## Checks

| Check | Status | Detail |
|---|---|---|
| `document.HUMAN_JUDGMENT.md.exists` | PASS | submissions\carlos-henrique\process-log\HUMAN_JUDGMENT.md |
| `document.HUMAN_JUDGMENT.md.headings` | PASS | all required headings present |
| `document.AI_TRACE.md.exists` | PASS | submissions\carlos-henrique\process-log\AI_TRACE.md |
| `document.AI_TRACE.md.headings` | PASS | all required headings present |
| `document.AI_ERRORS_AND_CORRECTIONS.md.exists` | PASS | submissions\carlos-henrique\process-log\AI_ERRORS_AND_CORRECTIONS.md |
| `document.AI_ERRORS_AND_CORRECTIONS.md.headings` | PASS | all required headings present |
| `document.REJECTED_HYPOTHESES.md.exists` | PASS | submissions\carlos-henrique\process-log\REJECTED_HYPOTHESES.md |
| `document.REJECTED_HYPOTHESES.md.headings` | PASS | all required headings present |
| `document.TRADE_OFFS.md.exists` | PASS | submissions\carlos-henrique\process-log\TRADE_OFFS.md |
| `document.TRADE_OFFS.md.headings` | PASS | all required headings present |
| `document.HUMAN_INTERVENTION_TIMELINE.md.exists` | PASS | submissions\carlos-henrique\process-log\HUMAN_INTERVENTION_TIMELINE.md |
| `document.HUMAN_INTERVENTION_TIMELINE.md.headings` | PASS | all required headings present |
| `document.EVIDENCE_MAP.md.exists` | PASS | submissions\carlos-henrique\process-log\EVIDENCE_MAP.md |
| `document.EVIDENCE_MAP.md.headings` | PASS | all required headings present |
| `ids.HUMAN_JUDGMENT.md.exact` | PASS | required=18 found=18 |
| `ids.HUMAN_JUDGMENT.md.unique` | PASS | occurrences=18 unique=18 |
| `ids.AI_ERRORS_AND_CORRECTIONS.md.exact` | PASS | required=16 found=16 |
| `ids.AI_ERRORS_AND_CORRECTIONS.md.unique` | PASS | occurrences=16 unique=16 |
| `ids.REJECTED_HYPOTHESES.md.exact` | PASS | required=13 found=13 |
| `ids.REJECTED_HYPOTHESES.md.unique` | PASS | occurrences=13 unique=13 |
| `ids.EVIDENCE_MAP.md.exact` | PASS | required=15 found=15 |
| `ids.EVIDENCE_MAP.md.unique` | PASS | occurrences=15 unique=15 |
| `content.human_decision_fields` | PASS | blocks=18; incomplete=[] |
| `content.error_validation_fields` | PASS | blocks=16; incomplete=[] |
| `content.rejection_fields` | PASS | blocks=13; incomplete=[] |
| `content.claim_support` | PASS | 47 decision/error/rejection blocks contain linked support |
| `trace.phase_coverage` | PASS | 12 required phases present |
| `trace.reconstructed_prompt_label` | PASS | label_occurrences=4 |
| `trace.verification_cycle` | PASS | suggestion-to-commit cycle present |
| `content.limitations` | PASS | limitations present in all process documents |
| `content.evidence_map_rows` | PASS | rows=15; malformed=0 |
| `content.tradeoffs` | PASS | rows=12; required=12 |
| `integration.readme.exists` | PASS | submissions\carlos-henrique\README.md |
| `integration.index.exists` | PASS | submissions\carlos-henrique\docs\README.md |
| `integration.readme.section` | PASS | section present |
| `integration.readme.word_count` | PASS | words=136; expected=120..180 |
| `integration.readme.links` | PASS | all seven links present |
| `integration.index.process_evidence` | PASS | category, metadata columns, and seven links present |
| `review.adversarial` | PASS | report exists; open CRITICAL=0; open HIGH=0; gate=PASS |
| `review.evaluator` | PASS | report exists; question_passes=7; gate=PASS |
| `language.placeholders` | PASS | zero placeholders |
| `language.ai_autonomy` | PASS | zero prohibited occurrences |
| `links.internal` | PASS | checked=238; broken=0 |
| `commits.references` | PASS | checked=13; missing=0 |
| `scope.changed_files` | PASS | outside=0 |

## Limitations

This validator checks versioned structure, identifiers, links, commits, attribution fields, language, and evaluator integration. It does not infer private reasoning or extend historical evidence to a live operating context. Future customer action, model use, or experiment execution requires a separate human-approved gate.
