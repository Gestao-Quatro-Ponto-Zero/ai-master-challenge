import pandas as pd


def _get_revenue_column(df):
    if "mrr" in df.columns:
        return "mrr"
    if "avg_mrr" in df.columns:
        return "avg_mrr"
    raise ValueError("Nenhuma coluna de receita encontrada. Esperado: 'mrr' ou 'avg_mrr'.")


def _get_active_df(df):
    if "churned" not in df.columns:
        return df.copy()
    return df[df["churned"] == 0].copy()


# =========================================================
# 📊 ANÁLISE EXPLORATÓRIA DE CHURN
# =========================================================
def churn_analysis(df):
    print("\n📊 INICIANDO ANÁLISE DE CHURN\n")

    revenue_col = _get_revenue_column(df)
    df = df.copy()

    churn_rate = df["churned"].mean()
    print(f"🔴 Churn geral: {churn_rate:.2%}")

    try:
        df["revenue_segment"] = pd.qcut(
            df[revenue_col],
            q=3,
            labels=["Baixo", "Médio", "Alto"],
            duplicates="drop"
        )
        revenue_churn = df.groupby("revenue_segment", observed=False)["churned"].mean()
        print("\n💰 Churn por Receita:")
        print(revenue_churn)
    except Exception as e:
        print(f"⚠️ Falha em segmentação por receita: {e}")

    try:
        df["usage_segment"] = pd.qcut(
            df["avg_usage_count"],
            q=2,
            labels=["Baixo uso", "Alto uso"],
            duplicates="drop"
        )
        usage_churn = df.groupby("usage_segment", observed=False)["churned"].mean()
        print("\n📈 Churn por uso:")
        print(usage_churn)
    except Exception as e:
        print(f"⚠️ Falha em segmentação por uso: {e}")

    try:
        df["error_segment"] = pd.qcut(
            df["avg_errors"],
            q=2,
            labels=["Baixo erro", "Alto erro"],
            duplicates="drop"
        )
        error_churn = df.groupby("error_segment", observed=False)["churned"].mean()
        print("\n⚠️ Churn por erro:")
        print(error_churn)
    except Exception as e:
        print(f"⚠️ Falha em segmentação por erros: {e}")

    print("\n✅ Análise concluída!")


# =========================================================
# 📊 PARETO ABC (SOMENTE CONTAS ATIVAS)
# =========================================================
def pareto_analysis(df):
    print("\n💰 ANÁLISE DE PARETO (CURVA ABC) — CONTAS ATIVAS\n")

    revenue_col = _get_revenue_column(df)
    active_df = _get_active_df(df)

    if active_df.empty:
        summary = pd.DataFrame(
            columns=[
                "segment",
                "num_accounts",
                "total_mrr",
                "churn_rate",
                "revenue_share",
                "high_risk_accounts",
                "high_risk_rate",
            ]
        )
        print("⚠️ Nenhuma conta ativa encontrada. Pareto não pôde ser calculado.")
        return active_df, summary

    df_sorted = active_df.sort_values(by=revenue_col, ascending=False).copy()
    total_revenue = df_sorted[revenue_col].sum()

    if total_revenue <= 0:
        summary = pd.DataFrame(
            columns=[
                "segment",
                "num_accounts",
                "total_mrr",
                "churn_rate",
                "revenue_share",
                "high_risk_accounts",
                "high_risk_rate",
            ]
        )
        print("⚠️ Receita total ativa igual a zero. Pareto não pôde ser calculado.")
        return df_sorted, summary

    df_sorted["cum_revenue"] = df_sorted[revenue_col].cumsum()
    df_sorted["cum_perc"] = df_sorted["cum_revenue"] / total_revenue

    def classify(p):
        if p <= 0.70:
            return "A"
        elif p <= 0.90:
            return "B"
        return "C"

    df_sorted["segment"] = df_sorted["cum_perc"].apply(classify)

    if "risk_level" in df_sorted.columns:
        df_sorted["is_high_risk"] = (df_sorted["risk_level"] == "Alto").astype(int)
    else:
        df_sorted["is_high_risk"] = 0

    summary = df_sorted.groupby("segment", observed=False).agg({
        "account_id": "count",
        revenue_col: "sum",
        "churned": "mean",
        "is_high_risk": "sum"
    }).reset_index()

    summary.columns = [
        "segment",
        "num_accounts",
        "total_mrr",
        "churn_rate",
        "high_risk_accounts"
    ]

    summary["revenue_share"] = summary["total_mrr"] / total_revenue
    summary["high_risk_rate"] = summary.apply(
        lambda x: x["high_risk_accounts"] / x["num_accounts"] if x["num_accounts"] > 0 else 0,
        axis=1
    )

    print(summary)

    return df_sorted, summary


