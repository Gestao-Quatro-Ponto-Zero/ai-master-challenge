"""Streamlit dashboard for descriptive monitoring."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

try:
    from dashboard.data import (
        FILTERS,
        apply_filters,
        audience_cross,
        kpis,
        load_data,
        performance_by,
    )
    from dashboard.decision import break_even, experiment_copy
except ModuleNotFoundError:  # Streamlit Cloud executes this file from its own directory.
    from decision import break_even, experiment_copy  # type: ignore[no-redef]

    from data import (  # type: ignore[no-redef]
        FILTERS,
        apply_filters,
        audience_cross,
        kpis,
        load_data,
        performance_by,
    )

st.set_page_config(page_title="Social Media Intelligence", layout="wide")
st.title("Social Media Intelligence")
st.caption("Decisões de marketing baseadas em evidência — sem rankings ou ROI fabricados")

data = load_data()
with st.sidebar:
    st.header("Filtros")
    st.caption("Use os filtros para auditar os dados; eles não criam uma recomendação causal.")
    selected: dict[str, list[object]] = {}
    filter_labels = {
        "platform": "Plataforma",
        "content_type": "Formato",
        "content_category": "Categoria",
        "creator_size": "Tamanho do creator",
        "is_sponsored": "Patrocinado",
    }
    for column in FILTERS:
        options = sorted(data[column].dropna().unique().tolist(), key=str)
        selected[column] = st.multiselect(filter_labels[column], options)

filtered = apply_filters(data, selected)
summary = kpis(filtered)

if filtered.empty:
    st.warning("Dados insuficientes para os filtros selecionados.")
    st.stop()

cols = st.columns(4)
cols[0].metric("Posts (n)", f"{summary['posts']:,}")
cols[1].metric("Engagement/view", f"{summary['engagement_mean']:.3%}")
cols[2].metric("Views médias", f"{summary['views_mean']:,.1f}")
cols[3].metric("Posts patrocinados", f"{summary['sponsored_share']:.1%}")

st.header("Decisão executiva")
st.error(
    "Não amplie patrocínio com base neste arquivo. O ganho ajustado foi praticamente zero "
    "e o dataset não possui custos, conversões ou receita."
)

now, avoid, approve = st.columns(3)
with now:
    st.subheader("Faça agora")
    st.markdown(
        """
- instrumente custo e conversão;
- teste hipóteses com grupo de comparação;
- defina a métrica antes de ver o resultado.
"""
    )
with avoid:
    st.subheader("Não faça")
    st.markdown(
        """
- escolher plataforma por diferença mínima;
- contratar apenas por seguidores;
- chamar alcance ou engagement de ROI.
"""
    )
with approve:
    st.subheader("Decisão do Head")
    st.markdown(
        """
- aprovar objetivo e orçamento;
- aprovar ganho mínimo aceitável;
- definir quando escalar ou interromper.
"""
    )

with st.expander("Tradução dos termos usados na análise"):
    st.markdown(
        """
- **Efeito incremental:** resultado adicional provocado pela ação, além do que ocorreria sem ela.
- **IC95%:** faixa de resultados compatíveis com os dados; quanto mais ampla, maior a incerteza.
- **MDE:** menor ganho que justificaria mudar uma decisão de negócio.
- **Break-even:** resultado mínimo necessário para pagar todos os custos da ação.
- **Guardrail:** indicador que não pode piorar enquanto buscamos o resultado principal.
"""
    )

st.header("Respostas explícitas às perguntas do desafio")

with st.container(border=True):
    st.subheader("1. O que gera engajamento?")
    st.success(
        "Resposta: nenhuma plataforma, formato, categoria ou faixa de creator apresenta "
        "vantagem material validada neste dataset."
    )
    st.markdown(
        """
- Plataforma: amplitude bruta de apenas **0,0105 p.p.**.
- Tipo de conteúdo: amplitude bruta de apenas **0,0121 p.p.**.
- O modelo ajustado explica menos de **0,1%** da variação (`R²=0,000899`).
- Conclusão: rankings observados não justificam realocação de esforço.
"""
    )

with st.container(border=True):
    st.subheader("2. Patrocínio funciona?")
    st.error(
        "Resposta: não foi detectado ganho material de engagement, views, shares ou "
        "alcance relativo após os controles."
    )
    st.markdown(
        """
