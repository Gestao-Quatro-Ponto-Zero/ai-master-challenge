#!/usr/bin/env bash
# SPEC-7: Survival Analysis (Kaplan-Meier + CoxPH)
set -euo pipefail
cd "$(dirname "$0")/.."

PASS=0
FAIL=0
pass() { ((PASS++)) || true; }
fail() { echo "FAIL: $*"; ((FAIL++)) || true; }

echo "━━━ SPEC-7: Survival Analysis ━━━"

TEST_DIR=$(mktemp -d)
trap 'rm -rf "$TEST_DIR"' EXIT

# ── 7-001: KM curves geram gráficos ──────────────────────────────
echo "  Test: KM curves"
PYTHONPATH=src python3 -c "
import pandas as pd
from churn_platform.survival.analysis import prepare_survival_data, plot_km_curves
df = pd.read_parquet('output/account_view.parquet')
data = prepare_survival_data(df)
assert len(data) == 500
assert 'tenure_days' in data.columns
assert 'event_observed' in data.columns
paths = plot_km_curves(data, output_dir='$TEST_DIR')
assert len(paths) == 2
print(f'  ✓ KM curves: {len(paths)} plots, {len(data)} accounts')
" && pass || fail "KM curves"

# ── 7-002: CoxPH produz hazard ratios ────────────────────────────
echo "  Test: CoxPH model"
PYTHONPATH=src python3 -c "
import pandas as pd
from churn_platform.survival.analysis import prepare_survival_data, fit_coxph
df = pd.read_parquet('output/account_view.parquet')
data = prepare_survival_data(df)
result = fit_coxph(data)
assert result['concordance_index'] > 0, 'C-index deve ser > 0'
assert len(result['hazard_ratios']) > 0, 'Deve ter hazard ratios'
has_sig = any(v['significant'] for v in result['hazard_ratios'].values())
print(f'  ✓ CoxPH: C-index={result[\"concordance_index\"]}, {result[\"features_significant\"]} significant features')
" && pass || fail "CoxPH"

# ── 7-003: Predições de sobrevivência ────────────────────────────
echo "  Test: Survival predictions"
PYTHONPATH=src python3 -c "
import pandas as pd
from lifelines import KaplanMeierFitter
from churn_platform.survival.analysis import prepare_survival_data, predict_survival
df = pd.read_parquet('output/account_view.parquet')
data = prepare_survival_data(df)
kmf = KaplanMeierFitter().fit(data['tenure_days'], event_observed=data['event_observed'])
preds = predict_survival(data, kmf)
assert len(preds) == 500
assert 'survival_90d' in preds.columns
assert preds['survival_90d'].between(0, 1).all()
print(f'  ✓ Predictions: {len(preds)} accounts, P(90d)={preds[\"survival_90d\"].mean():.3f}')
" && pass || fail "Survival predictions"

echo ""
echo "SPEC-7: $PASS passed, $FAIL failed"
exit $FAIL
