from __future__ import annotations
from pathlib import Path

import pandas as pd
import streamlit as st

from src.data_loader import DatasetNotFoundError, get_data_dir
from src.exports import build_excel_export, build_pdf_export
from src.scoring import load_data, score_open_pipeline, scoring_summary


# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
FAVICON_PATH = BASE_DIR / "src" / "favicon.png"


# -----------------------------------------------------------------------------
# Page configuration
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="G4 | Lead Scorer",
    page_icon=str(FAVICON_PATH),
    layout="wide",
    initial_sidebar_state="expanded",
)


# -----------------------------------------------------------------------------
# Styles
# -----------------------------------------------------------------------------

st.markdown(
    """
    <style>
    :root {
        /* Main backgrounds */
        --g4-background: #F4F7F9;
        --g4-sidebar: #E8EEF2;

        /* Elevated surfaces */
        --g4-surface: #DCE5EA;
        --g4-surface-2: #CBD8DF;

        /* KPI cards */
        --g4-card-dark: #001F35;
        --g4-card-border: #16445E;

        /* Borders */
        --g4-border: #B8C8D1;

        /* Typography */
        --g4-text: #001F35;
        --g4-text-inverse: #FFFFFF;
        --g4-muted: #607786;
        --g4-muted-inverse: #A9BCC8;

        /* Operational highlight */
        --g4-accent: #C7FF00;

        /* Brand / primary action */
        --g4-gold: #B9915B;
    }

    .stApp {
        background: var(--g4-background);
        color: var(--g4-text);
    }

    /* Main application content spacing */
    [data-testid="stMainBlockContainer"] {
        padding-top: 3rem;
        padding-bottom: 3rem;
    }

    [data-testid="stSidebar"] {
        background: var(--g4-sidebar);
        border-right: 1px solid var(--g4-border);
    }

    h1, h2, h3, h4, p, span, label {
        color: var(--g4-text);
    }

    .g4-eyebrow {
        color: var(--g4-gold);
        font-size: .82rem;
        font-weight: 800;
        letter-spacing: .12em;
    }

    .g4-title {
        font-size: 2.2rem;
        line-height: 1.05;
        font-weight: 900;
        margin: .1rem 0 .35rem 0;
    }

    .g4-subtitle {
        color: var(--g4-muted);
        margin-bottom: 1.2rem;
    }

    .metric-card {
        background: var(--g4-card-dark);
        border: 1px solid var(--g4-card-border);
        border-radius: 12px;
        padding: 16px;
        min-height: 104px;
    }

    .metric-label {
        color: var(--g4-muted-inverse);
        font-size: .78rem;
        text-transform: uppercase;
        letter-spacing: .08em;
    }

    .metric-value {
        color: var(--g4-text-inverse);
        font-size: 2rem;
        font-weight: 900;
        margin-top: .25rem;
    }

    .metric-accent {
        color: var(--g4-accent);
    }

    .deal-card {
        background: var(--g4-surface);
        border: 1px solid var(--g4-border);
        border-left: 4px solid var(--g4-gold);
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 10px;
    }

    .deal-meta {
        color: var(--g4-muted);
        font-size: .85rem;
    }

    .score {
        color: #3F5F00;
        font-size: 1.45rem;
        font-weight: 900;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid var(--g4-border);
        border-radius: 10px;
        overflow: hidden;
    }

    /* Standard buttons */
    .stButton > button {
        background: var(--g4-accent);
        color: #0A0A0A;
        border: 1px solid var(--g4-accent);
        font-weight: 800;
        border-radius: 8px;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        background: #D8FF4A;
        color: #0A0A0A;
        border-color: #D8FF4A;
    }

    /* Excel and PDF export buttons */
    div[data-testid="stDownloadButton"] button {
        background: var(--g4-gold);
        color: #FFFFFF;
        border: 1px solid var(--g4-gold);
        border-radius: 8px;
        transition: all 0.2s ease;
    }

    /* Text and icon */
    div[data-testid="stDownloadButton"] button * {
        color: #FFFFFF !important;
        font-weight: 700 !important;
        transition: color 0.2s ease;
    }

    /* Hover, focus and active */
    div[data-testid="stDownloadButton"] button:hover,
    div[data-testid="stDownloadButton"] button:focus,
    div[data-testid="stDownloadButton"] button:active {
        background: transparent;
        color: var(--g4-gold);
        border-color: var(--g4-gold);
    }

    /* Text and icon on hover, focus and active */
    div[data-testid="stDownloadButton"] button:hover *,
    div[data-testid="stDownloadButton"] button:focus *,
    div[data-testid="stDownloadButton"] button:active * {
        color: var(--g4-gold) !important;
    }

    /* Hide only the Streamlit Deploy button */
    [data-testid="stAppDeployButton"] {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Data loading
# -----------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def get_scored_data(data_dir: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    data = load_data(data_dir)
    scored = score_open_pipeline(data["enriched"])
    return scored, data["teams"]


try:
    DATA_DIR = get_data_dir()
    scored, teams = get_scored_data(str(DATA_DIR))

except DatasetNotFoundError as exc:
    st.markdown(
        '<div class="g4-eyebrow">G4 · REVENUE OPERATIONS</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="g4-title">LEAD SCORER</div>',
        unsafe_allow_html=True,
    )

    st.error("Dataset not found")

    st.code(
        str(exc),
        language=None,
    )

    st.info(
        "See solution/README.md for local dataset setup instructions."
    )

    st.stop()


# -----------------------------------------------------------------------------
# Filter state
# -----------------------------------------------------------------------------

FILTER_DEFAULTS = {
    "filter_manager": "All",
    "filter_sales_agent": "All",
    "filter_region": "All",
    "filter_stage": "All",
    "filter_product": "All",
    "filter_action": "All",
}


def clear_filters() -> None:
    """
    Restore all sidebar filters to their default values.
    """
    for key, default_value in FILTER_DEFAULTS.items():
        st.session_state[key] = default_value


# -----------------------------------------------------------------------------
# Header
# -----------------------------------------------------------------------------

st.markdown(
    '<div class="g4-eyebrow">G4 · REVENUE OPERATIONS</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="g4-title">LEAD SCORER</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="g4-subtitle">'
    'Turn your open pipeline into an explainable action plan.'
    '</div>',
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Sidebar filters
# -----------------------------------------------------------------------------

with st.sidebar:
    st.header("Filters")

    st.button(
        ":material/filter_alt_off: Clear all filters",
        key="clear_filters_button",
        help="Reset all filters to their default values",
        on_click=clear_filters,
        width="stretch",
    )

    managers = [
        "All",
        *sorted(
            scored["manager"]
            .dropna()
            .unique()
            .tolist()
        ),
    ]

    selected_manager = st.selectbox(
        "Manager",
        managers,
        key="filter_manager",
    )

    seller_source = (
        scored
        if selected_manager == "All"
        else scored[
            scored["manager"] == selected_manager
        ]
    )

    sellers = [
        "All",
        *sorted(
            seller_source["sales_agent"]
            .dropna()
            .unique()
            .tolist()
        ),
    ]

    # If the selected seller does not belong to the selected manager,
    # restore the seller filter before rendering the widget.
    current_seller = st.session_state.get(
        "filter_sales_agent",
        "All",
    )

    if current_seller not in sellers:
        st.session_state["filter_sales_agent"] = "All"

    selected_seller = st.selectbox(
        "Sales Agent",
        sellers,
        key="filter_sales_agent",
    )

    regions = [
        "All",
        *sorted(
            scored["regional_office"]
            .dropna()
            .unique()
            .tolist()
        ),
    ]

    selected_region = st.selectbox(
        "Regional Office",
        regions,
        key="filter_region",
    )

    selected_stage = st.selectbox(
        "Stage",
        [
            "All",
            "Engaging",
            "Prospecting",
        ],
        key="filter_stage",
    )

    products = [
        "All",
        *sorted(
            scored["product"]
            .dropna()
            .unique()
            .tolist()
        ),
    ]

    selected_product = st.selectbox(
        "Product",
        products,
        key="filter_product",
    )

    actions = [
        "All",
        *sorted(
            scored["action_category"]
            .dropna()
            .unique()
            .tolist()
        ),
    ]

    selected_action = st.selectbox(
        "Action Category",
        actions,
        key="filter_action",
    )


# -----------------------------------------------------------------------------
# Apply filters
# -----------------------------------------------------------------------------

filtered = scored.copy()

for column, value in [
    ("manager", selected_manager),
    ("sales_agent", selected_seller),
    ("regional_office", selected_region),
    ("deal_stage", selected_stage),
    ("product", selected_product),
    ("action_category", selected_action),
]:
    if value != "All":
        filtered = filtered[
            filtered[column] == value
        ]


# -----------------------------------------------------------------------------
# Summary metrics
# -----------------------------------------------------------------------------

summary = scoring_summary(filtered)

columns = st.columns(4)

metric_specs = [
    (
        "OPEN DEALS",
        summary["open_deals"],
        False,
    ),
    (
        "FOCUS NOW",
        summary["focus_now"],
        True,
    ),
    (
        "NEED DECISION",
        summary["need_decision"],
        False,
    ),
    (
        "LIMITED EVIDENCE",
        summary["limited_evidence"],
        False,
    ),
]

for column, (
    label,
    value,
    accent,
) in zip(
    columns,
    metric_specs,
):
    value_class = (
        "metric-value metric-accent"
        if accent
        else "metric-value"
    )

    column.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-label">{label}</div>'
        f'<div class="{value_class}">{value:,}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# Focus section
# -----------------------------------------------------------------------------

st.markdown("### Your focus")

priority_sections = [
    "Focus Now",
    "Review Now",
    "Follow Up",
    "Re-engage",
    "Requalify",
    "Qualify or Drop",
]

shown = 0

for action in priority_sections:
    action_deals = filtered[
        filtered["action_category"] == action
    ]

    subset = action_deals.head(5)

    if subset.empty:
        continue

    shown += 1

    with st.expander(
        f"{action} · {len(action_deals)} deals",
        expanded=(action == "Focus Now"),
    ):
        for _, row in subset.iterrows():
            account = (
                row["account"]
                if pd.notna(row["account"])
                else "Account unavailable"
            )

            st.markdown(
                f'<div class="deal-card">'
                f'<b>{row["opportunity_id"]} · {account}</b>'
                f'<div class="deal-meta">'
                f'{row["sales_agent"]} · '
                f'{row["product"]} · '
                f'{row["deal_stage"]}'
                f'</div>'
                f'<div class="score">'
                f'Priority {row["priority_score"]:.1f}'
                f'</div>'
                f'<div class="deal-meta">'
                f'Fit {row["historical_fit"]:.1f} · '
                f'{row["fit_category"]} · '
                f'Evidence {row["evidence_confidence"]}'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


if shown == 0:
    st.info(
        "No immediate-action deals match the current filters."
    )


# -----------------------------------------------------------------------------
# Prioritized pipeline
# -----------------------------------------------------------------------------

st.markdown("### Prioritized pipeline")

visible_columns = [
    "action_category",
    "opportunity_id",
    "account",
    "sales_agent",
    "manager",
    "regional_office",
    "product",
    "deal_stage",
    "priority_score",
    "historical_fit",
    "attention_state",
    "evidence_confidence",
]

table = filtered[
    visible_columns
].rename(
    columns={
        "action_category": "Action",
        "opportunity_id": "Opportunity",
        "account": "Account",
        "sales_agent": "Sales Agent",
        "manager": "Manager",
        "regional_office": "Region",
        "product": "Product",
        "deal_stage": "Stage",
        "priority_score": "Priority",
        "historical_fit": "Historical Fit",
        "attention_state": "Attention",
        "evidence_confidence": "Evidence",
    }
)

st.dataframe(
    table,
    width="stretch",
    hide_index=True,
    height=420,
)


# -----------------------------------------------------------------------------
# Deal detail
# -----------------------------------------------------------------------------

st.markdown("### Deal detail")

if not filtered.empty:
    selected_id = st.selectbox(
        "Select an opportunity",
        filtered[
            "opportunity_id"
        ].tolist(),
        label_visibility="collapsed",
    )

    row = filtered[
        filtered["opportunity_id"] == selected_id
    ].iloc[0]

    left, right = st.columns(
        [
            1,
            1.35,
        ]
    )

    with left:
        st.markdown(
            f'#### {row["opportunity_id"]}'
        )

        st.markdown(
            f'**{row["action_category"]}**'
        )

        st.metric(
            "Priority Score",
            f'{row["priority_score"]:.1f} / 100',
        )

        st.metric(
            "Historical Fit",
            f'{row["historical_fit"]:.1f} / 100',
        )

        st.write(
            f'**Fit:** {row["fit_category"]}'
        )

        st.write(
            f'**Attention:** {row["attention_state"]}'
        )

        st.write(
            f'**Evidence:** {row["evidence_confidence"]}'
        )

    with right:
        st.markdown(
            "#### Why this deal is here"
        )

        for index in range(
            1,
            5,
        ):
            text = row.get(
                f"explanation_{index}",
                "",
            )

            if (
                isinstance(text, str)
                and text.strip()
            ):
                st.write(
                    f"• {text}"
                )

        st.markdown(
            "#### Recommended action"
        )

        st.success(
            row["recommended_action"]
        )

        st.caption(
            "Priority Score is an operational ranking, "
            "not a probability of closing."
        )


# -----------------------------------------------------------------------------
# Export current view
# -----------------------------------------------------------------------------

st.markdown("### Export current view")

filters_payload = {
    "Manager": selected_manager,
    "Sales Agent": selected_seller,
    "Region": selected_region,
    "Stage": selected_stage,
    "Product": selected_product,
    "Action": selected_action,
}

export_columns = st.columns(2)


with export_columns[0]:
    st.download_button(
        label=":material/table_view: Export Excel",
        data=build_excel_export(filtered),
        file_name="g4-lead-scorer.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        width="stretch",
    )


with export_columns[1]:
    st.download_button(
        label=":material/picture_as_pdf: Export PDF",
        data=build_pdf_export(
            filtered,
            filters_payload,
        ),
        file_name="g4-lead-scorer.pdf",
        mime="application/pdf",
        width="stretch",
    )


# -----------------------------------------------------------------------------
# Footer
# -----------------------------------------------------------------------------

st.caption(
    f"Data source: CRM Sales Predictive Analytics (CC0) · "
    f"local path: ../ai-master-challenge/datasets/crm-sales-predictive-analytics. "
    "No synthetic CRM records are created by this application."
)
