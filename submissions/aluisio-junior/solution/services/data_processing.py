import pandas as pd


def _safe_numeric_fill(df, columns, fill_value=0):
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(fill_value)
    return df


def _find_first_existing_column(df, candidates):
    for col in candidates:
        if col in df.columns:
            return col
    return None


def build_analytical_dataset(accounts, subscriptions, feature_usage, support_tickets, churn_events):
    print("\n🔗 Iniciando construção do dataset analítico...")

    # Cópias defensivas
    accounts = accounts.copy()
    subscriptions = subscriptions.copy()
    feature_usage = feature_usage.copy()
    support_tickets = support_tickets.copy()
    churn_events = churn_events.copy()

    # -----------------------------
    # 📊 0. Padronização mínima
    # -----------------------------
    subscriptions = _safe_numeric_fill(
        subscriptions,
        ["mrr_amount", "arr_amount", "seats"]
    )

    feature_usage = _safe_numeric_fill(
        feature_usage,
        ["usage_count", "usage_duration_secs", "error_count"]
    )

    support_tickets = _safe_numeric_fill(
        support_tickets,
        [
            "resolution_time_hours",
            "first_response_time_minutes",
            "satisfaction_score",
            "escalation_flag"
        ]
    )

    # -----------------------------
    # 📊 1. Receita (subscriptions)
    # -----------------------------
    # IMPORTANTE:
    # Mantemos avg_* para não quebrar o modelo atual,
    # mas também criamos colunas totais corretas para KPIs executivos.
    revenue = subscriptions.groupby("account_id").agg(
        mrr=("mrr_amount", "sum"),
        avg_mrr=("mrr_amount", "mean"),
        arr=("arr_amount", "sum"),
        avg_arr=("arr_amount", "mean"),
        seats=("seats", "sum"),
        avg_seats=("seats", "mean"),
        subscription_count=("subscription_id", "nunique")
    ).reset_index()

    print("✅ Receita agregada")

    # -----------------------------
    # 📈 2. Uso (feature_usage)
    # -----------------------------
    usage = feature_usage.groupby("subscription_id").agg(
        usage_count=("usage_count", "sum"),
        usage_duration_secs=("usage_duration_secs", "sum"),
        error_count=("error_count", "sum")
    ).reset_index()

    usage = usage.merge(
        subscriptions[["subscription_id", "account_id"]],
        on="subscription_id",
        how="left"
    )

    usage = usage.groupby("account_id").agg(
        avg_usage_count=("usage_count", "mean"),
        total_usage_count=("usage_count", "sum"),
        avg_usage_duration=("usage_duration_secs", "mean"),
        total_usage_duration=("usage_duration_secs", "sum"),
        avg_errors=("error_count", "mean"),
        total_errors=("error_count", "sum")
    ).reset_index()

    print("✅ Uso agregado")

    # -----------------------------
    # 🎧 3. Suporte (tickets)
    # -----------------------------
    support = support_tickets.groupby("account_id").agg(
        avg_resolution_time=("resolution_time_hours", "mean"),
        avg_first_response=("first_response_time_minutes", "mean"),
        avg_satisfaction=("satisfaction_score", "mean"),
        total_escalations=("escalation_flag", "sum"),
        total_tickets=("account_id", "count")
    ).reset_index()

    print("✅ Suporte agregado")

    # -----------------------------
    # ⚠️ 4. Churn
    # -----------------------------
    churn = churn_events[["account_id"]].copy()
    churn["churned"] = 1
    churn = churn.groupby("account_id", as_index=False)["churned"].max()

    print("✅ Churn identificado")

    # -----------------------------
    # 🔗 5. Merge final
    # -----------------------------
    df = accounts.merge(revenue, on="account_id", how="left")
    df = df.merge(usage, on="account_id", how="left")
    df = df.merge(support, on="account_id", how="left")
    df = df.merge(churn, on="account_id", how="left")

    # -----------------------------
    # 🧼 6. Tratamento de nulos
    # -----------------------------
    numeric_cols = [
        "mrr",
        "avg_mrr",
        "arr",
        "avg_arr",
        "seats",
        "avg_seats",
        "subscription_count",
        "avg_usage_count",
        "total_usage_count",
        "avg_usage_duration",
        "total_usage_duration",
        "avg_errors",
        "total_errors",
        "avg_resolution_time",
        "avg_first_response",
        "avg_satisfaction",
        "total_escalations",
        "total_tickets",
        "churned"
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["churned"] = df["churned"].astype(int)

    # -----------------------------
    # 🧠 7. Flags auxiliares para KPIs
    # -----------------------------
    # Como é um snapshot, usamos receita > 0 como proxy de conta ativa.
    df["is_active"] = (df["mrr"] > 0).astype(int)

    # Revenue at-risk será calculado depois com risk_level,
    # mas já deixamos a base correta pronta.
    df["support_risk_score"] = (
        df["avg_resolution_time"].fillna(0) * 0.25 +
        df["avg_first_response"].fillna(0) * 0.15 +
        (5 - df["avg_satisfaction"].clip(lower=0, upper=5)).fillna(0) * 10 +
        df["total_escalations"].fillna(0) * 2
    )

    # Proxy simples de queda de uso: quando média é baixa em relação ao total por conta.
    # Não é série temporal ainda, mas ajuda em análises iniciais.
    df["usage_drop_proxy"] = (
        (df["total_usage_count"] - df["avg_usage_count"]).clip(lower=0)
    )

    print("✅ Dataset analítico criado!")
    print("\n📊 Shape final:", df.shape)

    expected_cols = [
        "account_id",
        "mrr",
        "avg_mrr",
        "arr",
        "avg_arr",
        "seats",
        "avg_seats",
        "subscription_count",
        "avg_usage_count",
        "total_usage_count",
        "avg_usage_duration",
        "total_usage_duration",
        "avg_errors",
        "total_errors",
        "avg_resolution_time",
        "avg_first_response",
        "avg_satisfaction",
        "total_escalations",
        "total_tickets",
        "support_risk_score",
        "usage_drop_proxy",
        "is_active",
        "churned"
    ]

    existing_expected = [col for col in expected_cols if col in df.columns]
    print("\n📌 Colunas-chave geradas:")
    print(existing_expected)

    return df