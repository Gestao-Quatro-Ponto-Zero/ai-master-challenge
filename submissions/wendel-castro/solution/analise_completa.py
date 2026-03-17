"""
Análise de Performance — Social Media Strategy
Challenge 004 — G4 AI Master Challenge
Wendel Castro | Março 2026
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import os
import warnings
warnings.filterwarnings('ignore')

# Config visual
sns.set_theme(style="whitegrid", font_scale=1.1)
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['figure.dpi'] = 150

# Paths
# O dataset deve ser baixado do Kaggle e colocado na pasta dataset/ ao lado deste script
# Link: https://www.kaggle.com/datasets/omenkj/social-media-sponsorship-and-engagement-dataset
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(SCRIPT_DIR, 'dataset', 'social_media_dataset.csv')
CHARTS_DIR = os.path.join(SCRIPT_DIR, 'charts')
os.makedirs(CHARTS_DIR, exist_ok=True)

print("Carregando dataset...")
df = pd.read_csv(DATA_PATH)
df['post_date'] = pd.to_datetime(df['post_date'], format='mixed')

# === FEATURE ENGINEERING ===
print("Criando features derivadas...")

# Engagement rate
df['engagement_rate'] = (df['likes'] + df['shares'] + df['comments_count']) / df['views'] * 100

# Faixas de seguidores (tamanho do criador)
def creator_tier(followers):
    if followers < 10000:
        return 'Nano (<10K)'
    elif followers < 50000:
        return 'Micro (10-50K)'
    elif followers < 100000:
        return 'Mid (50-100K)'
    elif followers < 500000:
        return 'Macro (100-500K)'
    else:
        return 'Mega (500K+)'

df['creator_tier'] = df['follower_count'].apply(creator_tier)

# Ordem das tiers para gráficos
tier_order = ['Nano (<10K)', 'Micro (10-50K)', 'Mid (50-100K)', 'Macro (100-500K)', 'Mega (500K+)']

# Mês/ano para análise temporal
df['year_month'] = df['post_date'].dt.to_period('M')
df['month'] = df['post_date'].dt.month
df['day_of_week'] = df['post_date'].dt.day_name()

# Contagem de hashtags
df['hashtag_count'] = df['hashtags'].fillna('').apply(lambda x: len(x.split(',')) if x else 0)

# Tamanho do conteúdo em faixas
df['content_length_bucket'] = pd.cut(df['content_length'], bins=[0, 100, 200, 300, 400, 600],
                                      labels=['Curto (0-100)', 'Médio (100-200)', 'Longo (200-300)',
                                              'Muito longo (300-400)', 'Extra (400+)'])

print(f"Dataset: {len(df)} posts, {df.shape[1]} colunas")
print()

# =====================================================
# ANÁLISE 1: ENGAGEMENT POR PLATAFORMA x TIPO DE CONTEÚDO
# =====================================================
print("=" * 60)
print("ANÁLISE 1: ENGAGEMENT POR PLATAFORMA x TIPO DE CONTEÚDO")
print("=" * 60)

pivot1 = df.pivot_table(values='engagement_rate', index='platform', columns='content_type', aggfunc='mean')
print(pivot1.round(2))
print()

# Melhor combinação
best = df.groupby(['platform', 'content_type'])['engagement_rate'].mean()
top5 = best.nlargest(5)
worst5 = best.nsmallest(5)
print("TOP 5 combinações (plataforma + tipo):")
for idx, val in top5.items():
    print(f"  {idx[0]} + {idx[1]}: {val:.2f}%")
print()
print("PIORES 5 combinações:")
for idx, val in worst5.items():
    print(f"  {idx[0]} + {idx[1]}: {val:.2f}%")
print()

# Gráfico
fig, ax = plt.subplots(figsize=(12, 6))
pivot1.plot(kind='bar', ax=ax, width=0.8)
ax.set_title('Engagement Rate por Plataforma e Tipo de Conteúdo', fontsize=14, fontweight='bold')
ax.set_ylabel('Engagement Rate (%)')
ax.set_xlabel('')
ax.legend(title='Tipo de Conteúdo')
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(os.path.join(CHARTS_DIR, '01_engagement_plataforma_tipo.png'), bbox_inches='tight')
plt.close()

# =====================================================
# ANÁLISE 2: ENGAGEMENT POR CATEGORIA DE CONTEÚDO
# =====================================================
print("=" * 60)
print("ANÁLISE 2: ENGAGEMENT POR CATEGORIA")
print("=" * 60)

pivot2 = df.pivot_table(values=['engagement_rate', 'views', 'likes', 'shares', 'comments_count'],
                         index='content_category', aggfunc='mean')
print(pivot2.round(2))
print()

# Por plataforma x categoria
pivot2b = df.pivot_table(values='engagement_rate', index='platform', columns='content_category', aggfunc='mean')
print("Engagement por plataforma x categoria:")
print(pivot2b.round(2))
print()

fig, ax = plt.subplots(figsize=(10, 6))
pivot2b.plot(kind='bar', ax=ax, width=0.8)
ax.set_title('Engagement Rate por Plataforma e Categoria', fontsize=14, fontweight='bold')
ax.set_ylabel('Engagement Rate (%)')
ax.set_xlabel('')
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(os.path.join(CHARTS_DIR, '02_engagement_plataforma_categoria.png'), bbox_inches='tight')
plt.close()

# =====================================================
# ANÁLISE 3: TAMANHO DO CRIADOR (CREATOR TIER)
# =====================================================
print("=" * 60)
print("ANÁLISE 3: ENGAGEMENT POR TAMANHO DO CRIADOR")
print("=" * 60)

tier_stats = df.groupby('creator_tier').agg(
    posts=('id', 'count'),
    eng_rate_mean=('engagement_rate', 'mean'),
    eng_rate_std=('engagement_rate', 'std'),
    views_mean=('views', 'mean'),
    likes_mean=('likes', 'mean'),
    shares_mean=('shares', 'mean'),
    followers_mean=('follower_count', 'mean')
).reindex(tier_order)
print(tier_stats.round(2))
print()

# Tier x plataforma
pivot3 = df.pivot_table(values='engagement_rate', index='creator_tier', columns='platform', aggfunc='mean')
pivot3 = pivot3.reindex(tier_order)
print("Engagement por tier x plataforma:")
print(pivot3.round(2))
print()

fig, ax = plt.subplots(figsize=(12, 6))
pivot3.plot(kind='bar', ax=ax, width=0.8)
ax.set_title('Engagement Rate por Tamanho do Criador e Plataforma', fontsize=14, fontweight='bold')
ax.set_ylabel('Engagement Rate (%)')
ax.set_xlabel('')
plt.xticks(rotation=15)
plt.tight_layout()
plt.savefig(os.path.join(CHARTS_DIR, '03_engagement_tier_plataforma.png'), bbox_inches='tight')
plt.close()

# =====================================================
# ANÁLISE 4: ORGÂNICO vs PATROCINADO (a pergunta de ouro)
# =====================================================
print("=" * 60)
print("ANÁLISE 4: ORGÂNICO vs PATROCINADO")
print("=" * 60)

spon_stats = df.groupby('is_sponsored').agg(
    posts=('id', 'count'),
    eng_rate=('engagement_rate', 'mean'),
    views=('views', 'mean'),
    likes=('likes', 'mean'),
    shares=('shares', 'mean'),
    comments=('comments_count', 'mean'),
    followers=('follower_count', 'mean')
)
spon_stats.index = ['Orgânico', 'Patrocinado']
print(spon_stats.round(2))
print()

# Patrocinado por plataforma
pivot4 = df.pivot_table(values='engagement_rate', index='platform', columns='is_sponsored', aggfunc='mean')
pivot4.columns = ['Orgânico', 'Patrocinado']
pivot4['Diferença (%)'] = ((pivot4['Patrocinado'] - pivot4['Orgânico']) / pivot4['Orgânico'] * 100)
print("Orgânico vs Patrocinado por plataforma:")
print(pivot4.round(2))
print()

# Patrocinado por tier do criador (controle justo)
pivot4b = df.pivot_table(values='engagement_rate', index='creator_tier', columns='is_sponsored', aggfunc='mean')
pivot4b.columns = ['Orgânico', 'Patrocinado']
pivot4b = pivot4b.reindex(tier_order)
pivot4b['Diferença (%)'] = ((pivot4b['Patrocinado'] - pivot4b['Orgânico']) / pivot4b['Orgânico'] * 100)
print("Orgânico vs Patrocinado por tier (comparação justa):")
print(pivot4b.round(2))
print()

# Patrocinado por categoria de sponsor
spon_cat = df[df['is_sponsored']].groupby('sponsor_category').agg(
    posts=('id', 'count'),
    eng_rate=('engagement_rate', 'mean'),
    views=('views', 'mean'),
    shares=('shares', 'mean')
).sort_values('eng_rate', ascending=False)
print("Performance por categoria de patrocinador:")
print(spon_cat.round(2))
print()

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
pivot4[['Orgânico', 'Patrocinado']].plot(kind='bar', ax=axes[0], width=0.7)
axes[0].set_title('Orgânico vs Patrocinado por Plataforma', fontweight='bold')
axes[0].set_ylabel('Engagement Rate (%)')
axes[0].set_xlabel('')
axes[0].tick_params(axis='x', rotation=0)

spon_cat['eng_rate'].plot(kind='barh', ax=axes[1], color='#2ecc71')
axes[1].set_title('Engagement por Categoria de Patrocínio', fontweight='bold')
axes[1].set_xlabel('Engagement Rate (%)')
plt.tight_layout()
plt.savefig(os.path.join(CHARTS_DIR, '04_organico_vs_patrocinado.png'), bbox_inches='tight')
plt.close()

# =====================================================
# ANÁLISE 5: PERFIL DEMOGRÁFICO DA AUDIÊNCIA
# =====================================================
print("=" * 60)
print("ANÁLISE 5: PERFIL DEMOGRÁFICO")
print("=" * 60)

# Por faixa etária
age_eng = df.groupby('audience_age_distribution').agg(
    posts=('id', 'count'),
    eng_rate=('engagement_rate', 'mean'),
    likes=('likes', 'mean'),
    shares=('shares', 'mean')
).sort_values('eng_rate', ascending=False)
print("Engagement por faixa etária:")
print(age_eng.round(2))
print()

# Por gênero
gender_eng = df.groupby('audience_gender_distribution').agg(
    posts=('id', 'count'),
    eng_rate=('engagement_rate', 'mean')
).sort_values('eng_rate', ascending=False)
print("Engagement por gênero da audiência:")
print(gender_eng.round(2))
print()

# Por localização
loc_eng = df.groupby('audience_location').agg(
    posts=('id', 'count'),
    eng_rate=('engagement_rate', 'mean')
).sort_values('eng_rate', ascending=False)
print("Engagement por localização:")
print(loc_eng.round(2))
print()

# Idade x plataforma
pivot5 = df.pivot_table(values='engagement_rate', index='audience_age_distribution', columns='platform', aggfunc='mean')
print("Engagement faixa etária x plataforma:")
print(pivot5.round(2))
print()

fig, axes = plt.subplots(1, 3, figsize=(18, 5))
age_eng['eng_rate'].plot(kind='bar', ax=axes[0], color='#3498db')
axes[0].set_title('Engagement por Faixa Etária', fontweight='bold')
axes[0].set_ylabel('Engagement Rate (%)')
axes[0].tick_params(axis='x', rotation=25)

gender_eng['eng_rate'].plot(kind='bar', ax=axes[1], color='#9b59b6')
axes[1].set_title('Engagement por Gênero', fontweight='bold')
axes[1].tick_params(axis='x', rotation=0)

loc_eng['eng_rate'].plot(kind='bar', ax=axes[2], color='#e67e22')
axes[2].set_title('Engagement por Localização', fontweight='bold')
axes[2].tick_params(axis='x', rotation=25)
plt.tight_layout()
plt.savefig(os.path.join(CHARTS_DIR, '05_perfil_demografico.png'), bbox_inches='tight')
plt.close()

# =====================================================
# ANÁLISE 6: DISCLOSURE TYPE (como o patrocínio é revelado)
# =====================================================
print("=" * 60)
print("ANÁLISE 6: TIPO DE DISCLOSURE")
print("=" * 60)

disc_stats = df[df['is_sponsored']].groupby('disclosure_type').agg(
    posts=('id', 'count'),
    eng_rate=('engagement_rate', 'mean'),
    shares=('shares', 'mean')
).sort_values('eng_rate', ascending=False)
print(disc_stats.round(2))
print()

disc_loc = df[df['is_sponsored']].groupby('disclosure_location').agg(
    posts=('id', 'count'),
    eng_rate=('engagement_rate', 'mean')
).sort_values('eng_rate', ascending=False)
print("Engagement por local do disclosure:")
print(disc_loc.round(2))
print()

# =====================================================
# ANÁLISE 7: HASHTAGS
# =====================================================
print("=" * 60)
print("ANÁLISE 7: ANÁLISE DE HASHTAGS")
print("=" * 60)

# Engagement por quantidade de hashtags
hash_eng = df.groupby('hashtag_count').agg(
    posts=('id', 'count'),
    eng_rate=('engagement_rate', 'mean')
)
print("Engagement por quantidade de hashtags:")
print(hash_eng.round(2))
print()

# Top hashtags individuais
all_hashtags = df['hashtags'].dropna().str.split(',').explode().str.strip()
top_hashtags = all_hashtags.value_counts().head(20)
print("Top 20 hashtags mais usadas:")
print(top_hashtags)
print()

# Engagement médio por hashtag (top 20)
def get_hashtag_engagement(tag):
    mask = df['hashtags'].fillna('').str.contains(tag, case=False, na=False)
    return df[mask]['engagement_rate'].mean()

hashtag_perf = pd.DataFrame({
    'hashtag': top_hashtags.index,
    'count': top_hashtags.values,
    'avg_engagement': [get_hashtag_engagement(h) for h in top_hashtags.index]
}).sort_values('avg_engagement', ascending=False)
print("Performance das top hashtags:")
print(hashtag_perf.to_string(index=False))
print()

fig, ax = plt.subplots(figsize=(12, 6))
ax.barh(hashtag_perf['hashtag'][:15], hashtag_perf['avg_engagement'][:15], color='#1abc9c')
ax.set_title('Engagement Médio das Top 15 Hashtags', fontsize=14, fontweight='bold')
ax.set_xlabel('Engagement Rate (%)')
plt.tight_layout()
plt.savefig(os.path.join(CHARTS_DIR, '06_hashtags_performance.png'), bbox_inches='tight')
plt.close()

# =====================================================
# ANÁLISE 8: CONTENT LENGTH vs ENGAGEMENT
# =====================================================
print("=" * 60)
print("ANÁLISE 8: TAMANHO DO CONTEÚDO")
print("=" * 60)

length_eng = df.groupby('content_length_bucket', observed=True).agg(
    posts=('id', 'count'),
    eng_rate=('engagement_rate', 'mean')
)
print("Engagement por tamanho do conteúdo:")
print(length_eng.round(2))
print()

# Length x content type
pivot8 = df.pivot_table(values='engagement_rate', index='content_length_bucket',
                         columns='content_type', aggfunc='mean', observed=True)
print("Tamanho x tipo:")
print(pivot8.round(2))
print()

# =====================================================
# ANÁLISE 9: TEMPORAL
# =====================================================
print("=" * 60)
print("ANÁLISE 9: ANÁLISE TEMPORAL")
print("=" * 60)

# Engagement por dia da semana
dow_eng = df.groupby('day_of_week')['engagement_rate'].mean()
dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
dow_eng = dow_eng.reindex(dow_order)
print("Engagement por dia da semana:")
print(dow_eng.round(2))
print()

# Volume de posts por mês
monthly = df.groupby(df['post_date'].dt.to_period('M')).agg(
    posts=('id', 'count'),
    eng_rate=('engagement_rate', 'mean')
)
print("Posts e engagement por mês (últimos 6):")
print(monthly.tail(6).round(2))
print()

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
dow_eng.plot(kind='bar', ax=axes[0], color='#2980b9')
axes[0].set_title('Engagement por Dia da Semana', fontweight='bold')
axes[0].set_ylabel('Engagement Rate (%)')
axes[0].tick_params(axis='x', rotation=30)

monthly['eng_rate'].plot(ax=axes[1], color='#e74c3c', linewidth=2)
axes[1].set_title('Engagement ao Longo do Tempo', fontweight='bold')
axes[1].set_ylabel('Engagement Rate (%)')
plt.tight_layout()
plt.savefig(os.path.join(CHARTS_DIR, '07_analise_temporal.png'), bbox_inches='tight')
plt.close()

# =====================================================
# ANÁLISE 10: O QUE NÃO FUNCIONA (eles pedem isso explicitamente)
# =====================================================
print("=" * 60)
print("ANÁLISE 10: O QUE NÃO FUNCIONA")
print("=" * 60)

# Posts com pior engagement (bottom 10%)
threshold_low = df['engagement_rate'].quantile(0.10)
low_eng = df[df['engagement_rate'] <= threshold_low]
print(f"Posts com engagement no bottom 10% (< {threshold_low:.2f}%):")
print(f"  Total: {len(low_eng)} posts")
print(f"  Plataformas: {low_eng['platform'].value_counts().to_dict()}")
print(f"  Tipo: {low_eng['content_type'].value_counts().to_dict()}")
print(f"  Categoria: {low_eng['content_category'].value_counts().to_dict()}")
print(f"  Sponsored: {low_eng['is_sponsored'].value_counts().to_dict()}")
print(f"  Tier: {low_eng['creator_tier'].value_counts().to_dict()}")
print()

# Posts com melhor engagement (top 10%)
threshold_high = df['engagement_rate'].quantile(0.90)
high_eng = df[df['engagement_rate'] >= threshold_high]
print(f"Posts com engagement no top 10% (> {threshold_high:.2f}%):")
print(f"  Total: {len(high_eng)} posts")
print(f"  Plataformas: {high_eng['platform'].value_counts().to_dict()}")
print(f"  Tipo: {high_eng['content_type'].value_counts().to_dict()}")
print(f"  Categoria: {high_eng['content_category'].value_counts().to_dict()}")
print(f"  Sponsored: {high_eng['is_sponsored'].value_counts().to_dict()}")
print(f"  Tier: {high_eng['creator_tier'].value_counts().to_dict()}")
print()

# =====================================================
# ANÁLISE 11: MELHORES COMBINAÇÕES (triple cross)
# =====================================================
print("=" * 60)
print("ANÁLISE 11: MELHORES COMBINAÇÕES (PLATAFORMA + TIPO + CATEGORIA)")
print("=" * 60)

triple = df.groupby(['platform', 'content_type', 'content_category']).agg(
    posts=('id', 'count'),
    eng_rate=('engagement_rate', 'mean'),
    shares_mean=('shares', 'mean')
).sort_values('eng_rate', ascending=False)

print("TOP 10 combinações:")
print(triple.head(10).round(2))
print()
print("PIORES 10 combinações:")
print(triple.tail(10).round(2))
print()

# =====================================================
# RESUMO EXECUTIVO (dados para o relatório)
# =====================================================
print("=" * 60)
print("RESUMO EXECUTIVO")
print("=" * 60)

print(f"""
DATASET: {len(df)} posts | {df['platform'].nunique()} plataformas | Mai/2023 a Mai/2025
NOTA: Dataset sintético detectado (variância baixa, distribuições uniformes)

