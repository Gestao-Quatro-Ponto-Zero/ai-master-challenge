# Evidence Register

All evidence below is reproducible from files generated in this folder:
- `segment_performance.csv`
- `sponsorship_comparison.csv`
- `analysis_summary.json`
- `data_qa_report.md`

## EVID-01 — YouTube organic efficiency cell
- Segment: `YouTube | sponsored=FALSE | beauty | creator_band=50k-200k | video | 120s+`
- Sample: `n=147`
- Metrics vs YouTube baseline:
  - `ERR rel = 1.0054` (+0.54%)
  - `share_rate rel = 1.0030` (+0.30%)
  - `reach_per_follower rel = 1.454` (+45.4%)
- Source: derived from `/Users/lenon/Programas em Desenvolvimento/Challenges/ai-master-challenge/submissions/lenon-cardozo/solution/analysis_summary.json` (`top_segments_head_20`) and reproducible via filter in source CSV.

## EVID-02 — Instagram organic efficiency cell
- Segment: `Instagram | sponsored=FALSE | lifestyle | creator_band=50k-200k | video | 120s+`
- Sample: `n=136`
- Metrics vs Instagram baseline:
  - `ERR rel = 0.9994` (-0.06%)
  - `share_rate rel = 1.0001` (+0.01%)
  - `reach_per_follower rel = 1.467` (+46.7%)
- Source: same method as EVID-01.

## EVID-03 — Seasonal TikTok beauty signal
- Segment: `TikTok | 2024-Q4 | beauty | creator_band=50k-200k`
- Sample: `n=80`
- Metrics vs TikTok baseline:
  - `ERR rel = 1.0007` (+0.07%)
  - `share_rate rel = 1.0185` (+1.85%)
- Source: reproducible via grouped filter over source CSV; values logged during analysis run.

## EVID-04 — YouTube lifestyle consistency in 2025
- Segment A: `YouTube | 2025-Q1 | lifestyle | creator_band=200k-500k | n=153`
  - `ERR rel = 1.0011` (+0.11%)
  - `share_rate rel = 1.0120` (+1.20%)
- Segment B: `YouTube | 2025-Q2 | lifestyle | creator_band=200k-500k | n=98`
  - `ERR rel = 1.0023` (+0.23%)
  - `share_rate rel = 1.0110` (+1.10%)
- Source: grouped filter from source CSV with same metric definitions as `data_qa_report.md`.

## EVID-05 — High-confidence positive sponsorship cells
- `YouTube|2024-Q3|beauty|500k+`
  - `n_sponsored=126`, `n_organic=168`
  - `lift_ratio_err=1.0058583141`
  - `lift_ratio_share=1.0131717981`
  - `confidence=High`
- `Instagram|2023-Q4|lifestyle|500k+`
  - `n_sponsored=126`, `n_organic=146`
  - `lift_ratio_err=1.0050076871`
  - `lift_ratio_share=1.0107060232`
  - `confidence=High`
- Source: `/Users/lenon/Programas em Desenvolvimento/Challenges/ai-master-challenge/submissions/lenon-cardozo/solution/sponsorship_comparison.csv`.

## EVID-06 — Negative sponsorship cells to pause
- `TikTok|2024-Q3|beauty|500k+`
  - `n_sponsored=105`, `n_organic=145`
  - `lift_ratio_err=0.9920764824` (‑0.79%)
  - `lift_ratio_share=0.9900115313` (‑1.00%)
  - `confidence=Medium`
- `YouTube|2024-Q3|lifestyle|500k+`
  - `n_sponsored=136`, `n_organic=127`
  - `lift_ratio_err=0.9944721564` (‑0.55%)
  - `lift_ratio_share=0.9903049776` (‑0.97%)
  - `confidence=High`
- Source: `sponsorship_comparison.csv`.

## EVID-07 — Distribution tail (anti-survivorship)
- No absolute zeros in `views`, `likes`, `shares`, `comments`.
- Bottom quartile thresholds:
  - `ERR p25 = 0.19575824` (13,054 posts, 25.00%)
  - `share_rate p25 = 0.02852050` (13,054 posts, 25.00%)
- Source: `data_qa_report.md` and `analysis_summary.json` (`near_zero_proxy`).

## EVID-08 — Portfolio-level sponsorship neutrality
- Matched strata count: `280`
- Weighted average lift:
  - `ERR ratio = 0.9999502815`
  - `share ratio = 0.9998230102`
- Confidence mix: `Low=239`, `Medium=38`, `High=3`
- Interpretation: sponsorship effect is near-zero on average and only pays off in specific strata.
- Source: `sponsorship_comparison.csv` plus weighted aggregation from analysis script logs.
