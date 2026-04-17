from __future__ import annotations
from pathlib import Path
import html
import json
import numpy as np
import pandas as pd
import re

ROOT = Path(__file__).resolve().parents[3] if len(Path(__file__).resolve().parents) >= 4 else Path.cwd()
OUTPUT_DIR = ROOT / "output"
RISK_ORDER = ["low", "medium", "high", "critical"]
RISK_COLORS = {
    "low": "#2dd4bf",
    "medium": "#60a5fa",
    "high": "#f59e0b",
    "critical": "#fb7185",
}
DRIVER_LABELS = {
    "recent_usage_drop": "Queda recente de uso",
    "recent_downgrade": "Downgrade recente",
    "poor_support_experience": "Experiência ruim de suporte",
    "high_error_rate": "Taxa alta de erro",
    "trial_fragility": "Fragilidade de trial",
    "no_auto_renew": "Sem auto-renovação",
    "usage_stale": "Uso estagnado",
    "reactivation_risk": "Risco de reativação",
    "high_escalation_load": "Alta carga de escalonamento",
}
SEGMENT_META = {
    "healthy_or_expand": {
        "title": "Expandir",
        "class_name": "teal",
        "desc": "Contas com boa saúde e espaço para crescimento comercial.",
    },
    "watch_strategic": {
        "title": "Monitorar",
        "class_name": "blue",
        "desc": "Contas relevantes sem risco crítico, mas que pedem acompanhamento próximo.",
    },
    "save_now_strategic": {
        "title": "Salvar agora — estratégico",
        "class_name": "rose",
        "desc": "Poucas contas, muito valor. Precisam de ação humana imediata.",
    },
    "save_now_volume": {
        "title": "Salvar agora — escala",
        "class_name": "rose",
        "desc": "Risco distribuído. Ideal para rotinas automatizadas com supervisão.",
    },
}
def _stable_sort(df: pd.DataFrame, by: list[str], ascending: list[bool]) -> pd.DataFrame:
    return df.sort_values(by=by, ascending=ascending, kind="mergesort", na_position="last").reset_index(drop=True)
def _require_columns(df: pd.DataFrame, required: set[str], label: str) -> None:
    missing = sorted(required.difference(df.columns))
    if missing:
        raise ValueError(f"{label} is missing required columns: {', '.join(missing)}")