- Efeito ajustado no engagement: **−0,0010 p.p.**.
- IC95%: **−0,0095 a +0,0074 p.p.**; `p=0,8115`.
- Views: **+0,26**, IC95% **−1,50 a +2,02**.
- Custos e receita não existem no arquivo; portanto **ROI não pode ser calculado**.
- Política: não expandir patrocínio fora de pilotos controlados com custo e conversão.
"""
    )

with st.container(border=True):
    st.subheader("3. Qual audiência mais engaja?")
    st.warning(
        "Resposta: não há perfil de audiência validado. As diferenças são pequenas e "
        "a audiência é uma categoria agregada do post, não um atributo individual."
    )
    st.markdown(
        "A amplitude entre localizações é aproximadamente **0,0211 p.p.**. "
        "Use os controles abaixo para verificar explicitamente idade, gênero ou "
        "localização por plataforma, formato e categoria."
    )
    audience_dimension = st.selectbox(
        "Dimensão de audiência",
        [
            "audience_age_distribution",
            "audience_gender_distribution",
            "audience_location",
        ],
        key="audience_dimension",
    )
    audience_context = st.selectbox(
        "Cruzar por",
        ["platform", "content_type", "content_category"],
        key="audience_context",
    )
    audience_table = audience_cross(filtered, audience_dimension, audience_context)
    audience_fig = px.scatter(
        audience_table,
        x="engagement_mean",
        y=audience_dimension,
        color=audience_context,
        size="n",
        hover_data=["n", "engagement_median", "views_mean"],
        labels={"engagement_mean": "Interações por view", "n": "Posts"},
    )
    audience_fig.update_layout(xaxis_range=[0.19, 0.21])
    st.plotly_chart(audience_fig, use_container_width=True)
    st.dataframe(audience_table, use_container_width=True, hide_index=True)

with st.container(border=True):
    st.subheader("4. O que não funciona?")
    st.markdown(
        """
- patrocínio indiscriminado;
- escolher plataforma ou formato por médias mínimas;
- contratar creator apenas por seguidores/engagement histórico;
- definir frequência com este arquivo;
- usar top performers como prova causal;
- chamar engagement ou alcance de ROI.
"""
    )

with st.container(border=True):
    st.subheader("5. Onde concentrar esforço?")
    st.info(
        "Resposta: concentrar em instrumentação, experimentação e qualidade de mensuração — "
        "não em uma plataforma ou formato supostamente vencedor."
    )
    st.markdown(
        "Coletar custo, fee, mídia, produção, reach único, cliques, conversões, "
        "receita/margem e grupo de comparação."
    )

st.divider()
st.header("Decidir e testar")
st.write(
    "Preencha premissas reais para transformar uma ideia em experimento. "
    "Os valores abaixo são exemplos editáveis e não vêm do dataset."
)

left, right = st.columns(2)
with left:
    objective = st.selectbox(
        "Qual é o objetivo principal?",
        ["Alcance", "Compartilhamento", "Conversa", "Conversão"],
        key="experiment_objective",
    )
    hypothesis = st.text_input(
        "Hipótese a testar",
        "Conteúdo patrocinado gera resultado incremental suficiente para pagar o investimento.",
    )
    owner = st.text_input("Responsável", "Social Media Lead")
    duration = st.number_input("Duração planejada (dias)", 7, 90, 30)

with right:
    campaign_cost = st.number_input("Custo total da campanha (R$)", 0.0, value=10_000.0, step=500.0)
    margin = st.number_input("Margem por conversão (R$)", 0.01, value=250.0, step=10.0)
    eligible = st.number_input("Pessoas elegíveis no teste", 1, value=100_000, step=1_000)

threshold = break_even(campaign_cost, margin, int(eligible))
copy = experiment_copy(objective)
decision_cols = st.columns(3)
decision_cols[0].metric(
    "Conversões incrementais mínimas", f"{threshold['incremental_conversions']:,}"
)
decision_cols[1].metric("Ganho mínimo na taxa", f"{threshold['incremental_rate']:.3%}")
decision_cols[2].metric("Margem mínima", f"R$ {threshold['required_margin']:,.2f}")

with st.container(border=True):
    st.subheader("Briefing do experimento")
    st.markdown(
        f"**Hipótese:** {hypothesis}\n\n"
        f"**Owner:** {owner}\n\n"
        f"**Prazo:** {int(duration)} dias\n\n"
        f"**Métrica principal:** {copy['metric']}\n\n"
        f"**Guardrail:** {copy['guardrail']}\n\n"
        "**Regra de escala:** escalar somente se o ganho incremental comprovado superar "
        "o break-even acima e o guardrail permanecer saudável.\n\n"
        "**Regra de parada:** interromper por dano no guardrail, falha de instrumentação "
        "ou inviabilidade do ganho mínimo antes de aumentar o orçamento."
    )
st.caption(
    "A calculadora define o mínimo econômico. Ela não prova causalidade nem substitui "
    "randomização, tamanho amostral e aprovação financeira."
)
with st.container(border=True):
    st.subheader("6. Qual frequência, creator e threshold usar?")
    st.warning("Resposta: o dataset não permite recomendar frequência nem threshold de seguidores.")
    st.markdown(
        "Testar cadências controladas. Escalar patrocínio somente quando o limite inferior "
        "do efeito incremental superar o break-even aprovado — não por follower count."
    )

with st.container(border=True):
    st.subheader("7. O que fazer esta semana?")
    st.markdown(
        """
