"""Streamlit dashboard for descriptive monitoring."""

from __future__ import annotations

from pathlib import Path

import plotly.express as px
import streamlit as st

px.defaults.color_discrete_sequence = [
    "#B9915B",
    "#1E526F",
    "#4F7C68",
    "#8E5A66",
    "#537A9E",
]

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
    from dashboard.i18n import LANGUAGES, option_label, text
except ModuleNotFoundError:  # Streamlit Cloud executes this file from its own directory.
    from decision import break_even, experiment_copy  # type: ignore[no-redef]
    from i18n import LANGUAGES, option_label, text  # type: ignore[no-redef]

    from data import (  # type: ignore[no-redef]
        FILTERS,
        apply_filters,
        audience_cross,
        kpis,
        load_data,
        performance_by,
    )

ASSETS = Path(__file__).resolve().parent / "assets"
LOGO = ASSETS / "g4-logo.svg"

st.set_page_config(page_title="G4 Social Intelligence", page_icon=str(LOGO), layout="wide")

with st.sidebar:
    st.image(str(LOGO), width=150)
    selected_language = st.selectbox("Idioma · Language", list(LANGUAGES), key="language")
    language = LANGUAGES[selected_language]
    tx = text(language)
    theme = st.radio(
        str(tx["theme"]),
        ["light", "dark"],
        format_func=lambda value: str(tx[value]),
        horizontal=True,
        key="theme_mode",
    )


def t(key: str) -> str:
    """Return a scalar translated UI label."""
    return str(tx[key])


def table_columns(extra: dict[str, str] | None = None) -> dict[str, str]:
    """Return localized, readable labels for embedded analytical tables."""
    labels = {
        "n": t("sample_size"),
        "engagement_mean": t("mean_engagement"),
        "engagement_median": t("median_engagement"),
        "views_mean": t("mean_views"),
        "is_sponsored": t("sponsored"),
        "platform": t("platform"),
    }
    if extra:
        labels.update(extra)
    return labels


palette = {
    "light": {
        "bg": "#F5F4F3",
        "surface": "#FFFFFF",
        "ink": "#152B3A",
        "muted": "#526876",
        "border": "#C7D2D9",
        "header": "rgba(245,244,243,.92)",
        "container": "rgba(255,255,255,.78)",
        "plot": "rgba(255,255,255,.72)",
    },
    "dark": {
        "bg": "#071721",
        "surface": "#0E2737",
        "ink": "#F5F4F3",
        "muted": "#B9C7CF",
        "border": "#365367",
        "header": "rgba(7,23,33,.92)",
        "container": "rgba(14,39,55,.90)",
        "plot": "rgba(14,39,55,.72)",
    },
}[theme]

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
    --g4-navy: #001F35;
    --g4-gold: #B9915B;
    --g4-bg: #F5F4F3;
    --g4-surface: #FFFFFF;
    --g4-white: #FFFFFF;
    --g4-ink: #152B3A;
    --g4-muted: #526876;
    --g4-border: #C7D2D9;
}

html, body, [data-testid="stAppViewContainer"] { font-family: "Manrope", sans-serif; }
[data-testid="stAppViewContainer"] { background: var(--g4-bg); color: var(--g4-ink); }
[data-testid="stHeader"] { background: rgba(245,244,243,.92); }
[data-testid="stSidebar"] { background: var(--g4-navy); }
[data-testid="stSidebar"] p, [data-testid="stSidebar"] label,
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: var(--g4-white) !important; }
[data-testid="stSidebar"] [data-baseweb="tag"] { background: var(--g4-gold); }
[data-testid="stSidebar"] input { color: var(--g4-white); }
.material-symbols-rounded, [data-testid="stIconMaterial"] {
    font-family: "Material Symbols Rounded" !important;
}

.block-container { max-width: 1240px; padding-top: 2.5rem; padding-bottom: 4rem; }
h1, h2, h3 { color: var(--g4-navy); letter-spacing: -0.025em; }
h1 { font-weight: 800; }
h2 { font-weight: 750; margin-top: 1.4rem; }
h3 { font-weight: 700; }

