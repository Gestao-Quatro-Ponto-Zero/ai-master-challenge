from __future__ import annotations

import numpy as np
import pandas as pd


FEATURE_LABELS = {
    "active_subscriptions": "Assinaturas ativas",
    "auto_renew_flag": "Auto-renovação",
    "avg_first_response_min": "Tempo de primeira resposta",
    "avg_resolution_hours": "Tempo médio de resolução",
    "avg_satisfaction": "Satisfação média de suporte",
    "avg_usage_per_event_30d": "Uso médio por evento (30d)",
    "beta_events_30d": "Uso de features beta (30d)",
    "billing_frequency": "Frequência de cobrança",
    "country": "País",
    "current_arr": "ARR atual",
    "current_billing_frequency": "Cobrança atual",
    "current_mrr": "MRR atual",
    "days_since_last_ticket": "Dias desde o último ticket",
    "days_since_last_usage": "Dias desde o último uso",
    "days_since_signup": "Tempo de relacionamento",
    "distinct_features": "Features distintas usadas",
    "downgrade_count": "Qtd. de downgrades",
    "error_rate_30d": "Taxa de erro (30d)",
    "escalation_count": "Qtd. de escalonamentos",
    "escalation_rate": "Taxa de escalonamento",
    "feature_churns": "Churns por falta de feature",
    "features_30d": "Features usadas (30d)",
    "high_tickets": "Tickets high",
    "industry": "Indústria",
    "is_current_trial": "Trial atual",
    "last_churn_was_reactivation": "Último churn foi reativação",
    "no_auto_renew": "Sem auto-renovação",
    "observed_churn_flag": "Flag observada de churn",
    "plan_tier": "Plano",
    "preceding_downgrade_events": "Downgrades prévios ao churn",
    "preceding_upgrade_events": "Upgrades prévios ao churn",
    "pricing_churns": "Churns por preço",
    "reactivation_events": "Eventos de reativação",
    "revenue_band": "Faixa de receita",
    "seats": "Assentos",
    "signup_month": "Mês de entrada",
    "support_burden_index": "Índice de carga de suporte",
    "support_churns": "Churns por suporte",
    "ticket_count": "Qtd. de tickets",
    "total_errors": "Erros totais",
    "total_refund_amount": "Valor total de refund",
    "total_usage_count": "Uso total",
    "upgrade_count": "Qtd. de upgrades",
    "urgent_ticket_rate": "Taxa de tickets urgentes",
    "urgent_tickets": "Tickets urgentes",
    "usage_count_30d": "Uso nos últimos 30 dias",
    "usage_count_prev_30d": "Uso nos 30 dias anteriores",
    "usage_drop_ratio": "Queda recente de uso",
    "usage_events_30d": "Eventos de uso (30d)",
    "usage_health_band": "Faixa de saúde de uso",
}


def feature_label(feature_name: str) -> str:
    return FEATURE_LABELS.get(
        feature_name,
        str(feature_name).replace("_", " ").strip().capitalize(),
    )


def aggregate_transformed_feature_importance(
    transformed_feature_names: list[str] | np.ndarray,
    importances: np.ndarray,
    original_feature_columns: list[str],
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for transformed_name, importance in zip(transformed_feature_names, importances):
        transformed_name = str(transformed_name)
        raw_feature = transformed_name
        if transformed_name.startswith("num__"):
            raw_feature = transformed_name.removeprefix("num__")
        elif transformed_name.startswith("cat__"):
            raw_feature = transformed_name.removeprefix("cat__")
            matched = next(
                (column for column in original_feature_columns if raw_feature == column or raw_feature.startswith(f"{column}_")),
                raw_feature,
            )
            raw_feature = matched

        rows.append(
            {
                "feature": raw_feature,
                "transformed_feature": transformed_name,
                "importance": float(importance),
            }
        )

    aggregated = (
        pd.DataFrame(rows)
        .groupby("feature", as_index=False)
        .agg(
            importance=("importance", "sum"),
            transformed_features=("transformed_feature", "count"),
        )
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )
    total_importance = float(aggregated["importance"].sum()) if not aggregated.empty else 0.0
    aggregated["normalized_importance"] = np.where(
        total_importance > 0,
        aggregated["importance"] / total_importance,
        0.0,
    )
    aggregated["feature_label"] = aggregated["feature"].map(feature_label)
    return aggregated


def build_reference_profile(reference_df: pd.DataFrame, feature_columns: list[str]) -> dict[str, object]:
    profile: dict[str, object] = {}
    scoped = reference_df.reindex(columns=feature_columns).copy()

    for column in feature_columns:
        series = scoped[column]
        if pd.api.types.is_numeric_dtype(series) or pd.api.types.is_bool_dtype(series):
            profile[column] = pd.to_numeric(series, errors="coerce").median()
        else:
            non_null = series.dropna()
            profile[column] = non_null.mode().iloc[0] if not non_null.empty else None
    return profile


def _serialize_feature_value(value: object) -> str:
    if pd.isna(value):
        return "-"
    if isinstance(value, (bool, np.bool_)):
        return "True" if bool(value) else "False"
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.3f}"
    return str(value)


