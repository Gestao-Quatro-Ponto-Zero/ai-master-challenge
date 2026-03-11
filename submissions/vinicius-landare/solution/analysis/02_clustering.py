"""
Fase 4 — Clustering de Audiência
=================================
Segmenta os 52K posts em clusters comportamentais usando K-Means.
Gera perfis de cluster e estratégias de comunicação por segmento.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import json
import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(os.path.dirname(BASE_DIR), "social_media_dataset.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "analysis", "outputs")

# Load data
print("Carregando dataset...")
df = pd.read_csv(CSV_PATH)
df["post_date"] = pd.to_datetime(df["post_date"], format="mixed")

# Calcular engagement rate
df["engagement_rate"] = ((df["likes"] + df["shares"] + df["comments_count"]) / df["views"]) * 100
df["engagement_rate_followers"] = ((df["likes"] + df["shares"] + df["comments_count"]) / df["follower_count"]) * 100

# ============================================================
# FEATURES PARA CLUSTERING
# ============================================================
# Encoding das variáveis categóricas
platform_map = {"Instagram": 0, "TikTok": 1, "YouTube": 2, "Bilibili": 3, "RedNote": 4}
content_type_map = {"video": 0, "image": 1, "mixed": 2, "text": 3}
category_map = {"beauty": 0, "lifestyle": 1, "tech": 2}
age_map = {"13-18": 0, "19-25": 1, "26-35": 2, "36-50": 3, "50+": 4}
gender_map = {"male": 0, "female": 1, "non-binary": 2, "unknown": 3}

df["platform_encoded"] = df["platform"].map(platform_map)
df["content_type_encoded"] = df["content_type"].map(content_type_map)
df["category_encoded"] = df["content_category"].map(category_map)
df["age_encoded"] = df["audience_age_distribution"].map(age_map)
df["gender_encoded"] = df["audience_gender_distribution"].map(gender_map)
df["is_sponsored_encoded"] = df["is_sponsored"].astype(int)

# Features de clustering
features = [
    "views", "likes", "shares", "comments_count",
    "follower_count", "engagement_rate", "content_length",
    "platform_encoded", "content_type_encoded", "category_encoded",
    "age_encoded", "gender_encoded", "is_sponsored_encoded"
]

X = df[features].copy()
X = X.fillna(X.median())

# Padronizar
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ============================================================
# DETERMINAR NÚMERO IDEAL DE CLUSTERS
# ============================================================
print("\n--- Determinando número ideal de clusters ---")
inertias = []
sil_scores = []
K_range = range(2, 9)

for k in K_range:
    km = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
    labels = km.fit_predict(X_scaled)
    inertias.append(km.inertia_)
    sil = silhouette_score(X_scaled, labels, sample_size=10000, random_state=42)
    sil_scores.append(sil)
    print(f"  k={k}: Inertia={km.inertia_:.0f}, Silhouette={sil:.4f}")

# Salvar dados do elbow
elbow_data = [{"k": int(k), "inertia": round(i, 2), "silhouette": round(s, 4)}
              for k, i, s in zip(K_range, inertias, sil_scores)]
with open(os.path.join(OUTPUT_DIR, "clustering_elbow.json"), "w") as f:
    json.dump(elbow_data, f, indent=2)

best_k = K_range[np.argmax(sil_scores)]
print(f"\nMelhor k pelo Silhouette Score: {best_k}")

# ============================================================
# CLUSTERING FINAL
# ============================================================
print(f"\n--- Executando K-Means com k={best_k} ---")
final_km = KMeans(n_clusters=best_k, random_state=42, n_init=10, max_iter=300)
df["cluster"] = final_km.fit_predict(X_scaled)

# ============================================================
# PERFIL DE CADA CLUSTER
# ============================================================
print("\n" + "=" * 70)
print(f"PERFIL DOS {best_k} CLUSTERS")
print("=" * 70)

# Métricas numéricas por cluster
numeric_profile = df.groupby("cluster").agg(
    posts=("id", "count"),
    avg_views=("views", "mean"),
    avg_likes=("likes", "mean"),
    avg_shares=("shares", "mean"),
    avg_comments=("comments_count", "mean"),
    avg_engagement_rate=("engagement_rate", "mean"),
    avg_followers=("follower_count", "mean"),
    avg_content_length=("content_length", "mean"),
    pct_sponsored=("is_sponsored", "mean"),
).round(4)
print("\n--- Métricas Numéricas ---")
print(numeric_profile.to_string())

# Distribuição categórica por cluster
print("\n--- Distribuição por Plataforma ---")
plat_dist = pd.crosstab(df["cluster"], df["platform"], normalize="index").round(4) * 100
print(plat_dist.to_string())

print("\n--- Distribuição por Tipo de Conteúdo ---")
type_dist = pd.crosstab(df["cluster"], df["content_type"], normalize="index").round(4) * 100
print(type_dist.to_string())

print("\n--- Distribuição por Categoria ---")
cat_dist = pd.crosstab(df["cluster"], df["content_category"], normalize="index").round(4) * 100
print(cat_dist.to_string())

print("\n--- Distribuição por Faixa Etária ---")
age_dist = pd.crosstab(df["cluster"], df["audience_age_distribution"], normalize="index").round(4) * 100
print(age_dist.to_string())

print("\n--- Distribuição por Gênero ---")
gender_dist = pd.crosstab(df["cluster"], df["audience_gender_distribution"], normalize="index").round(4) * 100
print(gender_dist.to_string())

print("\n--- Distribuição por Localização ---")
loc_dist = pd.crosstab(df["cluster"], df["audience_location"], normalize="index").round(4) * 100
print(loc_dist.to_string())

print("\n--- Distribuição por Tier de Creator ---")
def classify_tier(f):
    if f < 10_000: return "Nano"
    elif f < 50_000: return "Micro"
    elif f < 100_000: return "Mid"
    elif f < 500_000: return "Macro"
    else: return "Mega"
df["creator_tier"] = df["follower_count"].apply(classify_tier)
tier_dist = pd.crosstab(df["cluster"], df["creator_tier"], normalize="index").round(4) * 100
print(tier_dist.to_string())

# ============================================================
# DIFERENÇA RELATIVA DE CADA CLUSTER VS MÉDIA GERAL
# ============================================================
print("\n" + "=" * 70)
print("DIFERENÇA RELATIVA DE CADA CLUSTER VS MÉDIA GERAL (%)")
print("=" * 70)

overall_means = df[["views", "likes", "shares", "comments_count",
                     "engagement_rate", "follower_count", "content_length"]].mean()
cluster_means = df.groupby("cluster")[["views", "likes", "shares", "comments_count",
                                        "engagement_rate", "follower_count", "content_length"]].mean()
relative_diff = ((cluster_means - overall_means) / overall_means * 100).round(2)
print(relative_diff.to_string())

# ============================================================
# SALVAR RESULTADOS
# ============================================================
print("\n--- Salvando resultados ---")

# Perfil completo por cluster
cluster_profiles = []
for c in range(best_k):
    cluster_data = df[df["cluster"] == c]
    profile = {
        "cluster_id": int(c),
        "size": int(len(cluster_data)),
        "pct_total": round(len(cluster_data) / len(df) * 100, 2),
        "metrics": {
            "avg_engagement_rate": round(cluster_data["engagement_rate"].mean(), 4),
            "avg_views": round(cluster_data["views"].mean(), 2),
            "avg_likes": round(cluster_data["likes"].mean(), 2),
            "avg_shares": round(cluster_data["shares"].mean(), 2),
            "avg_comments": round(cluster_data["comments_count"].mean(), 2),
            "avg_followers": round(cluster_data["follower_count"].mean(), 2),
            "avg_content_length": round(cluster_data["content_length"].mean(), 2),
            "pct_sponsored": round(cluster_data["is_sponsored"].mean() * 100, 2),
        },
        "top_platform": cluster_data["platform"].value_counts().index[0],
        "top_content_type": cluster_data["content_type"].value_counts().index[0],
        "top_category": cluster_data["content_category"].value_counts().index[0],
        "top_age_group": cluster_data["audience_age_distribution"].value_counts().index[0],
        "top_gender": cluster_data["audience_gender_distribution"].value_counts().index[0],
        "top_location": cluster_data["audience_location"].value_counts().index[0],
        "top_creator_tier": cluster_data["creator_tier"].value_counts().index[0],
        "distributions": {
            "platform": cluster_data["platform"].value_counts(normalize=True).round(4).to_dict(),
            "content_type": cluster_data["content_type"].value_counts(normalize=True).round(4).to_dict(),
            "category": cluster_data["content_category"].value_counts(normalize=True).round(4).to_dict(),
            "age": cluster_data["audience_age_distribution"].value_counts(normalize=True).round(4).to_dict(),
            "gender": cluster_data["audience_gender_distribution"].value_counts(normalize=True).round(4).to_dict(),
            "location": cluster_data["audience_location"].value_counts(normalize=True).round(4).to_dict(),
            "creator_tier": cluster_data["creator_tier"].value_counts(normalize=True).round(4).to_dict(),
        }
    }
    cluster_profiles.append(profile)

with open(os.path.join(OUTPUT_DIR, "cluster_profiles.json"), "w") as f:
    json.dump(cluster_profiles, f, indent=2, default=str)
    print("  -> cluster_profiles.json")

# Relative diff
relative_diff.reset_index().to_json(
    os.path.join(OUTPUT_DIR, "cluster_relative_diff.json"), orient="records", indent=2
)
print("  -> cluster_relative_diff.json")

# Distribuições por cluster
distributions = {
    "platform": plat_dist.reset_index().to_dict(orient="records"),
    "content_type": type_dist.reset_index().to_dict(orient="records"),
    "category": cat_dist.reset_index().to_dict(orient="records"),
    "age": age_dist.reset_index().to_dict(orient="records"),
    "gender": gender_dist.reset_index().to_dict(orient="records"),
    "location": loc_dist.reset_index().to_dict(orient="records"),
    "creator_tier": tier_dist.reset_index().to_dict(orient="records"),
}
with open(os.path.join(OUTPUT_DIR, "cluster_distributions.json"), "w") as f:
    json.dump(distributions, f, indent=2)
    print("  -> cluster_distributions.json")

# ============================================================
# ANÁLISE DE TOP PERFORMERS POR CLUSTER
# ============================================================
print("\n" + "=" * 70)
print("TOP COMBINAÇÕES POR CLUSTER")
print("=" * 70)

for c in range(best_k):
    cluster_data = df[df["cluster"] == c]
    top = cluster_data.groupby(["platform", "content_type", "content_category"]).agg(
        posts=("id", "count"),
        avg_engagement_rate=("engagement_rate", "mean"),
    ).round(4)
    top = top[top["posts"] >= 10].sort_values("avg_engagement_rate", ascending=False)
    print(f"\n--- Cluster {c} - Top 5 combinações ---")
    print(top.head(5).to_string())

print("\nClustering concluído!")