.g4-hero {
    background: var(--g4-navy);
    border-radius: 18px;
    padding: 2.1rem 2.3rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 14px 34px rgba(0, 31, 53, 0.15);
}
.g4-eyebrow {
    color: var(--g4-gold);
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 0.14em;
    text-transform: uppercase;
}
.g4-hero h1 { color: var(--g4-white); margin: 0.4rem 0 0.45rem; }
.g4-hero p { color: #DCE5EA; max-width: 760px; margin: 0; font-size: 1.02rem; }

[data-testid="stMetric"] {
    background: var(--g4-white);
    border: 1px solid #D8E0E5;
    border-top: 4px solid var(--g4-gold);
    border-radius: 12px;
    padding: 1rem 1.1rem;
}
[data-testid="stMetricLabel"] { color: #526876; }
[data-testid="stMetricValue"] { color: var(--g4-navy); font-weight: 800; }
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] label,
[data-testid="stSelectbox"] label,
[data-testid="stNumberInput"] label,
[data-testid="stTextInput"] label { color: var(--g4-navy) !important; font-weight: 650; }
[data-testid="stAppViewContainer"] [data-baseweb="select"] > div,
[data-testid="stAppViewContainer"] [data-baseweb="input"] > div,
[data-testid="stAppViewContainer"] input {
    background: var(--g4-white) !important;
    color: var(--g4-navy) !important;
    border-color: #C7D2D9 !important;
}
[data-testid="stAppViewContainer"] [data-baseweb="select"] span,
[data-testid="stAppViewContainer"] [data-baseweb="select"] svg {
    color: var(--g4-navy) !important;
    fill: var(--g4-navy) !important;
}
[data-testid="stAlert"] p,
[data-testid="stAlert"] div { color: var(--g4-ink) !important; }
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary span,
[data-testid="stExpander"] summary p { color: var(--g4-navy) !important; }
[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255, 255, 255, 0.78);
    border-color: #D8E0E5;
    border-radius: 14px;
}
[data-testid="stAlert"] { border-radius: 12px; }
hr { border-color: rgba(0, 31, 53, 0.14); }
.g4-footer { color: #526876; text-align: center; padding-top: 1rem; }
.g4-footer strong { color: var(--g4-navy); }
.g4-footer a { color: var(--g4-gold); font-weight: 700; text-decoration: none; }
.g4-footer a:hover { text-decoration: underline; }
</style>
""",
    unsafe_allow_html=True,
)
st.markdown(
    f"""
<style>
:root {{
    --g4-bg: {palette["bg"]}; --g4-surface: {palette["surface"]};
    --g4-ink: {palette["ink"]}; --g4-muted: {palette["muted"]};
    --g4-border: {palette["border"]};
}}
[data-testid="stHeader"] {{ background: {palette["header"]}; }}
h1, h2, h3 {{ color: var(--g4-ink); }}
[data-testid="stMetric"] {{ background: var(--g4-surface); border-color: var(--g4-border); }}
[data-testid="stMetricLabel"] {{ color: var(--g4-muted); }}
[data-testid="stMetricValue"] {{ color: var(--g4-ink); }}
[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label,
[data-testid="stSelectbox"] label, [data-testid="stNumberInput"] label,
[data-testid="stTextInput"] label {{ color: var(--g4-ink) !important; }}
[data-testid="stAppViewContainer"] [data-baseweb="select"] > div,
[data-testid="stAppViewContainer"] [data-baseweb="input"] > div,
[data-testid="stAppViewContainer"] input {{
    background: var(--g4-surface) !important; color: var(--g4-ink) !important;
    border-color: var(--g4-border) !important;
}}
[data-testid="stAppViewContainer"] [data-baseweb="select"] span,
[data-testid="stAppViewContainer"] [data-baseweb="select"] svg {{
    color: var(--g4-ink) !important; fill: var(--g4-ink) !important;
}}
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary span,
[data-testid="stExpander"] summary p {{ color: var(--g4-ink) !important; }}
[data-testid="stExpander"] details,
[data-testid="stExpander"] summary {{
    background: var(--g4-surface) !important;
    border-color: var(--g4-border) !important;
}}
[data-testid="stExpander"] summary:hover {{
    background: {palette["container"]} !important;
}}
[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {palette["container"]}; border-color: var(--g4-border);
}}
[data-testid="stAlert"] {{ background: var(--g4-surface); border-color: var(--g4-border); }}
hr {{ border-color: var(--g4-border); }}
.g4-footer {{ color: var(--g4-muted); }}
.g4-footer strong {{ color: var(--g4-ink); }}

/* Sidebar must keep its own contrast independently of the selected main theme. */
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] label,
[data-testid="stSidebar"] [data-testid="stSelectbox"] label,
[data-testid="stSidebar"] [data-testid="stMultiSelect"] label {{
    color: #FFFFFF !important;
}}
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-baseweb="input"] > div,
[data-testid="stSidebar"] input {{
    background: #FFFFFF !important;
    color: #001F35 !important;
    border-color: #C7D2D9 !important;
}}
[data-testid="stSidebar"] [data-baseweb="select"] span,
[data-testid="stSidebar"] [data-baseweb="select"] svg {{
    color: #001F35 !important;
    fill: #001F35 !important;
}}
[data-testid="stSidebar"] [role="radiogroup"] label:nth-child(1) p::before,
[data-testid="stSidebar"] [role="radiogroup"] label:nth-child(2) p::before {{
    font-family: "Material Symbols Rounded" !important;
    font-size: 1.15rem;
    font-weight: normal;
    vertical-align: -0.18rem;
    margin-right: 0.35rem;
}}
[data-testid="stSidebar"] [role="radiogroup"] label:nth-child(1) p::before {{
    content: "light_mode";
}}
[data-testid="stSidebar"] [role="radiogroup"] label:nth-child(2) p::before {{
    content: "dark_mode";
}}
</style>
<section class="g4-hero">
  <div class="g4-eyebrow">{t("eyebrow")}</div>
  <h1>G4 Social Intelligence</h1>
  <p>{t("subtitle")}</p>
