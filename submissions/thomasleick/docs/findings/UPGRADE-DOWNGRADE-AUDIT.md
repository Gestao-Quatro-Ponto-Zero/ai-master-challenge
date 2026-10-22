# Upgrade and downgrade evidence audit

**Scope:** additive audit of explicit subscription-row flags and date-derived plan-transition candidates. The original source CSV and the daily ledger are preserved.

## Result

The subscription schema does contain `upgrade_flag` and `downgrade_flag`, described by the dataset documentation as mid-cycle plan changes. The flags are useful observed signals, so the earlier inference-only interpretation was incomplete. They do not, however, identify a dated source subscription and destination subscription for a particular transition. They therefore improve the evidence, but do not confirm any specific migration pair.

| Evidence | Count | Denominator / interpretation |
|---|---:|---|
| Rows with `upgrade_flag=True` | 529 | 529 / 5,000 subscription rows (10.58%) |
| Rows with `downgrade_flag=True` | 218 | 218 / 5,000 subscription rows (4.36%) |
| Rows with both flags | 23 | Overlap; do not add the two flag totals as unique rows |
| Accounts with at least one upgrade flag | 307 | Account-level presence, not transition count |
| Accounts with at least one downgrade flag | 177 | Account-level presence, not transition count |
| Upgrade-flagged rows with null `end_date` | 483 | 483 / 529 (91.30%) |
| Downgrade-flagged rows with null `end_date` | 193 | 193 / 218 (88.53%) |

The row flags occur across all three recorded plan tiers and both billing frequencies. The dataset does not document a rank field for `Basic`, `Pro`, and `Enterprise`. Their apparent order is not independently verified.

## Reconciliation with candidate transitions

The daily ledger's 0-, 1-, 7-, and 30-day candidate windows use the assumed name order `Basic < Pro < Enterprise`. Within 30 days it identifies **52 possible upgrade pairs and 51 possible downgrade pairs** (103 candidate pairs). They are contextual pairs built from an account's plan coverage ending and another plan's start; no contract foreign key links the two rows.

| Classification | Count | Why |
|---|---:|---|
| Confirmed migration | 0 | No explicit, linked from/to transition record |
| Inferred migration | 0 | Neither hierarchy nor flag-to-candidate temporal linkage is sufficiently established |
| Possible interval pairs | 103 | 52 upgrade-direction and 51 downgrade-direction candidates under assumed tier order |

The audit also exposes the explicit flags and candidate intervals separately in `GET /api/transition-audit`. In the monthly laboratory, possible upgrades and downgrades remain annotations. They do not increase acquisition, loss, or churn counts a second time.

## Financial interpretation

The CSV contains `mrr_amount` and `arr_amount` row fields. The audit can describe their recorded distributions by flag, but the rows lack a verified effective-period/from-to link that would establish the recurring value before and after each transition. A flag-row amount or a sum across flagged subscription rows is not revenue expansion or contraction. Consequently, revenue expansion, revenue contraction, gross revenue churn, and net revenue churn remain **UNKNOWN**.

## Business implication

The flags justify targeted contract reconciliation: Revenue Operations should join each flagged subscription row to its effective date, preceding contract, successor contract, and comparable recurring price. Until that mapping exists, a downgrade can be a reason to investigate but cannot be reported as a confirmed value contraction. A plan coverage loss remains a separate proxy event; a customer remains active if another plan-tier relation continues.

## Reproduction

From `solution/`:

```bash
python analysis/transition_audit/audit.py \
  --data-dir data/raw \
  --ledger analysis/daily_portfolio_churn/outputs/g4-alignment/daily-portfolio-churn.json \
  --output-dir analysis/transition_audit/outputs
```

The output JSON and candidate CSV are under `solution/analysis/transition_audit/outputs/`. Automated audit unit tests are under `solution/analysis/transition_audit/tests/`; API tests also verify the exposed counts.
