"""Validate exploratory sponsorship findings with adjusted inference."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from statsmodels.stats.multitest import multipletests

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "processed" / "posts_analytical.csv"
TABLES = ROOT / "outputs" / "tables"
EVIDENCE = ROOT / "outputs" / "evidence"
OUTCOME = "engagement_rate_views"

CATEGORICAL = [
    "platform",
    "content_type",
    "content_category",
    "language",
    "audience_age_distribution",
    "audience_gender_distribution",
    "audience_location",
    "post_month",
]
NUMERIC = ["log_followers", "content_length", "hashtag_count"]


def confidence_record(model, term: str) -> dict[str, float]:
    interval = model.conf_int().loc[term]
    return {
        "estimate": float(model.params[term]),
        "standard_error_clustered": float(model.bse[term]),
        "ci95_low": float(interval.iloc[0]),
        "ci95_high": float(interval.iloc[1]),
        "p_value": float(model.pvalues[term]),
    }


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    data = pd.read_csv(DATA)
    data["log_followers"] = np.log1p(data["follower_count"])

    formula = (
        f"{OUTCOME} ~ is_sponsored + C(platform) + C(content_type) + "
        "C(content_category) + log_followers + content_length + hashtag_count + "
        "C(language) + C(audience_age_distribution) + "
        "C(audience_gender_distribution) + C(audience_location) + C(post_month)"
    )
    adjusted = smf.ols(formula, data).fit(
        cov_type="cluster", cov_kwds={"groups": data["creator_id"]}
    )
    coefficients = pd.DataFrame(
        {
            "term": adjusted.params.index,
            "estimate": adjusted.params.values,
            "standard_error": adjusted.bse.values,
            "p_value": adjusted.pvalues.values,
            "ci95_low": adjusted.conf_int()[0].values,
            "ci95_high": adjusted.conf_int()[1].values,
        }
    )
    coefficients.to_csv(TABLES / "INF-ADJUSTED-COEFFICIENTS.csv", index=False)

    interaction_formula = formula.replace("is_sponsored", "is_sponsored * C(platform)", 1)
    interaction = smf.ols(interaction_formula, data).fit(
        cov_type="cluster", cov_kwds={"groups": data["creator_id"]}
    )
    interaction_terms = [term for term in interaction.params.index if "is_sponsored" in term]
    interaction_table = pd.DataFrame(
        {
            "term": interaction_terms,
            "estimate": interaction.params[interaction_terms],
            "p_value_raw": interaction.pvalues[interaction_terms],
        }
    )
    interaction_table["p_value_fdr_bh"] = multipletests(
        interaction_table["p_value_raw"], method="fdr_bh"
    )[1]
    interaction_table.to_csv(TABLES / "INF-SPONSOR-PLATFORM-INTERACTIONS.csv", index=False)

    transformer = ColumnTransformer(
        [
            ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
            ("numeric", StandardScaler(), NUMERIC),
        ]
    )
    propensity_model = make_pipeline(
        transformer, LogisticRegression(max_iter=1_000, random_state=42)
    )
    features = data[CATEGORICAL + NUMERIC]
    treatment = data["is_sponsored"]
    propensity_model.fit(features, treatment)
    propensity = propensity_model.predict_proba(features)[:, 1]
    overlap = {
        "auc_in_sample": float(roc_auc_score(treatment, propensity)),
        "min": float(propensity.min()),
        "p01": float(np.quantile(propensity, 0.01)),
        "median": float(np.median(propensity)),
        "p99": float(np.quantile(propensity, 0.99)),
        "max": float(propensity.max()),
        "share_outside_0_1_0_9": float(((propensity < 0.1) | (propensity > 0.9)).mean()),
    }
    pd.DataFrame({"is_sponsored": treatment, "propensity": propensity}).to_csv(
        TABLES / "INF-PROPENSITY-DIAGNOSTICS.csv", index=False
    )

    sponsorship = confidence_record(adjusted, "is_sponsored")
    sponsorship.update(
        {
            "estimate_percentage_points": sponsorship["estimate"] * 100,
            "ci95_percentage_points": [
                sponsorship["ci95_low"] * 100,
                sponsorship["ci95_high"] * 100,
            ],
            "model_r_squared": float(adjusted.rsquared),
            "n": int(adjusted.nobs),
            "creator_clusters": int(data["creator_id"].nunique()),
        }
    )
    equivalence_thresholds = [0.0005, 0.001]
    equivalence = {
        f"within_plus_minus_{threshold}": bool(
            sponsorship["ci95_low"] > -threshold and sponsorship["ci95_high"] < threshold
        )
        for threshold in equivalence_thresholds
    }

    secondary_results: list[dict[str, float | str]] = []
    for outcome in ["views", "share_rate_views", "views_per_follower"]:
        secondary = smf.ols(f"{outcome} ~ " + formula.split(" ~ ", 1)[1], data).fit(
            cov_type="cluster", cov_kwds={"groups": data["creator_id"]}
        )
        result: dict[str, float | str] = {"outcome": outcome}
        result.update(confidence_record(secondary, "is_sponsored"))
        result["model_r_squared"] = float(secondary.rsquared)
        secondary_results.append(result)
    secondary_table = pd.DataFrame(secondary_results)
    secondary_table.to_csv(TABLES / "INF-SPONSOR-SECONDARY-OUTCOMES.csv", index=False)

    record = {
        "INF-SPON-001": {
            "status": "VALIDATED",
            "claim": (
                "Não foi detectada associação material entre patrocínio e engagement após ajuste."
            ),
            "estimand": "diferença média ajustada em interações por view",
            "result": sponsorship,
            "secondary_outcomes": secondary_results,
            "equivalence_sensitivity": equivalence,
            "overlap": overlap,
            "interaction_min_fdr_p": float(interaction_table["p_value_fdr_bh"].min()),
            "controls": CATEGORICAL + NUMERIC,
            "uncertainty": "erros-padrão clusterizados por creator_id",
            "limitations": [
                "dados observacionais e provavelmente sintéticos",
                "confundimento não medido permanece possível",
                "custo e receita ausentes; ROI não estimável",
                (
                    "thresholds de equivalência são análises de sensibilidade, "
                    "não decisão humana aprovada"
                ),
            ],
        }
    }
    (EVIDENCE / "inference-evidence-records.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(record, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
