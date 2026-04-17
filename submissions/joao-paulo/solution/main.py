from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from churn_diagnosis.application.use_cases import BuildSolutionUseCase
from churn_diagnosis.infrastructure.loaders import CsvDataLoader
from churn_diagnosis.infrastructure.repository import OutputRepository
from churn_diagnosis.presentation.generate_executive_dashboard import generate_dashboard


def main() -> None:
    root = ROOT
    data_dir = root / "data"
    output_dir = root / "output"

    loader = CsvDataLoader(data_dir)
    repository = OutputRepository(output_dir)
    use_case = BuildSolutionUseCase()

    # =========================
    # EXECUTA PIPELINE
    # =========================
    artifacts = use_case.execute(loader.load())

    # =========================
    # SALVA OUTPUTS
    # =========================
    repository.save_dataframe(artifacts.account_360, "account_360.csv")
    repository.save_dataframe(artifacts.customer_health, "customer_health_score.csv")
    repository.save_dataframe(artifacts.churn_risk_drivers, "churn_risk_drivers.csv")
    repository.save_dataframe(artifacts.churn_reconciliation, "churn_reconciliation.csv")
    repository.save_dataframe(artifacts.current_churn_scoring, "current_churn_scoring.csv")
    repository.save_dataframe(artifacts.account_model_explanations, "account_model_explanations.csv")
    repository.save_dataframe(artifacts.model_global_explainability, "model_global_explainability.csv")
    repository.save_dataframe(artifacts.point_in_time_training_dataset, "point_in_time_training_dataset.csv")
    repository.save_dataframe(artifacts.model_comparison, "model_comparison.csv")
    repository.save_dataframe(artifacts.feature_importance.head(25), "feature_importance_top25.csv")
    repository.save_json(artifacts.model_metrics, "model_metrics.json")

    BuildSolutionUseCase.save_model(
        artifacts.model,
        str(output_dir / "churn_classifier.joblib")
    )

    print("Artifacts generated in:", output_dir)

    # =========================
    # GERA DASHBOARD HTML
    # =========================
    generate_dashboard(output_dir)

    print("Executive dashboard generated successfully.")


if __name__ == "__main__":
    main()
