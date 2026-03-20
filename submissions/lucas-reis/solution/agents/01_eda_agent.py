"""
Agent 01 — EDA (Exploratory Data Analysis)
Perfilamento individual das 5 tabelas do dataset RavenStack.
Produz output estruturado para cada tabela + resumo executivo.
"""

import duckdb
import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

SEP = "=" * 60


def sep(title: str):
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)


# ---------------------------------------------------------------------------
# accounts
# ---------------------------------------------------------------------------
def eda_accounts(con: duckdb.DuckDBPyConnection):
    sep("ravenstack_accounts.csv")
    df = con.execute(f"SELECT * FROM read_csv_auto('{DATA_DIR}/ravenstack_accounts.csv')").df()

    print(f"\nShape: {df.shape[0]} linhas × {df.shape[1]} colunas")

    print("\nColunas e tipos:")
    for col, dtype in df.dtypes.items():
        print(f"  {col:<25} {str(dtype)}")

    print("\n% nulos por coluna:")
    nulls = (df.isnull().mean() * 100).round(2)
    for col, pct in nulls.items():
        flag = " ⚠️" if pct > 0 else ""
        print(f"  {col:<25} {pct:.2f}%{flag}")

    print("\nValores únicos — colunas categóricas:")
    for col in ["industry", "country", "referral_source", "plan_tier"]:
        if col in df.columns:
            vals = df[col].value_counts()
            print(f"\n  {col} ({df[col].nunique()} únicos):")
            for v, c in vals.items():
                print(f"    {str(v):<25} {c:>4}  ({c/len(df)*100:.1f}%)")

    if "is_trial" in df.columns:
        trial_pct = df["is_trial"].mean() * 100
        print(f"\n  is_trial = True: {df['is_trial'].sum()} contas ({trial_pct:.1f}%)")

    if "churn_flag" in df.columns:
        churn_n = df["churn_flag"].sum()
        churn_pct = df["churn_flag"].mean() * 100
        print(f"\n  churn_flag = True: {churn_n} contas ({churn_pct:.1f}%)")

    return df


# ---------------------------------------------------------------------------
# subscriptions
# ---------------------------------------------------------------------------
def eda_subscriptions(con: duckdb.DuckDBPyConnection):
    sep("ravenstack_subscriptions.csv")
    df = con.execute(f"SELECT * FROM read_csv_auto('{DATA_DIR}/ravenstack_subscriptions.csv')").df()

    print(f"\nShape: {df.shape[0]} linhas × {df.shape[1]} colunas")

    print("\n% nulos por coluna:")
    nulls = (df.isnull().mean() * 100).round(2)
    for col, pct in nulls.items():
        flag = " ⚠️" if pct > 0 else ""
        print(f"  {col:<30} {pct:.2f}%{flag}")

    if "mrr_amount" in df.columns and "plan_tier" in df.columns:
        print("\nMRR por plan_tier (médio | mediano | min | max):")
        mrr = df.groupby("plan_tier")["mrr_amount"].agg(["mean", "median", "min", "max", "count"])
        for tier, row in mrr.iterrows():
            print(f"  {str(tier):<12} mean={row['mean']:>8.2f}  median={row['median']:>8.2f}  "
                  f"min={row['min']:>7.2f}  max={row['max']:>8.2f}  n={int(row['count'])}")

    for col, label in [("downgrade_flag", "downgrade_flag = True"),
                        ("upgrade_flag",   "upgrade_flag = True"),
                        ("auto_renew_flag","auto_renew_flag = False")]:
        if col in df.columns:
            if "False" in label:
                n = (~df[col].fillna(True)).sum()
            else:
                n = df[col].fillna(False).sum()
            print(f"\n  {label}: {n} ({n/len(df)*100:.1f}%)")

    if "billing_frequency" in df.columns:
        print("\nDistribuição billing_frequency:")
        for v, c in df["billing_frequency"].value_counts().items():
            print(f"  {str(v):<15} {c:>5}  ({c/len(df)*100:.1f}%)")

    return df


