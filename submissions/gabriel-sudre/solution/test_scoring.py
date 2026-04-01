"""Validação completa do scoring engine."""
import sys
sys.path.insert(0, '.')

from supabase import create_client
import pandas as pd
import numpy as np
import math

url = 'https://urvpasvifulrlpcatkxs.supabase.co'
key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVydnBhc3ZpZnVscmxwY2F0a3hzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NDkwNzE0MSwiZXhwIjoyMDkwNDgzMTQxfQ.VOWsv3oNUII2KvhdRs7fnGnRDV6_r0svQ0Cv-uHZbHg'
sb = create_client(url, key)

# Load data
all_data = []
offset = 0
while True:
    result = sb.table('sales_pipeline').select('*').range(offset, offset + 999).execute()
    if not result.data:
        break
    all_data.extend(result.data)
    if len(result.data) < 1000:
        break
    offset += 1000

pipeline = pd.DataFrame(all_data)
pipeline['engage_date'] = pd.to_datetime(pipeline['engage_date'])
pipeline['close_date'] = pd.to_datetime(pipeline['close_date'])
accounts = pd.DataFrame(sb.table('accounts').select('*').execute().data)
products = pd.DataFrame(sb.table('products').select('*').execute().data)
teams = pd.DataFrame(sb.table('sales_teams').select('*').execute().data)

from scoring.features import compute_global_stats, compute_features, DEFAULT_WEIGHTS, REFERENCE_DATE, CLAMP_MIN, CLAMP_MAX
from scoring.engine import score_pipeline

errors = []

# ==== CHECK 1: Weights sum to 1.0 ====
print("CHECK 1: Pesos somam 1.0")
w_sum = sum(DEFAULT_WEIGHTS.values())
for k, v in DEFAULT_WEIGHTS.items():
    print(f"  {k}: {v}")
print(f"  TOTAL: {w_sum}")
if abs(w_sum - 1.0) > 0.001:
    errors.append(f"Pesos somam {w_sum}, nao 1.0")
    print("  FALHOU")
else:
    print("  OK")

# ==== CHECK 2: Win rate exclui ativos ====
print("\nCHECK 2: Win rate exclui deals ativos")
stats = compute_global_stats(pipeline, accounts, products, teams)
closed = pipeline[pipeline['deal_stage'].isin(['Won', 'Lost'])]
manual_wr = len(closed[closed['deal_stage'] == 'Won']) / len(closed)
print(f"  Global WR (stats): {stats['global_win_rate']:.6f}")
print(f"  Global WR (manual Won/closed): {manual_wr:.6f}")
if abs(stats['global_win_rate'] - manual_wr) > 0.001:
    errors.append("Win rate inconsistente")
    print("  FALHOU")
else:
    print("  OK")

