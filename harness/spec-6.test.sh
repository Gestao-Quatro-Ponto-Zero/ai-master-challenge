#!/usr/bin/env bash
# SPEC-6: Modelagem Preditiva (XGBoost + SHAP)
set -euo pipefail
cd "$(dirname "$0")/.."

PASS=0
FAIL=0
pass() { ((PASS++)) || true; }
fail() { echo "FAIL: $*"; ((FAIL++)) || true; }

echo "━━━ SPEC-6: Modelagem Preditiva ━━━"

TEST_DIR=$(mktemp -d)
trap 'rm -rf "$TEST_DIR"' EXIT

# ── 6-001: Modelo treina sem erro ────────────────────────────────
echo "  Test: Modelo treina sem erro"
PYTHONPATH=src python3 -c "
import pandas as pd
from churn_platform.predictive.train import train_model
df = pd.read_parquet('output/account_view.parquet')
scored = pd.read_parquet('output/scored_accounts.parquet')
df = df.merge(scored[['account_id','health_score','pillar_usage','pillar_support','pillar_engagement','pillar_financial']], on='account_id')
m = train_model(df, output_dir='$TEST_DIR')
assert m['auc_roc'] > 0, 'AUC deve ser > 0'
assert m['n_accounts'] == 500
print(f'  ✓ Modelo treinado: AUC={m[\"auc_roc\"]}, {m[\"n_accounts\"]} contas')
" && pass || fail "Treinamento do modelo"

# ── 6-002: Predição produz scores ────────────────────────────────
echo "  Test: Predição produz scores"
PYTHONPATH=src python3 -c "
import pandas as pd
from churn_platform.predictive.predict import predict_churn
df = pd.read_parquet('output/account_view.parquet')
scored = pd.read_parquet('output/scored_accounts.parquet')
df = df.merge(scored[['account_id','health_score','pillar_usage','pillar_support','pillar_engagement','pillar_financial']], on='account_id')
preds = predict_churn(df, output_dir='$TEST_DIR')
assert len(preds) == 500, f'Esperado 500, got {len(preds)}'
assert 'churn_probability' in preds.columns
assert preds['churn_probability'].between(0, 1).all(), 'Probabilidades devem estar entre 0 e 1'
n_high = (preds['churn_risk_label'] == 'High').sum()
print(f'  ✓ Predições: {len(preds)} contas, {n_high} alto risco')
" && pass || fail "Predição"

# ── 6-003: SHAP produz explicações ───────────────────────────────
echo "  Test: SHAP explicações"
PYTHONPATH=src python3 -c "
import pandas as pd
from churn_platform.predictive.explain import explain_model
df = pd.read_parquet('output/account_view.parquet')
scored = pd.read_parquet('output/scored_accounts.parquet')
df = df.merge(scored[['account_id','health_score','pillar_usage','pillar_support','pillar_engagement','pillar_financial']], on='account_id')
exp = explain_model(df, output_dir='$TEST_DIR', top_n=5)
assert len(exp['global_feature_importance']) > 0, 'Deve ter feature importance'
assert len(exp['accounts']) == 5, f'Deve ter 5 contas, got {len(exp[\"accounts\"])}'
assert 'top_risk_factors' in exp['accounts'][0], 'Deve ter risk factors'
print(f'  ✓ SHAP: {len(exp[\"global_feature_importance\"])} features, {len(exp[\"accounts\"])} contas')
" && pass || fail "SHAP explicações"

echo ""
echo "SPEC-6: $PASS passed, $FAIL failed"
exit $FAIL
