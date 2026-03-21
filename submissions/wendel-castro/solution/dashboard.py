"""
Dashboard Interativo de Performance — Social Media Strategy
Challenge 004 — G4 AI Master Challenge
Wendel Castro | Março 2026

Para rodar: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# === CONFIG ===
st.set_page_config(
    page_title="Social Media Performance",
    page_icon="📊",
    layout="wide"
)

# === LOAD DATA ===
@st.cache_data
def load_data():
    # Tenta path relativo primeiro, depois absoluto
    paths = [
        os.path.join(os.path.dirname(__file__), '..', '..', '..', 'dataset', 'social_media_dataset.csv'),
        r'C:\Users\usuario\OneDrive - SER EDUCACIONAL\Inteligência Artificial\Projetos-Pessoais-Claude\G4 Educação\dataset\social_media_dataset.csv'
    ]
    for p in paths:
        if os.path.exists(p):
            df = pd.read_csv(p)
            break
    else:
        st.error("Dataset não encontrado. Coloque o CSV na pasta dataset/")
        st.stop()

    df['post_date'] = pd.to_datetime(df['post_date'], format='mixed')
    df['engagement_rate'] = (df['likes'] + df['shares'] + df['comments_count']) / df['views'] * 100
    df['total_interactions'] = df['likes'] + df['shares'] + df['comments_count']

    def creator_tier(f):
        if f < 10000: return 'Nano (<10K)'
        elif f < 50000: return 'Micro (10-50K)'
        elif f < 100000: return 'Mid (50-100K)'
        elif f < 500000: return 'Macro (100-500K)'
        else: return 'Mega (500K+)'

    df['creator_tier'] = df['follower_count'].apply(creator_tier)
    df['year_month'] = df['post_date'].dt.to_period('M').astype(str)
    df['hashtag_count'] = df['hashtags'].fillna('').apply(lambda x: len(x.split(',')) if x else 0)

    return df

df = load_data()

# === SIDEBAR FILTERS ===
st.sidebar.title("Filtros")

platforms = st.sidebar.multiselect(
    "Plataforma",
    options=sorted(df['platform'].unique()),
    default=sorted(df['platform'].unique())
)

content_types = st.sidebar.multiselect(
    "Tipo de Conteúdo",
    options=sorted(df['content_type'].unique()),
    default=sorted(df['content_type'].unique())
)

categories = st.sidebar.multiselect(
    "Categoria",
    options=sorted(df['content_category'].unique()),
    default=sorted(df['content_category'].unique())
)

sponsored_filter = st.sidebar.radio(
    "Patrocínio",
    options=["Todos", "Orgânico", "Patrocinado"]
)

date_range = st.sidebar.date_input(
    "Período",
    value=(df['post_date'].min().date(), df['post_date'].max().date()),
    min_value=df['post_date'].min().date(),
    max_value=df['post_date'].max().date()
)

# Apply filters
mask = (
    df['platform'].isin(platforms) &
    df['content_type'].isin(content_types) &
    df['content_category'].isin(categories)
)
if sponsored_filter == "Orgânico":
    mask &= ~df['is_sponsored']
elif sponsored_filter == "Patrocinado":
    mask &= df['is_sponsored']

if len(date_range) == 2:
    mask &= (df['post_date'].dt.date >= date_range[0]) & (df['post_date'].dt.date <= date_range[1])

filtered = df[mask]

# === HEADER ===
st.title("Social Media Performance Dashboard")
st.caption(f"Analisando {len(filtered):,} posts de {len(df):,} total | Filtros ativos: {len(df) - len(filtered):,} posts filtrados")

# === KPIs ===
col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Posts", f"{len(filtered):,}")
col2.metric("Eng. Rate Médio", f"{filtered['engagement_rate'].mean():.2f}%")
col3.metric("Views Médio", f"{filtered['views'].mean():,.0f}")
col4.metric("Likes Médio", f"{filtered['likes'].mean():,.0f}")
col5.metric("Shares Médio", f"{filtered['shares'].mean():,.0f}")
col6.metric("Comments Médio", f"{filtered['comments_count'].mean():,.0f}")

st.divider()

# === TAB LAYOUT ===
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Visão Geral", "Orgânico vs Patrocinado", "Audiência", "Creators", "Recomendador"
])

# --- TAB 1: VISÃO GERAL ---
with tab1:
    col_left, col_right = st.columns(2)

    with col_left:
        # Engagement por plataforma x tipo
        pivot = filtered.pivot_table(values='engagement_rate', index='platform',
                                     columns='content_type', aggfunc='mean').round(2)
        fig = px.imshow(pivot, text_auto='.2f', color_continuous_scale='Blues',
                        title='Engagement Rate: Plataforma x Tipo de Conteúdo',
                        labels=dict(color="Eng. Rate (%)"))
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        # Engagement por plataforma x categoria
        pivot2 = filtered.pivot_table(values='engagement_rate', index='platform',
                                      columns='content_category', aggfunc='mean').round(2)
        fig2 = px.imshow(pivot2, text_auto='.2f', color_continuous_scale='Greens',
                         title='Engagement Rate: Plataforma x Categoria',
                         labels=dict(color="Eng. Rate (%)"))
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)

    # Evolução temporal
    monthly = filtered.groupby(filtered['post_date'].dt.to_period('M').astype(str)).agg(
        posts=('id', 'count'),
        eng_rate=('engagement_rate', 'mean'),
        total_views=('views', 'sum')
    ).reset_index()

    fig3 = make_subplots(specs=[[{"secondary_y": True}]])
    fig3.add_trace(go.Bar(x=monthly['post_date'], y=monthly['posts'], name='Posts', opacity=0.5), secondary_y=False)
    fig3.add_trace(go.Scatter(x=monthly['post_date'], y=monthly['eng_rate'], name='Eng. Rate', mode='lines+markers'), secondary_y=True)
    fig3.update_layout(title='Volume de Posts e Engagement ao Longo do Tempo', height=400)
    fig3.update_yaxes(title_text="Posts", secondary_y=False)
    fig3.update_yaxes(title_text="Engagement Rate (%)", secondary_y=True)
    st.plotly_chart(fig3, use_container_width=True)

    # Top combinações
    st.subheader("Top 10 Combinações (Plataforma + Tipo + Categoria)")
    top_combos = filtered.groupby(['platform', 'content_type', 'content_category']).agg(
        posts=('id', 'count'),
        eng_rate=('engagement_rate', 'mean'),
        avg_shares=('shares', 'mean')
    ).sort_values('eng_rate', ascending=False).head(10).round(2)
    st.dataframe(top_combos, use_container_width=True)

# --- TAB 2: ORGÂNICO vs PATROCINADO ---
with tab2:
    st.subheader("Análise de ROI: Orgânico vs Patrocinado")

    col1, col2 = st.columns(2)
    organic = filtered[~filtered['is_sponsored']]
    sponsored = filtered[filtered['is_sponsored']]

    with col1:
        comparison = pd.DataFrame({
            'Métrica': ['Posts', 'Eng. Rate (%)', 'Views Médio', 'Likes Médio', 'Shares Médio', 'Comments Médio'],
            'Orgânico': [
                len(organic), organic['engagement_rate'].mean(),
                organic['views'].mean(), organic['likes'].mean(),
                organic['shares'].mean(), organic['comments_count'].mean()
            ],
            'Patrocinado': [
                len(sponsored), sponsored['engagement_rate'].mean(),
                sponsored['views'].mean(), sponsored['likes'].mean(),
                sponsored['shares'].mean(), sponsored['comments_count'].mean()
            ]
        })
        comparison['Diferença (%)'] = ((comparison['Patrocinado'] - comparison['Orgânico']) / comparison['Orgânico'] * 100).round(2)
        st.dataframe(comparison.round(2), use_container_width=True, hide_index=True)

    with col2:
        # Por categoria de sponsor
        if len(sponsored) > 0:
            spon_cat = sponsored.groupby('sponsor_category')['engagement_rate'].mean().sort_values(ascending=True)
            fig = px.bar(x=spon_cat.values, y=spon_cat.index, orientation='h',
                         title='Engagement por Categoria de Patrocínio',
                         labels={'x': 'Engagement Rate (%)', 'y': 'Categoria'})
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)

    # Orgânico vs patrocinado por plataforma
    comp_plat = filtered.pivot_table(values='engagement_rate', index='platform',
                                      columns='is_sponsored', aggfunc='mean').round(2)
    comp_plat.columns = ['Orgânico', 'Patrocinado']
    fig = go.Figure(data=[
        go.Bar(name='Orgânico', x=comp_plat.index, y=comp_plat['Orgânico']),
        go.Bar(name='Patrocinado', x=comp_plat.index, y=comp_plat['Patrocinado'])
    ])
    fig.update_layout(barmode='group', title='Orgânico vs Patrocinado por Plataforma', height=400)
    st.plotly_chart(fig, use_container_width=True)

    # Disclosure analysis
    st.subheader("Impacto do Tipo de Disclosure")
    disc = sponsored.groupby(['disclosure_type', 'disclosure_location']).agg(
        posts=('id', 'count'),
        eng_rate=('engagement_rate', 'mean')
    ).sort_values('eng_rate', ascending=False).round(2)
    st.dataframe(disc, use_container_width=True)

# --- TAB 3: AUDIÊNCIA ---
with tab3:
    st.subheader("Perfil Demográfico de Engajamento")

    col1, col2, col3 = st.columns(3)

    with col1:
        age_data = filtered.groupby('audience_age_distribution')['engagement_rate'].mean().sort_values(ascending=False)
        fig = px.bar(x=age_data.index, y=age_data.values,
                     title='Engagement por Faixa Etária',
                     labels={'x': 'Faixa Etária', 'y': 'Eng. Rate (%)'})
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        gender_data = filtered.groupby('audience_gender_distribution')['engagement_rate'].mean().sort_values(ascending=False)
        fig = px.bar(x=gender_data.index, y=gender_data.values,
                     title='Engagement por Gênero',
                     labels={'x': 'Gênero', 'y': 'Eng. Rate (%)'})
        st.plotly_chart(fig, use_container_width=True)

    with col3:
        loc_data = filtered.groupby('audience_location')['engagement_rate'].mean().sort_values(ascending=False)
        fig = px.bar(x=loc_data.index, y=loc_data.values,
                     title='Engagement por Localização',
                     labels={'x': 'País', 'y': 'Eng. Rate (%)'})
        st.plotly_chart(fig, use_container_width=True)

    # Heatmap idade x plataforma
    age_plat = filtered.pivot_table(values='engagement_rate', index='audience_age_distribution',
                                     columns='platform', aggfunc='mean').round(2)
    fig = px.imshow(age_plat, text_auto='.2f', color_continuous_scale='YlOrRd',
                    title='Engagement: Faixa Etária x Plataforma')
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

# --- TAB 4: CREATORS ---
with tab4:
    st.subheader("Análise por Tamanho do Criador")

    tier_order = ['Nano (<10K)', 'Micro (10-50K)', 'Mid (50-100K)', 'Macro (100-500K)', 'Mega (500K+)']

    tier_stats = filtered.groupby('creator_tier').agg(
        posts=('id', 'count'),
        eng_rate=('engagement_rate', 'mean'),
        avg_views=('views', 'mean'),
        avg_likes=('likes', 'mean'),
        avg_shares=('shares', 'mean'),
        avg_followers=('follower_count', 'mean')
    ).reindex(tier_order).round(2)

    st.dataframe(tier_stats, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(x=tier_stats.index, y=tier_stats['eng_rate'],
                     title='Engagement por Tier de Criador',
                     labels={'x': 'Tier', 'y': 'Eng. Rate (%)'},
                     color=tier_stats['eng_rate'], color_continuous_scale='Viridis')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Tier x plataforma
        tier_plat = filtered.pivot_table(values='engagement_rate', index='creator_tier',
                                          columns='platform', aggfunc='mean').reindex(tier_order).round(2)
        fig = px.imshow(tier_plat, text_auto='.2f', color_continuous_scale='Viridis',
                        title='Engagement: Tier x Plataforma')
        st.plotly_chart(fig, use_container_width=True)

    # Scatter: followers vs engagement
    sample = filtered.sample(min(5000, len(filtered)), random_state=42)
    fig = px.scatter(sample, x='follower_count', y='engagement_rate',
                     color='platform', opacity=0.3, title='Seguidores vs Engagement',
                     labels={'follower_count': 'Seguidores', 'engagement_rate': 'Eng. Rate (%)'})
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

# --- TAB 5: RECOMENDADOR ---
with tab5:
    st.subheader("Recomendador de Conteúdo")
    st.write("Selecione os parâmetros e veja a performance estimada com base nos dados históricos.")

    col1, col2, col3 = st.columns(3)

    with col1:
        rec_platform = st.selectbox("Plataforma", sorted(df['platform'].unique()))
    with col2:
        rec_type = st.selectbox("Tipo de Conteúdo", sorted(df['content_type'].unique()))
    with col3:
        rec_category = st.selectbox("Categoria", sorted(df['content_category'].unique()))

    col4, col5 = st.columns(2)
    with col4:
        rec_sponsored = st.checkbox("Patrocinado?")
    with col5:
        rec_tier = st.selectbox("Tier do Criador", tier_order)

    # Buscar posts similares
    similar = df[
        (df['platform'] == rec_platform) &
        (df['content_type'] == rec_type) &
        (df['content_category'] == rec_category) &
        (df['is_sponsored'] == rec_sponsored) &
        (df['creator_tier'] == rec_tier)
    ]

    if len(similar) > 0:
        st.success(f"Encontrados {len(similar)} posts com perfil similar")

        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        mcol1.metric("Eng. Rate Estimado", f"{similar['engagement_rate'].mean():.2f}%")
        mcol2.metric("Views Estimado", f"{similar['views'].mean():,.0f}")
        mcol3.metric("Likes Estimado", f"{similar['likes'].mean():,.0f}")
        mcol4.metric("Shares Estimado", f"{similar['shares'].mean():,.0f}")

        # Comparar com média geral
        diff = similar['engagement_rate'].mean() - df['engagement_rate'].mean()
        if diff > 0:
            st.info(f"Essa combinação performa {abs(diff):.2f}pp ACIMA da média geral")
        else:
            st.warning(f"Essa combinação performa {abs(diff):.2f}pp ABAIXO da média geral")

        # Hashtags mais comuns nessa combinação
        hashtags_similar = similar['hashtags'].dropna().str.split(',').explode().str.strip()
        top_hash = hashtags_similar.value_counts().head(10)
        if len(top_hash) > 0:
            st.write("**Hashtags mais usadas nesse perfil:**")
            st.write(", ".join([f"`{h}`" for h in top_hash.index]))
    else:
        st.warning("Nenhum post encontrado com essa combinação exata. Tente ajustar os filtros.")

    st.divider()
    st.subheader("Nota sobre os dados")
    st.info("""
    **Transparência metodológica:** Este dataset apresenta características de dados sintéticos
    (variância muito baixa nas métricas, distribuições uniformes, correlações próximas de zero).

    O dashboard foi construído com metodologia robusta que funciona independente da natureza dos dados.
    Com dados reais de produção, os padrões e insights seriam significativamente mais ricos.

    A estrutura, filtros e visualizações estão prontos para receber dados reais a qualquer momento.
    """)

# === FOOTER ===
st.divider()
st.caption("Dashboard criado por Wendel Castro | Challenge 004 — G4 AI Master Challenge | Março 2026")
st.caption("Construído com Streamlit + Plotly | Copiloto: Claude Code")
