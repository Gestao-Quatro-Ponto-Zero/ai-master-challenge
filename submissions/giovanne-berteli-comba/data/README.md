# Reproducing the D01 data audit

Runtime: Python 3.12.3, standard library only. No Kaggle package, token, model,
paid service or third-party Python dependency was used. Run from the submission:

```bash
python3 -I solution/acquire_data.py
python3 -I solution/audit_data.py
python3 -I -m unittest discover -s tests -v
python3 -I scripts/check_foundation.py
python3 -I scripts/check_foundation.py --receipt docs/review-evidence/data-audit-current.json
```

The acquisition command downloads the two public version-1 ZIP archives and
preserves their original CSV member bytes under `data/raw/`. Existing matching
files are reused; changed files stop the command rather than being overwritten.
The [manifest](manifest.json) freezes URLs, source version, publisher-declared
license, source update date, ZIP member names, byte sizes and SHA-256 hashes.
It was initialized once with `python3 -I solution/acquire_data.py --initialize`.
Do not reinitialize it to hide a source change. Public access worked anonymously
on 2026-11-02; a network or future Kaggle access failure is not a successful audit.

The audit verifies CSV hashes before reading, requires the expected schema and
writes [aggregate results](audit.json) deterministically. Null means an empty or
whitespace-only CSV cell. Dates use explicit formats; no imputation, timestamp
repair, deduplication or label correction is performed. Normalized duplicate
texts use NFKC, casefold and whitespace collapse, retaining punctuation. These
groups do not establish that all near-duplicates have been found.

The [Portuguese audit report](../docs/data-audit.md) explains usable metrics and
limitations. Raw names, emails, ticket text and resolutions are not exported in
the report/JSON; raw archives/CSVs remain ignored by Git. Source provenance and
de-identification beyond the inspected fields have not been independently proven.

## Revalidation

After a legitimate code/input change, regenerate `data/audit.json` and rerun the
affected tests before refreshing receipts. Preserve the manifest and raw files.
The D01 receipt is `docs/review-evidence/data-audit-current.json`; it fingerprints
the raw ZIPs/CSVs, manifest, scripts, aggregate output, report, setup, test output
and clean-reproduction evidence, in addition to the foundation dependencies.
It is automated evidence of a version, not a human approval or model evaluation.

The executed [clean reproduction](../docs/review-evidence/data-reproduction.json)
copied only the two scripts and manifest to a temporary directory, downloaded the
archives again and produced byte-identical audit JSON. This is stronger than
rerunning against already downloaded data, but depends on future source access.