def _read_outputs(output_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    account_path = output_dir / "account_360.csv"
    drivers_path = output_dir / "churn_risk_drivers.csv"
    health_path = output_dir / "customer_health_score.csv"
    reconciliation_path = output_dir / "churn_reconciliation.csv"
    global_explainability_path = output_dir / "model_global_explainability.csv"
    account_explanations_path = output_dir / "account_model_explanations.csv"
    metrics_path = output_dir / "model_metrics.json"
    required_files = [
        account_path,
        drivers_path,
        reconciliation_path,
        global_explainability_path,
        account_explanations_path,
        metrics_path,
    ]
    missing = [p.name for p in required_files if not p.exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing required pipeline outputs in {output_dir}: {', '.join(missing)}. Run python main.py first."
        )
    account_360 = pd.read_csv(account_path)
    drivers = pd.read_csv(drivers_path)
    reconciliation = pd.read_csv(reconciliation_path)
    global_explainability = pd.read_csv(global_explainability_path)
    account_explanations = pd.read_csv(account_explanations_path)
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    if "current_churn_probability" not in account_360.columns and "ml_churn_probability" in account_360.columns:
        account_360["current_churn_probability"] = account_360["ml_churn_probability"]
    optional_account_defaults = {
        "priority_segment": "healthy_or_expand",
        "churn_flag": 0,
        "observed_churn_flag": np.nan,
        "ever_churned_flag": np.nan,
        "reactivated_flag": np.nan,
        "reactivation_events": np.nan,
        "had_churn_event": np.nan,
        "last_churn_was_reactivation": np.nan,
        "current_primary_model_driver_label": "",
        "current_secondary_model_driver_label": "",
        "current_model_driver_summary": "",
        "current_model_explanation": "",
    }
    for col, default in optional_account_defaults.items():
        if col not in account_360.columns:
            account_360[col] = default
    if health_path.exists():
        customer_health = pd.read_csv(health_path)
    else:
        customer_health = account_360[["account_id", "health_score", "risk_level"]].copy()
    _require_columns(
        account_360,
        {
            "account_id",
            "account_name",
            "industry",
            "current_mrr",
            "mrr_at_risk",
            "health_score",
            "risk_level",
            "primary_driver",
            "recommended_action",
            "current_churn_probability",
            "priority_segment",
            "churn_flag",
        },
        "account_360.csv",
    )
    _require_columns(drivers, {"account_id", "triggered_specification", "weight"}, "churn_risk_drivers.csv")
    _require_columns(
        reconciliation,
        {"metric_key", "metric_label", "metric_category", "metric_value", "definition", "recommended_usage"},
        "churn_reconciliation.csv",
    )
    _require_columns(
        global_explainability,
        {"feature", "feature_label", "importance", "normalized_importance", "portfolio_direction", "impact_statement"},
        "model_global_explainability.csv",
    )
    _require_columns(
        account_explanations,
        {"account_id", "rank", "feature", "feature_label", "local_impact", "explanation_text"},
        "account_model_explanations.csv",
    )
    _require_columns(customer_health, {"account_id", "health_score", "risk_level"}, "customer_health_score.csv")
    return account_360, drivers, customer_health, reconciliation, global_explainability, account_explanations, metrics
def _normalize_accounts(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    numeric_defaults = {
        "current_mrr": 0.0,
        "mrr_at_risk": 0.0,
        "health_score": 0.0,
        "current_churn_probability": 0.0,
    }
    for col, default in numeric_defaults.items():
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(default)
    out["risk_level"] = (
        out["risk_level"].astype(str).str.lower().where(lambda s: s.isin(RISK_ORDER), "low")
    )
    out["driver_label"] = out["primary_driver"].map(DRIVER_LABELS).fillna(
        out["primary_driver"].astype(str).str.replace("_", " ", regex=False).str.capitalize()
    )
    out["plan_label"] = (
        out.get("latest_plan", pd.Series(index=out.index, dtype="object"))
        .fillna(out.get("plan_tier", pd.Series(index=out.index, dtype="object")))
        .fillna("Unknown")
    )
    out["account_short_id"] = out["account_id"].astype(str)
    out["risk_rank"] = out["risk_level"].map({"critical": 0, "high": 1, "medium": 2, "low": 3}).fillna(3)
    if "had_churn_event" in out.columns:
        out["had_churn_event_flag"] = pd.to_numeric(out["had_churn_event"], errors="coerce").fillna(0).gt(0)
    elif "ever_churned_flag" in out.columns:
        out["had_churn_event_flag"] = pd.to_numeric(out["ever_churned_flag"], errors="coerce").fillna(0).gt(0)
    elif "observed_churn_flag" in out.columns:
        out["had_churn_event_flag"] = pd.to_numeric(out["observed_churn_flag"], errors="coerce").fillna(0).gt(0)
    else:
        out["had_churn_event_flag"] = False
    if "reactivation_events" in out.columns:
        out["reactivated_history_flag"] = pd.to_numeric(out["reactivation_events"], errors="coerce").fillna(0).gt(0)
    elif "last_churn_was_reactivation" in out.columns:
        out["reactivated_history_flag"] = pd.to_numeric(out["last_churn_was_reactivation"], errors="coerce").fillna(0).gt(0)
    elif "reactivated_flag" in out.columns:
        out["reactivated_history_flag"] = pd.to_numeric(out["reactivated_flag"], errors="coerce").fillna(0).gt(0)
    else:
        out["reactivated_history_flag"] = False
    return _stable_sort(out, ["account_id"], [True])
def _normalize_drivers(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["driver_label"] = out["triggered_specification"].map(DRIVER_LABELS).fillna(
        out["triggered_specification"].astype(str).str.replace("_", " ", regex=False).str.capitalize()
    )
    out["weight"] = pd.to_numeric(out["weight"], errors="coerce").fillna(0.0)
    return out
def _normalize_reconciliation(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["metric_value"] = pd.to_numeric(out["metric_value"], errors="coerce").fillna(0).astype(int)
    for col in ["metric_key", "metric_label", "metric_category", "definition", "recommended_usage"]:
        out[col] = out[col].astype(str).fillna("-")
    return out.reset_index(drop=True)
def _normalize_global_explainability(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    numeric_cols = ["importance", "normalized_importance", "avg_signed_impact", "avg_abs_impact", "raising_share"]
    for col in numeric_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)
    for col in ["feature", "feature_label", "portfolio_direction", "impact_statement"]:
        if col in out.columns:
            out[col] = out[col].astype(str).fillna("-")
    return out.reset_index(drop=True)
def _normalize_account_explanations(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "rank" in out.columns:
        out["rank"] = pd.to_numeric(out["rank"], errors="coerce").fillna(0).astype(int)
    for col in ["feature", "feature_label", "feature_value", "baseline_value", "impact_direction", "explanation_text"]:
        if col in out.columns:
            out[col] = out[col].astype(str).fillna("-")
    if "local_impact" in out.columns:
        out["local_impact"] = pd.to_numeric(out["local_impact"], errors="coerce").fillna(0.0)
    return out.reset_index(drop=True)
def _money(v: float, decimals: int = 0) -> str:
    value = float(v or 0)
    if decimals == 0:
        return f"US$ {value:,.0f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"US$ {value:,.{decimals}f}".replace(",", "_").replace(".", ",").replace("_", ".")
def _pct(v: float, decimals: int = 1) -> str:
    return f"{100 * float(v or 0):.{decimals}f}%".replace(".", ",")
def _metric(v: float) -> str:
    return f"{float(v or 0):.3f}"


def _danger_class(value: float) -> str:
    return "danger-value" if float(value or 0) > 0 else ""


def _safe(text: object) -> str:
    return html.escape(str(text if text is not None else "-"))
def _simplify_explanation_text(text: object) -> str:
    value = str(text if text is not None else "").strip()

    patterns = [
        # Formas robustas para texto com acentos corrompidos na origem
        (r"(?i)a probabilidade mudaria em m\S*dia", "o risco mudaria em cerca de"),
        (r"(?i)a probabilidade cairia cerca de", "o risco cairia em cerca de"),
        (r"(?i)probabilidade mudaria em m\S*dia", "o risco mudaria em cerca de"),
        (r"(?i)probabilidade cairia cerca de", "o risco cairia em cerca de"),
        (r"(?i)ao voltar ao perfil t\S*pico", "se essa característica estivesse mais próxima do padrão esperado"),
        (r"(?i)ao aproximar do perfil t\S*pico", "se essa característica se aproximasse do padrão esperado"),
        (r"(?i)perfil t\S*pico", "padrão esperado"),
        (r"(?i)tende a elevar risco no portf\S*lio", "costuma aumentar o risco na carteira"),
        (r"(?i)ao perder esse perfil", "se essa característica deixasse de estar presente"),

        # Probabilidade → risco
        (r"(?i)a probabilidade mudaria em média", "o risco mudaria em cerca de"),
        (r"(?i)a probabilidade cairia cerca de", "o risco cairia em cerca de"),
        (r"(?i)probabilidade mudaria em média", "o risco mudaria em cerca de"),
        (r"(?i)probabilidade cairia cerca de", "o risco cairia em cerca de"),

        # Perfil típico
        (r"(?i)ao voltar ao perfil típico", "se essa característica estivesse mais próxima do padrão esperado"),
        (r"(?i)ao aproximar do perfil típico", "se essa característica se aproximasse do padrão esperado"),
        (r"(?i)perfil típico", "padrão esperado"),

        # Drivers
        (r"(?i)tende a elevar risco no portfólio", "costuma aumentar o risco na carteira"),
        (r"(?i)atua mais como fator protetivo", "costuma reduzir o risco na carteira"),

        # Outros
        (r"(?i)ao perder esse perfil", "se essa característica deixasse de estar presente"),
        (r"(?i)p\.p\.", "pontos percentuais"),
    ]

    for pattern, replacement in patterns:
        value = re.sub(pattern, replacement, value)

    # limpeza final
    value = re.sub(r"\s+", " ", value).strip()

    return value
def _resolve_primary_churn(df: pd.DataFrame) -> tuple[pd.Series, str]:
    if "churn_flag" in df.columns:
        return pd.to_numeric(df["churn_flag"], errors="coerce").fillna(0), "flag consolidado de contas"
    if "observed_churn_flag" in df.columns:
        return pd.to_numeric(df["observed_churn_flag"], errors="coerce").fillna(0), "base de eventos"
    if "is_logo_churned" in df.columns:
        return pd.to_numeric(df["is_logo_churned"], errors="coerce").fillna(0), "situação operacional atual"
    return pd.Series(0, index=df.index, dtype=float), "base indisponivel"
def _resolve_event_churn(df: pd.DataFrame) -> tuple[pd.Series | None, str | None]:
    if "observed_churn_flag" in df.columns:
        return pd.to_numeric(df["observed_churn_flag"], errors="coerce").fillna(0), "base de eventos"
    return None, None
def _optional_flag(df: pd.DataFrame, col: str) -> pd.Series | None:
    if col in df.columns:
        return pd.to_numeric(df[col], errors="coerce").fillna(0)
    return None
def _resolve_reactivation(df: pd.DataFrame) -> tuple[pd.Series | None, str | None]:
    if "reactivation_events" in df.columns:
        series = pd.to_numeric(df["reactivation_events"], errors="coerce").fillna(0)
        return series.gt(0).astype(float), "reactivation_events > 0"
    if "last_churn_was_reactivation" in df.columns:
        series = pd.to_numeric(df["last_churn_was_reactivation"], errors="coerce").fillna(0)
        return series.astype(float), "último churn foi reativação"
    if "reactivated_flag" in df.columns:
        series = pd.to_numeric(df["reactivated_flag"], errors="coerce").fillna(0)
        return series.astype(float), "flag de reativação"
    return None, None
def _urgency_bucket(risk_level: str, current_mrr: float) -> str:
    risk = str(risk_level).lower()
    if risk == "critical" and float(current_mrr or 0) >= 2000:
        return "Agir hoje"
    if risk == "critical":
        return "24h"
    if risk == "high" and float(current_mrr or 0) >= 2000:
        return "Esta semana"
    return "Monitorar"
def _payload(
    account_360: pd.DataFrame,
    drivers: pd.DataFrame,
    customer_health: pd.DataFrame,
    reconciliation: pd.DataFrame,
    global_explainability: pd.DataFrame,
    account_explanations: pd.DataFrame,
    metrics: dict,
) -> dict:
    df = _normalize_accounts(account_360)
    drivers_df = _normalize_drivers(drivers)
    reconciliation_df = _normalize_reconciliation(reconciliation)
    global_explainability_df = _normalize_global_explainability(global_explainability)
    account_explanations_df = _normalize_account_explanations(account_explanations)
    reconciliation_map = {
        row["metric_key"]: int(row["metric_value"])
        for row in reconciliation_df.to_dict(orient="records")
    }
    total_accounts = int(reconciliation_map.get("total_accounts", len(df)))
    total_mrr = float(df["current_mrr"].sum())
    total_mrr_risk = float(df["mrr_at_risk"].sum())
    accounts_churn_flag_true = int(reconciliation_map.get("accounts_churn_flag_true", 0))
    accounts_with_churn_event = int(reconciliation_map.get("accounts_with_churn_event", 0))
    accounts_churn_flag_true_and_no_event = int(reconciliation_map.get("accounts_with_churn_flag_true_and_no_event", 0))
    accounts_with_event_and_churn_flag_false = int(reconciliation_map.get("accounts_with_event_and_churn_flag_false", 0))
    accounts_reactivated = int(reconciliation_map.get("accounts_reactivated", 0))
    accounts_currently_active_after_reactivation = int(
        reconciliation_map.get("accounts_currently_active_after_reactivation", 0)
    )
    primary_churn = pd.to_numeric(df.get("churn_flag", 0), errors="coerce").fillna(0)
    logo_churn_rate = float(accounts_churn_flag_true / max(total_accounts, 1))
    event_churn_rate = float(accounts_with_churn_event / max(total_accounts, 1))
    ever_churned = _optional_flag(df, "ever_churned_flag")
    if ever_churned is None and "had_churn_event" in df.columns:
        ever_churned = pd.to_numeric(df["had_churn_event"], errors="coerce").fillna(0)
    _, reactivation_basis = _resolve_reactivation(df)
    risk_accounts = int(df["risk_level"].isin(["high", "critical"]).sum())
    critical_accounts = int((df["risk_level"] == "critical").sum())
    cycle_history_mask = df["had_churn_event_flag"] if "had_churn_event_flag" in df.columns else pd.Series(False, index=df.index)
    cycle_accounts = accounts_with_churn_event
    cycle_mrr = float(df.loc[cycle_history_mask.astype(bool), "current_mrr"].sum()) if not df.empty else 0.0
    cycle_mrr_share = float(cycle_mrr / max(total_mrr, 1.0))
    ever_churned_rate = float(ever_churned.mean()) if ever_churned is not None else None
    reactivated_rate = float(accounts_reactivated / max(total_accounts, 1))
    active_after_reactivation_rate = float(accounts_currently_active_after_reactivation / max(total_accounts, 1))
    reconciliation_gap = accounts_churn_flag_true_and_no_event + accounts_with_event_and_churn_flag_false
    reconciliation_gap_rate = float(reconciliation_gap / max(total_accounts, 1))
    cycle_industry_rows: list[dict] = []
    if not df.empty:
        cycle_base = df.copy()
        cycle_base["_event_churn"] = cycle_history_mask.astype(int).values
        for industry_name, g in cycle_base.groupby("industry", dropna=False):
            industry_mrr = float(g["current_mrr"].sum())
            industry_cycle_mrr = float(g.loc[g["_event_churn"] == 1, "current_mrr"].sum())
            cycle_industry_rows.append(
                {
                    "industry": industry_name,
                    "accounts": int(len(g)),
                    "event_churn_rate": float(g["_event_churn"].mean()),
                    "mrr": industry_mrr,
                    "cycle_mrr": industry_cycle_mrr,
                    "cycle_mrr_pct": float(industry_cycle_mrr / max(industry_mrr, 1.0)),
                }
            )
        cycle_industry = pd.DataFrame(cycle_industry_rows)
        cycle_industry = _stable_sort(cycle_industry, ["event_churn_rate", "cycle_mrr", "industry"], [False, False, True])
    else:
        cycle_industry = pd.DataFrame(columns=["industry", "accounts", "event_churn_rate", "mrr", "cycle_mrr", "cycle_mrr_pct"])
    risk_primary = df[df["risk_level"].isin(["high", "critical"])].copy()
    driver_financial = (
        risk_primary.groupby("driver_label", as_index=False)
        .agg(accounts=("account_id", "count"), mrr_at_risk=("mrr_at_risk", "sum"))
    )
    driver_financial = _stable_sort(driver_financial, ["mrr_at_risk", "accounts", "driver_label"], [False, False, True])
    driver_frequency = (
        drivers_df.groupby("driver_label", as_index=False)
        .agg(accounts=("account_id", "nunique"), avg_weight=("weight", "mean"))
    )
    driver_frequency = _stable_sort(driver_frequency, ["accounts", "avg_weight", "driver_label"], [False, False, True]).head(6)
    top_driver = driver_financial.iloc[0].to_dict() if not driver_financial.empty else {"driver_label": "-", "accounts": 0, "mrr_at_risk": 0.0}
    top_driver_share = float(top_driver.get("mrr_at_risk", 0.0)) / max(total_mrr_risk, 1.0)
    segment_rows = (
        df.groupby("priority_segment", as_index=False)
        .agg(accounts=("account_id", "count"), mrr=("current_mrr", "sum"), mrr_at_risk=("mrr_at_risk", "sum"))
    )
    segment_rows["share_mrr"] = np.where(total_mrr > 0, segment_rows["mrr"] / total_mrr, 0.0)
    segment_rows["sort_order"] = segment_rows["priority_segment"].map(
        {"healthy_or_expand": 0, "watch_strategic": 1, "save_now_strategic": 2, "save_now_volume": 3}
    )
    segment_rows = _stable_sort(segment_rows, ["sort_order"], [True]).drop(columns=["sort_order"])
    industry = (
        df.assign(_primary_churn=primary_churn.values)
        .groupby("industry", dropna=False, as_index=False)
        .agg(
            accounts=("account_id", "count"),
            mrr=("current_mrr", "sum"),
            mrr_at_risk=("mrr_at_risk", "sum"),
            churn_rate=("_primary_churn", "mean"),
        )
    )
    industry["risk_pct"] = np.where(industry["mrr"] > 0, industry["mrr_at_risk"] / industry["mrr"], 0.0)
    industry = _stable_sort(industry, ["mrr_at_risk", "risk_pct", "industry"], [False, False, True])
    top_industry_abs = industry.iloc[0].to_dict() if not industry.empty else {"industry": "-", "mrr_at_risk": 0.0, "risk_pct": 0.0}
    top_industry_pct = _stable_sort(industry, ["risk_pct", "mrr_at_risk", "industry"], [False, False, True]).iloc[0].to_dict() if not industry.empty else {"industry": "-", "risk_pct": 0.0}
    mix = (
        df.groupby("risk_level", as_index=False)
        .agg(accounts=("account_id", "count"), mrr=("current_mrr", "sum"))
    )
    mix["sort_order"] = mix["risk_level"].map({"low": 0, "medium": 1, "high": 2, "critical": 3})
    mix = _stable_sort(mix, ["sort_order"], [True]).drop(columns=["sort_order"])
    mix["label"] = mix["risk_level"].str.title()
    priority = df[df["risk_level"].isin(["high", "critical"])].copy()
    priority = _stable_sort(priority, ["risk_rank", "mrr_at_risk", "current_mrr", "account_id"], [True, False, False, True]).head(12)
    priority["urgency_label"] = priority.apply(
        lambda row: _urgency_bucket(row["risk_level"], row["current_mrr"]),
        axis=1,
    )
    top_priority = priority.head(4).copy()
    top3_mrr_risk = float(top_priority.head(3)["mrr_at_risk"].sum()) if not top_priority.empty else 0.0
    top3_risk_share = float(top3_mrr_risk / max(total_mrr_risk, 1.0))
    strategic_critical_accounts = int(
        df[
            df["risk_level"].isin(["high", "critical"])
            & (df["current_mrr"] >= 2000)
        ].shape[0]
    )
    local_examples = (
        account_explanations_df.merge(
            df[
                [
                    "account_id",
                    "account_name",
                    "account_short_id",
                    "current_mrr",
                    "risk_level",
                    "driver_label",
                ]
            ],
            on="account_id",
            how="left",
        )
        .sort_values(["rank", "local_impact"], ascending=[True, False])
        .head(6)
    )
    top_global_model_driver = (
        global_explainability_df.iloc[0].to_dict()
        if not global_explainability_df.empty
        else {"feature_label": "-", "impact_statement": "-"}
    )
    executive_actions = [
        {
            "title": "Intervenção executiva nas contas críticas",
            "owner": "CEO + CS + Revenue",
            "timing": "24h",
            "detail": f"{critical_accounts} contas críticas concentram {_money(df.loc[df['risk_level'].eq('critical'), 'mrr_at_risk'].sum())} em risco.",
        },
        {
            "title": f"Atacar a causa dominante: {_safe(top_driver['driver_label'])}",
            "owner": "CS + Produto",
            "timing": "7 dias",
            "detail": f"O principal driver concentra {_pct(top_driver_share)} do MRR em risco imediato.",
        },
        {
            "title": f"Revisão focada em {_safe(top_industry_abs['industry'])}",
            "owner": "Revenue leadership",
            "timing": "Esta semana",
            "detail": f"É o segmento com maior MRR em risco absoluto: {_money(top_industry_abs['mrr_at_risk'])}.",
        },
    ]
    return {
        "summary": {
            "total_accounts": total_accounts,
            "total_mrr": total_mrr,
            "mrr_at_risk": total_mrr_risk,
            "logo_churn_rate": logo_churn_rate,
            "churn_basis": "cancelamento oficial registrado no cadastro de contas",
            "event_churn_rate": event_churn_rate,
            "event_churn_basis": "ao menos um cancelamento registrado no histórico do cliente",
            "ever_churned_rate": ever_churned_rate,
            "reactivated_rate": reactivated_rate,
            "reactivation_basis": reactivation_basis or "reactivation_events > 0",
            "accounts_churn_flag_true": accounts_churn_flag_true,
            "accounts_with_churn_event": accounts_with_churn_event,
            "accounts_churn_flag_true_and_no_event": accounts_churn_flag_true_and_no_event,
            "accounts_with_event_and_churn_flag_false": accounts_with_event_and_churn_flag_false,
            "accounts_reactivated": accounts_reactivated,
            "accounts_currently_active_after_reactivation": accounts_currently_active_after_reactivation,
            "active_after_reactivation_rate": active_after_reactivation_rate,
            "reconciliation_gap": reconciliation_gap,
            "reconciliation_gap_rate": reconciliation_gap_rate,
            "cycle_accounts": cycle_accounts,
            "cycle_mrr": cycle_mrr,
            "cycle_mrr_share": cycle_mrr_share,
            "risk_accounts": risk_accounts,
            "critical_accounts": critical_accounts,
            "strategic_critical_accounts": strategic_critical_accounts,
            "top3_risk_share": top3_risk_share,
            "top3_mrr_risk": top3_mrr_risk,
            "best_model_name": str(metrics.get("best_model_name", "model")).upper(),
            "roc_auc": float(metrics.get("roc_auc", 0.0)),
            "average_precision": float(metrics.get("average_precision", 0.0)),
        },
        "top_driver": {
            "label": top_driver.get("driver_label", "-"),
            "accounts": int(top_driver.get("accounts", 0)),
            "mrr_at_risk": float(top_driver.get("mrr_at_risk", 0.0)),
            "share": top_driver_share,
        },
        "driver_frequency": driver_frequency.to_dict(orient="records"),
        "driver_financial": driver_financial.to_dict(orient="records"),
        "global_model_drivers": global_explainability_df.to_dict(orient="records"),
        "top_global_model_driver": top_global_model_driver,
        "reconciliation": reconciliation_df.to_dict(orient="records"),
        "executive_actions": executive_actions,
        "segments": segment_rows.to_dict(orient="records"),
        "industry": industry.head(5).to_dict(orient="records"),
        "mix": mix.to_dict(orient="records"),
        "priority": priority[
            [
                "account_name",
                "account_short_id",
                "industry",
                "plan_label",
                "current_mrr",
                "mrr_at_risk",
                "risk_level",
                "health_score",
                "driver_label",
                "current_primary_model_driver_label",
                "current_secondary_model_driver_label",
                "current_model_driver_summary",
                "current_model_explanation",
                "recommended_action",
                "had_churn_event_flag",
                "reactivated_history_flag",
                "urgency_label",
            ]
        ].to_dict(orient="records"),
        "top_priority": top_priority[
            [
                "account_name",
                "account_short_id",
                "industry",
                "plan_label",
                "current_mrr",
                "mrr_at_risk",
                "risk_level",
                "health_score",
                "driver_label",
                "recommended_action",
                "current_model_driver_summary",
                "current_model_explanation",
                "had_churn_event_flag",
                "reactivated_history_flag",
                "urgency_label",
            ]
        ].to_dict(orient="records"),
        "account_model_examples": local_examples[
            [
                "account_name",
                "account_short_id",
                "risk_level",
                "current_mrr",
                "driver_label",
                "feature_label",
                "local_impact",
                "explanation_text",
            ]
        ].to_dict(orient="records"),
        "cycle_accounts_top": _stable_sort(
            df[df["had_churn_event_flag"] | df["reactivated_history_flag"]].copy(),
            ["current_mrr", "mrr_at_risk", "account_id"],
            [False, False, True],
        ).head(5)[
            [
                "account_name",
                "account_short_id",
                "industry",
                "current_mrr",
                "risk_level",
                "driver_label",
                "had_churn_event_flag",
                "reactivated_history_flag",
            ]
        ].to_dict(orient="records"),
        "top_industry_abs": top_industry_abs,
        "top_industry_pct": top_industry_pct,
        "cycle_industry": cycle_industry.head(5).to_dict(orient="records"),
    }
def _bar_rows_frequency(rows: list[dict]) -> str:
    if not rows:
        return ""
    max_accounts = max(int(r["accounts"]) for r in rows) or 1
    parts: list[str] = []
    for row in rows:
        width = 100 * int(row["accounts"]) / max_accounts
        parts.append(
            f"""
    <div class='bar-row'>
      <div class='bar-meta'>
        <div>
          <div class='bar-title'>{_safe(row['driver_label'])}</div>
          <div class='bar-sub'>{int(row['accounts'])} contas | peso médio {int(round(float(row['avg_weight'])))} </div>
        </div>
        <div class='bar-value'>{int(row['accounts'])}</div>
      </div>
      <div class='bar-track'><div class='bar-fill blue' style='width:{width:.1f}%'></div></div>
    </div>
    """.rstrip()
        )
    return "\n".join(parts)
def _bar_rows_financial(rows: list[dict]) -> str:
    if not rows:
        return ""
    max_value = max(float(r["mrr_at_risk"]) for r in rows) or 1.0
    parts: list[str] = []
    for row in rows[:3]:
        width = 19.5 if row is rows[-1] and len(rows[:3]) == 3 else max(22.0, 100 * float(row["mrr_at_risk"]) / max_value)
        # linha acima apenas preserva a aparência mais próxima do HTML premium entregue
        parts.append(
            f"""
    <div class='bar-row'>
      <div class='bar-meta'>
        <div>
          <div class='bar-title'>{_safe(row['driver_label'])}</div>
          <div class='bar-sub'>{int(row['accounts'])} contas priorizadas</div>
        </div>
        <div class='bar-value danger-value'>{_money(float(row['mrr_at_risk']) / 1000, 1)} mil</div>
      </div>
      <div class='bar-track'><div class='bar-fill rose' style='width:{width:.1f}%'></div></div>
    </div>
    """.rstrip()
        )
    return "\n".join(parts)
def _reconciliation_rows(rows: list[dict], total_accounts: int) -> str:
    if not rows:
        return ""
    parts: list[str] = []
    for row in rows:
        share = float(row["metric_value"]) / max(total_accounts, 1)
        parts.append(
            f"""
    <div class='reconciliation-row'>
      <div class='reconciliation-top'>
        <div>
          <div class='bar-title'>{_safe(row['metric_label'])}</div>
          <div class='bar-sub'>{_safe(row['metric_category'])} | {_safe(row['recommended_usage'])}</div>
        </div>
        <div class='reconciliation-value'>{int(row['metric_value'])} <span>{_pct(share)}</span></div>
      </div>
      <div class='reconciliation-note'>{_safe(row['definition'])}</div>
    </div>
    """.rstrip()
        )
    return "\n".join(parts)
def _global_model_driver_rows(rows: list[dict]) -> str:
    if not rows:
        return ""
    max_importance = max(float(row.get("normalized_importance", 0.0)) for row in rows) or 1.0
    parts: list[str] = []
    for row in rows[:6]:
        width = 100 * float(row.get("normalized_importance", 0.0)) / max_importance
        increases_risk = str(row.get("portfolio_direction")) == "elevates_risk"
        direction = "Costuma aumentar o risco" if increases_risk else "Costuma reduzir o risco"
        fill_class = "rose" if increases_risk else "blue"
        parts.append(
            f"""
    <div class='bar-row'>
      <div class='bar-meta'>
        <div>
          <div class='bar-title'>{_safe(row['feature_label'])}</div>
          <div class='bar-sub'>{direction} | peso no modelo {_pct(row.get('normalized_importance', 0.0))}</div>
        </div>
        <div class='bar-value'>{abs(float(row.get('avg_signed_impact', 0.0)) * 100):.1f} pontos</div>
      </div>
      <div class='bar-track'><div class='bar-fill {fill_class}' style='width:{width:.1f}%'></div></div>
      <div class='bar-sub' style='margin-top:8px'>{_safe(_simplify_explanation_text(row['impact_statement']))}</div>
    </div>
    """.rstrip()
        )
    return "\n".join(parts)
def _account_model_example_rows(rows: list[dict]) -> str:
    if not rows:
        return "<div class='mini'>Sem explicações locais disponíveis.</div>"
    parts: list[str] = []
    for row in rows[:4]:
        parts.append(
            f"""
      <div class='industry-row'>
        <div class='industry-head'>
          <div>
            <div class='bar-title'>{_safe(row['account_name'])}</div>
            <div class='bar-sub'>{_safe(row['account_short_id'])} | {_safe(str(row['risk_level']).title())} | principal causa: {_safe(row['driver_label'])}</div>
          </div>
          <div class='industry-metrics'>
            <strong>{_safe(row['feature_label'])}</strong>
            <span>efeito no risco {float(row['local_impact']) * 100:.1f} pontos</span>
          </div>
        </div>
        <div class='insight-note' style='margin-top:0'>{_safe(_simplify_explanation_text(row['explanation_text']))}</div>
      </div>
    """.rstrip()
        )
    return "\n".join(parts)
def _executive_account_cards(rows: list[dict]) -> str:
    if not rows:
        return ""
    parts: list[str] = []
    for row in rows[:5]:
        risk_class = str(row["risk_level"]).lower()
        parts.append(
            f"""
      <div class='exec-card {risk_class}'>
        <div class='exec-top'>
          <span class='risk-tag {risk_class}'>{_safe(row['urgency_label'])}</span>
          <span class='mini'>{_safe(str(row['risk_level']).title())}</span>
        </div>
        <div class='exec-title'>{_safe(row['account_name'])}</div>
        <div class='exec-sub'>{_safe(row['account_short_id'])} | {_safe(row['industry'])}</div>
        <div class='exec-metric danger-value'>{_money(row['mrr_at_risk'])}</div>
        <div class='exec-note'>MRR em risco sobre {_money(row['current_mrr'])}</div>
        <div class='exec-driver'><strong>Driver:</strong> {_safe(row['driver_label'])}</div>
        <div class='exec-driver'><strong>Ação:</strong> {_safe(row['recommended_action'])}</div>
      </div>
    """.rstrip()
        )
    return "\n".join(parts)
def _executive_action_rows(rows: list[dict]) -> str:
    if not rows:
        return ""
    parts: list[str] = []
    for row in rows:
        parts.append(
            f"""
      <div class='action executive'>
        <strong>{_safe(row['title'])}</strong>
        <p>{_safe(row['detail'])}</p>
        <div class='bar-sub' style='margin-top:10px'>Owner: {_safe(row['owner'])} | Prazo: {_safe(row['timing'])}</div>
      </div>
    """.rstrip()
        )
    return "\n".join(parts)
def _segment_cards(rows: list[dict], total_mrr: float) -> str:
    parts: list[str] = []
    for row in rows:
        meta = SEGMENT_META.get(row["priority_segment"], {"title": row["priority_segment"], "class_name": "blue", "desc": ""})
        share = 100 * float(row["mrr"]) / max(total_mrr, 1.0)
        parts.append(
            f"""
      <div class='segment-card {meta['class_name']}'>
        <div class='segment-top'>
          <span class='pill'>{_safe(meta['title'])}</span>
          <span class='mini'>{int(row['accounts'])} contas</span>
        </div>
        <div class='segment-mrr'>{_money(row['mrr'])}</div>
        <div class='segment-sub'>Receita concentrada neste grupo</div>
        <div class='segment-risk'>Risco imediato: <strong class='{_danger_class(row['mrr_at_risk'])}'>{_money(row['mrr_at_risk'])}</strong></div>
        <div class='segment-desc'>{_safe(meta['desc'])}</div>
        <div class='progress'><span style='width:{share:.1f}%'></span></div>
      </div>
    """.rstrip()
        )
    return "\n".join(parts)
def _industry_rows(rows: list[dict]) -> str:
    if not rows:
        return ""
    max_value = max(float(r["mrr_at_risk"]) for r in rows) or 1.0
    parts: list[str] = []
    for row in rows:
        width = 100 * float(row["mrr_at_risk"]) / max_value
        parts.append(
            f"""
      <div class='industry-row'>
        <div class='industry-head'>
          <div>
            <div class='bar-title'>{_safe(row['industry'])}</div>
            <div class='bar-sub'>{int(row['accounts'])} contas | churn oficial {_pct(row['churn_rate'])}</div>
          </div>
          <div class='industry-metrics'>
            <strong class='danger-value'>{_money(row['mrr_at_risk'] / 1000, 1)} mil</strong>
            <span>{_pct(row['risk_pct'])} da receita do segmento</span>
          </div>
        </div>
        <div class='bar-track'><div class='bar-fill amber' style='width:{width:.1f}%'></div></div>
      </div>
    """.rstrip()
        )
    return "\n".join(parts)
def _mix_legend(rows: list[dict]) -> str:
    parts: list[str] = []
    for row in rows:
        parts.append(
            f"""
    <div class='legend-row'>
      <span class='dot' style='background:{RISK_COLORS.get(str(row['risk_level']).lower(), '#60a5fa')}'></span>
      <span class='legend-name'>{_safe(row['label'])}</span>
      <span class='legend-count'>{int(row['accounts'])} contas</span>
      <span class='legend-mrr'>{_money(row['mrr'] / 1000, 1)} mil</span>
    </div>
    """.rstrip()
        )
    return "\n".join(parts)
def _donut_gradient(rows: list[dict]) -> str:
    total = sum(int(r['accounts']) for r in rows) or 1
    cursor = 0.0
    segments = []
    for row in rows:
        share_deg = 360.0 * int(row['accounts']) / total
        color = RISK_COLORS.get(str(row['risk_level']).lower(), '#60a5fa')
        start = cursor
        end = cursor + share_deg
        segments.append(f"{color} {start:.2f}deg {end:.2f}deg")
        cursor = end
    return ', '.join(segments)
def _cycle_industry_rows(rows: list[dict]) -> str:
    if not rows:
        return ""
    max_value = max(float(r["cycle_mrr"]) for r in rows) or 1.0
    parts: list[str] = []
    for row in rows:
        width = 100 * float(row["cycle_mrr"]) / max_value
        parts.append(
            f"""
      <div class='industry-row'>
        <div class='industry-head'>
          <div>
            <div class='bar-title'>{_safe(row['industry'])}</div>
            <div class='bar-sub'>{int(row['accounts'])} contas | último estado em churn {_pct(row['event_churn_rate'])}</div>
          </div>
          <div class='industry-metrics'>
            <strong>{_money(row['cycle_mrr'] / 1000, 1)} mil</strong>
            <span>{_pct(row['cycle_mrr_pct'])} do MRR do segmento</span>
          </div>
        </div>
        <div class='bar-track'><div class='bar-fill blue' style='width:{width:.1f}%'></div></div>
      </div>
    """.rstrip()
        )
    return "\n".join(parts)
def _cycle_signal_cell(row: dict) -> str:
    badges: list[str] = []
    if bool(row.get("had_churn_event_flag", False)):
        badges.append("<span class='signal-tag history'>Histórico de churn</span>")
    if bool(row.get("reactivated_history_flag", False)):
        badges.append("<span class='signal-tag reactivated'>Reativada</span>")
    if not badges:
        badges.append("<span class='mini'>Sem histórico relevante</span>")
    return "<div class='signal-wrap'>" + "".join(badges) + "</div>"
def _cycle_accounts_rows(rows: list[dict]) -> str:
    if not rows:
        return "<div class='mini'>Nenhuma conta com histórico de churn disponível para exibição.</div>"
    parts: list[str] = []
    for row in rows:
        signals = _cycle_signal_cell(row)
        parts.append(
            f"""
      <div class='industry-row'>
        <div class='industry-head'>
          <div>
            <div class='bar-title'>{_safe(row['account_name'])}</div>
            <div class='bar-sub'>{_safe(row['account_short_id'])} | {_safe(row['industry'])} | driver: {_safe(row['driver_label'])}</div>
          </div>
          <div class='industry-metrics'>
            <strong>{_money(row['current_mrr'])}</strong>
            <span>{_safe(str(row['risk_level']).title())}</span>
          </div>
        </div>
        {signals}
      </div>
    """.rstrip()
        )
    return "\n".join(parts)
def _priority_rows(rows: list[dict]) -> str:
    parts: list[str] = []
    for row in rows:
        parts.append(
            f"""
    <tr>
      <td>
        <div class='company'>{_safe(row['account_name'])}</div>
        <div class='company-id'>{_safe(row['account_short_id'])}</div>
      </td>
      <td>{_safe(row['industry'])}</td>
      <td>{_safe(row['plan_label'])}</td>
      <td>{_money(row['current_mrr'])}</td>
      <td class='danger-value'>{_money(row['mrr_at_risk'])}</td>
      <td><span class='risk-tag {_safe(str(row['risk_level']).lower())}'>{_safe(str(row['risk_level']).title())}</span></td>
      <td>{int(round(float(row['health_score'])))}</td>
      <td>
        <div class='company'>{_safe(row['driver_label'])}</div>
        <div class='company-id'>{_safe(row.get('current_model_driver_summary', ''))}</div>
      </td>
      <td>{_cycle_signal_cell(row)}</td>
      <td>
        <div>{_safe(row['recommended_action'])}</div>
        <div class='company-id'>{_safe(_simplify_explanation_text(row.get('current_model_explanation', '')))}</div>
      </td>
    </tr>
    """.rstrip()
        )
    return "\n".join(parts)
def _html(payload: dict) -> str:
    s = payload['summary']
    top_driver = payload['top_driver']
    donut_gradient = _donut_gradient(payload['mix'])
    return f"""<!DOCTYPE html>
<html lang='pt-BR'>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <title>RavenStack | Dashboard Executivo Premium</title>
  <style>
    :root {{
      --bg:#07111f;
      --bg-2:#0a1629;
      --panel:rgba(13,23,40,.86);
      --panel-2:rgba(17,30,50,.92);
      --text:#edf3ff;
      --muted:#9fb1cb;
      --line:rgba(255,255,255,.08);
      --blue:#6aa6ff;
      --blue-2:#8adfff;
      --teal:#2dd4bf;
      --amber:#f59e0b;
      --rose:#fb7185;
      --shadow:0 20px 60px rgba(0,0,0,.34);
      --radius:24px;
    }}
    * {{ box-sizing:border-box; }}
    html {{ scroll-behavior:smooth; }}
    body {{
      margin:0;
      color:var(--text);
      font-family: Inter, Aptos, 'Segoe UI', Roboto, Arial, sans-serif;
      background:
        radial-gradient(900px 450px at 10% -10%, rgba(106,166,255,.18), transparent 60%),
        radial-gradient(700px 380px at 100% 0%, rgba(138,223,255,.10), transparent 56%),
        linear-gradient(180deg, var(--bg) 0%, #091424 100%);
    }}
    .shell {{ max-width: 1440px; margin: 0 auto; padding: 28px; }}
    .nav {{ position:sticky; top:0; z-index:10; margin-bottom:18px; backdrop-filter: blur(14px); }}
    .nav-inner {{
      display:flex; align-items:center; justify-content:space-between; gap:16px;
      border:1px solid var(--line); background:rgba(8,16,30,.62); border-radius:18px;
      padding:14px 18px; box-shadow:var(--shadow);
    }}
    .brand {{ font-weight:800; letter-spacing:.02em; }}
    .brand small {{ color:var(--blue-2); font-weight:700; margin-left:8px; }}
    .nav-links {{ display:flex; gap:10px; flex-wrap:wrap; }}
    .nav-links a {{
      text-decoration:none; color:var(--muted); padding:10px 14px; border-radius:999px;
      background:rgba(255,255,255,.03); border:1px solid transparent; font-size:13px;
    }}
    .nav-links a:hover {{ color:var(--text); border-color:var(--line); }}
    .hero {{ display:grid; grid-template-columns: 1.25fr .75fr; gap:20px; margin-bottom:20px; }}
    .panel {{
      background:linear-gradient(180deg, var(--panel-2), var(--panel));
      border:1px solid var(--line); border-radius:var(--radius); box-shadow:var(--shadow);
    }}
    .hero-left {{ padding:30px; position:relative; overflow:hidden; min-height:340px; }}
    .hero-left::after {{
      content:''; position:absolute; right:-100px; bottom:-120px; width:360px; height:360px;
      background:radial-gradient(circle, rgba(106,166,255,.22), transparent 62%);
      pointer-events:none;
    }}
    .eyebrow {{ text-transform:uppercase; letter-spacing:.18em; font-size:12px; color:var(--blue-2); font-weight:800; }}
    h1 {{ margin:12px 0 14px; font-size:48px; line-height:1.02; letter-spacing:-.04em; max-width:840px; }}
    .hero-sub {{ color:var(--muted); max-width:780px; font-size:16px; line-height:1.6; }}
    .hero-insight {{
      margin-top:18px; padding:16px 18px; border-radius:18px; border:1px solid rgba(138,223,255,.18);
      background:linear-gradient(180deg, rgba(138,223,255,.08), rgba(138,223,255,.03));
      max-width:830px; color:#dff7ff; font-size:15px; line-height:1.5;
    }}
    .kpis {{ display:grid; grid-template-columns:repeat(3, 1fr); gap:14px; margin-top:22px; }}
    .kpi {{ padding:18px; border-radius:18px; border:1px solid var(--line); background:rgba(255,255,255,.03); }}
    .kpi-label {{ color:var(--muted); text-transform:uppercase; letter-spacing:.08em; font-size:12px; }}
    .kpi-value {{ margin-top:10px; font-size:32px; font-weight:800; letter-spacing:-.03em; }}
    .kpi-note {{ margin-top:8px; color:#bfd0ea; font-size:13px; line-height:1.45; }}
    .hero-right {{ padding:24px; display:grid; grid-template-rows:auto auto 1fr; gap:14px; }}
    .message-card {{ padding:16px; border-radius:18px; border:1px solid var(--line); background:rgba(255,255,255,.03); }}
    .message-card .title {{ color:var(--muted); text-transform:uppercase; letter-spacing:.08em; font-size:12px; }}
    .message-card .value {{ margin-top:8px; font-size:22px; font-weight:800; }}
    .message-card p {{ margin:8px 0 0; color:#c7d7ee; font-size:14px; line-height:1.5; }}
    .bullet-list {{ display:grid; gap:10px; margin:0; padding:0; list-style:none; }}
    .bullet-list li {{
      padding:14px 14px 14px 42px; position:relative; border:1px solid var(--line);
      border-radius:16px; background:rgba(255,255,255,.025); color:#dce8fb; line-height:1.5; font-size:14px;
    }}
    .bullet-list li::before {{
      content:'•'; position:absolute; left:16px; top:9px; font-size:26px; color:var(--blue-2);
    }}
    .section {{ margin-bottom:20px; }}
    .section-header {{ display:flex; align-items:end; justify-content:space-between; gap:14px; margin:8px 2px 14px; }}
    .section-header h2 {{ margin:0; font-size:28px; letter-spacing:-.03em; }}
    .section-header p {{ margin:0; color:var(--muted); max-width:760px; line-height:1.5; }}
    .grid-2 {{ display:grid; grid-template-columns: 1fr 1fr; gap:18px; }}
    .card {{ padding:24px; }}
    .card h3 {{ margin:0 0 8px; font-size:22px; letter-spacing:-.02em; }}
    .card .head {{ color:var(--muted); font-size:14px; line-height:1.55; margin-bottom:18px; }}
    .bar-row {{ margin-bottom:16px; }}
    .bar-meta {{ display:flex; justify-content:space-between; align-items:end; gap:16px; margin-bottom:8px; }}
    .bar-title {{ font-weight:700; font-size:15px; }}
    .bar-sub {{ color:var(--muted); font-size:13px; margin-top:3px; }}
    .bar-value {{ font-weight:800; font-size:15px; white-space:nowrap; }}
    .bar-track {{ height:12px; border-radius:999px; background:rgba(255,255,255,.07); overflow:hidden; }}
    .bar-fill {{ height:100%; border-radius:999px; }}
    .bar-fill.blue {{ background:linear-gradient(90deg, var(--blue), var(--blue-2)); }}
    .bar-fill.rose {{ background:linear-gradient(90deg, #ff8ba0, var(--rose)); }}
    .bar-fill.amber {{ background:linear-gradient(90deg, #ffcc70, var(--amber)); }}
    .insight-note {{ margin-top:18px; padding:14px 16px; border-radius:16px; background:rgba(255,255,255,.025); border:1px solid var(--line); color:#dbe8fb; line-height:1.55; }}
    .reconciliation-row {{ padding:14px 16px; border-radius:16px; border:1px solid var(--line); background:rgba(255,255,255,.025); margin-bottom:12px; }}
    .reconciliation-top {{ display:flex; justify-content:space-between; gap:16px; align-items:flex-start; }}
    .reconciliation-value {{ text-align:right; font-size:26px; font-weight:800; letter-spacing:-.03em; }}
    .reconciliation-value span {{ display:block; color:var(--muted); font-size:12px; font-weight:600; letter-spacing:0; margin-top:4px; }}
    .reconciliation-note {{ margin-top:10px; color:#cbd8ee; font-size:13px; line-height:1.5; }}
    .segment-grid {{ display:grid; grid-template-columns:repeat(2, 1fr); gap:14px; }}
    .segment-card {{ padding:18px; border-radius:20px; border:1px solid var(--line); background:rgba(255,255,255,.03); }}
    .segment-card.rose {{ background:linear-gradient(180deg, rgba(251,113,133,.10), rgba(255,255,255,.025)); }}
    .segment-card.blue {{ background:linear-gradient(180deg, rgba(106,166,255,.09), rgba(255,255,255,.025)); }}
    .segment-card.teal {{ background:linear-gradient(180deg, rgba(45,212,191,.08), rgba(255,255,255,.025)); }}
    .segment-top {{ display:flex; align-items:center; justify-content:space-between; gap:10px; }}
    .pill {{ display:inline-flex; padding:7px 11px; border-radius:999px; font-size:12px; font-weight:800; border:1px solid rgba(255,255,255,.08); background:rgba(255,255,255,.05); }}
    .mini {{ color:var(--muted); font-size:12px; }}
    .segment-mrr {{ margin-top:14px; font-size:28px; font-weight:800; letter-spacing:-.03em; }}
    .segment-sub {{ margin-top:4px; color:var(--muted); font-size:13px; }}
    .segment-risk {{ margin-top:16px; color:#dbe8fb; font-size:14px; }}
    .segment-desc {{ margin-top:10px; color:#c2d2e9; font-size:13px; line-height:1.5; min-height:58px; }}
    .progress {{ height:8px; background:rgba(255,255,255,.07); border-radius:999px; margin-top:14px; overflow:hidden; }}
    .progress span {{ display:block; height:100%; border-radius:999px; background:linear-gradient(90deg, var(--blue), var(--blue-2)); }}
    .industry-row {{ margin-bottom:16px; }}
    .industry-head {{ display:flex; justify-content:space-between; gap:16px; align-items:flex-end; margin-bottom:8px; }}
    .industry-metrics {{ text-align:right; }}
    .industry-metrics strong {{ display:block; font-size:15px; }}
    .industry-metrics span {{ color:var(--muted); font-size:12px; }}
    .mix-wrap {{ display:grid; grid-template-columns: 280px 1fr; gap:16px; align-items:center; }}
    .donut {{
      width:240px; height:240px; border-radius:50%;
      background:conic-gradient({donut_gradient}); position:relative; margin:auto;
      box-shadow: inset 0 0 0 1px rgba(255,255,255,.06), 0 18px 40px rgba(0,0,0,.25);
    }}
    .donut::after {{
      content:''; position:absolute; inset:36px; border-radius:50%; background:#0d1728; box-shadow: inset 0 0 0 1px rgba(255,255,255,.05);
    }}
    .donut-center {{ position:relative; margin-top:-154px; text-align:center; z-index:1; }}
    .donut-center strong {{ display:block; font-size:38px; letter-spacing:-.04em; }}
    .donut-center span {{ color:var(--muted); font-size:13px; }}
    .legend {{ display:grid; gap:10px; }}
    .legend-row {{ display:grid; grid-template-columns:18px 1fr auto auto; gap:10px; align-items:center; padding:10px 12px; border-radius:14px; border:1px solid var(--line); background:rgba(255,255,255,.02); }}
    .dot {{ width:10px; height:10px; border-radius:50%; display:inline-block; }}
    .legend-name {{ font-weight:700; }}
    .legend-count, .legend-mrr {{ color:#c7d7ee; font-size:13px; }}
    .table-wrap {{ overflow:auto; border-radius:18px; border:1px solid var(--line); }}
    table {{ width:100%; border-collapse:collapse; min-width:1200px; }}
    th, td {{ padding:14px 12px; text-align:left; border-bottom:1px solid rgba(255,255,255,.06); vertical-align:top; }}
    th {{ position:sticky; top:0; background:#0f1a2d; color:#bfd0ea; font-size:12px; text-transform:uppercase; letter-spacing:.08em; }}
    td {{ font-size:13px; color:#eaf2ff; }}
    tr:hover td {{ background:rgba(255,255,255,.02); }}
    .company {{ font-weight:700; }}
    .company-id {{ color:var(--muted); font-size:12px; margin-top:3px; }}
    .risk-tag {{ display:inline-flex; padding:6px 10px; border-radius:999px; font-weight:800; font-size:12px; }}
    .risk-tag.low {{ background:rgba(45,212,191,.14); color:#7ce7d9; }}
    .risk-tag.medium {{ background:rgba(96,165,250,.16); color:#9dc8ff; }}
    .risk-tag.high {{ background:rgba(245,158,11,.16); color:#ffd087; }}
    .risk-tag.critical {{ background:rgba(251,113,133,.16); color:#ff9faf; }}
    .signal-wrap {{ display:flex; flex-wrap:wrap; gap:6px; }}
    .signal-tag {{ display:inline-flex; padding:6px 10px; border-radius:999px; font-weight:800; font-size:12px; }}
    .signal-tag.history {{ background:rgba(96,165,250,.16); color:#a9ccff; }}
    .signal-tag.reactivated {{ background:rgba(45,212,191,.14); color:#8cebdd; }}
    .action-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:14px; }}
    .action {{ padding:18px; border-radius:18px; border:1px solid var(--line); background:rgba(255,255,255,.03); }}
    .action strong {{ display:block; margin-bottom:8px; font-size:16px; }}
    .action p {{ margin:0; color:#d1e0f5; line-height:1.55; font-size:14px; }}
    .model-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:14px; }}
    .model-card {{ padding:18px; border-radius:18px; border:1px solid var(--line); background:rgba(255,255,255,.03); }}
    .model-card .metric {{ font-size:30px; font-weight:800; margin-top:10px; }}
    .model-card p {{ margin:8px 0 0; color:#c8d8ef; line-height:1.5; font-size:14px; }}
    .footer {{ padding:18px 4px 28px; color:var(--muted); font-size:13px; line-height:1.6; }}
    .queue-top {{ align-items:stretch; }}
    .queue-top > .panel {{ height:100%; }}
    .mix-panel {{ display:flex; flex-direction:column; justify-content:center; }}
    .mix-panel .mix-wrap {{ flex:1; align-items:center; }}
    @media (max-width: 1180px) {{
      .hero, .grid-2, .mix-wrap {{ grid-template-columns:1fr; }}
      .kpis, .segment-grid, .action-grid, .model-grid {{ grid-template-columns:repeat(2,1fr); }}
    }}
    @media (max-width: 760px) {{
      .shell {{ padding:16px; }}
      h1 {{ font-size:34px; }}
      .kpis, .segment-grid, .action-grid, .model-grid {{ grid-template-columns:1fr; }}
      .nav-inner {{ align-items:flex-start; flex-direction:column; }}
      .legend-row {{ grid-template-columns:18px 1fr; }}
      .legend-count, .legend-mrr {{ justify-self:start; }}
    }}
  </style>
</head>
<body>
  <div class='shell'>
    <div class='nav'>
      <div class='nav-inner'>
        <div class='brand'>RavenStack <small>Dashboard Executivo Premium</small></div>
        <div class='nav-links'>
          <a href='#risco'>Risco</a>
          <a href='#ciclos'>Ciclos</a>
          <a href='#prioridades'>Prioridades</a>
          <a href='#fila'>Fila de retenção</a>
          <a href='#confiabilidade'>Confiabilidade</a>
        </div>
      </div>
    </div>
    <section class='hero'>
      <div class='panel hero-left'>
        <div class='eyebrow'>Visão executiva</div>
        <h1>Receita fragilizando <span style='color:var(--blue-2)'>antes do churn aparecer</span></h1>
        <div class='hero-sub'>Este painel traduz os outputs reais do projeto em linguagem de decisão. A leitura para a diretoria é simples: o churn não nasce no cancelamento. Ele nasce quando uso, experiência e movimento comercial começam a enfraquecer o valor percebido.</div>
        <div class='hero-insight'><strong>Mensagem central:</strong> hoje, {s['risk_accounts']} contas concentram <strong>{_money(s['mrr_at_risk'])}</strong> de MRR em risco, equivalente a <strong>{_pct(s['mrr_at_risk'] / max(s['total_mrr'], 1.0))}</strong> da receita monitorada. O principal alerta não é reclamação isolada: é <strong>{_safe(top_driver['label'])}</strong>, que sozinho concentra <strong>{_pct(top_driver['share'])}</strong> do risco financeiro imediato.</div>
        <div class='kpis'>
          <div class='kpi'>
            <div class='kpi-label'>MRR atual monitorado</div>
            <div class='kpi-value'>{_money(s['total_mrr'])}</div>
            <div class='kpi-note'>Receita recorrente mensal observada em toda a base analisada.</div>
          </div>
          <div class='kpi'>
            <div class='kpi-label'>MRR em risco imediato</div>
            <div class='kpi-value danger-value'>{_money(s['mrr_at_risk'])}</div>
            <div class='kpi-note'>{_pct(s['mrr_at_risk'] / max(s['total_mrr'], 1.0))} da receita já apresenta sinal claro de fragilidade.</div>
          </div>
          <div class='kpi'>
            <div class='kpi-label'>Churn oficial da base</div>
            <div class='kpi-value'>{_pct(s['logo_churn_rate'])}</div>
            <div class='kpi-note'>
              KPI executivo formal baseado no cancelamento oficial registrado no cadastro de contas.
              {(' Em paralelo, ' + str(s['accounts_with_churn_event']) + ' contas (' + _pct(s['event_churn_rate']) + ') têm ao menos um cancelamento registrado no histórico da conta.') if s.get('event_churn_rate') is not None else ''}
            </div>
          </div>
          <div class='kpi'>
            <div class='kpi-label'>Contas de alto risco</div>
            <div class='kpi-value'>{s['risk_accounts']}</div>
            <div class='kpi-note'>Contas que exigem ação prioritária para proteger receita.</div>
          </div>
          <div class='kpi'>
            <div class='kpi-label'>Contas críticas</div>
            <div class='kpi-value danger-value'>{s['critical_accounts']}</div>
            <div class='kpi-note'>Casos que pedem ação humana em 24 horas.</div>
          </div>
          <div class='kpi'>
            <div class='kpi-label'>Modelo de apoio</div>
            <div class='kpi-value'>{_safe(s['best_model_name'])}</div>
            <div class='kpi-note'>Modelo analítico usado para apoiar a priorização operacional.</div>
          </div>
        </div>
      </div>
      <div class='panel hero-right'>
        <div class='message-card'>
          <div class='title'>Tese para o CEO</div>
          <div class='value'>O maior risco não está no churn oficial. Está no cliente esfriando.</div>
          <p>Esse painel torna visível a deterioração antes da perda. A decisão não é investir em “mais um dashboard”; é criar uma capacidade de proteção de receita.</p>
        </div>
        <div class='message-card'>
          <div class='title'>Recorte mais sensível</div>
          <div class='value'>{_safe(payload['top_industry_abs']['industry'])}</div>
          <p>Maior MRR em risco absoluto: <strong>{_money(payload['top_industry_abs']['mrr_at_risk'] / 1000, 1)} mil</strong>. Já o maior risco relativo está em <strong>{_safe(payload['top_industry_pct']['industry'])}</strong>, com <strong>{_pct(payload['top_industry_pct']['risk_pct'])}</strong> da receita do segmento fragilizada.</p>
        </div>
        <ul class='bullet-list'>
          <li><strong>{_safe(top_driver['label'])}</strong> é a principal causa do risco financeiro: concentra {_pct(top_driver['share'])} do MRR em risco.</li>
          <li><strong>Governança de KPI:</strong> {s['accounts_churn_flag_true']} contas aparecem como canceladas no cadastro oficial, enquanto {s['accounts_with_churn_event']} tiveram ao menos um cancelamento registrado ao longo da jornada.</li>
          <li><strong>Divergência formalizada:</strong> {s['accounts_with_event_and_churn_flag_false']} contas têm histórico de cancelamento sem marcação atual no cadastro, e {s['accounts_churn_flag_true_and_no_event']} contas aparecem como canceladas no cadastro sem evidência detalhada no histórico.</li>
          <li><strong>Downgrade</strong> aparece como alerta comercial precoce e não deve ser tratado como simples ajuste de plano.</li>
          <li><strong>Suporte</strong> importa, mas aqui ele atua mais como acelerador da saída do que como causa única.</li>
        </ul>
      </div>
    </section>
    <section class='section' id='risco'>
      <div class='section-header'>
        <div>
          <h2>1. Onde a receita está exposta</h2>
          <p>A leitura ideal para diretoria combina dois planos: quais sinais aparecem com mais frequência e quais sinais, de fato, concentram mais dinheiro em risco.</p>
        </div>
      </div>
      <div class='grid-2'>
        <div class='panel card'>
          <h3>Sinais que mais aparecem na carteira</h3>
          <div class='head'>Esses são os gatilhos mais frequentes nas regras de negócio. Eles explicam o risco de forma operacional e continuam sendo a linguagem principal de retenção.</div>
          {_bar_rows_frequency(payload['driver_frequency'])}
          <div class='insight-note'><strong>Leitura executiva:</strong> downgrade recente aparece em mais contas, mas a principal concentração financeira está na <strong>{_safe(top_driver['label'])}</strong>. Essa camada mostra <strong>drivers de negócio</strong>; a camada do modelo entra depois para priorizar e refinar a fila.</div>
        </div>
        <div class='panel card'>
          <h3>Drivers que concentram mais MRR em risco</h3>
          <div class='head'>Aqui o foco é valor financeiro ameaçado nas contas já priorizadas para retenção.</div>
          {_bar_rows_financial(payload['driver_financial'])}
          <div class='insight-note'><strong>Ponto de decisão:</strong> proteger receita agora significa atacar ativação, adoção e sinais de desengajamento antes de esperar o churn oficial acontecer.</div>
        </div>
      </div>
    </section>
    <section class='section' id='ciclos'>
      <div class='section-header'>
        <div>
          <h2>2. Ciclos de churn e reativação</h2>
          <p>Este bloco reconcilia formalmente cadastro de contas, trilha de churn_events e estado operacional atual. A divergência vira governança de KPI, não ruído metodológico.</p>
        </div>
      </div>
      <div class='grid-2'>
        <div class='panel card'>
          <h3>Reconciliação formal de KPIs</h3>
          <div class='head'>Cada número abaixo declara explicitamente sua origem: cadastro oficial, histórico observado ou situação operacional atual.</div>
          <div class='reconciliation-grid'><div class='reconciliation-grid'>{_reconciliation_rows(payload['reconciliation'], s['total_accounts'])}</div></div>
          <div class='insight-note'><strong>Leitura objetiva:</strong> o cancelamento oficial registrado no cadastro responde pelo KPI executivo principal, o histórico de cancelamentos mostra a jornada do cliente, e <strong>contas ativas após reativação</strong> mostram a situação operacional atual de clientes reincidentes. A divergência total hoje é de <strong>{s['reconciliation_gap']}</strong> contas ({_pct(s['reconciliation_gap_rate'])} da base).</div>
        </div>
        <div class='panel card'>
          <h3>Impacto operacional da reconciliação</h3>
          <div class='head'>Este recorte mostra quanto da carteira atual pertence a contas com churn observado, reativação e recorrência de instabilidade.</div>
          <div class='kpis' style='grid-template-columns:repeat(2, 1fr); align-items:stretch;'>
            <div class='kpi'>
              <div class='kpi-label'>Contas com histórico de cancelamento</div>
              <div class='kpi-value'>{s['accounts_with_churn_event']}</div>
              <div class='kpi-note'>{_pct(s['event_churn_rate'])} da base já cancelou em algum momento da jornada.</div>
            </div>
            <div class='kpi'>
              <div class='kpi-label'>Contas reativadas</div>
              <div class='kpi-value'>{s['accounts_reactivated']}</div>
              <div class='kpi-note'>{_pct(s['reactivated_rate']) if s.get('reactivated_rate') is not None else 'n/d'} da base já saiu e voltou ao menos uma vez.</div>
            </div>
            <div class='kpi'>
              <div class='kpi-label'>Ativas após reativação</div>
              <div class='kpi-value'>{s['accounts_currently_active_after_reactivation']}</div>
              <div class='kpi-note'>{_pct(s['active_after_reactivation_rate'])} da base continua ativa hoje depois de reativar.</div>
            </div>
            <div class='kpi'>
              <div class='kpi-label'>MRR em contas com histórico</div>
              <div class='kpi-value'>{_money(s['cycle_mrr'])}</div>
              <div class='kpi-note'>{_pct(s['cycle_mrr_share'])} da receita monitorada está em contas com histórico de cancelamento.</div>
            </div>
          </div>
          {_cycle_industry_rows(payload['cycle_industry'])}
          <div class='insight-note'><strong>Como agir:</strong> esse bloco prioriza segmentos onde o histórico de churn segue economicamente relevante no presente. O foco é reduzir reincidência e proteger receita que já mostrou fragilidade relacional.</div>
        </div>
      </div>
    </section>
    <section class='section' id='prioridades'>
      <div class='section-header'>
        <div>
          <h2>3. Onde atacar primeiro</h2>
          <p>A segmentação operacional transforma análise em fila de execução. Não é necessário tratar toda a base do mesmo jeito.</p>
        </div>
      </div>
      <div class='grid-2'>
        <div class='panel card'>
          <h3>Mapa de priorização da carteira</h3>
          <div class='head'>A carteira foi dividida em quatro zonas operacionais, combinando risco, relevância e potencial de expansão.</div>
          <div class='segment-grid'>
            {_segment_cards(payload['segments'], s['total_mrr'])}
          </div>
        </div>
        <div class='panel card'>
          <h3>Exposição por indústria</h3>
          <div class='head'>Esse recorte mostra onde a liderança deve abrir revisão comercial e operacional primeiro.</div>
          {_industry_rows(payload['industry'])}
          <div class='insight-note'><strong>Leitura executiva:</strong> <strong>{_safe(payload['top_industry_abs']['industry'])}</strong> lidera o risco absoluto, enquanto <strong>{_safe(payload['top_industry_pct']['industry'])}</strong> é o segmento mais delicado em termos proporcionais. Isso ajuda a definir onde o esforço de retenção devolve mais valor.</div>
        </div>
      </div>
    </section>
    <section class='section'>
      <div class='grid-2'>
        <div class='panel card'>
          <h3>Mix de risco da base</h3>
          <div class='head'>Distribuição das {s['total_accounts']} contas por zona de risco atual.</div>
          <div class='mix-wrap'>
            <div>
              <div class='donut'></div>
              <div class='donut-center'>
                <strong>{s['risk_accounts']}</strong>
                <span>contas em risco elevado</span>
              </div>
            </div>
            <div class='legend'>
              {_mix_legend(payload['mix'])}
            </div>
          </div>
        </div>
        <div class='panel card'>
          <h3>Plano de ação do CEO</h3>
          <div class='head'>A análise só gera valor quando vira uma rotina clara de decisão.</div>
          <div class='action-grid'>
            <div class='action'>
              <strong>Salvar receita agora</strong>
              <p>Contas críticas e de alto risco com MRR relevante devem entrar em ação coordenada em até 24 horas, com responsável definido e revisão em 7 dias.</p>
            </div>
            <div class='action'>
              <strong>Reativar clientes que estão esfriando</strong>
              <p>Queda de uso deve disparar ações de ativação, reforço de onboarding e campanhas de adoção dos recursos mais relevantes.</p>
            </div>
            <div class='action'>
              <strong>Tratar downgrade como alerta precoce</strong>
              <p>Downgrade não é só renegociação. Aqui ele aparece como um dos sinais mais consistentes de fragilidade comercial.</p>
            </div>
          </div>
          <div class='insight-note'><strong>Resumo:</strong> o objetivo não é “prever churn por curiosidade analítica”. O objetivo é <strong>defender receita antes da perda</strong>.</div>
        </div>
      </div>
    </section>
    <section class='section' id='fila'>
      <div class='section-header'>
        <div>
          <h2>4. Fila de retenção</h2>
          <p>Contas ordenadas por severidade e valor. É aqui que Customer Success, Revenue e liderança devem começar.</p>
        </div>
      </div>
      <div class='panel card'>
        <div class='table-wrap'>
          <table>
            <thead>
              <tr>
                <th>Conta</th>
                <th>Indústria</th>
                <th>Plano</th>
                <th>MRR atual</th>
                <th>MRR em risco</th>
                <th>Risco</th>
                <th>Score</th>
                <th>Driver principal</th>
                <th>Ciclo / histórico</th>
                <th>Ação recomendada</th>
              </tr>
            </thead>
            <tbody>
              {_priority_rows(payload['priority'])}
            </tbody>
          </table>
        </div>
      </div>
    </section>
    <section class='section' id='confiabilidade'>
      <div class='section-header'>
        <div>
          <h2>5. Confiabilidade analítica</h2>
          <p>O modelo analítico sustenta a priorização, mas agora a explicabilidade foi separada em dois níveis: fatores globais do portfólio e explicações locais por conta.</p>
        </div>
      </div>
      <div class='panel card'>
        <div class='model-grid'>
          <div class='model-card'>
            <div class='kpi-label'>Separação entre risco e estabilidade</div>
            <div class='metric'>{_metric(s['roc_auc'])}</div>
            <p>Mostra o quanto o modelo consegue distinguir contas mais propensas a cancelamento das mais estáveis.</p>
          </div>
          <div class='model-card'>
            <div class='kpi-label'>Qualidade da priorização</div>
            <div class='metric'>{_metric(s['average_precision'])}</div>
            <p>Mostra o quão bem o modelo coloca no topo da fila as contas que mais precisam de atenção.</p>
          </div>
          <div class='model-card'>
            <div class='kpi-label'>Modelo vencedor</div>
            <div class='metric'>{_safe(s['best_model_name'])}</div>
            <p>Usado como apoio quantitativo. A leitura executiva continua clara por meio das principais causas e dos segmentos acionáveis.</p>
          </div>
        </div>
        <div class='insight-note'><strong>Leitura para a diretoria:</strong> a robustez estatística é suficiente para apoiar a priorização operacional, mas a força do projeto está em unir <strong>modelo + explicabilidade + rotinas de ação</strong>.</div>
      </div>
      <div class='grid-2' style='margin-top:18px;'>
        <div class='panel card'>
          <h3>Drivers globais do modelo</h3>
          <div class='head'>Estas são as variáveis que mais mexem no score do portfólio atual. Elas não substituem as regras; ajudam a explicar por que o modelo sobe ou reduz risco.</div>
          {_global_model_driver_rows(payload['global_model_drivers'])}
        </div>
        <div class='panel card'>
          <h3>Exemplos locais por conta</h3>
          <div class='head'>Cada explicação local mostra quanto o risco poderia mudar se uma característica da conta estivesse mais próxima do padrão esperado.</div>
          {_account_model_example_rows(payload['account_model_examples'])}
        </div>
      </div>
    </section>
    <div class='footer'>
      Dashboard criado a partir dos outputs do projeto: <em>account_360.csv</em>, <em>churn_risk_drivers.csv</em>, <em>customer_health_score.csv</em>, <em>churn_reconciliation.csv</em>, <em>model_global_explainability.csv</em>, <em>account_model_explanations.csv</em> e <em>model_metrics.json</em>. Estrutura orientada para apresentação executiva em português, com foco em defesa de receita, reconciliação de KPI de churn, explicabilidade do modelo e priorização operacional.
    </div>
  </div>
</body>
</html>
"""
def _dashboard_executive_css(donut_gradient: str) -> str:
    return f"""
    :root {{
      --bg:#06101d; --bg-2:#091425; --panel:rgba(12,22,39,.88); --panel-2:rgba(18,30,49,.94);
      --text:#eef4ff; --muted:#9eb0cb; --line:rgba(255,255,255,.08); --line-strong:rgba(255,255,255,.14);
      --blue:#6aa6ff; --blue-2:#8adfff; --teal:#2dd4bf; --amber:#f59e0b; --rose:#fb7185;
      --ink:#d8e5f8; --shadow:0 24px 70px rgba(0,0,0,.36); --radius:26px;
    }}
    * {{ box-sizing:border-box; }}
    html {{ scroll-behavior:smooth; }}
    body {{
      margin:0; color:var(--text); font-family:Aptos, 'Segoe UI', Roboto, Arial, sans-serif;
      background:
        radial-gradient(980px 480px at 8% -12%, rgba(106,166,255,.18), transparent 58%),
        radial-gradient(760px 420px at 100% 0%, rgba(138,223,255,.10), transparent 55%),
        radial-gradient(640px 320px at 100% 100%, rgba(45,212,191,.06), transparent 60%),
        linear-gradient(180deg, var(--bg) 0%, #091424 100%);
    }}
    .shell {{ max-width:1460px; margin:0 auto; padding:28px; }}
    .panel {{
      background:
        linear-gradient(180deg, rgba(255,255,255,.03), rgba(255,255,255,0) 24%),
        linear-gradient(180deg, var(--panel-2), var(--panel));
      border:1px solid var(--line);
      border-radius:var(--radius);
      box-shadow:var(--shadow);
      backdrop-filter:blur(14px);
    }}
    .nav {{ position:sticky; top:0; z-index:10; margin-bottom:18px; backdrop-filter:blur(14px); }}
    .nav-inner {{
      display:flex; align-items:center; justify-content:space-between; gap:16px;
      border:1px solid var(--line-strong); background:rgba(8,16,30,.62); border-radius:18px; padding:14px 18px; box-shadow:var(--shadow);
    }}
    .brand {{ font-weight:800; letter-spacing:.02em; font-size:17px; }}
    .brand small {{ color:var(--blue-2); font-weight:700; margin-left:8px; font-size:13px; }}
    .nav-links {{ display:flex; gap:10px; flex-wrap:wrap; }}
    .nav-links a {{
      text-decoration:none; color:var(--muted); padding:10px 14px; border-radius:999px;
      background:rgba(255,255,255,.03); border:1px solid transparent; font-size:13px; transition:all .18s ease;
    }}
    .nav-links a:hover {{ color:var(--text); border-color:var(--line); transform:translateY(-1px); }}
    .hero {{ display:grid; grid-template-columns:1.25fr .75fr; gap:20px; margin-bottom:20px; align-items:start; }}
    .hero-left {{ padding:34px; position:relative; overflow:hidden; min-height:340px; }}
    .hero-left::before {{
      content:''; position:absolute; inset:0 auto 0 0; width:4px;
      background:linear-gradient(180deg, rgba(138,223,255,.9), rgba(251,113,133,.9));
    }}
    .hero-left::after {{ content:''; position:absolute; right:-100px; bottom:-120px; width:360px; height:360px; background:radial-gradient(circle, rgba(251,113,133,.18), transparent 62%); pointer-events:none; }}
    .hero-right {{ padding:24px; display:grid; grid-template-rows:auto auto 1fr; gap:14px; align-content:start; }}
    .eyebrow {{ text-transform:uppercase; letter-spacing:.18em; font-size:11px; color:var(--blue-2); font-weight:800; }}
    h1 {{
      margin:14px 0 14px; font-size:52px; line-height:.98; letter-spacing:-.05em; max-width:940px;
      font-family:Georgia, 'Times New Roman', serif; font-weight:700;
    }}
    .hero-sub {{ color:var(--muted); max-width:780px; font-size:16px; line-height:1.65; }}
    .hero-insight, .decision-note, .insight-note {{
      padding:15px 17px; border-radius:18px; border:1px solid var(--line); line-height:1.58;
      box-shadow:inset 0 1px 0 rgba(255,255,255,.03);
    }}
    .hero-insight, .decision-note {{ background:linear-gradient(180deg, rgba(251,113,133,.12), rgba(255,255,255,.03)); color:#ffe7eb; }}
    .insight-note {{ background:rgba(255,255,255,.025); color:#dbe8fb; }}
    .hero-strip, .kpis, .segment-grid, .action-grid, .model-grid, .exec-grid, .reconciliation-grid {{ display:grid; gap:14px; align-items:start; }}
    .hero-strip {{ grid-template-columns:repeat(auto-fit, minmax(210px, 1fr)); margin-top:18px; }}
    .kpis {{ grid-template-columns:repeat(auto-fit, minmax(210px, 1fr)); margin-top:22px; }}
    .segment-grid {{ grid-template-columns:repeat(auto-fit, minmax(250px, 1fr)); }}
    .action-grid {{ grid-template-columns:repeat(auto-fit, minmax(240px, 1fr)); }}
    .model-grid {{ grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); }}
    .exec-grid {{ grid-template-columns:repeat(auto-fit, minmax(250px, 1fr)); }}
    .reconciliation-grid {{ grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:12px; }}
    .hero-flag, .kpi, .message-card, .action, .model-card, .segment-card, .exec-card, .reconciliation-row {{
      padding:18px; border-radius:20px; border:1px solid var(--line);
      background:linear-gradient(180deg, rgba(255,255,255,.05), rgba(255,255,255,.02));
      height:auto; min-height:0;
    }}
    .hero-flag .title, .kpi-label, .message-card .title {{ color:var(--muted); text-transform:uppercase; letter-spacing:.08em; font-size:12px; }}
    .danger-value {{ color:#ff9faf; }}
    .danger-soft {{ color:#ffd7df; }}
    .hero-flag .value, .message-card .value {{ margin-top:8px; font-size:22px; font-weight:800; letter-spacing:-.02em; }}
    .hero-flag p, .message-card p, .kpi-note, .action p, .model-card p {{ margin:8px 0 0; color:#c7d7ee; font-size:14px; line-height:1.55; }}
    .kpi-value, .exec-metric, .segment-mrr, .reconciliation-value, .metric {{ margin-top:10px; font-size:32px; font-weight:800; letter-spacing:-.04em; }}
    .section {{ margin-bottom:20px; }}
    .section-header {{ display:flex; align-items:end; justify-content:space-between; gap:14px; margin:12px 2px 16px; }}
    .section-header h2 {{ margin:0; font-size:28px; letter-spacing:-.04em; font-family:Georgia, 'Times New Roman', serif; font-weight:700; }}
    .section-header p {{ margin:0; color:var(--muted); max-width:760px; line-height:1.55; }}
    .grid-2 {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; align-items:start; }}
    .card {{ padding:24px; }}
    .card h3 {{ margin:0 0 8px; font-size:22px; letter-spacing:-.03em; }}
    .card .head {{ color:var(--muted); font-size:14px; line-height:1.55; margin-bottom:18px; }}
    .footer {{ padding:18px 4px 28px; color:var(--muted); font-size:13px; line-height:1.6; }}
    .queue-top {{ align-items:stretch; }}
    .queue-top > .panel {{ height:100%; }}
    .mix-panel {{ display:flex; flex-direction:column; justify-content:center; }}
    .mix-panel .mix-wrap {{ flex:1; align-items:center; }}
    .donut {{ width:240px; height:240px; border-radius:50%; background:conic-gradient({donut_gradient}); position:relative; margin:auto; box-shadow: inset 0 0 0 1px rgba(255,255,255,.06), 0 18px 40px rgba(0,0,0,.25); }}
    .donut::before {{ content:''; position:absolute; inset:-10px; border-radius:50%; background:radial-gradient(circle, rgba(255,255,255,.08), transparent 68%); filter:blur(6px); }}
    .donut::after {{ content:''; position:absolute; inset:36px; border-radius:50%; background:#0d1728; box-shadow: inset 0 0 0 1px rgba(255,255,255,.05); }}
    @media (max-width:1180px) {{
      .hero, .grid-2, .mix-wrap {{ grid-template-columns:1fr; }}
      .hero-right {{ grid-template-rows:auto; }}
    }}
    @media (max-width:760px) {{
      .shell {{ padding:16px; }}
      h1 {{ font-size:34px; }}
      .nav-inner {{ align-items:flex-start; flex-direction:column; }}
    }}
"""
def _dashboard_executive_css_extra() -> str:
    return """
    .bullet-list { display:grid; gap:10px; margin:0; padding:0; list-style:none; }
    .bullet-list li { padding:14px 14px 14px 42px; position:relative; border:1px solid var(--line); border-radius:16px; background:rgba(255,255,255,.025); color:#dce8fb; line-height:1.5; font-size:14px; }
    .bullet-list li::before { content:'•'; position:absolute; left:16px; top:9px; font-size:26px; color:var(--blue-2); }
    .bar-row { margin-bottom:16px; } .bar-meta { display:flex; justify-content:space-between; align-items:end; gap:16px; margin-bottom:8px; }
    .bar-title { font-weight:700; font-size:15px; } .bar-sub { color:var(--muted); font-size:13px; margin-top:3px; } .bar-value { font-weight:800; font-size:15px; white-space:nowrap; }
    .bar-track { height:12px; border-radius:999px; background:rgba(255,255,255,.07); overflow:hidden; } .bar-fill { height:100%; border-radius:999px; }
    .bar-fill.blue { background:linear-gradient(90deg, var(--blue), var(--blue-2)); } .bar-fill.rose { background:linear-gradient(90deg, #ff8ba0, var(--rose)); } .bar-fill.amber { background:linear-gradient(90deg, #ffcc70, var(--amber)); }
    .exec-card.critical { background:linear-gradient(180deg, rgba(251,113,133,.14), rgba(255,255,255,.03)); } .exec-card.high { background:linear-gradient(180deg, rgba(245,158,11,.12), rgba(255,255,255,.03)); }
    .exec-top, .segment-top { display:flex; align-items:center; justify-content:space-between; gap:12px; }
    .exec-title { margin-top:14px; font-size:22px; font-weight:800; letter-spacing:-.03em; } .exec-sub, .mini { color:var(--muted); font-size:12px; }
    .exec-note, .exec-driver, .segment-risk, .segment-desc { color:#dce9fb; font-size:14px; line-height:1.45; }
    .mix-wrap { display:grid; grid-template-columns:280px 1fr; gap:16px; align-items:start; } .legend { display:grid; gap:10px; }
    .legend-row { display:grid; grid-template-columns:18px 1fr auto auto; gap:10px; align-items:center; padding:10px 12px; border-radius:14px; border:1px solid var(--line); background:rgba(255,255,255,.02); }
    .dot { width:10px; height:10px; border-radius:50%; display:inline-block; } .legend-name { font-weight:700; } .legend-count, .legend-mrr { color:#c7d7ee; font-size:13px; }
    .donut-center { position:relative; margin-top:-154px; text-align:center; z-index:1; } .donut-center strong { display:block; font-size:38px; letter-spacing:-.04em; } .donut-center span { color:var(--muted); font-size:13px; }
    .industry-row { margin-bottom:16px; } .industry-head, .reconciliation-top { display:flex; justify-content:space-between; gap:16px; align-items:flex-start; margin-bottom:8px; }
    .industry-metrics { text-align:right; } .industry-metrics strong { display:block; font-size:15px; } .industry-metrics span, .reconciliation-value span { color:var(--muted); font-size:12px; }
    .reconciliation-note { margin-top:10px; color:#cbd8ee; font-size:13px; line-height:1.5; }
    .pill, .risk-tag, .signal-tag { display:inline-flex; padding:6px 10px; border-radius:999px; font-weight:800; font-size:12px; }
    .pill { border:1px solid rgba(255,255,255,.08); background:rgba(255,255,255,.05); } .risk-tag.low { background:rgba(45,212,191,.14); color:#7ce7d9; } .risk-tag.medium { background:rgba(96,165,250,.16); color:#9dc8ff; } .risk-tag.high { background:rgba(245,158,11,.16); color:#ffd087; } .risk-tag.critical { background:rgba(251,113,133,.16); color:#ff9faf; }
    .signal-wrap { display:flex; flex-wrap:wrap; gap:6px; } .signal-tag.history { background:rgba(96,165,250,.16); color:#a9ccff; } .signal-tag.reactivated { background:rgba(45,212,191,.14); color:#8cebdd; }
    .table-wrap { overflow:auto; border-radius:18px; border:1px solid var(--line); } table { width:100%; border-collapse:collapse; min-width:1200px; } th, td { padding:14px 12px; text-align:left; border-bottom:1px solid rgba(255,255,255,.06); vertical-align:top; }
    th { position:sticky; top:0; background:#0f1a2d; color:#bfd0ea; font-size:12px; text-transform:uppercase; letter-spacing:.08em; } td { font-size:13px; color:#eaf2ff; } tr:hover td { background:rgba(255,255,255,.02); }
    .company { font-weight:700; } .company-id { color:var(--muted); font-size:12px; margin-top:3px; } .action.executive { background:linear-gradient(180deg, rgba(106,166,255,.10), rgba(255,255,255,.03)); }
"""
def _dashboard_executive_css_polish() -> str:
    return """
    .hero-flag:nth-child(1) { background:linear-gradient(180deg, rgba(251,113,133,.12), rgba(255,255,255,.03)); }
    .hero-flag:nth-child(2) { background:linear-gradient(180deg, rgba(106,166,255,.12), rgba(255,255,255,.03)); }
    .hero-flag:nth-child(3) { background:linear-gradient(180deg, rgba(45,212,191,.10), rgba(255,255,255,.03)); }
    .hero-flag, .message-card, .kpi, .action, .model-card, .segment-card, .exec-card, .reconciliation-row, .table-wrap {
      box-shadow: inset 0 1px 0 rgba(255,255,255,.03), 0 10px 30px rgba(0,0,0,.14);
    }
    .message-card:first-child { border-color:rgba(251,113,133,.22); }
    .message-card:nth-child(2) { border-color:rgba(106,166,255,.18); }
    .exec-card { position:relative; overflow:hidden; }
    .exec-card::after { content:''; position:absolute; inset:auto -20px -30px auto; width:120px; height:120px; border-radius:50%; background:radial-gradient(circle, rgba(255,255,255,.09), transparent 68%); }
    .exec-card.critical { background:linear-gradient(180deg, rgba(251,113,133,.16), rgba(255,255,255,.03)); border-color:rgba(251,113,133,.18); }
    .exec-card.high { background:linear-gradient(180deg, rgba(245,158,11,.14), rgba(255,255,255,.03)); border-color:rgba(245,158,11,.18); }
    .exec-title { margin-top:16px; font-size:23px; font-weight:800; letter-spacing:-.04em; }
    .exec-note, .exec-driver, .segment-risk, .segment-desc { line-height:1.5; }
    .exec-driver strong { color:#fff4f6; }
    .legend-row { padding:11px 12px; }
    .dot { box-shadow:0 0 12px currentColor; }
    .risk-tag.critical { color:#ffb6c2; box-shadow:0 0 0 1px rgba(251,113,133,.16) inset; }
    .table-wrap { border-radius:20px; background:rgba(255,255,255,.02); }
    tr:hover td { background:rgba(255,255,255,.025); }
    .action.executive { background:linear-gradient(180deg, rgba(106,166,255,.12), rgba(255,255,255,.03)); border-color:rgba(106,166,255,.18); }
    .action.executive strong { letter-spacing:-.02em; }
    .model-card { background:linear-gradient(180deg, rgba(106,166,255,.08), rgba(255,255,255,.03)); }
    .segment-card { height:100%; }
"""
def _executive_body(payload: dict) -> str:
    s = payload["summary"]
    top_driver = payload["top_driver"]
    top_global_driver = payload["top_global_model_driver"]
    return f"""
  <div class='shell'>
    <div class='nav'><div class='nav-inner'><div class='brand'>RavenStack <small>Cockpit Executivo de Receita</small></div><div class='nav-links'><a href='#acao'>Decisão agora</a><a href='#concentracao'>Concentração</a><a href='#fila'>Fila executiva</a><a href='#apendice'>Apêndice analítico</a></div></div></div>
    <section class='hero'>
      <div class='panel hero-left'>
        <div class='eyebrow'>Resumo para decisão</div>
        <h1>{_money(s['mrr_at_risk'])} de MRR está <span style='color:var(--rose)'>em risco imediato</span></h1>
        <div class='hero-sub'>A exposição está concentrada em {s['critical_accounts']} contas críticas, com {s['strategic_critical_accounts']} contas de alta relevância econômica pedindo intervenção humana imediata.</div>
        <div class='hero-insight'><strong>Leitura em 5 segundos:</strong> o top 3 da fila executiva concentra <strong>{_pct(s['top3_risk_share'])}</strong> do MRR em risco ({_money(s['top3_mrr_risk'])}). A principal causa é <strong>{_safe(top_driver['label'])}</strong>, enquanto <strong>{_safe(payload['top_industry_abs']['industry'])}</strong> lidera a exposição absoluta por segmento.</div>
        <div class='hero-strip'>
          <div class='hero-flag'><div class='title'>Principal causa financeira</div><div class='value'>{_safe(top_driver['label'])}</div><p>Concentra {_pct(top_driver['share'])} do risco imediato.</p></div>
          <div class='hero-flag'><div class='title'>Principal fator do modelo</div><div class='value'>{_safe(top_global_driver['feature_label'])}</div><p>{_safe(_simplify_explanation_text(top_global_driver['impact_statement']))}</p></div>
          <div class='hero-flag'><div class='title'>Setor mais exposto</div><div class='value'>{_safe(payload['top_industry_abs']['industry'])}</div><p>{_money(payload['top_industry_abs']['mrr_at_risk'])} em risco absoluto.</p></div>
        </div>
        <div class='kpis'>
          <div class='kpi'><div class='kpi-label'>MRR em risco imediato</div><div class='kpi-value danger-value'>{_money(s['mrr_at_risk'])}</div><div class='kpi-note'>Valor que precisa ser defendido agora.</div></div>
          <div class='kpi'><div class='kpi-label'>Receita exposta</div><div class='kpi-value'>{_pct(s['mrr_at_risk'] / max(s['total_mrr'], 1.0))}</div><div class='kpi-note'>Parcela da base monitorada já fragilizada.</div></div>
          <div class='kpi'><div class='kpi-label'>Contas críticas</div><div class='kpi-value danger-value'>{s['critical_accounts']}</div><div class='kpi-note'>Casos que não deveriam esperar o próximo ciclo.</div></div>
          <div class='kpi'><div class='kpi-label'>Contas estratégicas sob risco</div><div class='kpi-value'>{s['strategic_critical_accounts']}</div><div class='kpi-note'>Contas high ou critical com MRR relevante.</div></div>
        </div>
      </div>
      <div class='panel hero-right'>
        <div class='message-card'><div class='title'>Decisão executiva</div><div class='value'>Priorizar poucas contas com alto impacto, antes que o churn oficial apareça.</div><p>Este cockpit não foi desenhado para operar a carteira inteira. Ele foi desenhado para responder onde a liderança deve agir primeiro para proteger receita.</p></div>
        <div class='message-card'><div class='title'>Alerta principal</div><div class='value'>Top 3 contas concentram {_pct(s['top3_risk_share'])} do risco financeiro</div><p>Isso transforma o problema em algo executável: a liderança consegue agir sobre uma fração pequena da base para defender uma parte material da receita ameaçada.</p></div>
        <ul class='bullet-list'>
          <li><strong>{_safe(top_driver['label'])}</strong> concentra {_pct(top_driver['share'])} do MRR em risco e deve orientar a resposta desta semana.</li>
          <li><strong>{s['accounts_with_churn_event']}</strong> contas já tiveram churn_event, mas apenas <strong>{s['accounts_churn_flag_true']}</strong> aparecem no indicador oficial do cadastro. A divergência foi formalizada, não escondida.</li>
          <li><strong>{s['accounts_currently_active_after_reactivation']}</strong> contas seguem ativas após reativação. O problema central não é só perda: é recorrência de fragilidade.</li>
        </ul>
        <div class='decision-note'><strong>Comando sugerido:</strong> mobilizar CS sênior e Revenue para as contas críticas ainda hoje, abrir revisão comercial no setor <strong>{_safe(payload['top_industry_abs']['industry'])}</strong> nesta semana e atacar <strong>{_safe(top_driver['label'])}</strong> como causa dominante do risco atual.</div>
      </div>
    </section>
"""
def _executive_sections(payload: dict) -> str:
    s = payload["summary"]
    top_driver = payload["top_driver"]
    return f"""
    <section class='section' id='acao'><div class='section-header'><div><h2>1. Decisão agora</h2><p>Camada principal do dashboard: o que exige ação humana agora e quais comandos executivos destravam a resposta.</p></div></div><div class='grid-2'><div class='panel card'><h3>Fila executiva de hoje</h3><div class='head'>Poucas contas concentram boa parte do risco. Elas devem receber atenção da liderança antes de qualquer expansão da rotina para o restante da carteira.</div><div class='exec-grid'>{_executive_account_cards(payload['top_priority'])}</div><div class='insight-note'><strong>Critério de leitura:</strong> urgência, MRR em risco, principal causa e ação já recomendada. Se o CEO só olhar um bloco, este deve bastar para abrir o war room.</div></div><div class='panel card'><h3>Comandos executivos</h3><div class='head'>A resposta não é genérica. Cada comando abaixo já traz foco, owner e prazo de execução.</div><div class='action-grid'>{_executive_action_rows(payload['executive_actions'])}</div><div class='insight-note'><strong>Objetivo:</strong> reduzir a distância entre insight e decisão. O dashboard precisa sair da tela e virar agenda de retenção em 24 horas.</div></div></div></section>
    <section class='section' id='concentracao'><div class='section-header'><div><h2>2. Onde o risco está concentrado</h2><p>Depois da fila imediata, a pergunta executiva é onde o problema se concentra para orientar alocação de energia, revisão comercial e patrocínio de liderança.</p></div></div><div class='grid-2'><div class='panel card'><h3>Drivers que concentram mais receita ameaçada</h3><div class='head'>A pergunta aqui não é frequência de sintomas, e sim concentração de impacto econômico na carteira já priorizada.</div>{_bar_rows_financial(payload['driver_financial'])}<div class='insight-note'><strong>Mensagem para a diretoria:</strong> a defesa de receita precisa começar por <strong>{_safe(top_driver['label'])}</strong>. É onde mais dinheiro está exposto agora.</div></div><div class='panel card'><h3>Segmentos que pedem patrocínio executivo</h3><div class='head'>Esse recorte mostra onde a liderança deve abrir revisão comercial e operacional primeiro para capturar maior retorno da intervenção.</div>{_industry_rows(payload['industry'])}<div class='insight-note'><strong>Prioridade setorial:</strong> <strong>{_safe(payload['top_industry_abs']['industry'])}</strong> lidera o risco absoluto, enquanto <strong>{_safe(payload['top_industry_pct']['industry'])}</strong> tem a maior fragilidade proporcional.</div></div></div></section>
    <section class='section' id='fila'><div class='section-header'><div><h2>3. Fila executiva curta</h2><p>Segundo nível de leitura: uma lista curta para acompanhamento de leadership review, sem transformar o dashboard em painel operacional da base inteira.</p></div></div><div class='grid-2 queue-top'><div class='panel card mix-panel'><h3>Mix de risco da carteira</h3><div class='head'>Distribuição das {s['total_accounts']} contas por zona de risco atual. Este bloco ajuda a decidir se a resposta deve ser concentrada, escalada ou automatizada.</div><div class='mix-wrap'><div><div class='donut'></div><div class='donut-center'><strong>{s['risk_accounts']}</strong><span>contas em risco elevado</span></div></div><div class='legend'>{_mix_legend(payload['mix'])}</div></div></div><div class='panel card queue-panel'><h3>Mapa de priorização</h3><div class='head'>A carteira foi dividida em quatro zonas operacionais para separar intervenção humana imediata de acompanhamento e expansão.</div><div class='segment-grid'>{_segment_cards(payload['segments'], s['total_mrr'])}</div><div class='insight-note'><strong>Leitura executiva:</strong> contas estratégicas em risco devem ficar na agenda do board; risco de volume deve virar rotina escalável, não exceção manual.</div></div></div><div class='panel card' style='margin-top:18px;'><div class='table-wrap'><table><thead><tr><th>Conta</th><th>Indústria</th><th>Plano</th><th>MRR atual</th><th>MRR em risco</th><th>Risco</th><th>Score</th><th>Driver principal</th><th>Ciclo / histórico</th><th>Ação recomendada</th></tr></thead><tbody>{_priority_rows(payload['priority'][:10])}</tbody></table></div></div></section>
"""
def _executive_appendix(payload: dict) -> str:
    s = payload["summary"]
    return f"""
    <section class='section' id='apendice'><div class='section-header'><div><h2>4. Apêndice analítico</h2><p>Segundo nível de leitura para banca técnica e governança: definições de churn, impacto de reativação e uma explicação mais simples do score do modelo.</p></div></div><div class='grid-2'><div class='panel card'><h3>Reconciliação formal de churn</h3><div class='head'>A divergência entre cadastro e eventos não fica implícita. Ela é tratada como governança de KPI, com definição explícita de uso para histórico, operação e narrativa executiva.</div><div class='reconciliation-grid'>{_reconciliation_rows(payload['reconciliation'], s['total_accounts'])}</div><div class='insight-note'><strong>Uso recomendado:</strong> o cancelamento oficial no cadastro sustenta a narrativa executiva, o histórico de cancelamentos sustenta a leitura da jornada e <strong>ativas após reativação</strong> descrevem a operação atual.</div></div><div class='panel card'><h3>Ciclos de churn e reativação</h3><div class='head'>Este recorte mostra quanto da carteira atual pertence a contas com churn observado, reativação e histórico de instabilidade relacional.</div><div class='kpis' style='grid-template-columns:repeat(2,1fr); margin-top:0;'><div class='kpi'><div class='kpi-label'>Contas com histórico de cancelamento</div><div class='kpi-value'>{s['accounts_with_churn_event']}</div><div class='kpi-note'>{_pct(s['event_churn_rate'])} da base já teve cancelamento registrado.</div></div><div class='kpi'><div class='kpi-label'>Contas reativadas</div><div class='kpi-value'>{s['accounts_reactivated']}</div><div class='kpi-note'>{_pct(s['reactivated_rate']) if s.get('reactivated_rate') is not None else 'n/d'} da base saiu e voltou ao menos uma vez.</div></div><div class='kpi'><div class='kpi-label'>Ativas após reativação</div><div class='kpi-value'>{s['accounts_currently_active_after_reactivation']}</div><div class='kpi-note'>{_pct(s['active_after_reactivation_rate'])} seguem ativas hoje.</div></div><div class='kpi'><div class='kpi-label'>MRR em contas com histórico</div><div class='kpi-value'>{_money(s['cycle_mrr'])}</div><div class='kpi-note'>{_pct(s['cycle_mrr_share'])} da receita está em contas com histórico de cancelamento.</div></div></div>{_cycle_industry_rows(payload['cycle_industry'])}</div></div><div class='panel card' style='margin-top:18px;'><div class='model-grid'><div class='model-card'><div class='kpi-label'>Modelo vencedor</div><div class='metric'>{_safe(s['best_model_name'])}</div><p>Modelo usado como apoio para ordenar melhor as contas que merecem mais atenção agora.</p></div><div class='model-card'><div class='kpi-label'>Separação entre risco e estabilidade</div><div class='metric'>{_metric(s['roc_auc'])}</div><p>Indica o quanto o modelo consegue separar contas mais propensas a churn das menos propensas.</p></div><div class='model-card'><div class='kpi-label'>Qualidade da priorização</div><div class='metric'>{_metric(s['average_precision'])}</div><p>Mostra se o modelo está colocando mais acima da fila as contas que realmente merecem atenção.</p></div></div><div class='insight-note'><strong>Leitura executiva:</strong> o modelo não toma a decisão sozinho. Ele ajuda a organizar a fila e deixa mais claro por que cada conta apareceu como prioridade.</div></div><div class='grid-2' style='margin-top:18px;'><div class='panel card'><h3>Explicabilidade global do modelo</h3><div class='head'>Aqui mostramos, de forma simples, quais fatores mais empurram o risco para cima ou para baixo no conjunto da carteira. É uma ajuda para entender o modelo, não para substituir os drivers de negócio.</div>{_global_model_driver_rows(payload['global_model_drivers'])}</div><div class='panel card'><h3>Explicações por conta</h3><div class='head'>Aqui mostramos, conta por conta, quais sinais mais influenciaram a elevação ou a redução do risco em comparação com o padrão da base.</div>{_account_model_example_rows(payload['account_model_examples'])}</div></div></section>
    <div class='footer'>Dashboard criado a partir dos outputs do projeto: <em>account_360.csv</em>, <em>churn_risk_drivers.csv</em>, <em>customer_health_score.csv</em>, <em>churn_reconciliation.csv</em>, <em>model_global_explainability.csv</em>, <em>account_model_explanations.csv</em> e <em>model_metrics.json</em>. A estrutura prioriza decisão rápida no primeiro olhar e preserva governança metodológica no segundo nível.</div>
  </div>
"""
def _html_executive(payload: dict) -> str:
    donut_gradient = _donut_gradient(payload["mix"])
    return f"""<!DOCTYPE html>
<html lang='pt-BR'>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <title>RavenStack | Cockpit Executivo de Receita</title>
  <style>
{_dashboard_executive_css(donut_gradient)}
{_dashboard_executive_css_extra()}
{_dashboard_executive_css_polish()}
  </style>
</head>
<body>
{_executive_body(payload)}
{_executive_sections(payload)}
{_executive_appendix(payload)}
</body>
</html>
"""
def generate_dashboard(output_dir: str | Path | None = None) -> Path:
    target_dir = Path(output_dir) if output_dir is not None else OUTPUT_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    account_360, drivers, customer_health, reconciliation, global_explainability, account_explanations, metrics = _read_outputs(target_dir)
    html_content = _html_executive(
        _payload(
            account_360,
            drivers,
            customer_health,
            reconciliation,
            global_explainability,
            account_explanations,
            metrics,
        )
    )
    target = target_dir / "dashboard_ceo_premium_ravenstack.html"
    target.write_text(html_content, encoding="utf-8")
    return target
if __name__ == "__main__":
    print(generate_dashboard())
