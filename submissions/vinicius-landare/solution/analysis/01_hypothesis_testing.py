"""
Fase 3 — Teste de Hipóteses (Hypothesis-Driven Analysis)
=========================================================
Testa H1-H6 sobre os 52.214 posts do dataset de mídias sociais.
Gera resultados agregados em JSON para consumo pelo dashboard.
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
from scipy import stats as scipy_stats

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "assets", "social_media_dataset.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "analysis", "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

META = {
    "generated_at": datetime.now().isoformat(),
    "data_source": "dataset_v1",
    "sample_size": None,
    "period": None,
}

def compute_significance(group_a, group_b):
    """Testa significância estatística entre dois grupos usando Mann-Whitney U."""
    if len(group_a) < 5 or len(group_b) < 5:
        return {"is_significant": False, "p_value": None, "effect_size": None, "test": "insufficient_data"}
    stat, p_value = scipy_stats.mannwhitneyu(group_a, group_b, alternative="two-sided")
    pooled_std = np.sqrt((np.std(group_a)**2 + np.std(group_b)**2) / 2)
    effect_size = abs(np.mean(group_a) - np.mean(group_b)) / pooled_std if pooled_std > 0 else 0
    return {
        "is_significant": bool(p_value < 0.05),
        "p_value": round(float(p_value), 6),
        "effect_size": round(float(effect_size), 4),
        "test": "mann_whitney_u",
    }

def compute_kruskal(groups):
    """Testa significância entre 3+ grupos usando Kruskal-Wallis."""
    valid = [g for g in groups if len(g) >= 5]
    if len(valid) < 2:
        return {"is_significant": False, "p_value": None, "test": "insufficient_groups"}
    stat, p_value = scipy_stats.kruskal(*valid)
    return {
        "is_significant": bool(p_value < 0.05),
        "p_value": round(float(p_value), 6),
        "test": "kruskal_wallis",
    }

def confidence_interval(data, confidence=0.95):
    """Calcula intervalo de confiança para a média."""
    n = len(data)
    if n < 2:
        return {"ci_lower": None, "ci_upper": None, "margin": None}
    mean = np.mean(data)
    se = scipy_stats.sem(data)
    h = se * scipy_stats.t.ppf((1 + confidence) / 2, n - 1)
    return {
        "ci_lower": round(float(mean - h), 4),
        "ci_upper": round(float(mean + h), 4),
        "margin": round(float(h), 4),
    }

# Load data
print("Carregando dataset...")
df = pd.read_csv(CSV_PATH)
print(f"Dataset: {df.shape[0]:,} posts, {df.shape[1]} colunas\n")

# ============================================================
# PREPARAÇÃO: Calcular Engagement Rate
# ============================================================
# Engagement Rate baseado em views (melhor para performance de conteúdo)
df["engagement_rate"] = ((df["likes"] + df["shares"] + df["comments_count"]) / df["views"]) * 100

# Engagement Rate baseado em followers (padrão da indústria)
df["engagement_rate_followers"] = ((df["likes"] + df["shares"] + df["comments_count"]) / df["follower_count"]) * 100

# Classificar creators por tier de seguidores
def classify_creator_tier(followers):
    if followers < 10_000:
        return "Nano (< 10K)"
    elif followers < 50_000:
        return "Micro (10K-50K)"
    elif followers < 100_000:
        return "Mid (50K-100K)"
    elif followers < 500_000:
        return "Macro (100K-500K)"
    else:
        return "Mega (500K+)"

df["creator_tier"] = df["follower_count"].apply(classify_creator_tier)

# Parse post_date
df["post_date"] = pd.to_datetime(df["post_date"], format="mixed")
df["month"] = df["post_date"].dt.to_period("M").astype(str)
df["day_of_week"] = df["post_date"].dt.day_name()
df["hour"] = df["post_date"].dt.hour

# Preencher metadados globais
META["sample_size"] = int(df.shape[0])
META["period"] = f"{df['post_date'].min()} to {df['post_date'].max()}"

print("=" * 70)
print("H1: PATROCÍNIO EXPLÍCITO REDUZ ENGAGEMENT VS. ORGÂNICO?")
print("=" * 70)

# Orgânico vs Patrocinado — geral
h1_general = df.groupby("is_sponsored").agg(
    posts=("id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
    avg_likes=("likes", "mean"),
    avg_shares=("shares", "mean"),
    avg_comments=("comments_count", "mean"),
    avg_views=("views", "mean"),
    median_engagement_rate=("engagement_rate", "median"),
).round(4)
print("\n--- Orgânico vs Patrocinado (geral) ---")
print(h1_general.to_string())

# Orgânico vs Patrocinado — por plataforma
h1_platform = df.groupby(["platform", "is_sponsored"]).agg(
    posts=("id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
    avg_likes=("likes", "mean"),
    avg_shares=("shares", "mean"),
    avg_comments=("comments_count", "mean"),
).round(4)
print("\n--- Orgânico vs Patrocinado por Plataforma ---")
print(h1_platform.to_string())

# Orgânico vs Patrocinado — por tier de creator
h1_tier = df.groupby(["creator_tier", "is_sponsored"]).agg(
    posts=("id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
    avg_engagement_rate_followers=("engagement_rate_followers", "mean"),
).round(4)
print("\n--- Orgânico vs Patrocinado por Tier de Creator ---")
print(h1_tier.to_string())

# Orgânico vs Patrocinado — por categoria de conteúdo
h1_category = df.groupby(["content_category", "is_sponsored"]).agg(
    posts=("id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
).round(4)
print("\n--- Orgânico vs Patrocinado por Categoria ---")
print(h1_category.to_string())

# Impacto do tipo de disclosure
h1_disclosure = df[df["is_sponsored"] == True].groupby("disclosure_type").agg(
    posts=("id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
    avg_likes=("likes", "mean"),
    avg_shares=("shares", "mean"),
    avg_comments=("comments_count", "mean"),
).round(4)
print("\n--- Tipo de Disclosure (só patrocinados) ---")
print(h1_disclosure.to_string())

# Disclosure location
h1_disc_loc = df[df["is_sponsored"] == True].groupby("disclosure_location").agg(
    posts=("id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
).round(4)
print("\n--- Local do Disclosure (só patrocinados) ---")
print(h1_disc_loc.to_string())

# Patrocinado por categoria de sponsor
h1_sponsor_cat = df[df["is_sponsored"] == True].groupby("sponsor_category").agg(
    posts=("id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
    avg_views=("views", "mean"),
    avg_likes=("likes", "mean"),
).round(4).sort_values("avg_engagement_rate", ascending=False)
print("\n--- Performance por Categoria de Sponsor ---")
print(h1_sponsor_cat.to_string())


print("\n" + "=" * 70)
print("H2: MICRO-CREATORS TÊM MELHOR ENGAGEMENT QUE MEGA-INFLUENCERS?")
print("=" * 70)

# Engagement por tier de creator
h2_tier = df.groupby("creator_tier").agg(
    posts=("id", "count"),
    creators=("creator_id", "nunique"),
    avg_followers=("follower_count", "mean"),
    avg_engagement_rate=("engagement_rate", "mean"),
    avg_engagement_rate_followers=("engagement_rate_followers", "mean"),
    avg_likes=("likes", "mean"),
    avg_shares=("shares", "mean"),
    avg_comments=("comments_count", "mean"),
    avg_views=("views", "mean"),
    median_engagement_rate=("engagement_rate", "median"),
).round(4)
# Ordenar por tier lógico
tier_order = ["Nano (< 10K)", "Micro (10K-50K)", "Mid (50K-100K)", "Macro (100K-500K)", "Mega (500K+)"]
h2_tier = h2_tier.reindex(tier_order)
print("\n--- Engagement por Tier de Creator ---")
print(h2_tier.to_string())

# Tier × Plataforma
h2_tier_platform = df.groupby(["creator_tier", "platform"]).agg(
    posts=("id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
    avg_engagement_rate_followers=("engagement_rate_followers", "mean"),
).round(4)
print("\n--- Tier de Creator × Plataforma ---")
print(h2_tier_platform.to_string())

# Tier × Patrocínio (interação)
h2_tier_sponsored = df.groupby(["creator_tier", "is_sponsored"]).agg(
    avg_engagement_rate=("engagement_rate", "mean"),
    avg_engagement_rate_followers=("engagement_rate_followers", "mean"),
).round(4)
print("\n--- Tier × Patrocínio ---")
print(h2_tier_sponsored.to_string())


print("\n" + "=" * 70)
print("H3: COMBINAÇÃO IDEAL PLATAFORMA × TIPO × CATEGORIA × FAIXA ETÁRIA")
print("=" * 70)

# Plataforma × Tipo de Conteúdo
h3_plat_type = df.groupby(["platform", "content_type"]).agg(
    posts=("id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
    avg_likes=("likes", "mean"),
    avg_shares=("shares", "mean"),
    avg_comments=("comments_count", "mean"),
).round(4)
print("\n--- Plataforma × Tipo de Conteúdo ---")
print(h3_plat_type.to_string())

# Plataforma × Categoria
h3_plat_cat = df.groupby(["platform", "content_category"]).agg(
    posts=("id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
).round(4)
print("\n--- Plataforma × Categoria ---")
print(h3_plat_cat.to_string())

# Plataforma × Faixa Etária
h3_plat_age = df.groupby(["platform", "audience_age_distribution"]).agg(
    posts=("id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
    avg_likes=("likes", "mean"),
    avg_shares=("shares", "mean"),
).round(4)
print("\n--- Plataforma × Faixa Etária ---")
print(h3_plat_age.to_string())

# Top 20 combinações com melhor engagement
h3_top = df.groupby(["platform", "content_type", "content_category", "audience_age_distribution"]).agg(
    posts=("id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
    avg_likes=("likes", "mean"),
    avg_shares=("shares", "mean"),
    avg_comments=("comments_count", "mean"),
).round(4)
h3_top = h3_top[h3_top["posts"] >= 30].sort_values("avg_engagement_rate", ascending=False)
print("\n--- Top 20 Combinações (min 30 posts) ---")
print(h3_top.head(20).to_string())

print("\n--- Bottom 20 Combinações (min 30 posts) ---")
print(h3_top.tail(20).to_string())

# Tipo de conteúdo × Faixa Etária (independente de plataforma)
h3_type_age = df.groupby(["content_type", "audience_age_distribution"]).agg(
    posts=("id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
).round(4)
print("\n--- Tipo de Conteúdo × Faixa Etária ---")
print(h3_type_age.to_string())


print("\n" + "=" * 70)
print("H4: BRASIL SE COMPORTA DIFERENTE DOS OUTROS MERCADOS?")
print("=" * 70)

# Engagement por localização
h4_location = df.groupby("audience_location").agg(
    posts=("id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
    avg_likes=("likes", "mean"),
    avg_shares=("shares", "mean"),
    avg_comments=("comments_count", "mean"),
    avg_views=("views", "mean"),
    median_engagement_rate=("engagement_rate", "median"),
).round(4).sort_values("avg_engagement_rate", ascending=False)
print("\n--- Engagement por Localização ---")
print(h4_location.to_string())

# Brasil: plataforma preferida
h4_brazil = df[df["audience_location"] == "Brazil"]
h4_brazil_plat = h4_brazil.groupby("platform").agg(
    posts=("id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
).round(4).sort_values("avg_engagement_rate", ascending=False)
print("\n--- Brasil: Engagement por Plataforma ---")
print(h4_brazil_plat.to_string())

# Brasil: tipo de conteúdo
h4_brazil_type = h4_brazil.groupby("content_type").agg(
    posts=("id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
).round(4).sort_values("avg_engagement_rate", ascending=False)
print("\n--- Brasil: Engagement por Tipo de Conteúdo ---")
print(h4_brazil_type.to_string())

# Brasil: faixa etária
h4_brazil_age = h4_brazil.groupby("audience_age_distribution").agg(
    posts=("id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
).round(4).sort_values("avg_engagement_rate", ascending=False)
print("\n--- Brasil: Engagement por Faixa Etária ---")
print(h4_brazil_age.to_string())

# Brasil: patrocinado vs orgânico
h4_brazil_spon = h4_brazil.groupby("is_sponsored").agg(
    posts=("id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
).round(4)
print("\n--- Brasil: Patrocinado vs Orgânico ---")
print(h4_brazil_spon.to_string())

# Localização × Plataforma (comparação entre mercados)
h4_loc_plat = df.groupby(["audience_location", "platform"]).agg(
    posts=("id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
).round(4)
print("\n--- Localização × Plataforma ---")
pivot_loc_plat = h4_loc_plat.reset_index().pivot_table(
    index="audience_location", columns="platform", values="avg_engagement_rate"
).round(4)
print(pivot_loc_plat.to_string())


print("\n" + "=" * 70)
print("H5: DISCLOSURE IMPLÍCITO PERFORMA MELHOR QUE EXPLÍCITO?")
print("=" * 70)

# Já temos h1_disclosure acima, mas vamos cruzar com mais variáveis
sponsored = df[df["is_sponsored"] == True].copy()

# Disclosure × Plataforma
h5_disc_plat = sponsored.groupby(["disclosure_type", "platform"]).agg(
    posts=("id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
).round(4)
print("\n--- Disclosure Type × Plataforma ---")
pivot_disc_plat = h5_disc_plat.reset_index().pivot_table(
    index="disclosure_type", columns="platform", values="avg_engagement_rate"
).round(4)
print(pivot_disc_plat.to_string())

# Disclosure × Tier de Creator
h5_disc_tier = sponsored.groupby(["disclosure_type", "creator_tier"]).agg(
    posts=("id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
).round(4)
print("\n--- Disclosure Type × Tier de Creator ---")
print(h5_disc_tier.to_string())

# Disclosure × Categoria
h5_disc_cat = sponsored.groupby(["disclosure_type", "content_category"]).agg(
    posts=("id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
).round(4)
print("\n--- Disclosure Type × Categoria ---")
print(h5_disc_cat.to_string())

# Disclosure Location × Plataforma
h5_loc_plat = sponsored.groupby(["disclosure_location", "platform"]).agg(
    posts=("id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
).round(4)
print("\n--- Disclosure Location × Plataforma ---")
pivot_loc = h5_loc_plat.reset_index().pivot_table(
    index="disclosure_location", columns="platform", values="avg_engagement_rate"
).round(4)
print(pivot_loc.to_string())


print("\n" + "=" * 70)
print("H6: O QUE NÃO FUNCIONA? (BAIXO ENGAGEMENT SISTEMÁTICO)")
print("=" * 70)

# Posts com engagement rate abaixo do P10
p10 = df["engagement_rate"].quantile(0.10)
p25 = df["engagement_rate"].quantile(0.25)
p75 = df["engagement_rate"].quantile(0.75)
p90 = df["engagement_rate"].quantile(0.90)
print(f"\nDistribuição do Engagement Rate:")
print(f"  P10: {p10:.4f}%")
print(f"  P25: {p25:.4f}%")
print(f"  Mediana: {df['engagement_rate'].median():.4f}%")
print(f"  Média: {df['engagement_rate'].mean():.4f}%")
print(f"  P75: {p75:.4f}%")
print(f"  P90: {p90:.4f}%")

low_engagement = df[df["engagement_rate"] <= p10]
high_engagement = df[df["engagement_rate"] >= p90]

print(f"\nPosts baixo engagement (<=P10): {len(low_engagement):,}")
print(f"Posts alto engagement (>=P90): {len(high_engagement):,}")

# Perfil dos posts com BAIXO engagement
print("\n--- Perfil dos Posts com BAIXO Engagement (P10) ---")
for col in ["platform", "content_type", "content_category", "audience_age_distribution",
            "audience_gender_distribution", "audience_location", "is_sponsored", "creator_tier"]:
    dist = low_engagement[col].value_counts(normalize=True).round(4) * 100
    overall_dist = df[col].value_counts(normalize=True).round(4) * 100
    comparison = pd.DataFrame({"low_eng_%": dist, "overall_%": overall_dist, "diff": dist - overall_dist}).round(2)
    print(f"\n{col}:")
    print(comparison.to_string())

# Perfil dos posts com ALTO engagement
print("\n--- Perfil dos Posts com ALTO Engagement (P90) ---")
for col in ["platform", "content_type", "content_category", "audience_age_distribution",
            "audience_gender_distribution", "audience_location", "is_sponsored", "creator_tier"]:
    dist = high_engagement[col].value_counts(normalize=True).round(4) * 100
    overall_dist = df[col].value_counts(normalize=True).round(4) * 100
    comparison = pd.DataFrame({"high_eng_%": dist, "overall_%": overall_dist, "diff": dist - overall_dist}).round(2)
    print(f"\n{col}:")
    print(comparison.to_string())


# ============================================================
# ANÁLISES ADICIONAIS
# ============================================================

print("\n" + "=" * 70)
print("ANÁLISE TEMPORAL")
print("=" * 70)

# Engagement por dia da semana
temporal_dow = df.groupby("day_of_week").agg(
    posts=("id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
).round(4)
dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
temporal_dow = temporal_dow.reindex(dow_order)
print("\n--- Engagement por Dia da Semana ---")
print(temporal_dow.to_string())

# Engagement por hora do dia
temporal_hour = df.groupby("hour").agg(
    posts=("id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
).round(4)
print("\n--- Engagement por Hora do Dia ---")
print(temporal_hour.to_string())

# Gênero × Plataforma
gender_plat = df.groupby(["audience_gender_distribution", "platform"]).agg(
    posts=("id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
).round(4)
print("\n--- Gênero × Plataforma ---")
pivot_gender = gender_plat.reset_index().pivot_table(
    index="audience_gender_distribution", columns="platform", values="avg_engagement_rate"
).round(4)
print(pivot_gender.to_string())

# Idioma × Engagement
lang_eng = df.groupby("language").agg(
    posts=("id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
).round(4).sort_values("avg_engagement_rate", ascending=False)
print("\n--- Engagement por Idioma ---")
print(lang_eng.to_string())

# Content length vs engagement (bins)
df["content_length_bin"] = pd.cut(df["content_length"], bins=[0, 50, 100, 200, 300, 400, 600],
                                   labels=["0-50", "51-100", "101-200", "201-300", "301-400", "401-600"])
length_eng = df.groupby("content_length_bin", observed=True).agg(
    posts=("id", "count"),
    avg_engagement_rate=("engagement_rate", "mean"),
).round(4)
print("\n--- Engagement por Tamanho do Conteúdo ---")
print(length_eng.to_string())


# ============================================================
# SALVAR RESULTADOS EM JSON
# ============================================================
# ============================================================
# TESTES DE SIGNIFICÂNCIA ESTATÍSTICA
# ============================================================
print("\n" + "=" * 70)
print("TESTES DE SIGNIFICÂNCIA ESTATÍSTICA")
print("=" * 70)

# H1: Sponsored vs Organic — significância
organic_eng = df[df["is_sponsored"] == False]["engagement_rate"].values
sponsored_eng = df[df["is_sponsored"] == True]["engagement_rate"].values
h1_significance = compute_significance(organic_eng, sponsored_eng)
h1_ci_organic = confidence_interval(organic_eng)
h1_ci_sponsored = confidence_interval(sponsored_eng)
print(f"\nH1 Sponsored vs Organic: p={h1_significance['p_value']}, significant={h1_significance['is_significant']}, effect_size={h1_significance['effect_size']}")

# H2: Creator Tiers — significância (Kruskal-Wallis)
tier_groups = [df[df["creator_tier"] == t]["engagement_rate"].values for t in tier_order]
h2_significance = compute_kruskal(tier_groups)
print(f"H2 Creator Tiers: p={h2_significance['p_value']}, significant={h2_significance['is_significant']}")

# H3: Platforms — significância
platform_groups = [df[df["platform"] == p]["engagement_rate"].values for p in df["platform"].unique()]
h3_platform_significance = compute_kruskal(platform_groups)
print(f"H3 Platforms: p={h3_platform_significance['p_value']}, significant={h3_platform_significance['is_significant']}")

# H4: Brazil vs Others — significância
brazil_eng = df[df["audience_location"] == "Brazil"]["engagement_rate"].values
others_eng = df[df["audience_location"] != "Brazil"]["engagement_rate"].values
h4_significance = compute_significance(brazil_eng, others_eng)
print(f"H4 Brazil vs Others: p={h4_significance['p_value']}, significant={h4_significance['is_significant']}, effect_size={h4_significance['effect_size']}")

# H5: Disclosure types — significância
disc_groups = [sponsored[sponsored["disclosure_type"] == d]["engagement_rate"].values
               for d in sponsored["disclosure_type"].unique() if len(sponsored[sponsored["disclosure_type"] == d]) >= 5]
h5_significance = compute_kruskal(disc_groups)
print(f"H5 Disclosure Types: p={h5_significance['p_value']}, significant={h5_significance['is_significant']}")

# Confidence intervals para cada tier
tier_ci = {}
for t in tier_order:
    tier_data = df[df["creator_tier"] == t]["engagement_rate"].values
    tier_ci[t] = confidence_interval(tier_data)

# Confidence intervals para cada plataforma
platform_ci = {}
for p in df["platform"].unique():
    plat_data = df[df["platform"] == p]["engagement_rate"].values
    platform_ci[p] = confidence_interval(plat_data)

print("\n" + "=" * 70)
print("SALVANDO RESULTADOS EM JSON...")
print("=" * 70)

def df_to_json(dataframe, filename, extra_meta=None):
    """Salva DataFrame como JSON com metadados, resetando index se necessário."""
    path = os.path.join(OUTPUT_DIR, filename)
    records = json.loads(dataframe.reset_index().to_json(orient="records", force_ascii=False))
    output = {
        "_meta": {**META, **(extra_meta or {})},
        "data": records,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)
    print(f"  -> {filename}")

df_to_json(h1_general, "h1_sponsored_vs_organic.json", {
    "significance": h1_significance,
    "ci_organic": h1_ci_organic,
    "ci_sponsored": h1_ci_sponsored,
})
df_to_json(h1_platform, "h1_sponsored_by_platform.json")
df_to_json(h1_tier, "h1_sponsored_by_tier.json")
df_to_json(h1_category, "h1_sponsored_by_category.json")
df_to_json(h1_disclosure, "h1_disclosure_type.json", {"significance": h5_significance})
df_to_json(h1_disc_loc, "h1_disclosure_location.json")
df_to_json(h1_sponsor_cat, "h1_sponsor_category.json")
df_to_json(h2_tier, "h2_creator_tiers.json", {
    "significance": h2_significance,
    "confidence_intervals": tier_ci,
})
df_to_json(h2_tier_platform, "h2_tier_by_platform.json")
df_to_json(h3_plat_type, "h3_platform_content_type.json", {
    "significance": h3_platform_significance,
    "confidence_intervals": platform_ci,
})
df_to_json(h3_plat_cat, "h3_platform_category.json")
df_to_json(h3_plat_age, "h3_platform_age.json")
df_to_json(h3_top.head(20), "h3_top20_combinations.json")
df_to_json(h3_top.tail(20), "h3_bottom20_combinations.json")
df_to_json(h3_type_age, "h3_content_type_age.json")
df_to_json(h4_location, "h4_location_engagement.json", {
    "significance_brazil_vs_others": h4_significance,
})
df_to_json(h4_brazil_plat, "h4_brazil_platform.json")
df_to_json(h4_brazil_type, "h4_brazil_content_type.json")
df_to_json(h4_brazil_age, "h4_brazil_age.json")
df_to_json(temporal_dow, "temporal_day_of_week.json")
df_to_json(temporal_hour, "temporal_hour.json")
df_to_json(lang_eng, "language_engagement.json")
df_to_json(length_eng, "content_length_engagement.json")

# Salvar estatísticas gerais
stats = {
    "_meta": META,
    "total_posts": int(df.shape[0]),
    "total_creators": int(df["creator_id"].nunique()),
    "platforms": df["platform"].unique().tolist(),
    "date_range": {
        "start": str(df["post_date"].min()),
        "end": str(df["post_date"].max()),
    },
    "engagement_rate": {
        "mean": round(df["engagement_rate"].mean(), 4),
        "median": round(df["engagement_rate"].median(), 4),
        "p10": round(p10, 4),
        "p25": round(p25, 4),
        "p75": round(p75, 4),
        "p90": round(p90, 4),
    },
    "sponsored_ratio": round(df["is_sponsored"].mean() * 100, 2),
    "significance_tests": {
        "h1_sponsored_vs_organic": h1_significance,
        "h2_creator_tiers": h2_significance,
        "h3_platforms": h3_platform_significance,
        "h4_brazil_vs_others": h4_significance,
        "h5_disclosure_types": h5_significance,
    },
}
with open(os.path.join(OUTPUT_DIR, "general_stats.json"), "w", encoding="utf-8") as f:
    json.dump(stats, f, indent=2, default=str, ensure_ascii=False)
    print("  -> general_stats.json")

print("\nAnálise de hipóteses concluída!")
