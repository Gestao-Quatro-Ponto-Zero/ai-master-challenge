# Final Submission Validation

**Gate: PASS_WITH_WARNINGS.**

## Summary

- PASS: 25
- PASS_WITH_WARNINGS: 1
- BLOCKED: 0

## Checks

| Check | Status | Detail |
|---|---|---|
| `package.required_files` | PASS | required=38; missing=[] |
| `package.screenshots` | PASS | required=7; valid=7; missing=[] |
| `package.required_headings` | PASS | all required headings present |
| `pitch.30_seconds` | PASS | english_words=68; portuguese_words=74 |
| `pitch.90_seconds` | PASS | english_words=230; portuguese_words=218 |
| `video.srt.en` | PASS | cues=29; final_ms=185000; problems=[] |
| `video.srt.pt_br` | PASS | cues=29; final_ms=185000; problems=[] |
| `video.required_boundaries` | PASS | all six boundaries present |
| `summary.lengths` | PASS | 50=50; 100=97; 200=197; short_chars=448 |
| `links.local` | PASS | checked=233; broken=0 |
| `claims.prohibited` | PASS | occurrences=0 |
| `content.generic_placeholders` | PASS | occurrences=0 |
| `links.no_invented_urls` | PASS | unexpected=0 |
| `external.registry` | PASS | six link records present |
| `external.pending_actions` | PASS_WITH_WARNINGS | expected_pending_markers=7 |
| `metrics.canonical_snapshot` | PASS | canonical values present |
| `tests.reference_consistency` | PASS | Python=130/130; Vitest=19/19; Playwright=36/36 |
| `metrics.matrix` | PASS | metric consistency matrix gate present |
| `gate.clean_room` | PASS | clean-room PASS |
| `gate.adversarial` | PASS | CRITICAL=0; HIGH=0; gate=PASS |
| `gate.five_minute` | PASS | five-minute gate PASS |
| `gate.message_consistency` | PASS | message consistency PASS |
| `build.cross_platform_security` | PASS | eol_rules=16/16; builder_crlf=True; sharp_override=True; locked_sharp=0.35.3; next_requirement=^16.2.11; locked_next=16.2.11 |
| `git.change_scope` | PASS | outside=0 |
| `git.raw_csv` | PASS | tracked=0 |
| `git.build_artifacts` | PASS | tracked=0 |

## Publication Boundary

Internal readiness and external publication are separate gates. Recording, deployment, upload, push, Pull Request creation, form completion, and submission remain under explicit user control.

## Limitations

This report validates the repository package and expected placeholders. Hosting behavior and final external visibility must be tested after the user performs each external action.