ENGAGEMENT GERAL: {df['engagement_rate'].mean():.2f}% (range: {df['engagement_rate'].min():.2f}% - {df['engagement_rate'].max():.2f}%)

MELHOR PLATAFORMA: {df.groupby('platform')['engagement_rate'].mean().idxmax()} ({df.groupby('platform')['engagement_rate'].mean().max():.2f}%)
PIOR PLATAFORMA: {df.groupby('platform')['engagement_rate'].mean().idxmin()} ({df.groupby('platform')['engagement_rate'].mean().min():.2f}%)

MELHOR TIPO: {df.groupby('content_type')['engagement_rate'].mean().idxmax()} ({df.groupby('content_type')['engagement_rate'].mean().max():.2f}%)
PIOR TIPO: {df.groupby('content_type')['engagement_rate'].mean().idxmin()} ({df.groupby('content_type')['engagement_rate'].mean().min():.2f}%)

MELHOR CATEGORIA: {df.groupby('content_category')['engagement_rate'].mean().idxmax()} ({df.groupby('content_category')['engagement_rate'].mean().max():.2f}%)

ORGÂNICO: {df[~df['is_sponsored']]['engagement_rate'].mean():.2f}%
PATROCINADO: {df[df['is_sponsored']]['engagement_rate'].mean():.2f}%

MELHOR FAIXA ETÁRIA: {df.groupby('audience_age_distribution')['engagement_rate'].mean().idxmax()}
MELHOR GÊNERO: {df.groupby('audience_gender_distribution')['engagement_rate'].mean().idxmax()}
""")

print("Análise completa! Gráficos salvos em:", CHARTS_DIR)
print(f"Total de gráficos: {len(os.listdir(CHARTS_DIR))}")
