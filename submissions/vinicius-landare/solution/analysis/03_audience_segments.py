"""
Fase 4b — Segmentação Estratégica de Audiência
================================================
Em vez de K-Means genérico (que falhou com Silhouette 0.089),
usa segmentação baseada em regras de negócio + análise cruzada
para gerar clusters acionáveis para o time de marketing.
"""

import pandas as pd
import numpy as np
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(os.path.dirname(BASE_DIR), "social_media_dataset.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "analysis", "outputs")

print("Carregando dataset...")
df = pd.read_csv(CSV_PATH)
df["post_date"] = pd.to_datetime(df["post_date"], format="mixed")
df["engagement_rate"] = ((df["likes"] + df["shares"] + df["comments_count"]) / df["views"]) * 100
df["engagement_rate_followers"] = ((df["likes"] + df["shares"] + df["comments_count"]) / df["follower_count"]) * 100

def classify_tier(f):
    if f < 10_000: return "Nano (< 10K)"
    elif f < 50_000: return "Micro (10K-50K)"
    elif f < 100_000: return "Mid (50K-100K)"
    elif f < 500_000: return "Macro (100K-500K)"
    else: return "Mega (500K+)"
df["creator_tier"] = df["follower_count"].apply(classify_tier)

# ============================================================
# SEGMENTAÇÃO 1: Personas de Audiência (Idade × Plataforma × Comportamento)
# ============================================================
print("\n" + "=" * 70)
print("SEGMENTAÇÃO POR PERSONA DE AUDIÊNCIA")
print("=" * 70)

# Criar segmentos baseados em faixa etária + plataforma mais engajada
age_platform = df.groupby(["audience_age_distribution", "platform"]).agg(
    posts=("id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
    avg_likes=("likes", "mean"),
    avg_shares=("shares", "mean"),
    avg_comments=("comments_count", "mean"),
    pct_sponsored=("is_sponsored", "mean"),
).round(4).reset_index()

# Melhor plataforma por faixa etária
best_platform_by_age = age_platform.loc[
    age_platform.groupby("audience_age_distribution")["avg_engagement_rate"].idxmax()
]
print("\n--- Melhor Plataforma por Faixa Etária ---")
print(best_platform_by_age[["audience_age_distribution", "platform", "avg_engagement_rate", "posts"]].to_string(index=False))

# Melhor tipo de conteúdo por faixa etária
age_content = df.groupby(["audience_age_distribution", "content_type"]).agg(
    posts=("id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
).round(4).reset_index()
best_content_by_age = age_content.loc[
    age_content.groupby("audience_age_distribution")["avg_engagement_rate"].idxmax()
]
print("\n--- Melhor Tipo de Conteúdo por Faixa Etária ---")
print(best_content_by_age[["audience_age_distribution", "content_type", "avg_engagement_rate", "posts"]].to_string(index=False))

# Melhor categoria por faixa etária
age_cat = df.groupby(["audience_age_distribution", "content_category"]).agg(
    posts=("id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
).round(4).reset_index()
best_cat_by_age = age_cat.loc[
    age_cat.groupby("audience_age_distribution")["avg_engagement_rate"].idxmax()
]
print("\n--- Melhor Categoria por Faixa Etária ---")
print(best_cat_by_age[["audience_age_distribution", "content_category", "avg_engagement_rate", "posts"]].to_string(index=False))

# ============================================================
# SEGMENTAÇÃO 2: Perfil Cruzado Completo (Persona Cards)
# ============================================================
print("\n" + "=" * 70)
print("PERSONA CARDS — PERFIL COMPLETO POR FAIXA ETÁRIA")
print("=" * 70)

personas = []
for age in ["13-18", "19-25", "26-35", "36-50", "50+"]:
    age_data = df[df["audience_age_distribution"] == age]

    # Melhor plataforma
    plat_eng = age_data.groupby("platform")["engagement_rate"].mean()
    best_plat = plat_eng.idxmax()

    # Melhor tipo de conteúdo
    type_eng = age_data.groupby("content_type")["engagement_rate"].mean()
    best_type = type_eng.idxmax()

    # Melhor categoria
    cat_eng = age_data.groupby("content_category")["engagement_rate"].mean()
    best_cat = cat_eng.idxmax()

    # Melhor gênero (quem mais engaja)
    gender_eng = age_data.groupby("audience_gender_distribution")["engagement_rate"].mean()
    best_gender = gender_eng.idxmax()

    # Melhor tier de creator
    tier_eng = age_data.groupby("creator_tier")["engagement_rate"].mean()
    best_tier = tier_eng.idxmax()

    # Patrocinado vs orgânico
    spon_eng = age_data.groupby("is_sponsored")["engagement_rate"].mean()

    # Melhor horário
    age_data_copy = age_data.copy()
    age_data_copy["hour"] = age_data_copy["post_date"].dt.hour
    hour_eng = age_data_copy.groupby("hour")["engagement_rate"].mean()
    best_hour = int(hour_eng.idxmax())

    # Melhor dia da semana
    age_data_copy["dow"] = age_data_copy["post_date"].dt.day_name()
    dow_eng = age_data_copy.groupby("dow")["engagement_rate"].mean()
    best_dow = dow_eng.idxmax()

    # Top 3 localizações
    loc_eng = age_data.groupby("audience_location")["engagement_rate"].mean().sort_values(ascending=False)
    top_locations = loc_eng.head(3).index.tolist()

    # Disclosure type preferido (patrocinados)
    spon_data = age_data[age_data["is_sponsored"] == True]
    if len(spon_data) > 0:
        disc_eng = spon_data.groupby("disclosure_type")["engagement_rate"].mean()
        best_disc = disc_eng.idxmax()
        disc_loc_eng = spon_data.groupby("disclosure_location")["engagement_rate"].mean()
        best_disc_loc = disc_loc_eng.idxmax()
    else:
        best_disc = "N/A"
        best_disc_loc = "N/A"

    # Top combinação plataforma × tipo × categoria
    combo = age_data.groupby(["platform", "content_type", "content_category"]).agg(
        posts=("id", "count"),
        avg_eng=("engagement_rate", "mean"),
    ).round(4)
    combo = combo[combo["posts"] >= 20].sort_values("avg_eng", ascending=False)
    top_combo = combo.head(1).reset_index()

    persona = {
        "age_group": age,
        "total_posts": int(len(age_data)),
        "pct_dataset": round(len(age_data) / len(df) * 100, 2),
        "avg_engagement_rate": round(age_data["engagement_rate"].mean(), 4),
        "recommendations": {
            "best_platform": best_plat,
            "best_content_type": best_type,
            "best_category": best_cat,
            "best_creator_tier": best_tier,
            "best_post_hour": best_hour,
            "best_post_day": best_dow,
            "top_locations": top_locations,
            "disclosure_type": best_disc,
            "disclosure_location": best_disc_loc,
        },
        "engagement_by_platform": plat_eng.round(4).to_dict(),
        "engagement_by_content_type": type_eng.round(4).to_dict(),
        "engagement_by_category": cat_eng.round(4).to_dict(),
        "engagement_organic_vs_sponsored": {
            "organic": round(spon_eng.get(False, 0), 4),
            "sponsored": round(spon_eng.get(True, 0), 4),
        },
        "gender_engagement": gender_eng.round(4).to_dict(),
        "top_combination": {
            "platform": top_combo.iloc[0]["platform"] if len(top_combo) > 0 else "N/A",
            "content_type": top_combo.iloc[0]["content_type"] if len(top_combo) > 0 else "N/A",
            "category": top_combo.iloc[0]["content_category"] if len(top_combo) > 0 else "N/A",
            "engagement_rate": round(top_combo.iloc[0]["avg_eng"], 4) if len(top_combo) > 0 else 0,
        },
    }
    personas.append(persona)

    print(f"\n{'='*50}")
    print(f"PERSONA: Audiência {age}")
    print(f"{'='*50}")
    print(f"  Posts: {len(age_data):,} ({persona['pct_dataset']}% do dataset)")
    print(f"  Engagement Rate Médio: {persona['avg_engagement_rate']}%")
    print(f"  Melhor Plataforma: {best_plat} ({plat_eng[best_plat]:.4f}%)")
    print(f"  Melhor Tipo: {best_type} ({type_eng[best_type]:.4f}%)")
    print(f"  Melhor Categoria: {best_cat} ({cat_eng[best_cat]:.4f}%)")
    print(f"  Melhor Tier: {best_tier} ({tier_eng[best_tier]:.4f}%)")
    print(f"  Melhor Horário: {best_hour}h")
    print(f"  Melhor Dia: {best_dow}")
    print(f"  Top Localizações: {', '.join(top_locations)}")
    print(f"  Orgânico: {spon_eng.get(False, 0):.4f}% vs Patrocinado: {spon_eng.get(True, 0):.4f}%")
    if len(top_combo) > 0:
        print(f"  TOP COMBO: {top_combo.iloc[0]['platform']} × {top_combo.iloc[0]['content_type']} × {top_combo.iloc[0]['content_category']} = {top_combo.iloc[0]['avg_eng']:.4f}%")


# ============================================================
# SEGMENTAÇÃO 3: Análise de ROI de Patrocínio por Contexto
# ============================================================
print("\n\n" + "=" * 70)
print("ANÁLISE DE ROI DE PATROCÍNIO — QUANDO VALE A PENA?")
print("=" * 70)

# Para cada combinação tier × plataforma, comparar patrocinado vs orgânico
sponsored_roi = df.groupby(["creator_tier", "platform", "is_sponsored"]).agg(
    posts=("id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
).round(4).reset_index()

# Pivot para comparar lado a lado
roi_pivot = sponsored_roi.pivot_table(
    index=["creator_tier", "platform"],
    columns="is_sponsored",
    values="avg_engagement_rate"
).round(4)
roi_pivot.columns = ["organic", "sponsored"]
roi_pivot["diff"] = (roi_pivot["sponsored"] - roi_pivot["organic"]).round(4)
roi_pivot["pct_diff"] = ((roi_pivot["diff"] / roi_pivot["organic"]) * 100).round(4)
roi_pivot = roi_pivot.sort_values("diff", ascending=False)

print("\n--- ROI de Patrocínio: Tier × Plataforma (onde patrocínio GANHA) ---")
gains = roi_pivot[roi_pivot["diff"] > 0]
print(gains.to_string())

print(f"\nCombinações onde patrocínio GANHA: {len(gains)} de {len(roi_pivot)}")
print(f"Combinações onde patrocínio PERDE: {len(roi_pivot) - len(gains)} de {len(roi_pivot)}")

# Sponsor Category × Plataforma
sponsor_plat = df[df["is_sponsored"] == True].groupby(["sponsor_category", "platform"]).agg(
    posts=("id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
).round(4).reset_index()
best_sponsor = sponsor_plat.sort_values("avg_engagement_rate", ascending=False)
print("\n--- Top 10 Combinações Sponsor Category × Plataforma ---")
print(best_sponsor.head(10).to_string(index=False))

print("\n--- Bottom 10 Combinações Sponsor Category × Plataforma ---")
print(best_sponsor.tail(10).to_string(index=False))

# ============================================================
# HASHTAGS ANALYSIS
# ============================================================
print("\n\n" + "=" * 70)
print("ANÁLISE DE HASHTAGS")
print("=" * 70)

# Explodir hashtags
df_hash = df.dropna(subset=["hashtags"]).copy()
df_hash["hashtag_list"] = df_hash["hashtags"].str.split(",")
df_exploded = df_hash.explode("hashtag_list")
df_exploded["hashtag_list"] = df_exploded["hashtag_list"].str.strip()

# Top hashtags por engagement
hash_eng = df_exploded.groupby("hashtag_list").agg(
    uses=("id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
).round(4)
hash_eng = hash_eng[hash_eng["uses"] >= 50].sort_values("avg_engagement_rate", ascending=False)
print("\n--- Top 20 Hashtags por Engagement (min 50 usos) ---")
print(hash_eng.head(20).to_string())

print("\n--- Bottom 20 Hashtags por Engagement (min 50 usos) ---")
print(hash_eng.tail(20).to_string())

# Hashtags count vs engagement
df["hashtag_count"] = df["hashtags"].str.split(",").str.len().fillna(0).astype(int)
hash_count_eng = df.groupby("hashtag_count").agg(
    posts=("id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
).round(4)
print("\n--- Qtd de Hashtags vs Engagement ---")
print(hash_count_eng.to_string())


# ============================================================
# SALVAR TUDO
# ============================================================
print("\n--- Salvando resultados ---")

with open(os.path.join(OUTPUT_DIR, "persona_cards.json"), "w") as f:
    json.dump(personas, f, indent=2, default=str)
    print("  -> persona_cards.json")

roi_pivot.reset_index().to_json(
    os.path.join(OUTPUT_DIR, "sponsorship_roi.json"), orient="records", indent=2
)
print("  -> sponsorship_roi.json")

hash_eng.head(30).reset_index().to_json(
    os.path.join(OUTPUT_DIR, "top_hashtags.json"), orient="records", indent=2
)
print("  -> top_hashtags.json")

hash_count_eng.reset_index().to_json(
    os.path.join(OUTPUT_DIR, "hashtag_count_engagement.json"), orient="records", indent=2
)
print("  -> hashtag_count_engagement.json")

# Dados gerais agregados para dashboard
dashboard_summary = {
    "personas": personas,
    "total_posts": int(len(df)),
    "total_creators": int(df["creator_id"].nunique()),
    "avg_engagement_rate": round(df["engagement_rate"].mean(), 4),
    "platforms": df["platform"].unique().tolist(),
    "date_range": {
        "start": str(df["post_date"].min()),
        "end": str(df["post_date"].max()),
    },
    "sponsored_pct": round(df["is_sponsored"].mean() * 100, 2),
}
with open(os.path.join(OUTPUT_DIR, "dashboard_summary.json"), "w") as f:
    json.dump(dashboard_summary, f, indent=2, default=str)
    print("  -> dashboard_summary.json")

print("\nSegmentação de audiência concluída!")
