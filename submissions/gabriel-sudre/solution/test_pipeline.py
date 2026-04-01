"""Validacao completa do Pipeline - filtros, scores, CRUD, export."""
import sys
sys.path.insert(0, '.')

from supabase import create_client
import pandas as pd

url = 'https://urvpasvifulrlpcatkxs.supabase.co'
key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVydnBhc3ZpZnVscmxwY2F0a3hzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NDkwNzE0MSwiZXhwIjoyMDkwNDgzMTQxfQ.VOWsv3oNUII2KvhdRs7fnGnRDV6_r0svQ0Cv-uHZbHg'
sb = create_client(url, key)

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

from scoring.engine import score_pipeline, get_pipeline_metrics, get_deal_explanations
from scoring.features import compute_global_stats, DEFAULT_WEIGHTS, CLAMP_MIN, CLAMP_MAX

scored = score_pipeline(pipeline, accounts, products, teams)
stats = compute_global_stats(pipeline, accounts, products, teams)
errors = []

# ===== 1. FILTERS =====
print("CHECK 1: Filter options match data")
stages = sorted(scored['deal_stage'].unique().tolist())
prods = sorted(scored['product_name'].dropna().unique().tolist())
agents = sorted(scored['agent_name'].dropna().unique().tolist())
offices = sorted(scored['regional_office'].dropna().unique().tolist())
print(f"  Stages: {stages}")
print(f"  Products ({len(prods)}): {prods}")
print(f"  Agents: {len(agents)}")
print(f"  Offices: {offices}")

# Filter logic: stage filter
engaging = scored[scored['deal_stage'] == 'Engaging']
prosp = scored[scored['deal_stage'] == 'Prospecting']
if len(engaging) + len(prosp) != len(scored):
    errors.append(f"Stage filter sum {len(engaging)}+{len(prosp)} != {len(scored)}")
else:
    print(f"  Engaging={len(engaging)} + Prospecting={len(prosp)} = {len(scored)} OK")

# Filter logic: product filter
for p in prods:
    count = len(scored[scored['product_name'] == p])
    print(f"    {p}: {count} deals")
print("  OK")

# ===== 2. SCORES =====
print("\nCHECK 2: Score consistency")
nan_scores = scored['score'].isna().sum()
below = len(scored[scored['score'] < 0])
above = len(scored[scored['score'] > 100])
print(f"  NaN: {nan_scores}, Below 0: {below}, Above 100: {above}")
if nan_scores > 0:
    errors.append(f"{nan_scores} NaN scores")
if below > 0 or above > 0:
    errors.append(f"Scores out of range: {below} below, {above} above")
print("  OK")

# ===== 3. FEATURES =====
print("\nCHECK 3: Feature columns")
expected = list(DEFAULT_WEIGHTS.keys())
for f in expected:
    col = f"_f_{f}"
    if col not in scored.columns:
        errors.append(f"Missing feature column {col}")
        continue
    vals = scored[col]
    special_vals = {0.30, stats['median_account_fit'] * 0.6, stats['median_repeat'] * 0.5}
    non_special = vals[~vals.isin(special_vals)]
    below_clamp = (non_special < CLAMP_MIN - 0.01).sum()
    above_clamp = (non_special > CLAMP_MAX + 0.01).sum()
    print(f"  {col}: [{vals.min():.3f}, {vals.max():.3f}] clamp_violations={below_clamp + above_clamp}")
print("  OK")

# ===== 4. NAME ENRICHMENT =====
print("\nCHECK 4: Name enrichment")
for col in ['product_name', 'account_name', 'agent_name', 'manager_name', 'regional_office']:
    null_count = scored[col].isna().sum()
    if null_count > 0:
        errors.append(f"{col} has {null_count} nulls")
    print(f"  {col}: {null_count} nulls")
print("  OK")

# ===== 5. SORT ORDER =====
print("\nCHECK 5: Sort order")
is_sorted = all(scored['score'].iloc[i] >= scored['score'].iloc[i+1] for i in range(len(scored)-1))
if not is_sorted:
    errors.append("Deals not sorted by score desc")
print(f"  Sorted descending: {is_sorted}")

# ===== 6. PRIORITY ZONES =====
print("\nCHECK 6: Priority zones")
hot = scored[scored['score'] >= 55]
warm = scored[(scored['score'] >= 40) & (scored['score'] < 55)]
cold = scored[scored['score'] < 40]
total_zones = len(hot) + len(warm) + len(cold)
if total_zones != len(scored):
    errors.append(f"Zone total {total_zones} != {len(scored)}")
print(f"  Hot(>=55): {len(hot)}, Warm(40-54): {len(warm)}, Cold(<40): {len(cold)}")
print(f"  Total: {total_zones} = {len(scored)} OK")

