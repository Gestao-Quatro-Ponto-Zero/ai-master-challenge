CHECKPOINT: 48 — G4 Executive Paper
STATUS: PASS
OBJECTIVE: Deliver the primary executive artifact before starting the monthly laboratory.
WORK COMPLETED:
- Created a seven-page A4 executive paper, editable Markdown source, reproducible ReportLab generator, pinned paper dependency, instructions, and numerical evidence manifest.
- Paper answers the three official challenge questions, presents the monthly growth-versus-loss analysis, five-table evidence, account examples, bounded impact scenarios, methodology, and limitations.
- Revalidated source CSV hashes and key analytical artifact hashes in the manifest. The paper labels plan-tier movements as conditional date reconstruction and keeps certified customer churn and revenue impact UNKNOWN.
- Rendered all seven PDF pages and inspected the final page images, including the corrected impact table layout. `pdfinfo` confirms seven A4 pages; extracted text contains the three executive answers.
- Added the paper as the primary deliverable in the submission README. Prior analytical modules, reports, source data, and checkpoints remain in place.
FILES CREATED:
- docs/paper/RAVENSTACK-THE-CHURN-PARADOX.pdf
- docs/paper/RAVENSTACK-THE-CHURN-PARADOX.md
- docs/paper/generate_paper.py
- docs/paper/requirements-paper.txt
- docs/paper/README.md
- docs/paper/EVIDENCE-MANIFEST.json
- docs/paper/qa-render/ and qa-render-v2/ and qa-render-v3/ (PDF QA renders)
- process-log/checkpoints/48-g4-executive-paper.md
FILES MODIFIED:
- README.md (paper-first entry point)
COMMANDS EXECUTED:
- `python -m json.tool docs/paper/EVIDENCE-MANIFEST.json`
- `pdfinfo docs/paper/RAVENSTACK-THE-CHURN-PARADOX.pdf`
- `pdftotext docs/paper/RAVENSTACK-THE-CHURN-PARADOX.pdf ...`
- `pdftoppm -png -r 110 ...` for all pages
- `sha256sum` and analytical evidence extraction (see manifest)
TESTS EXECUTED:
- Paper generation and seven-page PDF validation.
- Text extraction for executive answer sections.
- Per-page visual inspection of the final rendered PDF.
TEST RESULTS: PASS — current PDF and manifest exist; manifest parses; seven rendered pages inspected; no clipping/overflow found in final review.
EVIDENCE LEVEL: STATIC + LOCAL_ARTIFACT
BUSINESS FINDINGS:
- Conditional 2024 opening-cohort plan-proxy gross loss: 7/374 = 1.87%; still without coverage at year end: 3/374 = 0.80%; complete account coverage loss: 0/190.
- Absolute event counts grew, while observed annualized exposure-normalized measures move in different directions. No verified commercial customer churn increase or causal root cause is established.
UNKNOWN:
- Certified customer churn, effective-dated recurring-revenue change, causal drivers, and intervention uplift.
BLOCKERS: None for this phase.
RISKS:
- These are conditional date-derived plan-tier proxies from synthetic data. Scenario values remain parameterized assumptions.
NEXT STEP: Phase 2 — add an observed-versus-scenario monthly commercial laboratory to the existing Decision Room, without changing the observed ledger.