def _build_local_explanation_text(
    feature_name: str,
    feature_value: object,
    baseline_value: object,
    local_impact: float,
) -> str:
    impact_pp = abs(float(local_impact) * 100)
    if local_impact >= 0:
        return (
            f"{feature_label(feature_name)} em { _serialize_feature_value(feature_value) } "
            f"eleva o risco; ao aproximar do perfil típico ({_serialize_feature_value(baseline_value)}), "
            f"a probabilidade cairia cerca de {impact_pp:.1f} p.p."
        )
    return (
        f"{feature_label(feature_name)} em { _serialize_feature_value(feature_value) } "
        f"ajuda a conter o risco; se voltasse ao perfil típico ({_serialize_feature_value(baseline_value)}), "
        f"a probabilidade subiria cerca de {impact_pp:.1f} p.p."
    )


def build_account_explainability(
    model,
    scoring_dataset: pd.DataFrame,
    feature_columns: list[str],
    reference_dataset: pd.DataFrame,
    top_k: int = 3,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    scoring_X = scoring_dataset.reindex(columns=feature_columns).copy()
    baseline_profile = build_reference_profile(reference_dataset, feature_columns)
    base_probabilities = model.predict_proba(scoring_X)[:, 1]

    impact_rows: list[pd.DataFrame] = []
    account_index = scoring_dataset[["account_id"]].copy()

    for feature in feature_columns:
        perturbed = scoring_X.copy()
        perturbed[feature] = baseline_profile[feature]
        perturbed_probabilities = model.predict_proba(perturbed)[:, 1]
        feature_impacts = base_probabilities - perturbed_probabilities

        feature_frame = account_index.copy()
        feature_frame["feature"] = feature
        feature_frame["feature_label"] = feature_label(feature)
        feature_frame["feature_value"] = scoring_X[feature].map(_serialize_feature_value)
        feature_frame["baseline_value"] = _serialize_feature_value(baseline_profile[feature])
        feature_frame["local_impact"] = feature_impacts
        feature_frame["abs_local_impact"] = np.abs(feature_impacts)
        feature_frame["impact_direction"] = np.where(
            feature_impacts >= 0,
            "raises_risk",
            "reduces_risk",
        )
        feature_frame["explanation_text"] = [
            _build_local_explanation_text(
                feature_name=feature,
                feature_value=scoring_X.iloc[idx][feature],
                baseline_value=baseline_profile[feature],
                local_impact=feature_impacts[idx],
            )
            for idx in range(len(scoring_X))
        ]
        impact_rows.append(feature_frame)

    all_impacts = pd.concat(impact_rows, ignore_index=True)
    all_impacts["impact_pp"] = all_impacts["local_impact"] * 100.0

    positive_impacts = (
        all_impacts[all_impacts["local_impact"] > 0]
        .sort_values(["account_id", "local_impact", "feature_label"], ascending=[True, False, True])
        .groupby("account_id", as_index=False, group_keys=False)
        .head(top_k)
        .copy()
    )
    positive_impacts["rank"] = positive_impacts.groupby("account_id").cumcount() + 1

    protective = (
        all_impacts.sort_values(["account_id", "local_impact", "feature_label"], ascending=[True, True, True])
        .groupby("account_id", as_index=False, group_keys=False)
        .head(1)
        .copy()
    )
    protective = protective.rename(
        columns={
            "feature": "protective_feature",
            "feature_label": "protective_feature_label",
            "feature_value": "protective_feature_value",
            "baseline_value": "protective_baseline_value",
            "local_impact": "protective_local_impact",
            "explanation_text": "protective_explanation_text",
        }
    )[
        [
            "account_id",
            "protective_feature",
            "protective_feature_label",
            "protective_feature_value",
            "protective_baseline_value",
            "protective_local_impact",
            "protective_explanation_text",
        ]
    ]

    top_one = positive_impacts[positive_impacts["rank"] == 1].rename(
        columns={
            "feature": "current_primary_model_driver",
            "feature_label": "current_primary_model_driver_label",
            "feature_value": "current_primary_model_driver_value",
            "baseline_value": "current_primary_model_driver_baseline",
            "local_impact": "current_primary_model_driver_impact",
            "explanation_text": "current_primary_model_driver_explanation",
        }
    )
    top_two = positive_impacts[positive_impacts["rank"] == 2].rename(
        columns={
            "feature": "current_secondary_model_driver",
            "feature_label": "current_secondary_model_driver_label",
            "feature_value": "current_secondary_model_driver_value",
            "baseline_value": "current_secondary_model_driver_baseline",
            "local_impact": "current_secondary_model_driver_impact",
            "explanation_text": "current_secondary_model_driver_explanation",
        }
    )

    summary = account_index.merge(
        top_one[
            [
                "account_id",
                "current_primary_model_driver",
                "current_primary_model_driver_label",
                "current_primary_model_driver_value",
                "current_primary_model_driver_baseline",
                "current_primary_model_driver_impact",
                "current_primary_model_driver_explanation",
            ]
        ],
        on="account_id",
        how="left",
    ).merge(
        top_two[
            [
                "account_id",
                "current_secondary_model_driver",
                "current_secondary_model_driver_label",
                "current_secondary_model_driver_value",
                "current_secondary_model_driver_baseline",
                "current_secondary_model_driver_impact",
                "current_secondary_model_driver_explanation",
            ]
        ],
        on="account_id",
        how="left",
    ).merge(
        protective,
        on="account_id",
        how="left",
    )

    summary["current_model_driver_summary"] = summary.apply(
        lambda row: " | ".join(
            [
                part
                for part in [
                    f"Modelo: {row['current_primary_model_driver_label']}"
                    if pd.notna(row.get("current_primary_model_driver_label"))
                    else "",
                    f"2º sinal: {row['current_secondary_model_driver_label']}"
                    if pd.notna(row.get("current_secondary_model_driver_label"))
                    else "",
                    f"Proteção: {row['protective_feature_label']}"
                    if pd.notna(row.get("protective_feature_label")) and float(row.get("protective_local_impact", 0) or 0) < 0
                    else "",
                ]
            ]
        ),
        axis=1,
    )
    summary["current_model_explanation"] = summary.apply(
        lambda row: (
            row["current_primary_model_driver_explanation"]
            if pd.notna(row.get("current_primary_model_driver_explanation"))
            else "Modelo sem driver local dominante para esta conta."
        ),
        axis=1,
    )

    return positive_impacts.reset_index(drop=True), summary.reset_index(drop=True), all_impacts.reset_index(drop=True)


def build_global_explainability(
    aggregated_feature_importance: pd.DataFrame,
    all_local_impacts: pd.DataFrame,
    top_k: int = 12,
) -> pd.DataFrame:
    local_summary = (
        all_local_impacts.groupby(["feature", "feature_label"], as_index=False)
        .agg(
            avg_signed_impact=("local_impact", "mean"),
            avg_abs_impact=("abs_local_impact", "mean"),
            median_abs_impact=("abs_local_impact", "median"),
            accounts_raising_risk=("impact_direction", lambda s: int((s == "raises_risk").sum())),
            accounts_reducing_risk=("impact_direction", lambda s: int((s == "reduces_risk").sum())),
            sample_size=("account_id", "count"),
        )
    )
    local_summary["raising_share"] = np.where(
        local_summary["sample_size"] > 0,
        local_summary["accounts_raising_risk"] / local_summary["sample_size"],
        0.0,
    )
    local_summary["portfolio_direction"] = np.where(
        local_summary["avg_signed_impact"] >= 0,
        "elevates_risk",
        "reduces_risk",
    )
    local_summary["impact_statement"] = local_summary.apply(
        lambda row: (
            f"{row['feature_label']} tende a elevar risco no portfólio; ao voltar ao perfil típico, "
            f"a probabilidade mudaria em média {abs(float(row['avg_signed_impact']) * 100):.1f} p.p."
            if row["avg_signed_impact"] >= 0
            else f"{row['feature_label']} atua mais como fator protetivo; ao perder esse perfil, "
            f"a probabilidade mudaria em média {abs(float(row['avg_signed_impact']) * 100):.1f} p.p."
        ),
        axis=1,
    )

    global_explainability = aggregated_feature_importance.merge(
        local_summary,
        on=["feature", "feature_label"],
        how="left",
    )
    for col in ["avg_signed_impact", "avg_abs_impact", "median_abs_impact", "raising_share"]:
        global_explainability[col] = pd.to_numeric(global_explainability[col], errors="coerce").fillna(0.0)
    global_explainability["portfolio_direction"] = global_explainability["portfolio_direction"].fillna("mixed")
    global_explainability["impact_statement"] = global_explainability["impact_statement"].fillna(
        global_explainability["feature_label"].map(lambda label: f"{label} aparece como variável relevante do modelo.")
    )

    return (
        global_explainability.sort_values(
            ["normalized_importance", "avg_abs_impact", "feature_label"],
            ascending=[False, False, True],
        )
        .head(top_k)
        .reset_index(drop=True)
    )