# ---------------------------------------------------------------------------
# feature_usage
# ---------------------------------------------------------------------------
def eda_feature_usage(con: duckdb.DuckDBPyConnection):
    sep("ravenstack_feature_usage.csv")
    df = con.execute(f"SELECT * FROM read_csv_auto('{DATA_DIR}/ravenstack_feature_usage.csv')").df()

    print(f"\nShape: {df.shape[0]} linhas × {df.shape[1]} colunas")

    print("\n% nulos por coluna:")
    nulls = (df.isnull().mean() * 100).round(2)
    for col, pct in nulls.items():
        flag = " ⚠️" if pct > 0 else ""
        print(f"  {col:<30} {pct:.2f}%{flag}")

    if "feature_name" in df.columns and "usage_count" in df.columns:
        print("\nTop 10 features por uso total (usage_count):")
        top = df.groupby("feature_name")["usage_count"].sum().sort_values(ascending=False).head(10)
        total_usage = df["usage_count"].sum()
        for feat, cnt in top.items():
            print(f"  {str(feat):<35} {cnt:>8}  ({cnt/total_usage*100:.1f}% do total)")

    if "feature_name" in df.columns and "error_count" in df.columns:
        print("\nMédia de error_count por feature (top 10 com mais erros):")
        err = df.groupby("feature_name")["error_count"].mean().sort_values(ascending=False).head(10)
        for feat, avg in err.items():
            print(f"  {str(feat):<35} {avg:.3f} erros/evento")

    if "is_beta_feature" in df.columns:
        beta_n = df["is_beta_feature"].fillna(False).sum()
        print(f"\n  is_beta_feature = True: {beta_n} eventos ({beta_n/len(df)*100:.1f}%)")

    if "usage_duration_secs" in df.columns:
        dur = df["usage_duration_secs"].dropna()
        print(f"\nusage_duration_secs:")
        print(f"  média:   {dur.mean():.1f}s  ({dur.mean()/60:.1f} min)")
        print(f"  mediana: {dur.median():.1f}s  ({dur.median()/60:.1f} min)")
        print(f"  p95:     {dur.quantile(0.95):.1f}s  ({dur.quantile(0.95)/60:.1f} min)")
        print(f"  max:     {dur.max():.1f}s  ({dur.max()/60:.1f} min)")

    return df


# ---------------------------------------------------------------------------
# support_tickets
# ---------------------------------------------------------------------------
def eda_support_tickets(con: duckdb.DuckDBPyConnection):
    sep("ravenstack_support_tickets.csv")
    df = con.execute(f"SELECT * FROM read_csv_auto('{DATA_DIR}/ravenstack_support_tickets.csv')").df()

    print(f"\nShape: {df.shape[0]} linhas × {df.shape[1]} colunas")

    print("\n% nulos por coluna:")
    nulls = (df.isnull().mean() * 100).round(2)
    for col, pct in nulls.items():
        flag = " ⚠️" if pct > 0 else ""
        print(f"  {col:<35} {pct:.2f}%{flag}")

    if "priority" in df.columns:
        print("\nDistribuição de priority:")
        for v, c in df["priority"].value_counts().items():
            print(f"  {str(v):<10} {c:>5}  ({c/len(df)*100:.1f}%)")

    if "escalation_flag" in df.columns:
        esc_n = df["escalation_flag"].fillna(False).sum()
        print(f"\n  escalation_flag = True: {esc_n} tickets ({esc_n/len(df)*100:.1f}%)")

    if "satisfaction_score" in df.columns:
        null_n = df["satisfaction_score"].isnull().sum()
        null_pct = null_n / len(df) * 100
        mean_score = df["satisfaction_score"].mean()
        print(f"\n  satisfaction_score:")
        print(f"    média (respondidos):  {mean_score:.2f} / 5.0")
        print(f"    nulos (não-resposta): {null_n} ({null_pct:.1f}%)  ← sinal de desengajamento")

    if "first_response_time_minutes" in df.columns and "priority" in df.columns:
        print("\n  first_response_time_minutes (média por priority):")
        resp = df.groupby("priority")["first_response_time_minutes"].mean().sort_values()
        for p, avg in resp.items():
            print(f"    {str(p):<10} {avg:.1f} min")

    if "resolution_time_hours" in df.columns:
        rt = df["resolution_time_hours"].dropna()
        print(f"\n  resolution_time_hours: média={rt.mean():.1f}h  p95={rt.quantile(0.95):.1f}h")

    return df