# =========================================================
# 📊 SEGMENTAÇÃO EXECUTIVA (SOMENTE CONTAS ATIVAS)
# =========================================================
def revenue_segmentation_executive(df):
    print("\n💰 SEGMENTAÇÃO EXECUTIVA (COM CHURN PREDITIVO)\n")

    revenue_col = _get_revenue_column(df)
    df = df.copy()

    # Criar faixas na base principal primeiro
    df["mrr_group"] = pd.qcut(
        df[revenue_col],
        5,
        duplicates="drop"
    )

    # Agora sim separar ativos e inativos já com mrr_group
    active_df = df[df["churned"] == 0].copy()
    inactive_df = df[df["churned"] == 1].copy()

    # Garantir churn_score
    if "churn_score" not in df.columns:
        df["churn_score"] = 0.0
        active_df["churn_score"] = 0.0

    # Base principal por faixa
    summary = df.groupby("mrr_group", observed=False).agg(
        num_contas=("account_id", "count"),
        receita_total=(revenue_col, "sum"),
        churn_rate=("churned", "mean")
    ).reset_index()

    # MRR ativo por faixa
    active_mrr = active_df.groupby("mrr_group", observed=False)[revenue_col].sum().reset_index()
    active_mrr.columns = ["mrr_group", "active_mrr"]

    # MRR inativo por faixa
    inactive_mrr = inactive_df.groupby("mrr_group", observed=False)[revenue_col].sum().reset_index()
    inactive_mrr.columns = ["mrr_group", "inactive_mrr"]

    # Churn preditivo médio por faixa (somente ativos)
    predictive = active_df.groupby("mrr_group", observed=False)["churn_score"].mean().reset_index()
    predictive.columns = ["mrr_group", "avg_churn_score"]

    # Faixa legível
    ranges = df.groupby("mrr_group", observed=False)[revenue_col].agg(["min", "max"]).reset_index()

    # Merges
    summary = summary.merge(active_mrr, on="mrr_group", how="left")
    summary = summary.merge(inactive_mrr, on="mrr_group", how="left")
    summary = summary.merge(predictive, on="mrr_group", how="left")
    summary = summary.merge(ranges, on="mrr_group", how="left")

    # Tratar nulos
    summary["active_mrr"] = summary["active_mrr"].fillna(0.0)
    summary["inactive_mrr"] = summary["inactive_mrr"].fillna(0.0)
    summary["avg_churn_score"] = summary["avg_churn_score"].fillna(0.0)

    # Faixa legível
    summary["faixa_mrr"] = summary.apply(
        lambda x: f"${int(x['min'])} - ${int(x['max'])}",
        axis=1
    )

    # Percentuais
    total_accounts = df.shape[0]
    total_revenue = df[revenue_col].sum()

    summary["%_contas"] = summary["num_contas"] / total_accounts if total_accounts > 0 else 0
    summary["%_receita"] = summary["receita_total"] / total_revenue if total_revenue > 0 else 0

    # Ordenação
    summary = summary.sort_values(by="min")

    # Seleção final
    summary = summary[[
        "faixa_mrr",
        "num_contas",
        "receita_total",
        "active_mrr",
        "inactive_mrr",
        "churn_rate",
        "avg_churn_score",
        "%_contas",
        "%_receita"
    ]]

    print(summary)

    return summary


