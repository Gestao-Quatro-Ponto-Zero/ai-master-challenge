"""
1) Testa se vendedor x is_new_combo INTERAGEM (ou só somam)
2) Constrói buckets empíricos com fallback hierárquico
3) Aplica o score em deals Engaging reais e mostra decomposição
"""
import pandas as pd
import numpy as np
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
prod = pd.read_csv(DATA / "products.csv")
team = pd.read_csv(DATA / "sales_teams.csv")
acc = pd.read_csv(DATA / "accounts.csv")
pipe = pd.read_csv(DATA / "sales_pipeline.csv")
pipe["product"] = pipe["product"].replace({"GTXPro": "GTX Pro"})
pipe["engage_date"] = pd.to_datetime(pipe["engage_date"])
pipe["close_date"] = pd.to_datetime(pipe["close_date"])

df = pipe.merge(prod, on="product", how="left") \
         .merge(team, on="sales_agent", how="left") \
         .merge(acc, on="account", how="left", suffixes=("", "_acc"))

closed = df[df["deal_stage"].isin(["Won", "Lost"])].copy()

# --- Recalcula features para todos os deals (closed + open) ---
df_sorted = df.sort_values(["engage_date"]).reset_index(drop=True)

# is_new_combo: este (vendedor, conta, produto) já apareceu antes em qualquer stage?
# Para deals sem account, vai como NaN.
seen_combo = set()
is_new = []
for _, row in df_sorted.iterrows():
    if pd.isna(row["account"]):
        is_new.append(np.nan)
        continue
    key = (row["sales_agent"], row["account"], row["product"])
    is_new.append(key not in seen_combo)
    seen_combo.add(key)
df_sorted["is_new_combo"] = is_new

# Histórico do vendedor: win rate em deals fechados
agent_wr = closed.groupby("sales_agent").apply(
    lambda x: (x["deal_stage"] == "Won").mean()
).rename("agent_wr")
agent_n = closed.groupby("sales_agent").size().rename("agent_n")

df_sorted = df_sorted.merge(agent_wr, on="sales_agent", how="left")
df_sorted = df_sorted.merge(agent_n, on="sales_agent", how="left")

# Tier do vendedor: top / mid / bottom (terços do win rate)
q33, q66 = agent_wr.quantile([0.33, 0.66])
def tier(wr):
    if pd.isna(wr): return "unknown"
    if wr >= q66: return "top"
    if wr >= q33: return "mid"
    return "low"
df_sorted["agent_tier"] = df_sorted["agent_wr"].apply(tier)

closed_enriched = df_sorted[df_sorted["deal_stage"].isin(["Won", "Lost"])].copy()

def section(t):
    print("\n" + "=" * 78); print(t); print("=" * 78)

# ============================================================
# (1) INTERAÇÃO: vendedor x is_new_combo
# ============================================================
section("INTERAÇÃO: tier_vendedor x is_new_combo (win rate observado)")
matrix = closed_enriched.dropna(subset=["is_new_combo"]).pivot_table(
    index="agent_tier", columns="is_new_combo",
    values="deal_stage",
    aggfunc=lambda x: (x == "Won").mean()
).round(3)
counts = closed_enriched.dropna(subset=["is_new_combo"]).pivot_table(
    index="agent_tier", columns="is_new_combo",
    values="opportunity_id", aggfunc="count"
)
print("Win rate:")
print(matrix.to_string())
print("\nVolume (deals fechados em cada bucket):")
print(counts.to_string())

# Teste: é aditivo ou multiplicativo?
section("ADITIVO vs INTERAÇÃO REAL")
base = (closed_enriched["deal_stage"] == "Won").mean()
print(f"baseline global: {base:.3f}")

for tier_name in ["top", "mid", "low"]:
    for new in [True, False]:
        sub = closed_enriched[(closed_enriched["agent_tier"] == tier_name) &
                              (closed_enriched["is_new_combo"] == new)]
        if len(sub) < 30:
            continue
        wr = (sub["deal_stage"] == "Won").mean()
        # Predição aditiva: base + tier_effect + combo_effect
        tier_effect = (closed_enriched[closed_enriched["agent_tier"] == tier_name]["deal_stage"] == "Won").mean() - base
        combo_effect = (closed_enriched[closed_enriched["is_new_combo"] == new]["deal_stage"] == "Won").mean() - base
        pred_add = base + tier_effect + combo_effect
        delta = wr - pred_add
        print(f"  {tier_name:>4} + new={str(new):<5}: real={wr:.3f}  aditivo={pred_add:.3f}  delta={delta:+.3f}  (n={len(sub)})")

