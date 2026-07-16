#!/usr/bin/env bash
# SPEC-5: Health Score
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0
FAIL=0

echo ""
echo "━━━ SPEC-5: Health Score ━━━"

python -c "
from churn_platform.scoring.health_score import compute_health_score
import pandas as pd

df = pd.DataFrame({
    'account_id': ['a', 'b'],
    'churn_flag': [False, True],
    'total_usage_count': [100, 10],
    'unique_features': [8, 2],
    'total_error_count': [5, 20],
    'avg_satisfaction': [4.5, 2.0],
    'escalation_count': [0, 5],
    'total_tickets': [3, 15],
    'usage_days': [25, 3],
    'beta_feature_used': [True, False],
    'downgrade_flag': [False, True],
    'billing_frequency': ['annual', 'monthly'],
})

result = compute_health_score(df)

# Test columns exist
required = ['health_score', 'health_tier', 'pillar_usage', 'pillar_support', 'pillar_engagement', 'pillar_financial']
for col in required:
    assert col in result.columns, f'Missing column: {col}'

# Test range
assert result['health_score'].between(0, 100).all(), 'Score out of range'

# Test churned has lower score
a_score = result[result['account_id'] == 'a']['health_score'].values[0]
b_score = result[result['account_id'] == 'b']['health_score'].values[0]
assert a_score > b_score, f'Expected a({a_score}) > b({b_score})'

print(f'  ✓ Health scores: a={a_score:.0f}, b={b_score:.0f}')
print('  ✓ All assertions passed')
" 2>/dev/null && PASS=$((PASS + 1)) || FAIL=$((FAIL + 1))

echo ""
echo "SPEC-5: $PASS passed, $FAIL failed"
exit $FAIL