# =========================================================
# 📊 KPI EXECUTIVO COMPLETO
# =========================================================
def build_executive_kpis(df):
    revenue_col = _get_revenue_column(df)
    df = df.copy()

    total_accounts = int(df.shape[0])
    churned_accounts = int(df["churned"].sum()) if "churned" in df.columns else 0

    active_df = _get_active_df(df)
    inactive_df = df[df["churned"] == 1].copy() if "churned" in df.columns else pd.DataFrame()

    active_accounts = int(active_df.shape[0])
    inactive_accounts = int(inactive_df.shape[0])

    total_mrr = float(df[revenue_col].sum()) if total_accounts > 0 else 0.0
    active_mrr = float(active_df[revenue_col].sum()) if active_accounts > 0 else 0.0
    inactive_mrr = float(inactive_df[revenue_col].sum()) if inactive_accounts > 0 else 0.0

    churn_rate_total = churned_accounts / total_accounts if total_accounts > 0 else 0.0
    revenue_churn = inactive_mrr / total_mrr if total_mrr > 0 else 0.0

    arpu_total = total_mrr / total_accounts if total_accounts > 0 else 0.0
    arpu_active = active_mrr / active_accounts if active_accounts > 0 else 0.0
    arpu_inactive = inactive_mrr / inactive_accounts if inactive_accounts > 0 else 0.0

    if "risk_level" in active_df.columns:
        risk_df = active_df[active_df["risk_level"] == "Alto"].copy()
        high_risk_active_accounts = int(risk_df.shape[0])
        risk_mrr = float(risk_df[revenue_col].sum()) if high_risk_active_accounts > 0 else 0.0

        high = int((active_df["risk_level"] == "Alto").sum())
        medium = int((active_df["risk_level"] == "Médio").sum())
        low = int((active_df["risk_level"] == "Baixo").sum())
    else:
        high_risk_active_accounts = 0
        risk_mrr = 0.0
        high, medium, low = 0, 0, 0

    arpu_risk = risk_mrr / high_risk_active_accounts if high_risk_active_accounts > 0 else 0.0

    # LTV proxy conservador baseado em churn histórico total
    ltv_total = arpu_total / churn_rate_total if churn_rate_total > 0 else 0.0
    ltv_active = arpu_active / churn_rate_total if churn_rate_total > 0 else 0.0
    ltv_inactive = arpu_inactive / churn_rate_total if churn_rate_total > 0 else 0.0
    ltv_risk = arpu_risk / churn_rate_total if churn_rate_total > 0 else 0.0

    kpis = {
        "customers": {
            "total": total_accounts,
            "active": active_accounts,
            "churned": churned_accounts,
            "inactive": inactive_accounts,
        },
        "revenue": {
            "mrr": total_mrr,
            "total_mrr": total_mrr,
            "active_mrr": active_mrr,
            "inactive_mrr": inactive_mrr,
            "mrr_at_risk": risk_mrr,
            "risk_mrr": risk_mrr,
            "revenue_churn": revenue_churn,
        },
        "arpu": {
            "total": arpu_total,
            "active": arpu_active,
            "inactive": arpu_inactive,
            "risk": arpu_risk,
        },
        "ltv": {
            "total": ltv_total,
            "active": ltv_active,
            "inactive": ltv_inactive,
            "risk": ltv_risk,
        },
        "churn": {
            "churn_rate": churn_rate_total,
            "churn_rate_total": churn_rate_total,
        },
        "risk": {
            "high_risk_accounts": high_risk_active_accounts,
            "high_risk_active_accounts": high_risk_active_accounts,
            "distribution": {
                "high": high,
                "medium": medium,
                "low": low,
            }
        }
    }

    print("\n📌 KPIs EXECUTIVOS")
    print(f"Total Accounts: {total_accounts}")
    print(f"Active Accounts: {active_accounts}")
    print(f"Inactive Accounts: {inactive_accounts}")
    print(f"Churned Accounts: {churned_accounts}")
    print(f"Total MRR: {total_mrr:.2f}")
    print(f"Active MRR: {active_mrr:.2f}")
    print(f"Inactive MRR: {inactive_mrr:.2f}")
    print(f"Risk MRR: {risk_mrr:.2f}")
    print(f"ARPU Total: {arpu_total:.2f}")
    print(f"ARPU Active: {arpu_active:.2f}")
    print(f"ARPU Inactive: {arpu_inactive:.2f}")
    print(f"ARPU Risk: {arpu_risk:.2f}")
    print(f"LTV Total: {ltv_total:.2f}")
    print(f"LTV Active: {ltv_active:.2f}")
    print(f"LTV Inactive: {ltv_inactive:.2f}")
    print(f"LTV Risk: {ltv_risk:.2f}")
    print(f"Churn Rate Total: {churn_rate_total:.2%}")
    print(f"Revenue Churn: {revenue_churn:.2%}")
    print(f"High Risk Active Accounts: {high_risk_active_accounts}")
    print(f"Risk Distribution Active Only: high={high}, medium={medium}, low={low}")

    return kpis