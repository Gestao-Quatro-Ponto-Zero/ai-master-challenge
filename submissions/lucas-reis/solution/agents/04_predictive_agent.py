"""
Agent 04 — Predictive Model (LightGBM + SHAP)
Pipeline completo: DuckDB → features → treino → SHAP → churn scores → CS list.

Reescrito em 2026-03-20 (prompt_005):
- Carrega dados reais via DuckDB (não sintéticos)
- Features segmentais priorizadas conforme achados do Agent 03
- SHAP por conta → top 3 risk factors individuais
- Gera churn_scores.csv com risk_tier (HIGH/MEDIUM/LOW)
- Lista de ação imediata para CS (HIGH risk + ainda ativas)
"""

import os
import duckdb
import pandas as pd
import numpy as np
import lightgbm as lgb
import shap
from pathlib import Path
from datetime import date
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report
from sklearn.preprocessing import LabelEncoder

DATA_DIR    = Path(__file__).parent.parent / "data"
SOLUTION_DIR = Path(__file__).parent.parent
SEP = "=" * 60
TODAY = date(2026, 3, 20)


def run_in_data_dir(con, query: str) -> pd.DataFrame:
    original = os.getcwd()
    os.chdir(DATA_DIR)
    try:
        return con.execute(query).df()
    finally:
        os.chdir(original)


