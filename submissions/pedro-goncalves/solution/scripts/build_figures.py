from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "artifacts/tables"
FIGURES = ROOT / "artifacts/figures"


def save(name: str) -> None:
    plt.tight_layout()
    plt.savefig(FIGURES / name, dpi=180, bbox_inches="tight")
    plt.close()


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    missing = pd.read_csv(TABLES / "support_missingness_by_status.csv")
    missing_long = missing.melt(
        id_vars=["Ticket Status", "tickets"],
        value_vars=["first_response_missing", "resolution_missing", "csat_missing"],
        var_name="field",
        value_name="missing",
    )
    missing_long["missing_rate"] = missing_long["missing"] / missing_long["tickets"]
    missing_long["field"] = missing_long["field"].map(
        {
            "first_response_missing": "First response",
            "resolution_missing": "Resolution",
            "csat_missing": "CSAT",
        }
    )
    plt.figure(figsize=(9, 4.8))
    sns.barplot(
        data=missing_long,
        x="Ticket Status",
        y="missing_rate",
        hue="field",
        palette=["#1463ff", "#ff8a00", "#d83b44"],
    )
    plt.title("Ausência de dados acompanha o status do ticket")
    plt.xlabel("")
    plt.ylabel("Parcela ausente")
    plt.ylim(0, 1.05)
    plt.legend(title="")
    save("support-missingness-by-status.png")

    classes = pd.read_csv(TABLES / "it_topic_distribution.csv").sort_values("tickets")
    plt.figure(figsize=(9, 5))
    sns.barplot(data=classes, x="tickets", y="topic_group", color="#1463ff")
    plt.title("Distribuição de classes no Dataset 2")
    plt.xlabel("Tickets")
    plt.ylabel("")
    save("it-class-distribution.png")

    thresholds = pd.read_csv(TABLES / "classifier_coverage_accuracy.csv")
    plt.figure(figsize=(8, 4.8))
    plt.plot(
        thresholds["coverage"],
        thresholds["accuracy_when_covered"],
        marker="o",
        color="#1463ff",
        linewidth=2,
    )
    for _, row in thresholds.iloc[::2].iterrows():
        plt.annotate(
            f"θ={row['threshold']:.2f}",
            (row["coverage"], row["accuracy_when_covered"]),
            xytext=(4, 5),
            textcoords="offset points",
            fontsize=8,
        )
    plt.title("Validação: abstenção troca cobertura por acurácia")
    plt.xlabel("Cobertura")
    plt.ylabel("Acurácia nos tickets cobertos")
    plt.xlim(0, 1)
    plt.ylim(0.85, 1.01)
    save("coverage-vs-accuracy.png")

    print(FIGURES)


if __name__ == "__main__":
    main()
