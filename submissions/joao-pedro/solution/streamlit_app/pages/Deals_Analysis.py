"""
Pipeline Analysis - Análise de tempo e saúde do pipeline
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from core.data_loader import load_benchmarks, load_deals, load_raw_data, preprocess_pipeline
from core.scoring_engine import score_all_deals

st.set_page_config(page_title="Pipeline Analysis", page_icon="📊", layout="wide")

st.page_link("pages/Navegacao.py", label="← Navegação", icon=None)


# Cache
@st.cache_data(ttl=3600)
def load_data():
    benchmarks = load_benchmarks()
    engaging_deals = load_deals(deal_stage='Engaging')
    results = score_all_deals(engaging_deals, benchmarks)
    pipeline_df, _, products_df, _ = load_raw_data()
    pipeline_df = preprocess_pipeline(pipeline_df, products_df)
    return benchmarks, results, pipeline_df


benchmarks, results, pipeline_df = load_data()

# =============================================================================
# HEADER
# =============================================================================
st.title("📊 Pipeline Analysis")
st.markdown("""
Análise de tempo no pipeline, distribuição de scores e saúde geral do funil de vendas.
""")

st.divider()

# =============================================================================
# OVERVIEW DO PIPELINE
# =============================================================================
st.subheader("📋 Overview do Pipeline")

total_deals = len(pipeline_df)
engaging_count = len(pipeline_df[pipeline_df['deal_stage'] == 'Engaging'])
won_count = len(pipeline_df[pipeline_df['deal_stage'] == 'Won'])
lost_count = len(pipeline_df[pipeline_df['deal_stage'] == 'Lost'])
prospecting_count = len(pipeline_df[pipeline_df['deal_stage'] == 'Prospecting'])

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total de Deals", f"{total_deals:,}")
with col2:
    st.metric("🔵 Engaging", f"{engaging_count:,}", delta=f"{engaging_count/total_deals*100:.1f}%")
with col3:
    st.metric("✅ Won", f"{won_count:,}", delta=f"{won_count/total_deals*100:.1f}%")
with col4:
    st.metric("❌ Lost", f"{lost_count:,}", delta=f"{lost_count/total_deals*100:.1f}%")
with col5:
    st.metric("🔍 Prospecting", f"{prospecting_count:,}", delta=f"{prospecting_count/total_deals*100:.1f}%")

st.divider()

# =============================================================================
# ANÁLISE DE TEMPO — A TESE
# =============================================================================
st.subheader("⏱️ Análise de Tempo: A Tese do Pipeline Travado")

st.markdown("""
**Achado central:** Deals que vencem são fechados rapidamente. Deals que se arrastam têm probabilidade
de fechamento progressivamente menor — e o pipeline Engaging está 2.9× acima da mediana dos deals Won.
""")

won_median = benchmarks['won_median']
lost_median = benchmarks['lost_median']
engaging_median = benchmarks['engaging_median']
engaging_ratio = engaging_median / won_median if won_median > 0 else 0

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Mediana Won",
        f"{won_median:.0f} dias",
        help="Tempo mediano para fechar um deal ganho"
    )
with col2:
    st.metric(
        "Mediana Lost",
        f"{lost_median:.0f} dias",
        help="Tempo mediano de deals perdidos (perdidos cedo — qualificação ruim)"
    )
with col3:
    st.metric(
        "Mediana Engaging",
        f"{engaging_median:.0f} dias",
        help="Tempo mediano dos deals abertos atualmente"
    )
with col4:
    st.metric(
        "Ratio Engaging / Won",
        f"{engaging_ratio:.1f}×",
        delta="acima do ideal",
        delta_color="inverse",
        help="Quantas vezes o pipeline está além da mediana Won"
    )

# Gráfico de comparação das medianas
fig = go.Figure()

stages = ['Won (fechados)', 'Lost (perdidos)', 'Engaging (abertos)']
medians = [won_median, lost_median, engaging_median]
colors = ['#2ecc71', '#e74c3c', '#3498db']

fig.add_trace(go.Bar(
    x=stages,
    y=medians,
    marker_color=colors,
    text=[f"{v:.0f} dias" for v in medians],
    textposition='outside'
))

fig.add_hline(
    y=won_median,
    line_dash="dash",
    line_color="#2ecc71",
    annotation_text=f"Referência Won: {won_median:.0f}d",
    annotation_position="right"
)

fig.update_layout(
    title='Mediana de Dias no Pipeline por Estágio',
    yaxis_title='Dias no Pipeline',
    showlegend=False,
    yaxis=dict(range=[0, max(medians) * 1.25])
)

st.plotly_chart(fig, use_container_width=True)

# Insight crítico
st.error(f"""
🔥 **O pipeline Engaging está {engaging_ratio:.1f}× acima da mediana Won**

