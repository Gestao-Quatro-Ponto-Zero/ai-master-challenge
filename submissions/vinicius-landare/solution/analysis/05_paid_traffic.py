"""
Fase 5 — Análise de Tráfego Pago (Campanhas Patrocinadas)
==========================================================
Extrai métricas de ROI, CPE e lift de patrocínio do dataset.
Gera JSONs para a tab "Tráfego Pago" no dashboard.
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
from scipy import stats as scipy_stats

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "assets", "social_media_dataset.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "analysis", "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

META = {
    "generated_at": datetime.now().isoformat(),
    "data_source": "dataset_v1",
    "analysis": "paid_traffic",
}

print("Carregando dataset...")
df = pd.read_csv(CSV_PATH)
df["engagement_rate"] = ((df["likes"] + df["shares"] + df["comments_count"]) / df["views"]) * 100

def classify_tier(f):
    if f < 10_000: return "Nano (< 10K)"
    elif f < 50_000: return "Micro (10K-50K)"
    elif f < 100_000: return "Mid (50K-100K)"
    elif f < 500_000: return "Macro (100K-500K)"
    else: return "Mega (500K+)"

df["creator_tier"] = df["follower_count"].apply(classify_tier)

# ============================================================
# SEPARAR PATROCINADO VS ORGÂNICO
# ============================================================
sponsored = df[df["is_sponsored"] == True].copy()
organic = df[df["is_sponsored"] == False].copy()

print(f"Posts patrocinados: {len(sponsored):,}")
print(f"Posts orgânicos: {len(organic):,}")

# ============================================================
# 1. KPIs GERAIS DE TRÁFEGO PAGO
# ============================================================
print("\n" + "=" * 70)
print("KPIs GERAIS DE TRÁFEGO PAGO")
print("=" * 70)

# Engagement médio orgânico (baseline)
baseline_eng = organic["engagement_rate"].mean()
sponsored_eng = sponsored["engagement_rate"].mean()
lift_geral = sponsored_eng - baseline_eng

# CPE simulado: inverso normalizado do engagement (menor engagement = maior custo)
# Normalizamos para uma escala relativa
sponsored["cpe_score"] = 1 / (sponsored["engagement_rate"] / 100)

kpis = {
    "total_sponsored_posts": int(len(sponsored)),
    "total_organic_posts": int(len(organic)),
    "avg_engagement_sponsored": round(float(sponsored_eng), 4),
    "avg_engagement_organic": round(float(baseline_eng), 4),
    "lift_geral_pp": round(float(lift_geral), 4),
    "avg_cpe_score": round(float(sponsored["cpe_score"].mean()), 2),
    "sponsor_categories": int(sponsored["sponsor_category"].nunique()),
    "platforms_with_sponsored": sponsored["platform"].nunique(),
}

# Teste de significância: patrocinado vs orgânico
from scipy.stats import mannwhitneyu
stat, p_val = mannwhitneyu(organic["engagement_rate"].values, sponsored["engagement_rate"].values, alternative="two-sided")
kpis["significance"] = {
    "is_significant": bool(p_val < 0.05),
    "p_value": round(float(p_val), 6),
    "test": "mann_whitney_u",
}

print(f"Engagement patrocinado: {sponsored_eng:.4f}%")
print(f"Engagement orgânico: {baseline_eng:.4f}%")
print(f"Lift geral: {lift_geral:+.4f}pp")
print(f"Significativo: {kpis['significance']['is_significant']} (p={kpis['significance']['p_value']})")

# ============================================================
# 2. ROI POR CATEGORIA DE SPONSOR
# ============================================================
print("\n" + "=" * 70)
print("ROI POR CATEGORIA DE SPONSOR")
print("=" * 70)

# Para cada sponsor_category, calcular o lift vs orgânico geral
sponsor_roi = sponsored.groupby("sponsor_category").agg(
    posts=("id", "count"),
    avg_engagement=("engagement_rate", "mean"),
    avg_views=("views", "mean"),
    avg_likes=("likes", "mean"),
    avg_shares=("shares", "mean"),
    avg_comments=("comments_count", "mean"),
    avg_cpe=("cpe_score", "mean"),
).round(4).reset_index()

sponsor_roi["lift_vs_organic"] = round(sponsor_roi["avg_engagement"] - baseline_eng, 4)
sponsor_roi["roi_positive"] = sponsor_roi["lift_vs_organic"] > 0
sponsor_roi = sponsor_roi.sort_values("lift_vs_organic", ascending=False)

print(sponsor_roi[["sponsor_category", "posts", "avg_engagement", "lift_vs_organic", "roi_positive"]].to_string(index=False))

pct_positive = sponsor_roi["roi_positive"].mean() * 100
print(f"\nCategorias com ROI positivo: {pct_positive:.0f}%")

# ============================================================
# 3. ROI POR SPONSOR × PLATAFORMA
# ============================================================
print("\n" + "=" * 70)
print("ROI POR SPONSOR × PLATAFORMA")
print("=" * 70)

# Calcular baseline por plataforma (orgânico)
organic_by_platform = organic.groupby("platform")["engagement_rate"].mean().to_dict()

sponsor_platform = sponsored.groupby(["sponsor_category", "platform"]).agg(
    posts=("id", "count"),
    avg_engagement=("engagement_rate", "mean"),
).round(4).reset_index()

# Lift relativo ao orgânico da mesma plataforma
sponsor_platform["organic_baseline"] = sponsor_platform["platform"].map(organic_by_platform)
sponsor_platform["lift"] = round(sponsor_platform["avg_engagement"] - sponsor_platform["organic_baseline"], 4)
sponsor_platform = sponsor_platform.sort_values("lift", ascending=False)

# Top 10 e Bottom 10
top_campaigns = sponsor_platform.head(10)
bottom_campaigns = sponsor_platform.tail(10)

print("--- Top 10 Campanhas ---")
print(top_campaigns[["sponsor_category", "platform", "posts", "avg_engagement", "lift"]].to_string(index=False))
print("\n--- Bottom 10 Campanhas ---")
print(bottom_campaigns[["sponsor_category", "platform", "posts", "avg_engagement", "lift"]].to_string(index=False))

# ============================================================
# 4. ROI POR SPONSOR × TIER DE CREATOR
# ============================================================
print("\n" + "=" * 70)
print("ROI POR SPONSOR × TIER")
print("=" * 70)

organic_by_tier = organic.groupby("creator_tier")["engagement_rate"].mean().to_dict()

sponsor_tier = sponsored.groupby(["sponsor_category", "creator_tier"]).agg(
    posts=("id", "count"),
    avg_engagement=("engagement_rate", "mean"),
).round(4).reset_index()

sponsor_tier["organic_baseline"] = sponsor_tier["creator_tier"].map(organic_by_tier)
sponsor_tier["lift"] = round(sponsor_tier["avg_engagement"] - sponsor_tier["organic_baseline"], 4)

# ============================================================
# 5. RECOMENDAÇÃO DE BUDGET
# ============================================================
print("\n" + "=" * 70)
print("RECOMENDAÇÃO DE BUDGET")
print("=" * 70)

# Top 5 onde investir (maior lift positivo com volume)
invest = sponsor_platform[
    (sponsor_platform["lift"] > 0) & (sponsor_platform["posts"] >= 10)
].head(5)

# Top 5 onde cortar (maior lift negativo)
cut = sponsor_platform[
    (sponsor_platform["lift"] < 0) & (sponsor_platform["posts"] >= 10)
].tail(5)

budget_recommendation = {
    "invest": invest[["sponsor_category", "platform", "lift", "posts"]].to_dict(orient="records"),
    "cut": cut[["sponsor_category", "platform", "lift", "posts"]].to_dict(orient="records"),
    "estimated_lift_if_reallocated": round(
        float(invest["lift"].mean() - cut["lift"].mean()), 4
    ) if len(invest) > 0 and len(cut) > 0 else 0,
}

print(f"Investir em: {len(invest)} combinações")
print(f"Cortar de: {len(cut)} combinações")
print(f"Lift estimado se realocar: {budget_recommendation['estimated_lift_if_reallocated']:+.4f}pp")

# ============================================================
# SALVAR RESULTADOS
# ============================================================
print("\n--- Salvando resultados ---")

def save_json(data, filename):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    print(f"  -> {filename}")

# paid_traffic_summary.json — KPIs gerais
save_json({
    "_meta": META,
    "kpis": kpis,
    "pct_roi_positive": round(float(pct_positive), 1),
}, "paid_traffic_summary.json")

# campaign_roi.json — ROI por categoria
save_json({
    "_meta": META,
    "data": json.loads(sponsor_roi.to_json(orient="records", force_ascii=False)),
}, "campaign_roi.json")

# campaign_platform_roi.json — ROI por sponsor × plataforma
save_json({
    "_meta": META,
    "data": json.loads(sponsor_platform.to_json(orient="records", force_ascii=False)),
    "top_campaigns": json.loads(top_campaigns.to_json(orient="records", force_ascii=False)),
    "bottom_campaigns": json.loads(bottom_campaigns.to_json(orient="records", force_ascii=False)),
}, "campaign_platform_roi.json")

# campaign_tier_roi.json — ROI por sponsor × tier
save_json({
    "_meta": META,
    "data": json.loads(sponsor_tier.to_json(orient="records", force_ascii=False)),
}, "campaign_tier_roi.json")

# budget_allocation.json — Recomendação de budget
save_json({
    "_meta": META,
    **budget_recommendation,
}, "budget_allocation.json")

print("\nAnálise de tráfego pago concluída!")
