#!/usr/bin/env bash
# SPEC-12: LLM Integration (OpenCode on-demand)
# Testes para LLMExplainer com fallback e cache

set -euo pipefail
cd "$(dirname "$0")/.."

PASS=0
FAIL=0

pass() { ((PASS++)) || true; }
fail() { echo "FAIL: $*"; ((FAIL++)) || true; }

# ── 12-001: LLMExplainer deve inicializar com cache_dir ──────────
echo "=== SPEC-12-001: LLMExplainer init ==="
PYTHONPATH=src python3 -c "
from churn_platform.llm import LLMExplainer
explainer = LLMExplainer(cache_ttl=3600, cache_dir='/tmp/churn_test_cache')
assert explainer.cache_ttl == 3600
print(f'OK: LLMExplainer init com cache_ttl={explainer.cache_ttl}')
print(f'  cache_dir={explainer.cache_dir}')
" && pass || fail "LLMExplainer init"

# ── 12-002: Fallback explain sem OpenCode ────────────────────────
echo "=== SPEC-12-002: Fallback explicação ==="
PYTHONPATH=src python3 -c "
from churn_platform.llm import LLMExplainer
explainer = LLMExplainer(cache_dir='/tmp/churn_test_cache')
account = {
    'account_id': 'A-12345',
    'industry': 'FinTech',
    'plan_tier_account': 'Enterprise',
    'mrr_amount': 5000,
    'seats_account': 50,
    'health_score': 35.0,
    'health_tier': 'Critical',
    'pillar_usage': 30.0,
    'pillar_support': 45.0,
    'pillar_engagement': 60.0,
    'pillar_financial': 80.0,
    'total_usage_count': 120,
    'total_error_count': 45,
    'total_tickets': 12,
    'escalation_count': 3,
    'avg_satisfaction': 2.5,
    'downgrade_flag': True,
}
narrative = explainer._fallback_explain(account)
assert len(narrative) > 20, f'Fallback muito curto: {narrative}'
assert 'A-12345' in narrative, 'Account ID não encontrado no fallback'
assert 'Health Score' in narrative or 'Critical' in narrative, 'Health data não encontrado'
print(f'OK: Fallback explicação gerada ({len(narrative)} chars)')
print(f'  Preview: {narrative[:80]}...')
" && pass || fail "Fallback explicação"

# ── 12-003: Cache deve funcionar ─────────────────────────────────
echo "=== SPEC-12-003: Cache LLM ==="
PYTHONPATH=src python3 -c "
import asyncio
from churn_platform.llm import LLMExplainer
explainer = LLMExplainer(cache_ttl=86400, cache_dir='/tmp/churn_test_cache')
account = {
    'account_id': 'A-cache-test',
    'industry': 'EdTech',
    'plan_tier_account': 'Basic',
    'mrr_amount': 1000,
    'seats_account': 10,
    'health_score': 50.0,
    'health_tier': 'At Risk',
    'pillar_usage': 40.0,
    'pillar_support': 50.0,
    'pillar_engagement': 55.0,
    'pillar_financial': 60.0,
    'total_usage_count': 50,
    'total_error_count': 5,
    'total_tickets': 3,
    'escalation_count': 0,
    'avg_satisfaction': 4.0,
}
result1 = asyncio.run(explainer.explain(account, depth='short'))
result2 = asyncio.run(explainer.explain(account, depth='short'))
assert result1['account_id'] == result2['account_id'], 'account_id mismatch'
assert result1['narrative'] == result2['narrative'], 'Cache não retornou mesmo resultado'
print(f'OK: Cache funcionou — mesma narrative em 2 chamadas')
print(f'  account_id={result1[\"account_id\"]}')
print(f'  risk_factors={result1[\"risk_factors\"]}')
print(f'  actions={result1[\"recommended_actions\"]}')
" && pass || fail "Cache LLM"

# ── 12-004: Risk factors e recommended actions ───────────────────
echo "=== SPEC-12-004: Risk factors ==="
PYTHONPATH=src python3 -c "
from churn_platform.llm import LLMExplainer
explainer = LLMExplainer(cache_dir='/tmp/churn_test_cache')
account = {
    'pillar_usage': 30.0,
    'escalation_count': 5,
    'downgrade_flag': True,
    'avg_satisfaction': 2.0,
    'health_score': 35.0,
    'total_usage_count': 50,
    'total_error_count': 30,
    'beta_feature_used': False,
}
factors = explainer._extract_risk_factors(account)
assert len(factors) >= 3, f'Poucos fatores: {factors}'
assert 'usage_drop_significant' in factors
assert 'multiple_escalations' in factors
assert 'recent_downgrade' in factors
actions = explainer._recommend_actions(account)
assert len(actions) >= 2, f'Poucas ações: {actions}'
print(f'OK: {len(factors)} fatores de risco extraídos: {factors}')
print(f'   {len(actions)} ações recomendadas: {[a[\"action\"] for a in actions]}')
" && pass || fail "Risk factors"

# ── 12-005: Invalidate cache ─────────────────────────────────────
echo "=== SPEC-12-005: Invalidate cache ==="
PYTHONPATH=src python3 -c "
from churn_platform.llm import LLMExplainer
import asyncio
explainer = LLMExplainer(cache_dir='/tmp/churn_test_cache')
account = {'account_id': 'A-inv-test', 'industry': 'Test', 'plan_tier_account': 'Basic',
           'mrr_amount': 100, 'seats_account': 5, 'health_score': 60, 'health_tier': 'Neutral',
           'pillar_usage': 50, 'pillar_support': 50, 'pillar_engagement': 50, 'pillar_financial': 50,
           'total_usage_count': 10, 'total_error_count': 1, 'total_tickets': 1, 'escalation_count': 0,
           'avg_satisfaction': 4.0}
asyncio.run(explainer.explain(account))
assert len(explainer.cache) > 0, 'Cache vazio após explain'
explainer.invalidate_cache()
assert len(explainer.cache) == 0, 'Cache não foi limpo'
print(f'OK: Cache invalidado com sucesso')
" && pass || fail "Invalidate cache"

# ── Results ──────────────────────────────────────────────────────
echo ""
echo "╔════════════════════════════════════╗"
echo "║  SPEC-12: LLM Integration           ║"
echo "║  Passed: $PASS / $((PASS+FAIL))                ║"
echo "╚════════════════════════════════════╝"

# Cleanup
rm -rf /tmp/churn_test_cache 2>/dev/null || true

exit $FAIL
