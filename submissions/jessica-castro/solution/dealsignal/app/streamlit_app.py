"""
DealSignal - Streamlit App

Run with:
    streamlit run app/streamlit_app.py
"""

import json
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
import plotly.express as px
import streamlit as st

# Resolve project root and ensure utils/ is importable
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from utils.report import (  # noqa: E402
    generate_csv,
    generate_pdf,
    make_csv_filename,
    make_pdf_filename,
)
from utils.signals import (  # noqa: E402
    FEATURE_EXPLANATIONS,
    FEATURE_TO_ENGINE,
    compute_engine_scores,
    get_signals,
    parse_factors,
)

RESULTS_PATH = ROOT / "data" / "results.csv"
METADATA_PATH = ROOT / "model" / "artifacts" / "metadata.json"

# ── Paleta de cores — rating ──────────────────────────────────────────────────
RATING_COLORS = {
    "AAA": "#1a7a1a",
    "AA":  "#2ecc71",
    "A":   "#82e0aa",
    "BBB": "#f39c12",
    "BB":  "#e67e22",
    "B":   "#e74c3c",
    "CCC": "#922b21",
}

RATING_ORDER = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC"]

RATING_RANGES = {
    "AAA": "> 90%",
    "AA":  "80 – 90%",
    "A":   "70 – 80%",
    "BBB": "60 – 70%",
    "BB":  "50 – 60%",
    "B":   "40 – 50%",
    "CCC": "< 40%",
}

# Emoji mapeado para cada rating (usado na tabela)
# Cores próximas às do RATING_COLORS: verde / laranja / vermelho
RATING_EMOJI = {
    "AAA": "🟢",
    "AA":  "🟢",
    "A":   "🟢",
    "BBB": "🟠",
    "BB":  "🟠",
    "B":   "🔴",
    "CCC": "🔴",
}

# Constantes de estilo para gráficos Plotly
_CHART_FONT   = dict(family="sans-serif", size=12, color="#C0C4D0")
_CHART_MARGIN = dict(l=10, r=90, t=10, b=30)


# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DealSignal",
    layout="wide",
)

