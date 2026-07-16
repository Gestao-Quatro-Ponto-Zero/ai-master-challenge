#!/usr/bin/env bash
# SPEC-2: Pipeline de Dados — Load, Clean, Merge, Validate
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0
FAIL=0

assert() {
    local desc="$1"
    if eval "$2"; then
        echo "  ✓ $desc"
        PASS=$((PASS + 1))
    else
        echo "  ✗ $desc"
        FAIL=$((FAIL + 1))
    fi
}

echo ""
echo "━━━ SPEC-2: Pipeline ━━━"

# Test 1: Load CSV
echo "  Test: Load CSV"
python -c "
from churn_platform.pipeline.loader import load_source
src = {'path': 'submissions/rodolfo/data/ravenstack_accounts.csv'}
df = load_source(src)
assert len(df) == 500, f'Expected 500 rows, got {len(df)}'
assert 'account_id' in df.columns, 'Missing account_id'
print('  ✓ Load CSV: 500 rows, cols:', list(df.columns))
" 2>/dev/null && PASS=$((PASS + 1)) || FAIL=$((FAIL + 1))

# Test 2: Schema validation
echo "  Test: Schema Validation"
python -c "
from churn_platform.pipeline.validator import validate_schema
import pandas as pd
df = pd.DataFrame({'account_id': ['a'], 'churn_flag': [True]})
schema = {'required': ['account_id', 'churn_flag'], 'types': {'churn_flag': 'boolean'}}
validate_schema(df, schema, 'test')
print('  ✓ Schema validation OK')
" 2>/dev/null && PASS=$((PASS + 1)) || FAIL=$((FAIL + 1))

# Test 3: Schema FAIL on missing required col
echo "  Test: Schema rejects missing column"
python -c "
from churn_platform.pipeline.validator import validate_schema, ValidationError
import pandas as pd
df = pd.DataFrame({'name': ['a']})
schema = {'required': ['account_id']}
try:
    validate_schema(df, schema, 'test')
    print('  ✗ Should have raised')
    exit(1)
except ValidationError as e:
    print('  ✓ Correctly rejected:', str(e)[:50])
" 2>/dev/null && PASS=$((PASS + 1)) || FAIL=$((FAIL + 1))

# Test 4: Data Quality Report
echo "  Test: DQR Generation"
python -c "
from churn_platform.pipeline.validator import generate_dqr
import pandas as pd
sources = {'test': pd.DataFrame({'a': [1, 2, None], 'b': ['x', 'y', 'z']})}
dqr = generate_dqr(sources)
assert 'test' in dqr
assert dqr['test']['rows'] == 3
print('  ✓ DQR generated')
" 2>/dev/null && PASS=$((PASS + 1)) || FAIL=$((FAIL + 1))

echo ""
echo "SPEC-2: $PASS passed, $FAIL failed"
exit $FAIL