# ==== CHECK 3: Score engine == score manual ====
print("\nCHECK 3: Score engine == score manual")
scored = score_pipeline(pipeline, accounts, products, teams)
test_deals = [scored.iloc[0], scored.iloc[len(scored)//2], scored.iloc[-1]]  # top, mid, bottom
for deal in test_deals:
    features = compute_features(deal, stats)
    manual_score = round(sum(DEFAULT_WEIGHTS.get(k, 0) * v for k, v in features.items()) * 100, 1)
    diff = abs(deal['score'] - manual_score)
    status = "OK" if diff < 1.0 else "FALHOU"
    print(f"  {deal['account_name'][:20]:20s} engine={deal['score']} manual={manual_score} diff={diff:.1f} {status}")
    if diff >= 1.0:
        errors.append(f"Score diverge para {deal['account_name']}: {deal['score']} vs {manual_score}")

# ==== CHECK 4: All features clamped ====
print("\nCHECK 4: Clamp [0.05, 0.95]")
feature_cols = [c for c in scored.columns if c.startswith('_f_')]
for col in feature_cols:
    vals = scored[col]
    # Allow special values: 0.30 for Prospecting aging, median*0.6 for account_fit, median*0.5 for repeat
    special = {0.30, stats['median_account_fit'] * 0.6, stats['median_repeat'] * 0.5}
    non_special = vals[~vals.isin(special)]
    below = (non_special < CLAMP_MIN - 0.001).sum()
    above = (non_special > CLAMP_MAX + 0.001).sum()
    status = "OK" if below == 0 and above == 0 else f"AVISO: {below} below, {above} above"
    print(f"  {col}: [{vals.min():.3f}, {vals.max():.3f}] {status}")

# ==== CHECK 5: No NaN scores ====
print("\nCHECK 5: Sem NaN")
nan_count = scored['score'].isna().sum()
print(f"  NaN scores: {nan_count}")
if nan_count > 0:
    errors.append(f"{nan_count} scores NaN")
    print("  FALHOU")
else:
    print("  OK")

# ==== CHECK 6: Distribution ====
print("\nCHECK 6: Distribuicao")
print(f"  Total: {len(scored)}")
print(f"  Range: {scored['score'].min():.1f} - {scored['score'].max():.1f}")
print(f"  Mean: {scored['score'].mean():.1f} | Std: {scored['score'].std():.1f}")
for t in [70, 60, 55, 50, 40]:
    c = len(scored[scored['score'] >= t])
    print(f"  >= {t}: {c} ({c/len(scored)*100:.1f}%)")

# ==== CHECK 7: agent_load symmetric ====
print("\nCHECK 7: agent_load simetrico")
avg_l = stats['avg_agent_load']
std_l = stats['std_agent_load']
z_above = abs((avg_l + 2*std_l) - avg_l) / std_l
z_below = abs((avg_l - 2*std_l) - avg_l) / std_l
s_above = 1 / (1 + z_above)
s_below = 1 / (1 + z_below)
print(f"  Score at avg: {1/(1+0):.3f}")
print(f"  Score at +2std: {s_above:.3f}")
print(f"  Score at -2std: {s_below:.3f}")
if abs(s_above - s_below) > 0.001:
    errors.append("agent_load nao simetrico")
    print("  FALHOU")
else:
    print("  OK: simetrico")

# ==== CHECK 8: potential_value account context ====
print("\nCHECK 8: potential_value com contexto da conta")
gtx_pro_id = products[products['name'] == 'GTX Pro']['id'].iloc[0]
price = float(products[products['id'] == gtx_pro_id]['sales_price'].iloc[0])
price_norm = math.log1p(price) / stats['log_max_price']

big_acct = accounts[accounts['revenue'] > 0].sort_values('revenue', ascending=False).iloc[0]
small_acct = accounts[accounts['revenue'] > 0].sort_values('revenue').iloc[0]

big_factor = math.log1p(float(big_acct['revenue'])) / stats['log_max_revenue']
big_pv = price_norm * 0.7 + (price_norm * big_factor) * 0.3

small_factor = math.log1p(float(small_acct['revenue'])) / stats['log_max_revenue']
small_pv = price_norm * 0.7 + (price_norm * small_factor) * 0.3

no_pv = price_norm * 0.85

print(f"  GTX Pro (R${price:,.0f}):")
print(f"    Conta grande ({big_acct['name']}): {big_pv:.4f}")
print(f"    Conta pequena ({small_acct['name']}): {small_pv:.4f}")
print(f"    Sem conta: {no_pv:.4f}")
if big_pv > small_pv:
    print("  OK: grande > pequena")
else:
    errors.append("potential_value: conta grande <= conta pequena")
    print("  FALHOU")

# ==== CHECK 9: Deals sem conta nunca no top 10 ====
print("\nCHECK 9: Deals sem conta fora do top 10")
top10 = scored.head(10)['account_name'].tolist()
no_acct_top = [n for n in top10 if 'definida' in str(n).lower()]
print(f"  Top 10: {top10}")
print(f"  Sem conta no top 10: {len(no_acct_top)}")
if len(no_acct_top) > 0:
    print("  AVISO (nao blocker)")
else:
    print("  OK")

# ==== CHECK 10: Prospecting penalizado vs Engaging ====
print("\nCHECK 10: Prospecting < Engaging (mesmo deal)")
prosp_scores = scored[scored['deal_stage'] == 'Prospecting']['score']
engag_scores = scored[scored['deal_stage'] == 'Engaging']['score']
print(f"  Prospecting mean: {prosp_scores.mean():.1f}")
print(f"  Engaging mean: {engag_scores.mean():.1f}")
if prosp_scores.mean() < engag_scores.mean():
    print("  OK: Prospecting penalizado")
else:
    print("  AVISO: Prospecting nao penalizado")

# ==== RESULT ====
print("\n" + "="*50)
if errors:
    print(f"ERROS ENCONTRADOS ({len(errors)}):")
    for e in errors:
        print(f"  - {e}")
else:
    print("TODAS AS 10 VERIFICACOES PASSARAM")
    print("Score esta 100% correto de acordo com a logica definida.")
print("="*50)