# ---------------------------------------------------------------------------
# Step 1 — Build feature table via DuckDB
# ---------------------------------------------------------------------------
def build_features(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    query = """
    WITH sub_agg AS (
        SELECT
            account_id,
            COUNT(subscription_id)                                          AS n_subscriptions,
            AVG(mrr_amount)                                                 AS avg_mrr,
            SUM(CASE WHEN billing_frequency = 'annual' THEN 1 ELSE 0 END)  AS n_annual_subs,
            SUM(CASE WHEN auto_renew_flag = false THEN 1 ELSE 0 END)        AS n_no_autorenew,
            SUM(CASE WHEN downgrade_flag THEN 1 ELSE 0 END)                 AS n_downgrades,
            SUM(CASE WHEN upgrade_flag THEN 1 ELSE 0 END)                   AS n_upgrades
        FROM read_csv_auto('ravenstack_subscriptions.csv')
        GROUP BY account_id
    ),
    usage_agg AS (
        SELECT
            s.account_id,
            COUNT(f.usage_id) * 1.0
                / NULLIF(COUNT(DISTINCT f.subscription_id), 0)               AS avg_session_count,
            COUNT(DISTINCT f.feature_name)                                   AS distinct_features_used,
            AVG(f.error_count)                                               AS avg_error_count,
            AVG(f.usage_duration_secs / 60.0)                               AS avg_usage_duration_min
        FROM read_csv_auto('ravenstack_feature_usage.csv') f
        JOIN read_csv_auto('ravenstack_subscriptions.csv') s
          ON f.subscription_id = s.subscription_id
        GROUP BY s.account_id
    ),
    ticket_agg AS (
        SELECT
            account_id,
            COUNT(ticket_id)                                                  AS n_tickets,
            SUM(CASE WHEN escalation_flag THEN 1 ELSE 0 END)                 AS n_escalations,
            CAST(SUM(CASE WHEN satisfaction_score IS NULL THEN 1 ELSE 0 END) AS DOUBLE)
                / NULLIF(COUNT(ticket_id), 0)                                 AS satisfaction_no_response_rate,
            SUM(CASE WHEN priority = 'urgent' THEN 1 ELSE 0 END)             AS n_urgent_tickets
        FROM read_csv_auto('ravenstack_support_tickets.csv')
        GROUP BY account_id
    ),
    churn_info AS (
        SELECT account_id, preceding_downgrade_flag, preceding_upgrade_flag
        FROM (
            SELECT *,
                ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY churn_date DESC) AS rn
            FROM read_csv_auto('ravenstack_churn_events.csv')
        ) t
        WHERE rn = 1
    )
    SELECT
        a.account_id,
        a.industry,
        a.referral_source,
        a.plan_tier                                                  AS initial_plan_tier,
        a.seats,
        a.signup_date,
        CAST(a.churn_flag AS INTEGER)                                AS churned,
        COALESCE(sa.avg_mrr, 0)                                     AS avg_mrr,
        COALESCE(sa.n_annual_subs, 0)                               AS n_annual_subs,
        CAST(COALESCE(sa.n_no_autorenew, 0) > 0 AS INTEGER)         AS has_auto_renew_false,
        COALESCE(sa.n_downgrades, 0)                                AS n_downgrades,
        COALESCE(sa.n_upgrades, 0)                                  AS n_upgrades,
        COALESCE(ua.avg_session_count, 0)                           AS avg_session_count,
        COALESCE(ua.distinct_features_used, 0)                      AS distinct_features_used,
        COALESCE(ua.avg_error_count, 0)                             AS avg_error_count,
        COALESCE(ua.avg_usage_duration_min, 0)                      AS avg_usage_duration_min,
        COALESCE(ta.n_tickets, 0)                                   AS n_tickets,
        COALESCE(ta.n_escalations, 0)                               AS n_escalations,
        COALESCE(ta.satisfaction_no_response_rate, 0)               AS satisfaction_no_response_rate,
        COALESCE(ta.n_urgent_tickets, 0)                            AS n_urgent_tickets,
        CAST(COALESCE(c.preceding_downgrade_flag, false) AS INTEGER) AS preceding_downgrade_flag,
        CAST(COALESCE(c.preceding_upgrade_flag, false) AS INTEGER)   AS preceding_upgrade_flag
    FROM read_csv_auto('ravenstack_accounts.csv') a
    LEFT JOIN sub_agg sa      ON a.account_id = sa.account_id
    LEFT JOIN usage_agg ua    ON a.account_id = ua.account_id
    LEFT JOIN ticket_agg ta   ON a.account_id = ta.account_id
    LEFT JOIN churn_info c    ON a.account_id = c.account_id
    """
    return run_in_data_dir(con, query)


# ---------------------------------------------------------------------------
# Step 2 — Feature preparation
# ---------------------------------------------------------------------------
FEATURE_COLS = [
    # Segmental (high importance expected from H1)
    "industry",
    "referral_source",
    "initial_plan_tier",
    "seats",
    # Contract behavior
    "avg_mrr",
    "n_annual_subs",
    "has_auto_renew_false",
    "n_downgrades",
    "n_upgrades",
    "preceding_downgrade_flag",
    "preceding_upgrade_flag",
    # Usage (low importance expected from H3)
    "avg_session_count",
    "distinct_features_used",
    "avg_error_count",
    "avg_usage_duration_min",
    # Support
    "n_tickets",
    "n_escalations",
    "satisfaction_no_response_rate",
    "n_urgent_tickets",
]

CATEGORICAL_COLS = ["industry", "referral_source", "initial_plan_tier"]


def prepare_features(df: pd.DataFrame, encoders=None, fit: bool = False):
    """Prepara feature matrix. Retorna (X, encoders)."""
    available = [c for c in FEATURE_COLS if c in df.columns]
    X = df[available].copy()

    if encoders is None:
        encoders = {}

    for col in CATEGORICAL_COLS:
        if col not in X.columns:
            continue
        if fit:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].fillna("unknown").astype(str))
            encoders[col] = le
        else:
            le = encoders[col]
            X[col] = le.transform(X[col].fillna("unknown").astype(str))

    return X, encoders