# ============================================================
# (2) BUCKETS EMPÍRICOS COM FALLBACK
# ============================================================
section("BUCKETS EMPÍRICOS — win rate por (tier x is_new_combo) usado como score base")
buckets = closed_enriched.dropna(subset=["is_new_combo"]).groupby(
    ["agent_tier", "is_new_combo"]
).agg(
    n=("opportunity_id", "size"),
    wr=("deal_stage", lambda x: (x == "Won").mean())
).round(3)
print(buckets.to_string())

# Smoothed: shrink to global mean if n < 50
def smoothed(wr, n, prior=base, k=30):
    return (n * wr + k * prior) / (n + k)

buckets["smoothed_wr"] = buckets.apply(lambda r: round(smoothed(r["wr"], r["n"]), 3), axis=1)
print("\ncom smoothing (k=30):")
print(buckets.to_string())

# ============================================================
# (3) FUNÇÃO DE SCORE
# ============================================================
def score_deal(row, bucket_lookup, base_wr=base, agent_wr_map=None):
    """
    Retorna dict com decomposição completa do score de um deal.
    """
    # 1. Probabilidade base (lookup empírico, com fallback)
    tier = row["agent_tier"]
    is_new = row["is_new_combo"]

    if pd.isna(is_new) or tier == "unknown":
        # Fallback nível 1: win rate do vendedor sozinho
        if pd.notna(row.get("agent_wr")):
            prob = row["agent_wr"]
            prob_source = f"vendedor histórico (sem dado de combo)"
            confidence = "média"
        else:
            prob = base_wr
            prob_source = "baseline global (sem histórico)"
            confidence = "baixa"
    else:
        try:
            prob = bucket_lookup.loc[(tier, is_new), "smoothed_wr"]
            prob_source = f"bucket (tier={tier}, novo={is_new})"
            n = bucket_lookup.loc[(tier, is_new), "n"]
            confidence = "alta" if n >= 100 else "média"
        except KeyError:
            prob = base_wr
            prob_source = "fallback global"
            confidence = "baixa"

    # 2. Valor potencial = sales_price (já confirmamos: ≈ close_value)
    value = row["sales_price"]

    # 3. Expected value
    ev = prob * value

    # 4. Categoria de ação
    if pd.isna(is_new):
        action = "QUALIFICAR (faltam dados)"
    elif prob >= 0.70 and ev >= 1000:
        action = "AGIR HOJE — alta chance + valor"
    elif prob >= 0.70:
        action = "FECHAR — alta chance"
    elif prob >= 0.60 and ev >= 2000:
        action = "PRIORIZAR — bom retorno esperado"
    elif prob < 0.55:
        action = "REVISAR — baixa chance"
    else:
        action = "ACOMPANHAR"

    return {
        "opportunity_id": row["opportunity_id"],
        "sales_agent": row["sales_agent"],
        "account": row["account"],
        "product": row["product"],
        "sales_price": value,
        "agent_tier": tier,
        "agent_wr": round(row.get("agent_wr", np.nan), 3) if pd.notna(row.get("agent_wr")) else None,
        "is_new_combo": is_new,
        "prob_estimada": round(prob, 3),
        "prob_source": prob_source,
        "expected_value": round(ev, 0),
        "confidence": confidence,
        "action": action,
    }

# ============================================================
# (4) APLICAR EM DEALS ENGAGING REAIS — focar no Darcel (194 abertos)
# ============================================================
section("APLICAÇÃO: 5 deals reais do Darcel Schlecht (194 deals abertos)")
darcel = df_sorted[
    (df_sorted["sales_agent"] == "Darcel Schlecht") &
    (df_sorted["deal_stage"] == "Engaging")
].head(5)

results = [score_deal(row, buckets) for _, row in darcel.iterrows()]
for r in results:
    print()
    for k, v in r.items():
        print(f"  {k:<18} {v}")

section("APLICAÇÃO: 3 deals VARIADOS para mostrar contraste")
# Pega um Engaging com is_new_combo=True, um com False, e um sem account
sample_new = df_sorted[(df_sorted["deal_stage"] == "Engaging") & (df_sorted["is_new_combo"] == True)].head(1)
sample_old = df_sorted[(df_sorted["deal_stage"] == "Engaging") & (df_sorted["is_new_combo"] == False)].head(1)
sample_na = df_sorted[(df_sorted["deal_stage"] == "Engaging") & (df_sorted["account"].isna())].head(1)

for label, sample in [("COMBO NOVO", sample_new), ("COMBO RECORRENTE", sample_old), ("SEM CONTA (Engaging incompleto)", sample_na)]:
    print(f"\n--- {label} ---")
    for _, row in sample.iterrows():
        r = score_deal(row, buckets)
        for k, v in r.items():
            print(f"  {k:<18} {v}")
