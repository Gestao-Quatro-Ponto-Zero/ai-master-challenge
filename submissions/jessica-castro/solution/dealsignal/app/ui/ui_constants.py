"""
DealSignal UI — Static constants for the Streamlit interface.

Holds CSS, chart style dicts, and lookup tables used by multiple UI modules.
"""

# ── Page-level CSS injected once on startup ──────────────────────────────────
APP_CSS: str = """
    <style>
    /* Streamlit injeta padding-top inline — !important necessário */
    .block-container { padding-top: 1rem !important; }
    [data-testid="stAppViewContainer"] > section > div:first-child { padding-top: 0 !important; }

    /* ── Design tokens ───────────────────────── */
    :root {
        --surface:    #1E2130;
        --border:     rgba(255,255,255,0.09);
        --text-muted: #8A8FA8;
    }

    /* KPI cards — layout sem !important onde possível */
    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid rgba(0,0,0,0.07);
        border-radius: 12px;
        padding: 1rem 1.4rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    /* Streamlit define font/color inline nos filhos — !important necessário aqui */
    [data-testid="stMetricLabel"] p {
        font-size: 13px !important;
        color: #6b7280 !important;
        font-weight: 500 !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 28px !important;
        font-weight: 700 !important;
        color: #111827 !important;
    }
    [data-testid="stMetricDelta"] > div {
        border-radius: 20px !important;
        padding: 2px 10px !important;
        font-size: 12px !important;
        font-weight: 600 !important;
    }

    /* Tabela compacta */
    [data-testid="stDataFrame"] { font-size: 13px; }

    /* Painel direito fixo (sticky) */
    [data-testid="stHorizontalBlock"]:last-of-type > div:last-child {
        position: sticky;
        top: 60px;
        align-self: flex-start;
        max-height: calc(100vh - 80px);
        overflow-y: auto;
        border-left: 1px solid var(--border);
        padding-left: 1.2rem;
    }

    /* Expander — Streamlit adiciona border/shadow via classe interna, !important necessário */
    [data-testid="stExpander"] {
        border: none !important;
        box-shadow: none !important;
        margin-top: 2px;
        margin-bottom: 2px;
    }
    [data-testid="stExpander"] summary {
        padding: 3px 0;
        font-size: 13px;
        color: #888;
        min-height: unset !important; /* Streamlit define min-height inline */
    }
    [data-testid="stExpander"] summary:hover { color: #555; }
    [data-testid="stExpander"] > div[data-testid="stExpanderDetails"] {
        padding: 6px 4px 4px 4px;
    }
    [data-testid="stExpander"] > div[data-testid="stExpanderDetails"] p,
    [data-testid="stExpander"] > div[data-testid="stExpanderDetails"] li {
        font-size: 13px;
        line-height: 1.5;
        margin-bottom: 2px;
    }
    </style>
    """

# ── Plotly chart style ────────────────────────────────────────────────────────
_CHART_FONT:   dict = dict(family="sans-serif", size=12, color="#C0C4D0")
_CHART_MARGIN: dict = dict(l=10, r=90, t=10, b=30)

# ── Engine interpretation texts ───────────────────────────────────────────────
_ENGINE_INTERPRETATIONS: dict[str, dict[str, str]] = {
    "Seller Power": {
        "strong":   "Vendedor entre os melhores do time — bom histórico de fechamentos.",
        "moderate": "Vendedor com desempenho na média — acompanhe de perto.",
        "weak":     "Vendedor abaixo da média do time — deal pode precisar de suporte adicional.",
    },
    "Deal Momentum": {
        "strong":   "Deal avançando rapidamente — alta chance de fechamento no curto prazo.",
        "moderate": "Deal em ritmo normal — acompanhe para manter o momentum.",
        "weak":     "Deal estagnado no pipeline — recomendado acompanhamento ativo para reativar engajamento.",
    },
    "Product Performance": {
        "strong":   "Produto entre os melhores do portfólio — forte histórico de conversão.",
        "moderate": "Produto com conversão na média — sem vantagem competitiva clara.",
        "weak":     "Produto entre os mais fracos do portfólio — considere reforçar o pitch ou mudar o produto.",
    },
    "Stagnation Risk": {
        "strong":   "Deal ativo e recente — sem sinais de estagnação.",
        "moderate": "Deal com algum tempo parado — monitore o engajamento.",
        "weak":     "Deal parado há muito tempo — risco real de perda por inatividade.",
    },
}

# ── Engine label → PT-BR display name ────────────────────────────────────────
_ENGINE_LABELS_PT: dict[str, str] = {
    "Seller Power":        "Força do Vendedor",
    "Deal Momentum":       "Momento do Deal",
    "Product Performance": "Desempenho do Produto",
    "Deal Size":           "Tamanho do Deal",
    "Stagnation Risk":     "Risco de Estagnação",
}

# ── Inline badge CSS (shared between rating badges and table cells) ───────────
_BADGE_STYLE: str = (
    "color:white; font-size:12px; font-weight:700; "
    "border-radius:5px; padding:3px 10px; display:inline-block; "
    "letter-spacing:0.5px;"
)