# ---------------------------------------------------------------------------
# Step 3 — Train + evaluate
# ---------------------------------------------------------------------------
def train_and_evaluate(df: pd.DataFrame) -> dict:
    print(f"\n{SEP}\n  Step 2 — Treinamento LightGBM\n{SEP}")

    X_full, encoders = prepare_features(df, fit=True)
    y_full = df["churned"]

    X_train, X_test, y_train, y_test = train_test_split(
        X_full, y_full, test_size=0.2, random_state=42, stratify=y_full
    )
    print(f"\n  Train: {len(X_train)} ({y_train.mean():.1%} churn) | "
          f"Test: {len(X_test)} ({y_test.mean():.1%} churn)")

    model = lgb.LGBMClassifier(
        n_estimators=200,
        learning_rate=0.05,
        num_leaves=31,
        min_child_samples=10,
        class_weight="balanced",
        random_state=42,
        verbose=-1,
    )
    model.fit(X_train, y_train)

    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred_label = (y_pred_proba >= 0.5).astype(int)
    auc = roc_auc_score(y_test, y_pred_proba)

    print(f"\n  AUC-ROC:   {auc:.4f}")
    print(f"\n  Classification report (threshold=0.5):")
    print(classification_report(y_test, y_pred_label, target_names=["Retained", "Churned"]))

    return {"model": model, "encoders": encoders, "auc": auc,
            "X_full": X_full, "X_test": X_test, "y_test": y_test,
            "feature_names": X_full.columns.tolist()}


# ---------------------------------------------------------------------------
# Step 4 — SHAP analysis
# ---------------------------------------------------------------------------
def run_shap(model, X_full: pd.DataFrame, X_test: pd.DataFrame) -> tuple:
    print(f"\n{SEP}\n  Step 3 — SHAP Analysis\n{SEP}")

    explainer  = shap.TreeExplainer(model)
    sv_test    = explainer.shap_values(X_test)
    sv_full    = explainer.shap_values(X_full)

    feature_names = X_full.columns.tolist()
    imp = pd.DataFrame({
        "feature":       feature_names,
        "shap_mean_abs": np.abs(sv_test).mean(axis=0),
    }).sort_values("shap_mean_abs", ascending=False).reset_index(drop=True)

    # Direção: correlação de Pearson entre feature value e SHAP value
    directions = []
    for col in feature_names:
        col_vals  = X_test[col].values
        shap_vals = sv_test[:, feature_names.index(col)]
        corr = np.corrcoef(col_vals, shap_vals)[0, 1] if col_vals.std() > 0 else 0
        directions.append("↑ mais churn" if corr > 0 else "↓ menos churn")

    dir_map = dict(zip(feature_names, directions))
    imp["direction"] = imp["feature"].map(dir_map)

    print(f"\n  {'Rank':<5} {'Feature':<35} {'SHAP Importance':>16} {'Direção':>15}")
    print("  " + "-" * 73)
    for i, row in imp.head(10).iterrows():
        print(f"  {i+1:<5} {row['feature']:<35} {row['shap_mean_abs']:>16.4f} {row['direction']:>15}")

    return sv_full, imp


# ---------------------------------------------------------------------------
# Step 5 — Churn scores + CSV
# ---------------------------------------------------------------------------
def build_score_table(df: pd.DataFrame, model, encoders: dict,
                      sv_full: np.ndarray, feature_names: list) -> pd.DataFrame:
    print(f"\n{SEP}\n  Step 4 — Churn Scores por Conta\n{SEP}")

    X_full, _ = prepare_features(df, encoders=encoders, fit=False)
    proba     = model.predict_proba(X_full)[:, 1]
    scores    = (proba * 100).round(1)

    def risk_tier(s):
        if s >= 70: return "HIGH"
        if s >= 40: return "MEDIUM"
        return "LOW"

    # Top 3 risk factors por conta (por |SHAP|)
    top1, top2, top3 = [], [], []
    for i in range(len(df)):
        sv_i   = sv_full[i, :]
        idx    = np.argsort(np.abs(sv_i))[::-1][:3]
        names  = [feature_names[j] for j in idx]
        top1.append(names[0] if len(names) > 0 else "")
        top2.append(names[1] if len(names) > 1 else "")
        top3.append(names[2] if len(names) > 2 else "")

    out = pd.DataFrame({
        "account_id":         df["account_id"].values,
        "churn_probability":  proba.round(4),
        "churn_score":        scores,
        "risk_tier":          [risk_tier(s) for s in scores],
        "top_risk_factor_1":  top1,
        "top_risk_factor_2":  top2,
        "top_risk_factor_3":  top3,
        "industry":           df["industry"].values,
        "acquisition_channel": df["referral_source"].values,
        "mrr":                df["avg_mrr"].round(2).values,
        "churned":            df["churned"].values,
    })

    # Distribuição de risk_tier
    tier_counts = out["risk_tier"].value_counts()
    print(f"\n  Distribuição de risk_tier:")
    for tier in ["HIGH", "MEDIUM", "LOW"]:
        n = tier_counts.get(tier, 0)
        print(f"    {tier:<8} {n:>4} contas  ({n/len(out)*100:.1f}%)")

    return out