1. Suspender expansão de campanhas sem mensuração.
2. Adicionar custos, conversões e receita ao contrato.
3. Criar três hipóteses com métrica, MDE e stop condition.
4. Usar este dashboard com `n` e limitações visíveis.
5. Revisar 90 dias de patrocínios quando custos reais estiverem disponíveis.
"""
    )

with st.container(border=True):
    st.subheader("8. Machine Learning vale a pena?")
    st.info(
        "Resposta: não agora. O gate foi marcado SKIPPED porque o dataset não contém "
        "sinal preditivo útil; modelar seria aprender ruído sintético."
    )

st.divider()
st.header("Exploração dos dados")

dimension = st.selectbox(
    "Dimensão",
    [
        "platform",
        "content_type",
        "content_category",
        "creator_size",
        "audience_age_distribution",
        "audience_location",
    ],
)
grouped = performance_by(filtered, dimension)

st.subheader("Performance por dimensão")
fig = px.scatter(
    grouped,
    x="engagement_mean",
    y=dimension,
    size="n",
    hover_data=["n", "views_mean"],
    labels={"engagement_mean": "Interações por view", "n": "Posts"},
)
fig.update_layout(xaxis_range=[0.19, 0.21])
st.plotly_chart(fig, use_container_width=True)
st.dataframe(grouped, use_container_width=True, hide_index=True)

st.subheader("Patrocinado versus orgânico — descritivo")
sponsor = (
    filtered.groupby(["platform", "is_sponsored"], observed=True)
    .agg(
        n=("id", "size"),
        engagement_mean=("engagement_rate_views", "mean"),
        views_mean=("views", "mean"),
    )
    .reset_index()
)
st.dataframe(sponsor, use_container_width=True, hide_index=True)

with st.expander("Como interpretar"):
    st.markdown(
        """
- As diferenças observadas não são causais.
- O dataset não contém custos ou receita; este painel não calcula ROI.
- Rankings pequenos não constituem recomendação e devem considerar `n` e incerteza.
- O relatório estatístico não encontrou ganho material de patrocínio.
- Fonte: dataset Kaggle declarado no contrato; período 29/05/2023–28/05/2025.
"""
    )

st.divider()
st.markdown("**Felipe de Oliveira Freire**")
st.caption("Cientista/Analista de Dados")
