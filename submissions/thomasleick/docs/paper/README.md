# Executive paper source and reproduction

The deliverable PDF is generated from the local daily-ledger and five-table analysis outputs by `generate_paper.py`. The narrative source is `RAVENSTACK-THE-CHURN-PARADOX.md`; quantitative claims, scenario arithmetic, source hashes and output hashes are indexed in `PAPER-NUMERICAL-EVIDENCE-MANIFEST.md` and `EVIDENCE-MANIFEST.json`. The prior paper and generator are preserved in `archive/2026-10-22-pre-rewrite/`.

From the candidate package root:

```bash
python3 -m pip install -r docs/paper/requirements-paper.txt
python3 docs/paper/generate_paper.py
pdfinfo docs/paper/RAVENSTACK-THE-CHURN-PARADOX.pdf
pdftoppm -png -r 160 docs/paper/RAVENSTACK-THE-CHURN-PARADOX.pdf docs/paper/qa-render/page
python3 docs/paper/test_paper_evidence.py
```

The generator reads, but does not modify, the original CSV files or analytical JSON artifacts. It checks the original CSV hashes against the ledger before building. It requires ReportLab 5.1.0, DejaVu Sans at `/usr/share/fonts/truetype/dejavu/` and Poppler (`pdfinfo`, `pdftoppm`) for render verification. The final rendered QA pages are retained under `qa-render-v11/`.

The PDF is a seven-page A4 editorial paper. It is an independent challenge submission, not a G4 publication or endorsement. The current paper names conditional plan-tier reconstruction as such; no commercial customer churn, revenue loss, causal effect or calibrated future-risk score is asserted.
