"""
Fase 6 — Ranking de Influenciadores
=====================================
Calcula score composto (0-100) para cada creator no dataset.
Gera influencer_ranking.json para a tab "Ranking" no dashboard.
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "assets", "social_media_dataset.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "analysis", "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

META = {
    "generated_at": datetime.now().isoformat(),
    "data_source": "dataset_v1",
    "analysis": "influencer_ranking",
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
# 1. MÉTRICAS POR CREATOR
# ============================================================
print("\nCalculando métricas por creator...")

creator_stats = df.groupby("creator_id").agg(
    creator_name=("creator_name", "first"),
    total_posts=("id", "count"),
    avg_engagement=("engagement_rate", "mean"),
    std_engagement=("engagement_rate", "std"),
    median_engagement=("engagement_rate", "median"),
    avg_views=("views", "mean"),
    avg_likes=("likes", "mean"),
    avg_shares=("shares", "mean"),
    avg_comments=("comments_count", "mean"),
    follower_count=("follower_count", "first"),
    creator_tier=("creator_tier", "first"),
    primary_platform=("platform", lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else "unknown"),
    primary_category=("content_category", lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else "unknown"),
    primary_content_type=("content_type", lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else "unknown"),
    sponsored_posts=("is_sponsored", "sum"),
    total_sponsored=("is_sponsored", "count"),
).reset_index()

# Consistência: inverso do std (menor std = mais consistente)
creator_stats["consistency"] = creator_stats["std_engagement"].fillna(0)

# Taxa de patrocínio
creator_stats["sponsored_rate"] = round(creator_stats["sponsored_posts"] / creator_stats["total_sponsored"] * 100, 2)

# ============================================================
# 2. LIFT DE PATROCÍNIO POR CREATOR
# ============================================================
print("Calculando lift de patrocínio...")

# Para creators com posts orgânicos E patrocinados
organic_by_creator = df[df["is_sponsored"] == False].groupby("creator_id")["engagement_rate"].mean()
sponsored_by_creator = df[df["is_sponsored"] == True].groupby("creator_id")["engagement_rate"].mean()

creator_stats["eng_organic"] = creator_stats["creator_id"].map(organic_by_creator)
creator_stats["eng_sponsored"] = creator_stats["creator_id"].map(sponsored_by_creator)
creator_stats["sponsorship_lift"] = creator_stats["eng_sponsored"] - creator_stats["eng_organic"]

# ============================================================
# 3. CALCULAR SCORE COMPOSTO (0-100)
# ============================================================
print("Calculando scores...")

def percentile_rank(series):
    """Converte uma série em percentile rank (0-100)."""
    return series.rank(pct=True, na_option="bottom") * 100

# Engagement percentile (maior = melhor)
creator_stats["engagement_pctl"] = percentile_rank(creator_stats["avg_engagement"])

# Consistência percentile (menor std = melhor, então invertemos)
creator_stats["consistency_pctl"] = percentile_rank(-creator_stats["consistency"])

# Volume percentile (mais posts = melhor)
creator_stats["volume_pctl"] = percentile_rank(creator_stats["total_posts"])

# Sponsorship lift percentile (maior lift = melhor)
creator_stats["sponsorship_lift_pctl"] = percentile_rank(creator_stats["sponsorship_lift"].fillna(0))

# Audience reach percentile (mais views = melhor)
creator_stats["reach_pctl"] = percentile_rank(creator_stats["avg_views"])

# Score composto
creator_stats["score"] = (
    creator_stats["engagement_pctl"] * 0.35 +
    creator_stats["consistency_pctl"] * 0.25 +
    creator_stats["volume_pctl"] * 0.15 +
    creator_stats["sponsorship_lift_pctl"] * 0.15 +
    creator_stats["reach_pctl"] * 0.10
).round(1)

# ============================================================
# 4. CLASSIFICAÇÃO DE AÇÃO
# ============================================================
print("Classificando ações...")

def classify_action(score):
    if score >= 80:
        return "incentivar"
    elif score >= 60:
        return "manter"
    elif score >= 40:
        return "alinhar"
    else:
        return "reavaliar"

creator_stats["action"] = creator_stats["score"].apply(classify_action)

# Ordenar por score
creator_stats = creator_stats.sort_values("score", ascending=False).reset_index(drop=True)
creator_stats["rank"] = range(1, len(creator_stats) + 1)

# ============================================================
# 5. ESTATÍSTICAS DO RANKING
# ============================================================
print("\n" + "=" * 70)
print("ESTATÍSTICAS DO RANKING")
print("=" * 70)

action_counts = creator_stats["action"].value_counts()
print(f"\nTotal de creators: {len(creator_stats):,}")
print(f"Incentivar: {action_counts.get('incentivar', 0):,}")
print(f"Manter: {action_counts.get('manter', 0):,}")
print(f"Alinhar: {action_counts.get('alinhar', 0):,}")
print(f"Reavaliar: {action_counts.get('reavaliar', 0):,}")

print(f"\nTop 5 creators:")
top5 = creator_stats.head(5)
for _, row in top5.iterrows():
    print(f"  #{row['rank']} {row['creator_name']} (score: {row['score']}, eng: {row['avg_engagement']:.2f}%, tier: {row['creator_tier']})")

# ============================================================
# 6. DISTRIBUIÇÃO POR TIER × AÇÃO
# ============================================================
tier_action = creator_stats.groupby(["creator_tier", "action"]).size().unstack(fill_value=0)
print(f"\n--- Distribuição Tier × Ação ---")
print(tier_action.to_string())

# ============================================================
# SALVAR RESULTADOS
# ============================================================
print("\n--- Salvando resultados ---")

# Selecionar colunas para output (sem os percentis internos)
output_cols = [
    "rank", "creator_id", "creator_name", "score", "action",
    "avg_engagement", "std_engagement", "median_engagement", "consistency",
    "total_posts", "follower_count", "creator_tier",
    "primary_platform", "primary_category", "primary_content_type",
    "sponsored_posts", "sponsored_rate",
    "eng_organic", "eng_sponsored", "sponsorship_lift",
    "avg_views", "avg_likes", "avg_shares", "avg_comments",
]

output_df = creator_stats[output_cols].copy()
output_df = output_df.round(4)

# influencer_ranking.json — ranking completo
ranking_data = json.loads(output_df.to_json(orient="records", force_ascii=False))

ranking_output = {
    "_meta": META,
    "total_creators": len(ranking_data),
    "action_summary": {
        "incentivar": int(action_counts.get("incentivar", 0)),
        "manter": int(action_counts.get("manter", 0)),
        "alinhar": int(action_counts.get("alinhar", 0)),
        "reavaliar": int(action_counts.get("reavaliar", 0)),
    },
    "score_distribution": {
        "mean": round(float(creator_stats["score"].mean()), 1),
        "median": round(float(creator_stats["score"].median()), 1),
        "std": round(float(creator_stats["score"].std()), 1),
        "min": round(float(creator_stats["score"].min()), 1),
        "max": round(float(creator_stats["score"].max()), 1),
    },
    "data": ranking_data,
}

path = os.path.join(OUTPUT_DIR, "influencer_ranking.json")
with open(path, "w", encoding="utf-8") as f:
    json.dump(ranking_output, f, indent=2, ensure_ascii=False, default=str)
print(f"  -> influencer_ranking.json")

# tier_action_distribution.json — distribuição tier × ação
tier_action_data = tier_action.reset_index().to_dict(orient="records")
tier_action_output = {
    "_meta": META,
    "data": tier_action_data,
}
path = os.path.join(OUTPUT_DIR, "tier_action_distribution.json")
with open(path, "w", encoding="utf-8") as f:
    json.dump(tier_action_output, f, indent=2, ensure_ascii=False, default=str)
print(f"  -> tier_action_distribution.json")

print("\nRanking de influenciadores concluído!")