# ---------------------------------------------------------------------------
# Step 6 — CS action list
# ---------------------------------------------------------------------------
def cs_action_list(df_base: pd.DataFrame, scores: pd.DataFrame):
    print(f"\n{SEP}\n  Step 5 — Lista de Ação Imediata para CS\n{SEP}")

    df_base["signup_date_dt"] = pd.to_datetime(df_base["signup_date"])
    df_base["dias_cliente"]   = (pd.Timestamp(TODAY) - df_base["signup_date_dt"]).dt.days

    combined = scores.merge(df_base[["account_id", "dias_cliente"]], on="account_id")
    active_high = combined[
        (combined["risk_tier"] == "HIGH") & (combined["churned"] == 0)
    ].sort_values("mrr", ascending=False).head(20)

    mrr_total = active_high["mrr"].sum()
    print(f"\n  Contas HIGH risk e ainda ativas: {len(combined[(combined['risk_tier']=='HIGH') & (combined['churned']==0)])}")
    print(f"  MRR total em risco: ${mrr_total:,.0f}")
    print(f"\n  Top 20 para intervenção imediata do CS:")
    print(f"\n  {'Account ID':<12} {'Score':>6} {'MRR':>9} {'Industry':<14} {'Canal':<10} "
          f"{'Top Risk Factor':<30} {'Dias Cliente':>12}")
    print("  " + "-" * 100)
    for _, row in active_high.iterrows():
        print(f"  {row['account_id']:<12} {row['churn_score']:>5.0f} "
              f"${row['mrr']:>8,.0f} {str(row['industry']):<14} {str(row['acquisition_channel']):<10} "
              f"{str(row['top_risk_factor_1']):<30} {int(row['dias_cliente']):>12}")

    return active_high, mrr_total


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def run_model():
    print("[MODEL] Iniciando pipeline Agent 04...")
    con = duckdb.connect()

    print(f"\n{SEP}\n  Step 1 — Build Features via DuckDB\n{SEP}")
    df = build_features(con)
    con.close()
    print(f"  Shape: {df.shape} | Churn: {df['churned'].mean():.1%}")

    results  = train_and_evaluate(df)
    sv_full, imp = run_shap(results["model"], results["X_full"], results["X_test"])

    scores = build_score_table(
        df, results["model"], results["encoders"],
        sv_full, results["feature_names"]
    )

    cs_list, mrr_risk = cs_action_list(df, scores)

    # Salvar CSV
    out_path = SOLUTION_DIR / "churn_scores.csv"
    scores.to_csv(out_path, index=False)
    print(f"\n  ✅ churn_scores.csv salvo em: {out_path}")

    print(f"\n{SEP}\n  RESUMO FINAL\n{SEP}")
    print(f"  AUC-ROC:                {results['auc']:.4f}")
    print(f"  Contas HIGH risk ativas: {(scores[scores['risk_tier']=='HIGH']['churned']==0).sum()}")
    print(f"  MRR em risco imediato:  ${mrr_risk:,.0f}")
    print(f"  Top feature (SHAP):     {imp.iloc[0]['feature']} ({imp.iloc[0]['direction']})")

    return {
        "model":     results["model"],
        "auc":       results["auc"],
        "shap_imp":  imp,
        "scores":    scores,
        "cs_list":   cs_list,
        "mrr_risk":  mrr_risk,
    }


if __name__ == "__main__":
    run_model()
