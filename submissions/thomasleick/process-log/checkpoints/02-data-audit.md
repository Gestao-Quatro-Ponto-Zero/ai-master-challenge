CHECKPOINT: 02 — Dataset acquisition and audit (revalidated current execution)
STATUS: PASS with known data-quality limitations
OBJECTIVE: Verify all five source CSVs and their schema, cardinality, temporal integrity, attribution, and reproducibility.
WORK COMPLETED:
- Confirmed original staged source files exist and candidate raw CSV files match all five source hashes.
- Revalidated that staging profile and analysis JSON parse, and that copies of the staging scripts reproduce identical JSON SHA-256 values without altering original artifacts.
- API analysis was later exercised against all five source CSVs; current output is saved as process-log/evidence/api-analysis.json. The field-level standard-library profile remains preserved separately.
- Recorded exact raw file hashes in the copied prior audit report.
FILES CREATED: Current workspace copy of the audit report, raw five CSVs and source README; evidence hashes are unchanged from staging.
FILES MODIFIED: None to source CSVs.
COMMANDS EXECUTED:
- sha256sum over staged and copied profile/analysis JSON — hashes match:
  profile 18a3e7bf04a26e3275dcf17d4e4bbcf6c2c060aec18957302bc6e8baae2f2f4b
  analysis ff7ad2b688f41666d8d5c197d3d5bbae3c62029e20e4546c246a7f8283a5045e
- sha256sum of five candidate CSVs — matches raw hashes listed in the data audit.
- diff -qr /tmp/ravenstack-data candidate raw — no differences.
TESTS EXECUTED: Reproduction checks of audit/analysis JSON outputs (not application tests).
TEST RESULTS: 500 accounts, 5,000 subscriptions, 25,000 usage rows, 2,000 tickets, 600 event rows; no file mismatch. Detailed schemas/null rates/cardinalities are in this report and evidence JSON.
EVIDENCE LEVEL: LOCAL_RUNTIME; source acquisition provenance recorded as REMOTE in the prior report.
BUSINESS FINDINGS: NONE; those are documented at checkpoint 03.
UNKNOWN: The Kaggle page HTML did not expose the field in browser extraction, so a read-only request to Kaggle public metadata API was made during this execution and returned title “SaaS Subscription & Churn Analytics Dataset”, owner Riv, licenseName MIT. Challenge README also says MIT; bundled README says MIT-like, synthetic/no PII, and asks attribution. All three notices are retained.
BLOCKERS: No data acquisition blocker for local execution.
RISKS: Synthetic source. The Kaggle metadata field and challenge README identify MIT; the dataset README wording differs slightly (“MIT-like”). Keep original source README and attribution intact.
NEXT STEP: Complete and verify analysis and application against these real CSVs.
