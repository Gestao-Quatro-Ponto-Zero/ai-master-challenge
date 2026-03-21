"""
Fase 7 — Sponsorship Explorer (dados granulares para filtros interativos)
==========================================================================
Gera cruzamentos de organico vs patrocinado por todas as dimensoes
para permitir filtro interativo no dashboard.
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "assets", "social_media_dataset.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "analysis", "outputs")

print("Carregando dataset...")
df = pd.read_csv(CSV_PATH)
df["engagement_rate"] = ((df["likes"] + df["shares"] + df["comments_count"]) / df["views"]) * 100
df["reach_score"] = df["views"] / df["follower_count"]  # alcance relativo
df["cost_per_engagement"] = df["views"] / (df["likes"] + df["shares"] + df["comments_count"])  # custo implicito

def classify_tier(f):
    if f < 10_000: return "Nano (< 10K)"
    elif f < 50_000: return "Micro (10K-50K)"
    elif f < 100_000: return "Mid (50K-100K)"
    elif f < 500_000: return "Macro (100K-500K)"
    else: return "Mega (500K+)"

df["creator_tier"] = df["follower_count"].apply(classify_tier)

# Dimensoes disponiveis para filtro
DIMENSIONS = {
    "platform": df["platform"].unique().tolist(),
    "content_category": df["content_category"].unique().tolist(),
    "content_type": df["content_type"].unique().tolist(),
    "creator_tier": ["Nano (< 10K)", "Micro (10K-50K)", "Mid (50K-100K)", "Macro (100K-500K)", "Mega (500K+)"],
    "audience_age": df["audience_age_distribution"].unique().tolist(),
    "audience_location": df["audience_location"].unique().tolist(),
    "sponsor_category": df[df["is_sponsored"] == True]["sponsor_category"].dropna().unique().tolist(),
}

print(f"Dimensoes: {list(DIMENSIONS.keys())}")

# ============================================================
# 1. CRUZAMENTO POR CADA DIMENSAO INDIVIDUAL
# ============================================================
print("\nGerando cruzamentos por dimensao...")

results = []

# Para cada dimensao, calcular organico vs patrocinado
dim_columns = {
    "platform": "platform",
    "content_category": "content_category",
    "content_type": "content_type",
    "creator_tier": "creator_tier",
    "audience_age": "audience_age_distribution",
    "audience_location": "audience_location",
}

for dim_name, col_name in dim_columns.items():
    for value in df[col_name].unique():
        subset = df[df[col_name] == value]
        organic = subset[subset["is_sponsored"] == False]
        sponsored = subset[subset["is_sponsored"] == True]

        if len(organic) < 10 or len(sponsored) < 10:
            continue

        results.append({
            "dimension": dim_name,
            "value": str(value),
            "organic_engagement": round(float(organic["engagement_rate"].mean()), 4),
            "sponsored_engagement": round(float(sponsored["engagement_rate"].mean()), 4),
            "lift": round(float(sponsored["engagement_rate"].mean() - organic["engagement_rate"].mean()), 4),
            "organic_reach": round(float(organic["reach_score"].mean()), 4),
            "sponsored_reach": round(float(sponsored["reach_score"].mean()), 4),
            "organic_cpe": round(float(organic["cost_per_engagement"].mean()), 4),
            "sponsored_cpe": round(float(sponsored["cost_per_engagement"].mean()), 4),
            "organic_posts": int(len(organic)),
            "sponsored_posts": int(len(sponsored)),
            "organic_avg_likes": round(float(organic["likes"].mean()), 1),
            "sponsored_avg_likes": round(float(sponsored["likes"].mean()), 1),
            "organic_avg_shares": round(float(organic["shares"].mean()), 1),
            "sponsored_avg_shares": round(float(sponsored["shares"].mean()), 1),
            "organic_avg_comments": round(float(organic["comments_count"].mean()), 1),
            "sponsored_avg_comments": round(float(sponsored["comments_count"].mean()), 1),
            "organic_avg_views": round(float(organic["views"].mean()), 1),
            "sponsored_avg_views": round(float(sponsored["views"].mean()), 1),
        })

# ============================================================
# 2. CRUZAMENTO POR PARES DE DIMENSOES (plataforma × tier, etc.)
# ============================================================
print("Gerando cruzamentos por pares...")

pair_combos = [
    ("platform", "platform", "creator_tier", "creator_tier"),
    ("platform", "platform", "content_category", "content_category"),
    ("platform", "platform", "audience_age", "audience_age_distribution"),
    ("creator_tier", "creator_tier", "content_category", "content_category"),
    ("creator_tier", "creator_tier", "audience_age", "audience_age_distribution"),
]

pairs = []
for dim1_name, col1, dim2_name, col2 in pair_combos:
    for v1 in df[col1].unique():
        for v2 in df[col2].unique():
            subset = df[(df[col1] == v1) & (df[col2] == v2)]
            organic = subset[subset["is_sponsored"] == False]
            sponsored = subset[subset["is_sponsored"] == True]

            if len(organic) < 5 or len(sponsored) < 5:
                continue

            pairs.append({
                "dim1": dim1_name,
                "val1": str(v1),
                "dim2": dim2_name,
                "val2": str(v2),
                "organic_engagement": round(float(organic["engagement_rate"].mean()), 4),
                "sponsored_engagement": round(float(sponsored["engagement_rate"].mean()), 4),
                "lift": round(float(sponsored["engagement_rate"].mean() - organic["engagement_rate"].mean()), 4),
                "organic_reach": round(float(organic["reach_score"].mean()), 4),
                "sponsored_reach": round(float(sponsored["reach_score"].mean()), 4),
                "organic_cpe": round(float(organic["cost_per_engagement"].mean()), 4),
                "sponsored_cpe": round(float(sponsored["cost_per_engagement"].mean()), 4),
                "organic_posts": int(len(organic)),
                "sponsored_posts": int(len(sponsored)),
            })

# ============================================================
# 3. SPONSOR CATEGORY BREAKDOWN
# ============================================================
print("Gerando breakdown por sponsor category...")

sponsor_detail = []
for cat in df[df["is_sponsored"] == True]["sponsor_category"].dropna().unique():
    for plat in df["platform"].unique():
        subset_spon = df[(df["is_sponsored"] == True) & (df["sponsor_category"] == cat) & (df["platform"] == plat)]
        subset_org = df[(df["is_sponsored"] == False) & (df["platform"] == plat)]

        if len(subset_spon) < 5:
            continue

        for tier in df["creator_tier"].unique():
            tier_spon = subset_spon[subset_spon["creator_tier"] == tier]
            tier_org = subset_org[subset_org["creator_tier"] == tier]

            if len(tier_spon) < 3 or len(tier_org) < 3:
                continue

            sponsor_detail.append({
                "sponsor_category": str(cat),
                "platform": str(plat),
                "creator_tier": str(tier),
                "sponsored_engagement": round(float(tier_spon["engagement_rate"].mean()), 4),
                "organic_engagement": round(float(tier_org["engagement_rate"].mean()), 4),
                "lift": round(float(tier_spon["engagement_rate"].mean() - tier_org["engagement_rate"].mean()), 4),
                "sponsored_posts": int(len(tier_spon)),
            })

# ============================================================
# SALVAR
# ============================================================
print("\n--- Salvando ---")

output = {
    "_meta": {
        "generated_at": datetime.now().isoformat(),
        "data_source": "dataset_v1",
        "analysis": "sponsorship_explorer",
    },
    "dimensions": DIMENSIONS,
    "by_dimension": results,
    "by_pair": pairs,
    "by_sponsor_detail": sponsor_detail,
    "totals": {
        "organic_engagement": round(float(df[df["is_sponsored"] == False]["engagement_rate"].mean()), 4),
        "sponsored_engagement": round(float(df[df["is_sponsored"] == True]["engagement_rate"].mean()), 4),
        "organic_reach": round(float(df[df["is_sponsored"] == False]["reach_score"].mean()), 4),
        "sponsored_reach": round(float(df[df["is_sponsored"] == True]["reach_score"].mean()), 4),
        "organic_cpe": round(float(df[df["is_sponsored"] == False]["cost_per_engagement"].mean()), 4),
        "sponsored_cpe": round(float(df[df["is_sponsored"] == True]["cost_per_engagement"].mean()), 4),
        "total_organic": int(len(df[df["is_sponsored"] == False])),
        "total_sponsored": int(len(df[df["is_sponsored"] == True])),
    },
}

path = os.path.join(OUTPUT_DIR, "sponsorship_explorer.json")
with open(path, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False, default=str)
print(f"  -> sponsorship_explorer.json ({len(results)} dimensoes, {len(pairs)} pares, {len(sponsor_detail)} detalhes)")

print("\nSponorship Explorer concluido!")