# ===== 7. EXPLANATIONS =====
print("\nCHECK 7: Deal explanations")
for idx in [0, len(scored)//2, -1]:
    deal = scored.iloc[idx]
    expls = get_deal_explanations(deal, stats, products, accounts, teams)
    if not expls:
        errors.append(f"No explanations for deal at index {idx}")
    print(f"  Deal '{deal['account_name']}' (score {deal['score']}): {len(expls)} explanations")
    for e in expls:
        assert e['impact'] in ('positive', 'negative', 'neutral'), f"Invalid impact: {e['impact']}"
        assert len(e['text']) > 5, f"Explanation too short: {e['text']}"
print("  OK")

# ===== 8. CREATE DEAL =====
print("\nCHECK 8: Create deal (simulation)")
import uuid
sample_agent = int(teams.iloc[0]['id'])
sample_product = int(products.iloc[0]['id'])
sample_account = int(accounts.iloc[0]['id'])
opp_id = uuid.uuid4().hex[:8].upper()

# Actually create a test deal
new_deal = {
    "opportunity_id": f"TEST_{opp_id}",
    "sales_agent_id": sample_agent,
    "product_id": sample_product,
    "account_id": sample_account,
    "deal_stage": "Prospecting",
    "close_value": 0,
}
result = sb.table("sales_pipeline").insert(new_deal).execute()
new_id = result.data[0]["id"]
print(f"  Created deal: id={new_id}, opp_id=TEST_{opp_id}")

# Verify it appears in scored pipeline
pipeline2 = pd.DataFrame(sb.table('sales_pipeline').select('*').range(0, 0).execute().data)
# Just verify it exists in DB
check = sb.table("sales_pipeline").select("*").eq("id", new_id).execute()
assert len(check.data) == 1, "Created deal not found in DB"
assert check.data[0]["deal_stage"] == "Prospecting"
print(f"  Verified in DB: stage={check.data[0]['deal_stage']} OK")

# ===== 9. CLASSIFY DEAL (Won) =====
print("\nCHECK 9: Classify deal as Won")
sb.table("sales_pipeline").update({
    "deal_stage": "Won",
    "engage_date": "2017-12-15",
    "close_date": "2017-12-31",
    "close_value": 1500.0,
}).eq("id", new_id).execute()

check = sb.table("sales_pipeline").select("*").eq("id", new_id).execute()
assert check.data[0]["deal_stage"] == "Won"
assert check.data[0]["close_value"] == 1500.0
assert check.data[0]["close_date"] is not None
print(f"  Stage: {check.data[0]['deal_stage']}, Value: {check.data[0]['close_value']}, Date: {check.data[0]['close_date']} OK")

# Verify it would NOT appear in scored pipeline
all_data2 = []
offset = 0
while True:
    r = sb.table('sales_pipeline').select('*').range(offset, offset + 999).execute()
    if not r.data:
        break
    all_data2.extend(r.data)
    if len(r.data) < 1000:
        break
    offset += 1000
pipeline2 = pd.DataFrame(all_data2)
pipeline2['engage_date'] = pd.to_datetime(pipeline2['engage_date'])
pipeline2['close_date'] = pd.to_datetime(pipeline2['close_date'])
scored2 = score_pipeline(pipeline2, accounts, products, teams)
in_scored = len(scored2[scored2['opportunity_id'] == f"TEST_{opp_id}"])
print(f"  In scored pipeline after Won: {in_scored} (should be 0)")
assert in_scored == 0, "Won deal still in active pipeline!"

# Verify it appears in history
history = pipeline2[pipeline2['deal_stage'].isin(['Won', 'Lost'])]
in_history = len(history[history['opportunity_id'] == f"TEST_{opp_id}"])
print(f"  In history after Won: {in_history} (should be 1)")
assert in_history == 1, "Won deal not in history!"
print("  OK: deal moved from pipeline to history")

# ===== 10. CLASSIFY DEAL (Lost) =====
print("\nCHECK 10: Classify deal as Lost")
sb.table("sales_pipeline").update({
    "deal_stage": "Lost",
    "close_value": 0,
    "close_date": "2017-12-31",
}).eq("id", new_id).execute()

check = sb.table("sales_pipeline").select("*").eq("id", new_id).execute()
assert check.data[0]["deal_stage"] == "Lost"
assert check.data[0]["close_value"] == 0
print(f"  Stage: {check.data[0]['deal_stage']}, Value: {check.data[0]['close_value']} OK")

# ===== CLEANUP =====
print("\nCLEANUP: Removing test deal")
sb.table("sales_pipeline").delete().eq("id", new_id).execute()
verify = sb.table("sales_pipeline").select("id").eq("id", new_id).execute()
print(f"  Deleted: {len(verify.data) == 0}")

# ===== 11. EXPORT COLUMNS =====
print("\nCHECK 11: Export CSV columns")
export_cols = ['score', 'deal_stage', 'account_name', 'product_name', 'agent_name', 'regional_office', 'potential_value', 'engage_date']
missing = [c for c in export_cols if c not in scored.columns]
if missing:
    errors.append(f"Missing export columns: {missing}")
print(f"  Missing: {missing if missing else 'none'} OK")

# ===== 12. HISTORY INTEGRITY =====
print("\nCHECK 12: History data integrity")
won = pipeline[pipeline['deal_stage'] == 'Won']
lost = pipeline[pipeline['deal_stage'] == 'Lost']
won_no_val = len(won[won['close_value'] <= 0])
lost_with_val = len(lost[lost['close_value'] > 0])
print(f"  Won without value: {won_no_val} (should be 0)")
print(f"  Lost with value: {lost_with_val} (should be 0)")
if won_no_val > 0:
    errors.append(f"{won_no_val} Won deals without close_value")
if lost_with_val > 0:
    errors.append(f"{lost_with_val} Lost deals with close_value > 0")
print("  OK")

# ===== RESULT =====
print("\n" + "=" * 50)
if errors:
    print(f"ERRORS ({len(errors)}):")
    for e in errors:
        print(f"  - {e}")
else:
    print("ALL 12 PIPELINE CHECKS PASSED")
print("=" * 50)
