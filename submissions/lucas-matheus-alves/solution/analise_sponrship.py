"""
=============================================================================
Análise de Sponsorship & Engagement - Social Media Dataset
Analista: Script automatizado de Influencer Marketing Analytics
=============================================================================
Objetivo: Comparar performance orgânica vs patrocinada, calcular lift de
engajamento e estimar ROI proxy financeiro para decisões de patrocínio.
=============================================================================
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# 1. CARREGAMENTO DO DATASET
# =============================================================================
print("=" * 65)
print("  SOCIAL MEDIA SPONSORSHIP & ENGAGEMENT ANALYTICS")
print("=" * 65)
print("\n[1/8] Carregando dataset...")

df = pd.read_csv('social_media_dataset.csv')
print(f"      ✓ Dataset carregado: {df.shape[0]:,} linhas | {df.shape[1]} colunas")
print(f"      ✓ Colunas disponíveis: {list(df.columns)}")

# =============================================================================
# 2. FILTRAGEM INICIAL
# =============================================================================
print("\n[2/8] Aplicando filtros...")

tamanho_original = len(df)

# Filtrar plataformas alvo
plataformas_alvo = ['Instagram', 'TikTok', 'YouTube']
df = df[df['platform'].isin(plataformas_alvo)]
print(f"      ✓ Plataformas (Instagram/TikTok/YouTube): {len(df):,} linhas")

# Filtrar views > 100
df = df[df['views'] > 100]
print(f"      ✓ Views > 100: {len(df):,} linhas")

# Filtrar follower_count > 500
df = df[df['follower_count'] > 500]
print(f"      ✓ Follower_count > 500: {len(df):,} linhas")

print(f"\n      → Registros removidos na filtragem: {tamanho_original - len(df):,}")
print(f"      → Registros finais para análise:    {len(df):,}")

# =============================================================================
# 3. ENGENHARIA DE FEATURES
# =============================================================================
print("\n[3/8] Criando features...")

# --- post_date → datetime ---
df['post_date'] = pd.to_datetime(df['post_date'], format='mixed', dayfirst=False)

# --- Dia da semana (em inglês para facilitar agrupamentos) ---
df['day_of_week'] = df['post_date'].dt.day_name()

# --- hour_bin: faixas horárias ---
hora = df['post_date'].dt.hour
conditions = [
    (hora >= 0)  & (hora < 6),
    (hora >= 6)  & (hora < 12),
    (hora >= 12) & (hora < 18),
    (hora >= 18) & (hora < 24),
]
labels_hora = ['Madrugada', 'Manhã', 'Tarde', 'Noite']
df['hour_bin'] = np.select(conditions, labels_hora, default='Desconhecido')

# --- Tier por faixa de seguidores ---
df['tier'] = pd.cut(
    df['follower_count'],
    bins=[0, 10_000, 100_000, 500_000, float('inf')],
    labels=['Nano/Micro baixo', 'Micro', 'Mid/Macro', 'Mega'],
    right=True
)

# --- Engagement total ---
# Colunas reais: likes, shares, comments_count
df['engagement_total'] = df['likes'] + df['shares'] + df['comments_count']

# --- Engagement Rate (ER) ---
df['ER'] = (df['engagement_total'] / df['views'].clip(lower=1)) * 100

# --- is_sponsored como booleano limpo ---
# Pode vir como TRUE/FALSE string ou bool
df['is_sponsored'] = df['is_sponsored'].astype(str).str.upper().str.strip() == 'TRUE'

print(f"      ✓ post_date convertido para datetime")
print(f"      ✓ day_of_week criado")
print(f"      ✓ hour_bin criado (Madrugada/Manhã/Tarde/Noite)")
print(f"      ✓ tier criado: {df['tier'].value_counts().to_dict()}")
print(f"      ✓ engagement_total = likes + shares + comments_count")
print(f"      ✓ ER calculado (engagement_total / views * 100)")
print(f"      ✓ is_sponsored: {df['is_sponsored'].value_counts().to_dict()}")

# =============================================================================
# 4. G_FACTOR: ER normalizado pela mediana do grupo (platform + tier)
# =============================================================================
print("\n[4/8] Calculando G_Factor...")

# Mediana de ER por plataforma + tier
mediana_er = df.groupby(['platform', 'tier'], observed=True)['ER'].transform('median')

# G_Factor = ER individual / mediana do grupo — evita divisão por zero
df['G_Factor'] = df['ER'] / mediana_er.clip(lower=0.0001)

print(f"      ✓ G_Factor calculado (ER / mediana ER por platform+tier)")
print(f"      ✓ G_Factor médio geral: {df['G_Factor'].mean():.3f}")
print(f"      ✓ G_Factor mediano geral: {df['G_Factor'].median():.3f}")

# =============================================================================
# 5. TABELA LIFT: ER e G por grupo (orgânico vs patrocinado)
# =============================================================================
print("\n[5/8] Construindo tabela de lift...")

# Agregar métricas por grupo de análise
lift_agg = df.groupby(
    ['platform', 'tier', 'is_sponsored', 'content_category', 'day_of_week'],
    observed=True
).agg(
    ER_medio=('ER', 'mean'),
    G_medio=('G_Factor', 'mean'),
    posts=('id', 'count')
).reset_index()

# Separar orgânico e patrocinado antes do pivot
lift_org  = lift_agg[lift_agg['is_sponsored'] == False].copy()
lift_spon = lift_agg[lift_agg['is_sponsored'] == True].copy()

# Renomear colunas para merge
lift_org  = lift_org.rename(columns={'ER_medio': 'ER_org',  'G_medio': 'G_org',  'posts': 'posts_org'})
lift_spon = lift_spon.rename(columns={'ER_medio': 'ER_spon', 'G_medio': 'G_spon', 'posts': 'posts_spon'})

# Remover coluna is_sponsored antes do merge
lift_org  = lift_org.drop(columns=['is_sponsored'])
lift_spon = lift_spon.drop(columns=['is_sponsored'])

# Merge pelos grupos comuns
chaves_grupo = ['platform', 'tier', 'content_category', 'day_of_week']
lift_pivot = pd.merge(
    lift_org[chaves_grupo + ['ER_org', 'G_org', 'posts_org']],
    lift_spon[chaves_grupo + ['ER_spon', 'G_spon', 'posts_spon']],
    on=chaves_grupo,
    how='inner'
)

# Calcular lift_G
lift_pivot['lift_G'] = lift_pivot['G_spon'] / lift_pivot['G_org'].clip(lower=0.0001)

# Filtrar grupos com volume mínimo para confiabilidade estatística
lift_pivot = lift_pivot[
    (lift_pivot['posts_spon'] >= 5) &
    (lift_pivot['posts_org']  >= 10)
]

print(f"      ✓ Grupos com posts_spon ≥ 5 e posts_org ≥ 10: {len(lift_pivot):,} grupos")

# Salvar
lift_pivot.to_csv('lift_roi_por_grupo.csv', index=False)
print(f"      ✓ Salvo: lift_roi_por_grupo.csv ({len(lift_pivot):,} linhas)")

# =============================================================================
# 6. ROI FINANCEIRO PROXY (somente patrocinados)
# =============================================================================
print("\n[6/8] Calculando ROI financeiro proxy...")

# Isolar posts patrocinados
df_spon = df[df['is_sponsored'] == True].copy()

# Custo estimado por tier (tabela de referência de mercado)
custo_por_tier = {
    'Nano/Micro baixo': 800,
    'Micro':            5_000,
    'Mid/Macro':       20_000,
    'Mega':            60_000,
}

df_spon['custo_estimado'] = df_spon['tier'].astype(str).map(custo_por_tier).astype(float)

# Valor gerado: cada unidade de engajamento = R$0,03 de valor de mídia estimado
df_spon['valor_gerado'] = df_spon['engagement_total'] * 0.03

# ROI estimado em %
df_spon['roi_estimado_%'] = (
    (df_spon['valor_gerado'] - df_spon['custo_estimado']) /
    df_spon['custo_estimado'].clip(lower=0.01)
) * 100

# Agregar por platform + tier + content_category
roi_agg = df_spon.groupby(
    ['platform', 'tier', 'content_category'],
    observed=True
).agg(
    roi_medio_pct=('roi_estimado_%', 'mean'),
    lift_G_medio=('G_Factor', 'mean'),
    posts_patrocinados=('id', 'count'),
    valor_gerado_total=('valor_gerado', 'sum'),
    custo_total=('custo_estimado', 'sum'),
    engagement_medio=('engagement_total', 'mean')
).reset_index()

# Ordenar por ROI descendente
roi_agg = roi_agg.sort_values('roi_medio_pct', ascending=False)

# Salvar
roi_agg.to_csv('roi_financeiro_por_tier.csv', index=False)
print(f"      ✓ Salvo: roi_financeiro_por_tier.csv ({len(roi_agg):,} linhas)")

# =============================================================================
# 7. EXPORTAR DATASET PROCESSADO COMPLETO
# =============================================================================
print("\n[7/8] Exportando dataset processado...")

df.to_csv('dados_processados_com_gfactor.csv', index=False)
print(f"      ✓ Salvo: dados_processados_com_gfactor.csv ({len(df):,} linhas)")

# =============================================================================
# 8. PRINTS FINAIS — INSIGHTS EXECUTIVOS
# =============================================================================
print("\n[8/8] Gerando insights finais...")

# ── Separador visual ──────────────────────────────────────────────────────────
sep = "─" * 65

print(f"\n{'=' * 65}")
print("  📊  INSIGHTS EXECUTIVOS — ANÁLISE DE SPONSORSHIP")
print(f"{'=' * 65}")

# --- Top 5 lift_G ---
print(f"\n🏆  TOP 5 GRUPOS POR LIFT DE G_FACTOR (patrocinado vs orgânico)")
print(sep)
top_lift = (
    lift_pivot[['platform', 'tier', 'content_category', 'day_of_week',
                'lift_G', 'ER_spon', 'ER_org', 'posts_spon', 'posts_org']]
    .sort_values('lift_G', ascending=False)
    .head(5)
    .reset_index(drop=True)
)
top_lift.index += 1
for _, row in top_lift.iterrows():
    print(
        f"  {_}. {row['platform']:10s} | {str(row['tier']):18s} | "
        f"{row['content_category']:12s} | {row['day_of_week']:9s} | "
        f"lift_G={row['lift_G']:.2f}x  "
        f"(ER org={row['ER_org']:.2f}% → spon={row['ER_spon']:.2f}%)"
    )

# --- Top 5 ROI estimado ---
print(f"\n💰  TOP 5 GRUPOS POR ROI FINANCEIRO ESTIMADO (patrocinados)")
print(sep)
top_roi = roi_agg.head(5).reset_index(drop=True)
top_roi.index += 1
for _, row in top_roi.iterrows():
    print(
        f"  {_}. {row['platform']:10s} | {str(row['tier']):18s} | "
        f"{row['content_category']:12s} | "
        f"ROI={row['roi_medio_pct']:+.1f}%  "
        f"lift_G={row['lift_G_medio']:.2f}x  "
        f"posts={int(row['posts_patrocinados'])}"
    )

# --- Médias gerais ---
print(f"\n📈  MÉDIAS GERAIS DO DATASET FILTRADO")
print(sep)

er_org_med  = df[df['is_sponsored'] == False]['ER'].mean()
er_spon_med = df[df['is_sponsored'] == True]['ER'].mean()
g_org_med   = df[df['is_sponsored'] == False]['G_Factor'].mean()
g_spon_med  = df[df['is_sponsored'] == True]['G_Factor'].mean()
roi_geral   = df_spon['roi_estimado_%'].mean()

print(f"  • ER médio orgânico:          {er_org_med:.3f}%")
print(f"  • ER médio patrocinado:       {er_spon_med:.3f}%")
print(f"  • G_Factor médio orgânico:    {g_org_med:.3f}")
print(f"  • G_Factor médio patrocinado: {g_spon_med:.3f}")
print(f"  • ROI médio estimado geral:   {roi_geral:+.1f}%")
print(f"  • Total de posts analisados:  {len(df):,}")
print(f"  • Posts patrocinados:         {df['is_sponsored'].sum():,} ({df['is_sponsored'].mean()*100:.1f}%)")
print(f"  • Posts orgânicos:            {(~df['is_sponsored']).sum():,} ({(~df['is_sponsored']).mean()*100:.1f}%)")

# --- Distribuição de tier ---
print(f"\n📊  DISTRIBUIÇÃO POR TIER (pós-filtro)")
print(sep)
tier_dist = df['tier'].value_counts().sort_index()
for tier, cnt in tier_dist.items():
    pct = cnt / len(df) * 100
    bar = "█" * int(pct / 2)
    print(f"  {str(tier):20s}: {cnt:6,} posts ({pct:5.1f}%)  {bar}")

# --- Breakdown por plataforma ---
print(f"\n📱  BREAKDOWN POR PLATAFORMA")
print(sep)
plat_dist = df.groupby('platform').agg(
    posts=('id', 'count'),
    er_medio=('ER', 'mean'),
    pct_patrocinado=('is_sponsored', 'mean')
).reset_index()
for _, row in plat_dist.iterrows():
    print(
        f"  {row['platform']:10s}: {int(row['posts']):6,} posts | "
        f"ER={row['er_medio']:.2f}% | "
        f"% patrocinado={row['pct_patrocinado']*100:.1f}%"
    )

print(f"\n{'=' * 65}")
print("  ✅  ANÁLISE CONCLUÍDA — 3 arquivos exportados com sucesso")
print(f"{'=' * 65}")
print("\n  Arquivos gerados:")
print("    1. dados_processados_com_gfactor.csv  — dataset completo enriquecido")
print("    2. lift_roi_por_grupo.csv             — tabela de lift org vs spon")
print("    3. roi_financeiro_por_tier.csv        — ROI estimado por segmento")
print()