- Deals ganhos: mediana de **{won_median:.0f} dias**
- Deals perdidos: mediana de **{lost_median:.0f} dias** (descartados cedo — qualificação insuficiente)
- Pipeline atual: mediana de **{engaging_median:.0f} dias** (arrasto estrutural)

**Conclusão:** O pipeline não está travado por falta de qualidade — está travado por falta de ação.
""")

st.divider()

# =============================================================================
# WIN RATE POR FAIXA DE TEMPO
# =============================================================================
st.subheader("📉 Win Rate por Faixa de Tempo")

st.markdown("""
Quanto mais tempo um deal passa no pipeline, menor é a chance de fechamento.
""")

# Calcular win rate por bucket de tempo
closed_df = pipeline_df[pipeline_df['deal_stage'].isin(['Won', 'Lost'])].copy()
closed_df = closed_df[closed_df['days_in_pipeline'].notna() & (closed_df['days_in_pipeline'] >= 0)]

def assign_bucket(days):
    if days < 28:
        return '< 28d'
    elif days < 57:
        return '28–57d'
    elif days < 85:
        return '57–85d'
    elif days < 165:
        return '85–165d'
    elif days < 200:
        return '165–200d'
    else:
        return '> 200d'

bucket_order = ['< 28d', '28–57d', '57–85d', '85–165d', '165–200d', '> 200d']

closed_df['bucket'] = closed_df['days_in_pipeline'].apply(assign_bucket)
closed_df['won'] = (closed_df['deal_stage'] == 'Won').astype(int)

bucket_stats = (
    closed_df
    .groupby('bucket', observed=True)
    .agg(total=('won', 'count'), won_count=('won', 'sum'))
    .reset_index()
)
bucket_stats['win_rate'] = bucket_stats['won_count'] / bucket_stats['total'] * 100
bucket_stats['bucket'] = pd.Categorical(bucket_stats['bucket'], categories=bucket_order, ordered=True)
bucket_stats = bucket_stats.sort_values('bucket')

col1, col2 = st.columns([1, 2])

with col1:
    st.dataframe(
        bucket_stats[['bucket', 'total', 'won_count', 'win_rate']].rename(columns={
            'bucket': 'Faixa',
            'total': 'Total Deals',
            'won_count': 'Won',
            'win_rate': 'Win Rate'
        }),
        use_container_width=True,
        hide_index=True,
        column_config={
            'Win Rate': st.column_config.NumberColumn('Win Rate', format="%.1f%%")
        }
    )

with col2:
    fig = px.bar(
        bucket_stats,
        x='bucket',
        y='win_rate',
        title='Win Rate por Faixa de Tempo no Pipeline',
        color='win_rate',
        color_continuous_scale='RdYlGn',
        text=bucket_stats['win_rate'].apply(lambda x: f"{x:.1f}%"),
        labels={'bucket': 'Tempo no Pipeline', 'win_rate': 'Win Rate (%)'}
    )
    fig.update_traces(textposition='outside')
    fig.add_hline(
        y=benchmarks['global_wr'],
        line_dash="dash",
        line_color="gray",
        annotation_text=f"Global {benchmarks['global_wr']:.1f}%"
    )
    fig.update_layout(coloraxis_showscale=False, yaxis=dict(range=[0, bucket_stats['win_rate'].max() * 1.2]))
    st.plotly_chart(fig, use_container_width=True)

st.caption("💡 A degradação de win rate por tempo confirma que deals antigos devem ser acelerados ou descartados.")

st.divider()

# =============================================================================
# DISTRIBUIÇÃO DO PIPELINE ENGAGING POR FAIXA
# =============================================================================
st.subheader("🗂️ Pipeline Atual por Faixa de Tempo")

engaging_df = pipeline_df[pipeline_df['deal_stage'] == 'Engaging'].copy()
engaging_df = engaging_df[engaging_df['days_in_pipeline'].notna()]
engaging_df['bucket'] = engaging_df['days_in_pipeline'].apply(assign_bucket)
engaging_df['bucket'] = pd.Categorical(engaging_df['bucket'], categories=bucket_order, ordered=True)

bucket_engaging = engaging_df['bucket'].value_counts().sort_index().reset_index()
bucket_engaging.columns = ['Faixa', 'Deals']
bucket_engaging['%'] = bucket_engaging['Deals'] / bucket_engaging['Deals'].sum() * 100

# Identificar deals que já passaram da mediana Won
above_won = (engaging_df['days_in_pipeline'] >= won_median).sum()
above_won_pct = above_won / len(engaging_df) * 100

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Deals abaixo da mediana Won", f"{int((engaging_df['days_in_pipeline'] < won_median).sum())}", help=f"< {won_median:.0f} dias")
with col2:
    st.metric("Deals acima da mediana Won", f"{int(above_won)}", delta=f"{above_won_pct:.1f}%", delta_color="inverse")
with col3:
    critical = (engaging_df['days_in_pipeline'] >= engaging_median).sum()
    st.metric("Deals acima da mediana Engaging", f"{int(critical)}", delta=f"{critical/len(engaging_df)*100:.1f}%", delta_color="inverse")

fig = px.bar(
    bucket_engaging,
    x='Faixa',
    y='Deals',
    title='Distribuição do Pipeline Engaging por Faixa de Tempo',
    color='Deals',
    color_continuous_scale='RdYlGn_r',
    text=bucket_engaging['%'].apply(lambda x: f"{x:.1f}%"),
    labels={'Faixa': 'Tempo no Pipeline'}
)
fig.update_traces(textposition='outside')
fig.add_vline(x=2.5, line_dash="dash", line_color="#2ecc71", annotation_text=f"Mediana Won ({won_median:.0f}d)", annotation_position="top")
fig.update_layout(coloraxis_showscale=False)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# =============================================================================
# DISTRIBUIÇÃO DE SCORES (PIPELINE ATUAL)
# =============================================================================
st.subheader("🎯 Distribuição de Scores — Pipeline Engaging")

scores = [r['score'] for r in results]
viabilities = [r['viability'] for r in results]

avg_score = sum(scores) / len(scores)
avg_viability = sum(viabilities) / len(viabilities)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Score Médio", f"{avg_score:.1f}")
with col2:
    st.metric("Viabilidade Média", f"{avg_viability:.1f}")
with col3:
    high_score = sum(1 for s in scores if s >= 70)
    st.metric("Score ≥ 70 (Alta Prioridade)", f"{high_score}", delta=f"{high_score/len(scores)*100:.1f}%")
with col4:
    low_score = sum(1 for s in scores if s < 40)
    st.metric("Score < 40 (Baixa Prioridade)", f"{low_score}", delta=f"{low_score/len(scores)*100:.1f}%", delta_color="inverse")

col1, col2 = st.columns(2)

with col1:
    score_df = pd.DataFrame({'score': scores})
    fig = px.histogram(
        score_df,
        x='score',
        nbins=20,
        title='Distribuição de Scores',
        labels={'score': 'Score', 'count': 'Deals'},
        color_discrete_sequence=['#3498db']
    )
    fig.add_vline(x=avg_score, line_dash="dash", line_color="orange", annotation_text=f"Média {avg_score:.1f}")
    fig.add_vline(x=70, line_dash="dash", line_color="green", annotation_text="Threshold 70")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    viab_df = pd.DataFrame({'viability': viabilities})
    fig = px.histogram(
        viab_df,
        x='viability',
        nbins=20,
        title='Distribuição de Viabilidade',
        labels={'viability': 'Viabilidade', 'count': 'Deals'},
        color_discrete_sequence=['#9b59b6']
    )
    fig.add_vline(x=avg_viability, line_dash="dash", line_color="orange", annotation_text=f"Média {avg_viability:.1f}")
    fig.add_vline(x=60, line_dash="dash", line_color="green", annotation_text="Threshold 60")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# =============================================================================
# SAÚDE DO PIPELINE: PROSPECTING
# =============================================================================
st.subheader("🌱 Saúde do Pipeline: Prospecting")

seller_prosp = benchmarks.get('seller_prospecting', {})
seller_active = benchmarks.get('seller_active_deals', {})

sellers_total = len(seller_prosp)
sellers_no_prosp = sum(1 for v in seller_prosp.values() if v == 0)
sellers_overloaded = sum(1 for v in seller_active.values() if v > 100)

col1, col2, col3 = st.columns(3)

with col1:
    pct_no_prosp = sellers_no_prosp / sellers_total * 100 if sellers_total > 0 else 0
    st.metric(
        "Vendedores sem Prospecting",
        f"{sellers_no_prosp}/{sellers_total}",
        delta=f"{pct_no_prosp:.0f}% do time",
        delta_color="inverse"
    )

with col2:
    pct_overloaded = sellers_overloaded / sellers_total * 100 if sellers_total > 0 else 0
    st.metric(
        "Vendedores Sobrecarregados (>100 deals)",
        f"{sellers_overloaded}/{sellers_total}",
        delta=f"{pct_overloaded:.0f}% do time",
        delta_color="inverse"
    )

with col3:
    # Correlação: sobrecarregado E sem prospecting
    both = sum(
        1 for seller in seller_prosp
        if seller_prosp.get(seller, 0) == 0 and seller_active.get(seller, 0) > 100
    )
    both_pct = both / sellers_total * 100 if sellers_total > 0 else 0
    st.metric(
        "Sobrecarga + Sem Prospecting",
        f"{both}/{sellers_total}",
        delta=f"{both_pct:.0f}% — ciclo travado",
        delta_color="inverse"
    )

# Scatter prospecting vs carga
scatter_data = [
    {
        'Vendedor': seller,
        'Prospecting': seller_prosp.get(seller, 0),
        'Carga': seller_active.get(seller, 0)
    }
    for seller in seller_prosp
]

scatter_df = pd.DataFrame(scatter_data)

fig = px.scatter(
    scatter_df,
    x='Carga',
    y='Prospecting',
    hover_name='Vendedor',
    title='Carga vs Prospecting por Vendedor',
    labels={'Carga': 'Deals Ativos', 'Prospecting': 'Novos Deals (Prospecting)'},
    color='Prospecting',
    color_continuous_scale='RdYlGn'
)
fig.add_vline(x=100, line_dash="dash", line_color="orange", annotation_text="Threshold Alta Carga")
fig.add_hline(y=0.5, line_dash="dash", line_color="red", annotation_text="0 Prospecting")
st.plotly_chart(fig, use_container_width=True)

if pct_no_prosp > 50:
    st.warning(f"""
    ⚠️ **{pct_no_prosp:.0f}% dos vendedores estão sem prospecção ativa**

    O ciclo se retroalimenta:
    1. Alta carga → zero energia para prospectar
    2. Zero prospecting → pipeline não se renova
    3. Pipeline antigo → scores baixos, mais DISCARDs
    4. Mais DISCARDs → vendedor "protege" deals ruins para não perder deals ativos
    5. Volta ao passo 1

    **Ação recomendada:** Limpar o pipeline (DISCARD) para liberar capacidade de prospecting.
    """)