</section>
""",
    unsafe_allow_html=True,
)

data = load_data()
with st.sidebar:
    st.caption(t("independent"))
    st.divider()
    st.header(t("filters"))
    st.caption(t("filter_help"))
    selected: dict[str, list[object]] = {}
    filter_labels = {
        "platform": t("platform"),
        "content_type": t("format"),
        "content_category": t("category"),
        "creator_size": t("creator"),
        "is_sponsored": t("sponsored"),
    }
    for column in FILTERS:
        options = sorted(data[column].dropna().unique().tolist(), key=str)
        selected[column] = st.multiselect(
            filter_labels[column],
            options,
            format_func=lambda value: option_label(language, value),
        )

filtered = apply_filters(data, selected)
summary = kpis(filtered)

if filtered.empty:
    st.warning(t("insufficient"))
    st.stop()

cols = st.columns(4)
cols[0].metric(t("posts"), f"{summary['posts']:,}")
cols[1].metric(t("engagement"), f"{summary['engagement_mean']:.3%}")
cols[2].metric(t("views"), f"{summary['views_mean']:,.1f}")
cols[3].metric(t("sponsored_posts"), f"{summary['sponsored_share']:.1%}")

st.header(t("executive"))
st.error(t("main_decision"))

now, avoid, approve = st.columns(3)
with now:
    st.subheader(t("do"))
    st.markdown(t("do_items"))
with avoid:
    st.subheader(t("avoid"))
    st.markdown(t("avoid_items"))
with approve:
    st.subheader(t("head"))
    st.markdown(t("head_items"))

with st.expander(t("glossary")):
    st.markdown(t("glossary_text"))

st.header(t("answers"))
st.info(t("answer_summary"))

with st.container(border=True):
    st.subheader(t("q1_title"))
    st.success(t("q1_answer"))
    st.markdown(t("q1_body"))

with st.container(border=True):
    st.subheader(t("q2_title"))
    st.error(t("q2_answer"))
    st.markdown(t("q2_body"))

with st.container(border=True):
    st.subheader(t("q3_title"))
    st.warning(t("q3_answer"))
    st.markdown(t("q3_body"))
    audience_dimension = st.selectbox(
        t("audience_dimension"),
        [
            "audience_age_distribution",
            "audience_gender_distribution",
            "audience_location",
        ],
        format_func=lambda value: option_label(language, value),
        key="audience_dimension",
    )
    audience_context = st.selectbox(
        t("cross_by"),
        ["platform", "content_type", "content_category"],
        format_func=lambda value: option_label(language, value),
        key="audience_context",
    )
    audience_table = audience_cross(filtered, audience_dimension, audience_context)
    audience_display = audience_table.copy()
    audience_display[audience_dimension] = audience_display[audience_dimension].map(
        lambda value: option_label(language, value)
    )
    audience_display[audience_context] = audience_display[audience_context].map(
        lambda value: option_label(language, value)
    )
    audience_fig = px.scatter(
        audience_display,
        x="engagement_mean",
        y=audience_dimension,
        color=audience_context,
        size="n",
        hover_data=["n", "engagement_median", "views_mean"],
        labels={"engagement_mean": t("interactions_view"), "n": t("posts")},
    )
    audience_fig.update_layout(
        xaxis_range=[0.19, 0.21],
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=palette["plot"],
        font={"family": "Manrope", "color": palette["ink"]},
    )
    st.plotly_chart(audience_fig, use_container_width=True, theme=None)
    st.dataframe(
        audience_display,
        use_container_width=True,
        hide_index=True,
        column_config=table_columns(
            {
                audience_dimension: option_label(language, audience_dimension),
                audience_context: option_label(language, audience_context),
            }
        ),
    )

with st.container(border=True):
    st.subheader(t("q4_title"))
    st.markdown(t("q4_body"))

with st.container(border=True):
    st.subheader(t("q5_title"))
    st.info(t("q5_answer"))
    st.markdown(t("q5_body"))

st.divider()
st.header(t("decide"))
st.write(t("decide_intro"))

left, right = st.columns(2)
with left:
    objective_options = list(tx["objectives"])
    objective = st.selectbox(t("objective"), objective_options, key="experiment_objective")
    hypothesis = st.text_input(
        t("hypothesis"),
        t("hypothesis_default"),
    )
    owner = st.text_input(t("owner"), "Social Media Lead")
    duration = st.number_input(t("duration"), 7, 90, 30)

with right:
    campaign_cost = st.number_input(t("cost"), 0.0, value=10_000.0, step=500.0)
    margin = st.number_input(t("margin"), 0.01, value=250.0, step=10.0)
    eligible = st.number_input(t("eligible"), 1, value=100_000, step=1_000)

threshold = break_even(campaign_cost, margin, int(eligible))
canonical_objectives = ["Alcance", "Compartilhamento", "Conversa", "Conversão"]
canonical_objective = canonical_objectives[objective_options.index(objective)]
copy = experiment_copy(canonical_objective, language)
decision_cols = st.columns(3)
decision_cols[0].metric(t("min_conversions"), f"{threshold['incremental_conversions']:,}")
decision_cols[1].metric(t("min_rate"), f"{threshold['incremental_rate']:.3%}")
decision_cols[2].metric(t("min_margin"), f"R$ {threshold['required_margin']:,.2f}")

with st.container(border=True):
    st.subheader(t("brief"))
    st.markdown(
        f"**{t('hypothesis')}:** {hypothesis}\n\n"
        f"**{t('owner')}:** {owner}\n\n"
        f"**{t('duration')}:** {int(duration)}\n\n"
        f"**{t('metric')}:** {copy['metric']}\n\n"
        f"**{t('guardrail')}:** {copy['guardrail']}\n\n"
        f"**{t('scale')}:** {t('scale_text')}\n\n"
        f"**{t('stop')}:** {t('stop_text')}"
    )
st.caption(t("calculator_note"))
with st.container(border=True):
    st.subheader(t("q6_title"))
    st.warning(t("q6_answer"))
    st.markdown(t("q6_body"))

with st.container(border=True):
    st.subheader(t("q7_title"))
    st.markdown(t("q7_body"))

with st.container(border=True):
    st.subheader(t("q8_title"))
    st.info(t("q8_answer"))

st.divider()
st.header(t("explore"))

dimension = st.selectbox(
    t("dimension"),
    [
        "platform",
        "content_type",
        "content_category",
        "creator_size",
        "audience_age_distribution",
        "audience_location",
    ],
    format_func=lambda value: option_label(language, value),
)
grouped = performance_by(filtered, dimension)
grouped_display = grouped.copy()
grouped_display[dimension] = grouped_display[dimension].map(
    lambda value: option_label(language, value)
)

st.subheader(t("performance_dimension"))
fig = px.scatter(
    grouped_display,
    x="engagement_mean",
    y=dimension,
    size="n",
    hover_data=["n", "views_mean"],
    labels={"engagement_mean": t("interactions_view"), "n": t("posts")},
)
fig.update_layout(
    xaxis_range=[0.19, 0.21],
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor=palette["plot"],
    font={"family": "Manrope", "color": palette["ink"]},
)
st.plotly_chart(fig, use_container_width=True, theme=None)
st.dataframe(
    grouped_display,
    use_container_width=True,
    hide_index=True,
    column_config=table_columns({dimension: option_label(language, dimension)}),
)

st.subheader(t("sponsor_comparison"))
sponsor = (
    filtered.groupby(["platform", "is_sponsored"], observed=True)
    .agg(
        n=("id", "size"),
        engagement_mean=("engagement_rate_views", "mean"),
        views_mean=("views", "mean"),
    )
    .reset_index()
)
sponsor_display = sponsor.copy()
sponsor_display["is_sponsored"] = sponsor_display["is_sponsored"].map(
    lambda value: option_label(language, value)
)
st.dataframe(
    sponsor_display,
    use_container_width=True,
    hide_index=True,
    column_config=table_columns(),
)

with st.expander(t("interpret")):
    st.markdown(t("interpret_body"))

st.divider()
st.markdown(
    f"""
<footer class="g4-footer">
  <strong>Felipe de Oliveira Freire</strong><br>
  {t("footer_role")}<br>
  <a href="https://www.linkedin.com/in/felipe-freire-659615284/" target="_blank">
    LinkedIn · felipe-freire-659615284
  </a>
</footer>
""",
    unsafe_allow_html=True,
)