st.markdown(
    """
    <style>
    /* ── Design tokens ───────────────────────── */
    :root {
        --surface:    #1E2130;
        --border:     rgba(255,255,255,0.09);
        --text-muted: #8A8FA8;
    }

    /* KPI cards — fundo e borda */
    [data-testid="stMetric"] {
        background: #f0f2f6;
        border: 1px solid rgba(0,0,0,0.08);
        border-radius: 10px;
        padding: 1rem 1.2rem;
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
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Data loaders ─────────────────────────────────────────────────────────────
@st.cache_data
def load_results() -> pd.DataFrame:
    if not RESULTS_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(RESULTS_PATH)
    df["win_probability"] = pd.to_numeric(df["win_probability"], errors="coerce")
    df["expected_revenue"] = pd.to_numeric(df["expected_revenue"], errors="coerce")
    df["effective_value"] = pd.to_numeric(df["effective_value"], errors="coerce")
    return df


@st.cache_data
def load_metadata() -> dict:
    if not METADATA_PATH.exists():
        return {}
    with open(METADATA_PATH) as f:
        return json.load(f)


ALL = "Todos"
FILTER_KEYS = ["sel_office", "sel_manager", "sel_agent"]


# ── Formatadores ──────────────────────────────────────────────────────────────

def format_probability_bar(prob: float) -> str:
    pct = round(float(prob) * 100, 1)
    filled = max(0, min(10, round(float(prob) * 10)))
    return f"{pct}%  {'█' * filled}{'░' * (10 - filled)}"


def format_currency(value: float) -> str:
    return f"${value:,.0f}" if pd.notna(value) else "—"


def _engine_label(score: int) -> str:
    if score >= 70:
        return "🟢 Forte"
    if score >= 45:
        return "🟡 Moderado"
    return "🔴 Fraco"


def _engine_position(score: int) -> str:
    if score >= 70:
        return "Entre os mais fortes"
    if score >= 45:
        return "Na faixa intermediária"
    return "Entre os mais fracos"


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


def _engine_interpretation(engine: str, score: int) -> str:
    texts = _ENGINE_INTERPRETATIONS.get(engine, {})
    if score >= 70:
        return texts.get("strong", "")
    if score >= 45:
        return texts.get("moderate", "")
    return texts.get("weak", "")


_BADGE_STYLE = (
    "color:white; font-size:12px; font-weight:700; "
    "border-radius:5px; padding:3px 10px; display:inline-block; "
    "letter-spacing:0.5px;"
)


def _rating_badge(rating: str) -> str:
    """Badge colorido padronizado — usado no painel de análise."""
    color = RATING_COLORS.get(rating, "#888888")
    return f'<span style="background:{color}; {_BADGE_STYLE}">{rating}</span>'



# ── Display dataframe ─────────────────────────────────────────────────────────

def build_display_dataframe(scored_df: pd.DataFrame) -> pd.DataFrame:
    """Retorna DataFrame compacto para exibição na tabela de pipeline."""
    out = pd.DataFrame()
    out["opportunity_id"] = scored_df["opportunity_id"].values
    out["Rating"] = scored_df["deal_rating"].apply(
        lambda r: f"{RATING_EMOJI.get(r, '')} {r}"
    ).values
    out["Conta"]   = scored_df["account"].values
    out["Produto"] = scored_df["product"].values
    out["Vendedor"]   = scored_df["sales_agent"].values
    out["Estágio"]    = scored_df["deal_stage"].values
    out["Engajamento"] = pd.to_datetime(scored_df["engage_date"], errors="coerce").dt.strftime("%d/%m/%Y")
    # Coluna float para ProgressColumn (nativa do Streamlit)
    out["_win_prob"] = (scored_df["win_probability"].values * 100).round(1)
    out["Rec. Esperada"] = scored_df["expected_revenue"].apply(format_currency).values
    if "deal_health_score" in scored_df.columns:
        out["Saúde"] = scored_df["deal_health_status"].values
    if "priority_tier" in scored_df.columns:
        out["Prioridade"] = scored_df["priority_tier"].values
    return out


# ── Signal payload ────────────────────────────────────────────────────────────

def build_signals_for_deal(row: pd.Series, df: pd.DataFrame) -> dict:
    """Monta payload estruturado de sinais para o painel de análise."""
    factors_raw = row.get("top_contributing_factors", "")
    factors = parse_factors(str(factors_raw) if pd.notna(factors_raw) else "")

    seen_engines: set = set()
    positive_signals = []
    risk_signals = []
    for feat, val in factors:
        engine = FEATURE_TO_ENGINE.get(feat)
        if not engine or engine in seen_engines:
            continue
        seen_engines.add(engine)
        desc = FEATURE_EXPLANATIONS.get(feat, feat)
        entry = {"title": engine, "description": desc}
        if val > 0.05:
            positive_signals.append(entry)
        elif val < -0.05:
            risk_signals.append(entry)

    engine_scores = compute_engine_scores(row, df)
    return {
        "positive_signals": positive_signals[:3],
        "risk_signals":     risk_signals[:3],
        "rating_engines":   engine_scores,
        "model_factors":    factors,
        "engine_details":   build_engine_details(row, df, engine_scores),
    }


def build_top_seller_benchmark(df: pd.DataFrame, min_deals: int = 10) -> dict:
    """Retorna métricas agregadas do melhor vendedor (maior agent_win_rate com min_deals)."""
    win_rate_col = "seller_win_rate" if "seller_win_rate" in df.columns else "agent_win_rate"
    agg = (
        df.groupby("sales_agent")
        .agg(
            deals       =("sales_agent",      "count"),
            win_rate    =(win_rate_col,        "mean"),
            exp_revenue =("expected_revenue",  "mean"),
            eff_value   =("effective_value",   "mean"),
            win_prob    =("win_probability",   "mean"),
        )
        .reset_index()
    )
    candidates = agg[agg["deals"] >= min_deals]
    if candidates.empty:
        return {}
    best = candidates.loc[candidates["win_rate"].idxmax()]
    return {
        "name":        best["sales_agent"],
        "deals":       int(best["deals"]),
        "win_rate":    best["win_rate"],
        "exp_revenue": best["exp_revenue"],
        "eff_value":   best["eff_value"],
        "win_prob":    best["win_prob"],
    }


def build_engine_details(row: pd.Series, df: pd.DataFrame, engine_scores: dict) -> dict:
    """Métricas explicativas por motor — interpretações derivadas do score relativo."""
    agent   = row.get("sales_agent", "—")
    product = row.get("product", "—")
    account = row.get("account", "—")

    # ── Seller Power ──────────────────────────────────────────────────────────
    # Prefer V2 seller_win_rate; fall back to V1 agent_win_rate
    agent_wr    = pd.to_numeric(
        row.get("seller_win_rate") if "seller_win_rate" in row.index else row.get("agent_win_rate"),
        errors="coerce",
    )
    seller_rank = pd.to_numeric(row.get("seller_rank_percentile"), errors="coerce")
    seller_load = pd.to_numeric(row.get("seller_pipeline_load"), errors="coerce")
    agent_deals = df[df["sales_agent"] == agent]
    agent_exp   = agent_deals["expected_revenue"].mean() if len(agent_deals) else None
    agent_eff   = agent_deals["effective_value"].mean()  if len(agent_deals) else None
    agent_wp    = agent_deals["win_probability"].mean()  if len(agent_deals) else None
    top         = build_top_seller_benchmark(df)
    sp_score    = engine_scores.get("Seller Power", 50)

    # ── Deal Momentum ─────────────────────────────────────────────────────────
    days_eng = pd.to_numeric(row.get("days_since_engage"), errors="coerce")
    is_stale = int(row.get("is_stale_flag", 0)) if pd.notna(row.get("is_stale_flag")) else 0
    if pd.notna(days_eng) and days_eng <= 7:
        momentum_status = "Acelerado"
    elif pd.notna(days_eng) and days_eng < 45:
        momentum_status = "Adequado"
    else:
        momentum_status = "Lento"
    dm_score = engine_scores.get("Deal Momentum", 50)

    # ── Product Performance ───────────────────────────────────────────────────
    prod_wr    = pd.to_numeric(row.get("product_win_rate"), errors="coerce")
    prod_rank  = pd.to_numeric(row.get("product_rank_percentile"), errors="coerce")
    prod_deals = df[df["product"] == product]
    prod_exp   = prod_deals["expected_revenue"].mean() if len(prod_deals) else None
    pp_score   = engine_scores.get("Product Performance", 50)

    # ── Stagnation Risk ───────────────────────────────────────────────────────
    age_pct      = pd.to_numeric(row.get("deal_age_percentile"), errors="coerce")
    pipeline_avg = df["days_since_engage"].mean()
    sr_score     = engine_scores.get("Stagnation Risk", 50)

    return {
        "Seller Power": {
            "metrics": [
                ("Vendedor",                  agent),
                ("Taxa de conversão (V2)",    f"{agent_wr:.0%}" if pd.notna(agent_wr) else "—"),
                ("Percentil no time",         f"{seller_rank * 100:.0f}º" if pd.notna(seller_rank) else "—"),
                ("Deals em aberto",           f"{int(seller_load)}" if pd.notna(seller_load) else "—"),
                ("Posição no time",           _engine_position(sp_score)),
            ],
            "benchmark":   top,
            "agent_stats": {
                "name":        agent,
                "deals":       len(agent_deals),
                "win_rate":    agent_wr,
                "exp_revenue": agent_exp,
                "eff_value":   agent_eff,
                "win_prob":    agent_wp,
            },
            "interpretation": _engine_interpretation("Seller Power", sp_score),
        },
        "Deal Momentum": {
            "metrics": [
                ("Estágio atual",        row.get("deal_stage", "—")),
                ("Sem contato há",       f"{int(days_eng)} dias" if pd.notna(days_eng) else "—"),
                ("Ritmo do Deal",        momentum_status),
                ("Deal parado",          "⚠️ Sim" if is_stale else "✅ Não"),
                ("Posição no pipeline",  _engine_position(dm_score)),
                ("Data de engajamento",  str(row.get("engage_date", "—"))[:10]),
            ],
            "interpretation": _engine_interpretation("Deal Momentum", dm_score),
        },
        "Product Performance": {
            "metrics": [
                ("Produto",                     product),
                ("Taxa de conversão histórica", f"{prod_wr:.0%}" if pd.notna(prod_wr) else "—"),
                ("Ranking do produto",          f"{prod_rank * 100:.0f}º percentil" if pd.notna(prod_rank) else "—"),
                ("Posição entre os produtos",   _engine_position(pp_score)),
                ("Deals com este produto",      str(len(prod_deals))),
                ("Receita esperada média",      format_currency(prod_exp) if prod_exp else "—"),
            ],
            "interpretation": _engine_interpretation("Product Performance", pp_score),
        },
        "Stagnation Risk": {
            "metrics": [
                ("Dias no pipeline",          f"{int(days_eng)} dias" if pd.notna(days_eng) else "—"),
                ("Percentil de idade",        f"{age_pct * 100:.0f}º percentil" if pd.notna(age_pct) else "—"),
                ("Deal parado (flag)",        "⚠️ Sim" if is_stale else "✅ Não"),
                ("Média do pipeline",         f"{pipeline_avg:.0f} dias"),
                ("Posição (saúde da idade)",  _engine_position(sr_score)),
            ],
            "interpretation": _engine_interpretation("Stagnation Risk", sr_score),
        },
    }


# ── Helpers de filtro ─────────────────────────────────────────────────────────

def _valid_options(df: pd.DataFrame, col: str, filters: dict) -> list:
    mask = pd.Series(True, index=df.index)
    for filter_col, value in filters.items():
        if filter_col != col and value != ALL:
            mask &= df[filter_col] == value
    return sorted(df.loc[mask, col].dropna().unique().tolist())


def _init_filters():
    for key in FILTER_KEYS:
        if key not in st.session_state:
            st.session_state[key] = ALL
    if "selected_deal_id" not in st.session_state:
        st.session_state["selected_deal_id"] = None


def _reset_filters():
    for key in FILTER_KEYS:
        st.session_state[key] = ALL
    if "sel_ratings" in st.session_state:
        st.session_state["sel_ratings"] = RATING_ORDER
    st.session_state["selected_deal_id"] = None


def _validate_and_apply_cascade(df: pd.DataFrame):
    current = {
        "office":      st.session_state.get("sel_office", ALL),
        "manager":     st.session_state.get("sel_manager", ALL),
        "sales_agent": st.session_state.get("sel_agent", ALL),
    }
    valid = {col: _valid_options(df, col, current) for col in current}
    if current["office"] != ALL and current["office"] not in valid["office"]:
        st.session_state["sel_office"] = ALL
    if current["manager"] != ALL and current["manager"] not in valid["manager"]:
        st.session_state["sel_manager"] = ALL
    if current["sales_agent"] != ALL and current["sales_agent"] not in valid["sales_agent"]:
        st.session_state["sel_agent"] = ALL
    return valid


# ── Painel de Análise do Deal ─────────────────────────────────────────────────

def render_deal_header(row: pd.Series) -> None:
    """Cabeçalho compacto — exibe apenas informações não presentes na tabela."""
    account = row.get("account", "—")
    product = row.get("product", "—")
    rating  = str(row.get("deal_rating", ""))

    st.markdown(
        f"<div style='display:flex; align-items:center; gap:10px;'>"
        f"{_rating_badge(rating)}"
        f"<span style='font-weight:700; font-size:15px;'>{account} · {product}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    prob  = float(row.get("win_probability", 0.0))
    value = format_currency(row.get("effective_value", 0.0))
    pct   = round(prob * 100, 1)
    st.markdown(
        f"<div style='margin-top:8px;'>"
        f"<div style='display:flex; align-items:center; gap:12px;'>"
        f"<div>"
        f"<span style='font-size:15px; font-weight:600; color:#333;'>{value}</span>"
        f"<span style='font-size:11px; color:#aaa; margin-left:4px;'>preço do produto</span>"
        f"</div>"
        f"<div style='display:flex; align-items:center; gap:8px; flex:1;'>"
        f"<div style='flex:1; background:#e0e0e0; border-radius:4px; height:6px;'>"
        f"<div style='width:{pct}%; background:#71808b; border-radius:4px; height:6px;'></div>"
        f"</div>"
        f"<span style='font-size:12px; color:#777; white-space:nowrap;'>{pct}% fechamento</span>"
        f"</div>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    health_score  = row.get("deal_health_score",  None)
    health_status = row.get("deal_health_status", None)
    priority_tier = row.get("priority_tier",       None)

    if health_score is not None and pd.notna(health_score):
        st.metric("Saúde do Deal", f"{health_score:.0f}", delta=str(health_status))
    if priority_tier is not None and str(priority_tier) != "nan":
        st.metric("Prioridade", str(priority_tier))


def render_positive_signals(signal_payload: dict) -> None:
    st.markdown("**✅ Sinais Positivos**")
    if signal_payload["positive_signals"]:
        for s in signal_payload["positive_signals"]:
            st.success(f"**{s['title']}** — {s['description']}")
    else:
        st.info("Nenhum sinal positivo forte identificado.")


def render_risk_signals(signal_payload: dict) -> None:
    st.markdown("**⚠️ Sinais de Risco**")
    if signal_payload["risk_signals"]:
        for s in signal_payload["risk_signals"]:
            st.error(f"**{s['title']}** — {s['description']}")
    else:
        st.info("Nenhum sinal de risco relevante detectado.")


_ENGINE_LABELS_PT: dict[str, str] = {
    "Seller Power":        "Força do Vendedor",
    "Deal Momentum":       "Momento do Deal",
    "Product Performance": "Desempenho do Produto",
    "Deal Size":           "Tamanho do Deal",
    "Stagnation Risk": "Risco de Estagnação",
}


def _render_seller_benchmark(current: dict, top: dict) -> None:
    """Tabela HTML comparando vendedor atual vs melhor vendedor do time."""
    def _fmt_wr(v):
        return f"{v:.0%}" if v is not None and pd.notna(v) else "—"
    def _fmt_cur(v):
        return format_currency(v) if v is not None and pd.notna(v) else "—"
    def _fmt_wp(v):
        return f"{v:.0%}" if v is not None and pd.notna(v) else "—"

    is_top  = current["name"] == top["name"]
    cur_badge = " 🏆" if is_top else ""

    rows = [
        ("Vendedor",               current["name"] + cur_badge,          top["name"] + " 🏆"),
        ("Deals no pipeline",      str(current["deals"]),                  str(top["deals"])),
        ("Taxa de conversão",      _fmt_wr(current["win_rate"]),           _fmt_wr(top["win_rate"])),
        ("Expected Revenue médio", _fmt_cur(current["exp_revenue"]),       _fmt_cur(top["exp_revenue"])),
        ("Valor efetivo médio",    _fmt_cur(current["eff_value"]),         _fmt_cur(top["eff_value"])),
        ("Win Probability média",  _fmt_wp(current["win_prob"]),           _fmt_wp(top["win_prob"])),
    ]

    html = (
        "<table style='width:100%;border-collapse:collapse;font-size:12px;margin-bottom:8px;'>"
        "<thead><tr>"
        "<th style='text-align:left;padding:4px 6px;border-bottom:2px solid #ddd;color:#555;'>Métrica</th>"
        "<th style='text-align:center;padding:4px 6px;border-bottom:2px solid #ddd;color:#1976D2;'>Vendedor Atual</th>"
        "<th style='text-align:center;padding:4px 6px;border-bottom:2px solid #ddd;color:#388E3C;'>🏆 Melhor Vendedor</th>"
        "</tr></thead><tbody>"
    )
    for metric, cur_val, top_val in rows:
        html += (
            f"<tr>"
            f"<td style='padding:4px 6px;border-bottom:1px solid #f0f0f0;color:#444;'>{metric}</td>"
            f"<td style='padding:4px 6px;border-bottom:1px solid #f0f0f0;text-align:center;font-weight:600;color:#1976D2;'>{cur_val}</td>"
            f"<td style='padding:4px 6px;border-bottom:1px solid #f0f0f0;text-align:center;font-weight:600;color:#388E3C;'>{top_val}</td>"
            f"</tr>"
        )
    html += "</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)


def render_rating_engines(signal_payload: dict) -> None:
    _LABEL_COLOR   = {"🟢 Forte": "#4CAF50", "🟡 Moderado": "#FF9800", "🔴 Fraco": "#F44336"}
    _LABEL_TEXT    = {"🟢 Forte": "Forte",   "🟡 Moderado": "Moderado", "🔴 Fraco": "Fraco"}
    engine_details = signal_payload.get("engine_details", {})
    st.markdown("**⚡ Motores de Rating**")
    for engine, score in signal_payload["rating_engines"].items():
        label   = _engine_label(score)
        name_pt = _ENGINE_LABELS_PT.get(engine, engine)
        color   = _LABEL_COLOR.get(label, "#888")
        text    = _LABEL_TEXT.get(label, label)
        st.markdown(
            f"<div style='margin-bottom:2px;'>"
            f"<div style='display:flex;align-items:center;gap:6px;margin-bottom:5px;'>"
            f"<span style='font-size:12px;font-weight:600;color:#333;'>{name_pt}</span>"
            f"<span style='font-size:10px;font-weight:600;color:white;background:{color};"
            f"padding:1px 7px;border-radius:10px;line-height:16px;'>{text}</span>"
            f"</div>"
            f"<div style='display:flex;align-items:center;gap:8px;'>"
            f"<div style='width:70%;background:#e0e0e0;border-radius:3px;height:5px;flex-shrink:0;'>"
            f"<div style='width:{score}%;background:{color};height:5px;border-radius:3px;'></div>"
            f"</div>"
            f"<span style='font-size:12px;font-weight:700;color:{color};'>{score}</span>"
            f"</div></div>",
            unsafe_allow_html=True,
        )
        details = engine_details.get(engine, {})
        if details:
            with st.expander("Ver detalhes", expanded=False):
                if engine == "Seller Power":
                    benchmark   = details.get("benchmark", {})
                    agent_stats = details.get("agent_stats", {})
                    if benchmark and agent_stats:
                        _render_seller_benchmark(agent_stats, benchmark)
                for k, v in details.get("metrics", []):
                    st.markdown(f"**{k}:** {v}")
                if details.get("interpretation"):
                    st.info(details["interpretation"])


def render_deal_explanation(row: pd.Series) -> None:
    """Natural language explanation combining win probability, health and value."""
    prob   = float(row.get("win_probability", 0))
    health = str(row.get("deal_health_status", "—"))
    days   = row.get("days_since_engage", None)
    value  = row.get("effective_value", None)
    stale  = int(row.get("is_stale_flag", 0))

    prob_text  = "alta probabilidade histórica" if prob >= 0.65 else "probabilidade moderada"
    value_text = f"impacto financeiro de {format_currency(value)}" if value else ""
    stale_text = f", parado há **{int(days)} dias**" if stale and days else ""

    parts = [p for p in [prob_text, value_text] if p]
    st.info(f"Deal com {', '.join(parts)}{stale_text}. Saúde atual: **{health}**.")


def render_deal_insight_panel(row: pd.Series, signal_payload: dict) -> None:
    st.markdown("#### Análise do Deal")
    render_deal_header(row)
    render_deal_explanation(row)
    st.divider()
    render_rating_engines(signal_payload)


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    logo_path = ROOT / "assets" / "dealsignal_logo.png"
    if logo_path.exists():
        st.image(str(logo_path), width=260)
    st.caption("Priorização inteligente de oportunidades com base em probabilidade de fechamento e receita esperada")

    df = load_results()
    metadata = load_metadata()

    if df.empty:
        st.error(
            "Nenhum resultado encontrado. Execute o pipeline primeiro:\n\n"
            "```bash\npython run_pipeline.py\n```"
        )
        return

    _init_filters()
    valid = _validate_and_apply_cascade(df)

    # Aplicar filtros
    selected_office  = st.session_state["sel_office"]
    selected_manager = st.session_state["sel_manager"]
    selected_agent   = st.session_state["sel_agent"]
    ratings = st.session_state.get("sel_ratings", RATING_ORDER)

    filtered = df.copy()
    if selected_office != ALL:
        filtered = filtered[filtered["office"] == selected_office]
    if selected_manager != ALL:
        filtered = filtered[filtered["manager"] == selected_manager]
    if selected_agent != ALL:
        filtered = filtered[filtered["sales_agent"] == selected_agent]
    if ratings:
        filtered = filtered[filtered["deal_rating"].isin(ratings)]
    filtered = filtered.sort_values("expected_revenue", ascending=False).reset_index(drop=True)

    auc = metadata.get("cv_auc", None)
    kpis = {
        "Pipeline Total":  format_currency(filtered["expected_revenue"].sum()),
        "Top 10 Pipeline": format_currency(filtered.head(10)["expected_revenue"].sum()),
        "Deals Ativos":    str(len(filtered)),
        "AUC do Modelo":   f"{auc:.3f}" if auc else "—",
    }
    active_filters = {
        "Escritório": selected_office,
        "Gerente":    selected_manager,
        "Vendedor":   selected_agent,
    }

    # ── Sidebar — filtros + legenda de rating + downloads ─────────────────────
    with st.sidebar:
        st.header("Filtros")
        st.selectbox("Escritório", options=[ALL] + valid["office"],      key="sel_office")
        st.selectbox("Gerente",    options=[ALL] + valid["manager"],     key="sel_manager")
        st.selectbox("Vendedor",   options=[ALL] + valid["sales_agent"], key="sel_agent")

        st.multiselect(
            "Rating",
            options=RATING_ORDER,
            default=RATING_ORDER,
            key="sel_ratings",
        )
        st.button("Limpar Filtros", on_click=_reset_filters, use_container_width=True)

        st.markdown("**Escala de Rating**")
        rows = "".join(
            f"<tr>"
            f"<td style='padding:3px 6px;'>{_rating_badge(r)}</td>"
            f"<td style='padding:3px 6px; font-size:12px; color:#555;'>{RATING_RANGES[r]}</td>"
            f"</tr>"
            for r in RATING_ORDER
        )
        st.markdown(
            f"<table style='border-collapse:collapse; width:100%;'>{rows}</table>",
            unsafe_allow_html=True,
        )

        st.divider()
        st.markdown("**Exportar Relatório**")
        dl_col1, dl_col2 = st.columns(2)
        dl_col1.download_button(
            label="CSV",
            data=generate_csv(filtered),
            file_name=make_csv_filename(active_filters),
            mime="text/csv",
            use_container_width=True,
        )
        dl_col2.download_button(
            label="PDF",
            data=generate_pdf(filtered, kpis, active_filters, metadata),
            file_name=make_pdf_filename(active_filters),
            mime="application/pdf",
            use_container_width=True,
        )

    # ── KPIs ──────────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Pipeline Total",  kpis["Pipeline Total"])
    col2.metric("Top 10 Pipeline", kpis["Top 10 Pipeline"])
    col3.metric("Deals Ativos",    kpis["Deals Ativos"])
    col4.metric("AUC do Modelo",   kpis["AUC do Modelo"])

    st.divider()

    # ── Top 10 + Distribuição por Rating lado a lado ───────────────────────────
    col_top10, col_dist = st.columns([2, 1])

    with col_top10:
        st.subheader("Top 10 Deals para Priorizar")
        top10 = filtered.head(10).copy()
        top10["label"]   = top10["account"] + " · " + top10["product"]
        top10["win_pct"] = (top10["win_probability"] * 100).round(1)

        if not top10.empty:
            fig = px.bar(
                top10,
                x="expected_revenue",
                y="label",
                orientation="h",
                color="deal_rating",
                color_discrete_map=RATING_COLORS,
                category_orders={"deal_rating": RATING_ORDER},
                text=top10["win_pct"].astype(str) + "%",
                labels={"expected_revenue": "", "label": ""},
                height=420,
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(
                yaxis={"autorange": "reversed"},
                showlegend=True,
                legend_title="Rating",
                legend=dict(orientation="v", x=1.01, y=1),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=_CHART_FONT,
                margin=_CHART_MARGIN,
                xaxis_title="",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhum deal corresponde aos filtros selecionados.")

    with col_dist:
        st.subheader("Distribuição por Rating")
        rating_counts = (
            filtered["deal_rating"]
            .value_counts()
            .reindex(RATING_ORDER)
            .dropna()
            .reset_index()
        )
        rating_counts.columns = ["Rating", "Quantidade"]
        fig2 = px.bar(
            rating_counts,
            x="Rating",
            y="Quantidade",
            color="Rating",
            color_discrete_map=RATING_COLORS,
            category_orders={"Rating": RATING_ORDER},
            text="Quantidade",
            height=420,
        )
        fig2.update_traces(textposition="outside")
        fig2.update_layout(
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=_CHART_FONT,
            margin=_CHART_MARGIN,
            xaxis_title="",
            yaxis_title="Qtd",
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # ── Master-detail: tabela (esquerda) | Análise do Deal (direita) ──────────
    col_left, col_right = st.columns([3, 1])

    with col_left:
        st.markdown(
            f"#### Pipeline Completo "
            f"<span style='font-size:12px; font-weight:400; color:#888;'>"
            f"{len(filtered)} deals</span>",
            unsafe_allow_html=True,
        )

        display_df = build_display_dataframe(filtered)

        event = st.dataframe(
            display_df,
            column_config={
                "opportunity_id": None,
                "_win_prob": st.column_config.ProgressColumn(
                    "% Fechamento",
                    min_value=0,
                    max_value=100,
                    format="%.1f%%",
                    width="medium",
                ),
                "Rating":        st.column_config.TextColumn("Rating",        width="small"),
                "Conta":         st.column_config.TextColumn("Conta",         width="medium"),
                "Produto":       st.column_config.TextColumn("Produto",       width="medium"),
                "Vendedor":      st.column_config.TextColumn("Vendedor",      width="medium"),
                "Estágio":       st.column_config.TextColumn("Estágio",       width="medium"),
                "Engajamento":   st.column_config.TextColumn("Engajamento",   width="small"),
                "Rec. Esperada": st.column_config.TextColumn("Rec. Esperada", width="small"),
            },
            use_container_width=True,
            height=760,
            selection_mode="single-row",
            on_select="rerun",
            hide_index=True,
            key="pipeline_table",
        )
        rows = event.selection.rows
        if rows:
            st.session_state["selected_deal_id"] = display_df.iloc[rows[0]]["opportunity_id"]

    # Validar que o deal selecionado ainda está no dataset filtrado
    selected_id = st.session_state.get("selected_deal_id")
    if selected_id and selected_id not in filtered["opportunity_id"].values:
        st.session_state["selected_deal_id"] = None
        selected_id = None

    with col_right:
        if selected_id:
            row = filtered[filtered["opportunity_id"] == selected_id].iloc[0]
            payload = build_signals_for_deal(row, filtered)
            render_deal_insight_panel(row, payload)
        else:
            st.info("← Clique em uma linha da tabela para ver a análise do deal.")


if __name__ == "__main__":
    main()
