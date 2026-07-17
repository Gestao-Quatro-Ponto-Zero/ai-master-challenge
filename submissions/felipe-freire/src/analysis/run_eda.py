"""Generate reproducible exploratory tables, figures, and evidence records."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
import pandas as pd
import seaborn as sns

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "processed" / "posts_analytical.csv"
TABLES = ROOT / "outputs" / "tables"
FIGURES = ROOT / "outputs" / "figures"
EVIDENCE = ROOT / "outputs" / "evidence"
METRIC = "engagement_rate_views"


def group_summary(data: pd.DataFrame, dimensions: list[str]) -> pd.DataFrame:
    """Return a consistent descriptive summary for one or more dimensions."""
    return (
        data.groupby(dimensions, observed=True)
        .agg(
            n=("id", "size"),
            engagement_mean=(METRIC, "mean"),
            engagement_median=(METRIC, "median"),
            engagement_std=(METRIC, "std"),
            views_mean=("views", "mean"),
            shares_mean=("shares", "mean"),
            comments_mean=("comments_count", "mean"),
            views_per_follower_median=("views_per_follower", "median"),
        )
        .reset_index()
    )


def save_table(frame: pd.DataFrame, name: str) -> None:
    frame.to_csv(TABLES / name, index=False, float_format="%.8f")


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    data = pd.read_csv(DATA, parse_dates=["post_datetime"])

    required = {METRIC, "platform", "content_type", "content_category", "creator_size"}
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"missing analytical columns: {sorted(missing)}")
    if len(data) != 52_214:
        raise ValueError(f"unexpected row count: {len(data)}")

    overview = pd.DataFrame(
        {
            "metric": ["rows", "creators", "date_min", "date_max", "sponsored_share"],
            "value": [
                len(data),
                data["creator_id"].nunique(),
                data["post_datetime"].min().isoformat(),
                data["post_datetime"].max().isoformat(),
                data["is_sponsored"].mean(),
            ],
        }
    )
    save_table(overview, "EDA-OVERVIEW.csv")

    dimensions = [
        "platform",
        "content_type",
        "content_category",
        "creator_size",
        "is_sponsored",
        "audience_age_distribution",
        "audience_gender_distribution",
        "audience_location",
        "language",
    ]
    summaries: dict[str, pd.DataFrame] = {}
    for dimension in dimensions:
        summaries[dimension] = group_summary(data, [dimension])
        save_table(summaries[dimension], f"EDA-BY-{dimension.upper()}.csv")

    combinations = group_summary(
        data, ["platform", "content_type", "content_category", "creator_size"]
    )
    combinations = combinations.loc[combinations["n"] >= 100].sort_values(
        "engagement_mean", ascending=False
    )
    save_table(combinations, "EDA-COMBINATIONS-N100.csv")

    sponsor = group_summary(data, ["platform", "content_category", "creator_size", "is_sponsored"])
    sponsor_pivot = sponsor.pivot_table(
        index=["platform", "content_category", "creator_size"],
        columns="is_sponsored",
        values=["n", "engagement_mean", "views_mean"],
    )
    sponsor_pivot.columns = [
        f"{metric}_{'sponsored' if flag else 'organic'}" for metric, flag in sponsor_pivot.columns
    ]
    sponsor_pivot = sponsor_pivot.reset_index()
    sponsor_pivot["engagement_crude_diff"] = (
        sponsor_pivot["engagement_mean_sponsored"] - sponsor_pivot["engagement_mean_organic"]
    )
    sponsor_pivot["views_crude_diff"] = (
        sponsor_pivot["views_mean_sponsored"] - sponsor_pivot["views_mean_organic"]
    )
    save_table(sponsor_pivot, "EDA-SPONSOR-CRUDE-SEGMENTS.csv")

    monthly = group_summary(
        data.assign(month=data["post_datetime"].dt.to_period("M").astype(str)), ["month"]
    )
    save_table(monthly, "EDA-BY-MONTH.csv")

    correlations = data[
        [
            METRIC,
            "views",
            "likes",
            "shares",
            "comments_count",
            "follower_count",
            "content_length",
            "hashtag_count",
        ]
    ].corr(numeric_only=True)
    correlations.to_csv(TABLES / "EDA-CORRELATIONS.csv", float_format="%.8f")

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.histplot(data=data, x=METRIC, bins=50, ax=ax, color="#2563EB")
    ax.set(
        title="Engagement por view é fortemente concentrado",
        xlabel="Interações por view",
        ylabel="Posts",
    )
    fig.tight_layout()
    fig.savefig(FIGURES / "EDA-ENGAGEMENT-DISTRIBUTION.png", dpi=160)
    plt.close(fig)

    platform = summaries["platform"].sort_values("engagement_mean", ascending=False)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    sns.barplot(data=platform, x="engagement_mean", y="platform", ax=ax, color="#2563EB")
    ax.set(
        title="Plataformas têm engagement médio praticamente indistinguível",
        xlabel="Interações por view (média)",
        ylabel="Plataforma",
    )
    ax.set_xlim(0, 0.21)
    fig.tight_layout()
    fig.savefig(FIGURES / "EDA-PLATFORM-ENGAGEMENT.png", dpi=160)
    plt.close(fig)

    sponsor_platform = group_summary(data, ["platform", "is_sponsored"])
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.pointplot(
        data=sponsor_platform,
        x="platform",
        y="engagement_mean",
        hue="is_sponsored",
        ax=ax,
        palette={0: "#64748B", 1: "#F97316"},
    )
    ax.set(
        title="Contrastes brutos de patrocínio são pequenos e mudam de sinal",
        xlabel="Plataforma",
        ylabel="Interações por view (média)",
    )
    ax.set_ylim(0.19, 0.21)
    ax.legend(title="Patrocinado")
    fig.tight_layout()
    fig.savefig(FIGURES / "EDA-SPONSOR-BY-PLATFORM.png", dpi=160)
    plt.close(fig)

    overall = data[METRIC].agg(["mean", "median", "std", "min", "max"]).to_dict()
    platform_delta = platform["engagement_mean"].max() - platform["engagement_mean"].min()
    content = summaries["content_type"].sort_values("engagement_mean", ascending=False)
    content_delta = content["engagement_mean"].max() - content["engagement_mean"].min()
    sponsor_means = data.groupby("is_sponsored")[METRIC].mean()
    sponsor_delta = sponsor_means.loc[1] - sponsor_means.loc[0]
    top_combo = combinations.iloc[0]
    bottom_combo = combinations.iloc[-1]
    audience_location = summaries["audience_location"]
    audience_delta = (
        audience_location["engagement_mean"].max() - audience_location["engagement_mean"].min()
    )
    monthly_delta = monthly["engagement_mean"].max() - monthly["engagement_mean"].min()
    records = {
        "EDA-BASE-001": {
            "status": "EXPLORATORY",
            "claim": "A distribuição de engagement é muito estreita e não contém posts zerados.",
            "n": len(data),
            "estimate": overall,
            "source": "outputs/tables/EDA-OVERVIEW.csv",
            "limitations": ["provável geração sintética", "validade externa limitada"],
        },
        "EDA-PLAT-001": {
            "status": "EXPLORATORY",
            "claim": "A amplitude bruta entre médias de plataforma é mínima.",
            "n": len(data),
            "estimate_absolute": platform_delta,
            "estimate_percentage_points": platform_delta * 100,
            "source": "outputs/tables/EDA-BY-PLATFORM.csv",
            "limitations": ["não ajustado", "relevância prática ainda não validada"],
        },
        "EDA-CONTENT-001": {
            "status": "EXPLORATORY",
            "claim": "A amplitude bruta entre tipos de conteúdo é mínima.",
            "n": len(data),
            "estimate_absolute": content_delta,
            "estimate_percentage_points": content_delta * 100,
            "source": "outputs/tables/EDA-BY-CONTENT_TYPE.csv",
            "limitations": ["não ajustado", "interações podem existir"],
        },
        "EDA-COMBO-001": {
            "status": "EXPLORATORY",
            "claim": (
                "Extremos de combinações elegíveis têm diferença pequena e "
                "alto risco de multiplicidade."
            ),
            "n": int(combinations["n"].sum()),
            "estimate": {
                "top_mean": float(top_combo["engagement_mean"]),
                "top_n": int(top_combo["n"]),
                "bottom_mean": float(bottom_combo["engagement_mean"]),
                "bottom_n": int(bottom_combo["n"]),
                "absolute_range": float(
                    top_combo["engagement_mean"] - bottom_combo["engagement_mean"]
                ),
            },
            "source": "outputs/tables/EDA-COMBINATIONS-N100.csv",
            "limitations": [
                "somente células com n >= 100",
                "múltiplas comparações",
                "não validado para recomendação",
            ],
        },
        "EDA-AUD-001": {
            "status": "EXPLORATORY",
            "claim": "Localizações de audiência têm médias brutas muito próximas.",
            "n": len(data),
            "estimate_absolute_range": float(audience_delta),
            "estimate_percentage_points": float(audience_delta * 100),
            "source": "outputs/tables/EDA-BY-AUDIENCE_LOCATION.csv",
            "limitations": [
                "audiência agregada por post",
                "não permite inferência individual",
                "não ajustado",
            ],
        },
        "EDA-TIME-001": {
            "status": "EXPLORATORY",
            "claim": "Médias mensais são excessivamente estáveis.",
            "n": len(data),
            "estimate_absolute_range": float(monthly_delta),
            "estimate_percentage_points": float(monthly_delta * 100),
            "source": "outputs/tables/EDA-BY-MONTH.csv",
            "limitations": [
                "estabilidade pode refletir geração sintética",
                "não prova ausência de sazonalidade real",
            ],
        },
        "EDA-SPON-001": {
            "status": "EXPLORATORY",
            "claim": "Patrocinado e orgânico têm médias brutas praticamente iguais.",
            "n": len(data),
            "estimate_sponsored_minus_organic": sponsor_delta,
            "estimate_percentage_points": sponsor_delta * 100,
            "source": "outputs/tables/EDA-SPONSOR-CRUDE-SEGMENTS.csv",
            "limitations": [
                "não causal",
                "requer ajuste e diagnóstico de overlap",
                "custos ausentes",
            ],
        },
    }
    (EVIDENCE / "eda-evidence-records.json").write_text(
        json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(records, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