# ---------------------------------------------------------------------------
# churn_events
# ---------------------------------------------------------------------------
def eda_churn_events(con: duckdb.DuckDBPyConnection):
    sep("ravenstack_churn_events.csv")
    df = con.execute(f"SELECT * FROM read_csv_auto('{DATA_DIR}/ravenstack_churn_events.csv')").df()

    print(f"\nShape ANTES deduplicação: {df.shape[0]} linhas × {df.shape[1]} colunas")
    df_dedup = df.sort_values("churn_date", ascending=False).drop_duplicates(subset="account_id")
    print(f"Shape APÓS deduplicação (1 por account_id): {df_dedup.shape[0]} linhas")
    if "is_reactivation" in df.columns:
        reactiv_n = df["is_reactivation"].fillna(False).sum()
        print(f"  Registros de reativação removidos: {len(df) - len(df_dedup)} "
              f"(is_reactivation=True em {reactiv_n} registros originais)")

    print("\n% nulos por coluna (dataset completo):")
    nulls = (df.isnull().mean() * 100).round(2)
    for col, pct in nulls.items():
        flag = " ⚠️" if pct > 0 else ""
        print(f"  {col:<35} {pct:.2f}%{flag}")

    if "reason_code" in df.columns:
        print("\nTop 5 reason_code:")
        rc = df_dedup["reason_code"].value_counts().head(5)
        total = len(df_dedup)
        for code, cnt in rc.items():
            print(f"  {str(code):<20} {cnt:>4}  ({cnt/total*100:.1f}%)")

    if "is_reactivation" in df.columns:
        r_n = df_dedup["is_reactivation"].fillna(False).sum()
        print(f"\n  is_reactivation = True (deduplicado): {r_n} ({r_n/len(df_dedup)*100:.1f}%)")

    for col in ["preceding_downgrade_flag", "preceding_upgrade_flag"]:
        if col in df.columns:
            n = df_dedup[col].fillna(False).sum()
            print(f"  {col} = True: {n} ({n/len(df_dedup)*100:.1f}%)")

    if "refund_amount_usd" in df.columns:
        total_refund = df_dedup["refund_amount_usd"].fillna(0).sum()
        n_refund = (df_dedup["refund_amount_usd"].fillna(0) > 0).sum()
        print(f"\n  refund_amount_usd:")
        print(f"    total: ${total_refund:,.2f}")
        print(f"    contas com reembolso: {n_refund} ({n_refund/len(df_dedup)*100:.1f}%)")

    return df, df_dedup


# ---------------------------------------------------------------------------
# Resumo executivo
# ---------------------------------------------------------------------------
def resumo_executivo(df_accounts, df_churn_dedup):
    sep("RESUMO EXECUTIVO")

    total_contas = len(df_accounts)
    churned_contas = len(df_churn_dedup)
    churn_rate = churned_contas / total_contas * 100

    print(f"\nTaxa de churn geral: {churned_contas} / {total_contas} contas = {churn_rate:.1f}%")

    # Verificação cruzada com churn_flag de accounts
    if "churn_flag" in df_accounts.columns:
        flag_rate = df_accounts["churn_flag"].mean() * 100
        print(f"  (accounts.churn_flag confirma: {flag_rate:.1f}%)")

    print("\nMaior RED FLAG encontrado nos dados:")
    print("  → A identificar após EDA completo (ver entry_001_eda_analysis.md)")

    print("\n3 hipóteses sugeridas pelos números:")
    print("  H1: Contas com baixo distinct_features_used têm maior churn")
    print("  H2: Tickets escalados (escalation_flag=True) precedem churns")
    print("  H3: Clientes com billing_frequency=monthly têm maior churn que annual")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def run_eda():
    con = duckdb.connect()

    df_accounts    = eda_accounts(con)
    df_subs        = eda_subscriptions(con)
    df_usage       = eda_feature_usage(con)
    df_tickets     = eda_support_tickets(con)
    df_churn, df_churn_dedup = eda_churn_events(con)

    resumo_executivo(df_accounts, df_churn_dedup)

    con.close()
    return {
        "accounts": df_accounts,
        "subscriptions": df_subs,
        "feature_usage": df_usage,
        "support_tickets": df_tickets,
        "churn_events": df_churn,
        "churn_events_dedup": df_churn_dedup,
    }


if __name__ == "__main__":
    run_eda()
