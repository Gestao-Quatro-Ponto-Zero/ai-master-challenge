import os
import zipfile
import pandas as pd
from kaggle.api.kaggle_api_extended import KaggleApi

from services.data_processing import build_analytical_dataset
from services.analysis import (
    churn_analysis,
    pareto_analysis,
    revenue_segmentation_executive,
    build_executive_kpis,
)
from services.ml_model import run_ml_model
from services.shap_analysis import run_shap

os.environ["KAGGLE_CONFIG_DIR"] = r"C:\Users\junio\.kaggle"

DATASET = "rivalytics/saas-subscription-and-churn-analytics-dataset"
DOWNLOAD_PATH = "data/raw"


def download_dataset():
    print("🔽 Iniciando download do dataset...")

    api = KaggleApi()
    api.authenticate()
    api.dataset_download_files(DATASET, path=DOWNLOAD_PATH, unzip=False)

    print("✅ Download concluído!")


def extract_dataset():
    print("📦 Extraindo arquivos...")

    for file in os.listdir(DOWNLOAD_PATH):
        if file.endswith(".zip"):
            zip_path = os.path.join(DOWNLOAD_PATH, file)

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(DOWNLOAD_PATH)

            print(f"✅ Extraído: {file}")


def load_data():
    print("📊 Carregando arquivos CSV...")

    base_path = "data/raw"

    accounts = pd.read_csv(f"{base_path}/ravenstack_accounts.csv")
    subscriptions = pd.read_csv(f"{base_path}/ravenstack_subscriptions.csv")
    feature_usage = pd.read_csv(f"{base_path}/ravenstack_feature_usage.csv")
    support_tickets = pd.read_csv(f"{base_path}/ravenstack_support_tickets.csv")
    churn_events = pd.read_csv(f"{base_path}/ravenstack_churn_events.csv")

    print("✅ Arquivos carregados com sucesso!")

    return accounts, subscriptions, feature_usage, support_tickets, churn_events


def validate_data(accounts, subscriptions, feature_usage, support_tickets, churn_events):
    print("\n🔍 Validando dados...")

    print(f"Accounts: {accounts.shape}")
    print(f"Subscriptions: {subscriptions.shape}")
    print(f"Feature Usage: {feature_usage.shape}")
    print(f"Support Tickets: {support_tickets.shape}")
    print(f"Churn Events: {churn_events.shape}")

    print("\n📌 Colunas principais:")
    print("\nAccounts:", accounts.columns.tolist())
    print("\nSubscriptions:", subscriptions.columns.tolist())
    print("\nFeature Usage:", feature_usage.columns.tolist())
    print("\nSupport Tickets:", support_tickets.columns.tolist())
    print("\nChurn Events:", churn_events.columns.tolist())

    print("\n✅ Validação concluída!")


def get_full_dataset(run_analysis=False):
    accounts, subscriptions, feature_usage, support_tickets, churn_events = load_data()

    validate_data(accounts, subscriptions, feature_usage, support_tickets, churn_events)

    print("\n🔗 Construindo dataset analítico...")
    df = build_analytical_dataset(
        accounts,
        subscriptions,
        feature_usage,
        support_tickets,
        churn_events,
    )
    print("✅ Dataset analítico pronto!")

    if run_analysis:
        print("\n🧠 Rodando análises...")

        churn_analysis(df)

        model, importance = run_ml_model(df)

        run_shap(
            model,
            df[
                [
                    "avg_mrr",
                    "avg_arr",
                    "avg_seats",
                    "avg_usage_count",
                    "avg_usage_duration",
                    "avg_errors",
                    "avg_resolution_time",
                    "avg_first_response",
                    "avg_satisfaction",
                    "total_escalations",
                ]
            ],
        )

        _, pareto_summary = pareto_analysis(df)
        revenue_summary = revenue_segmentation_executive(df)

        summary = build_summary(df, pareto_summary, revenue_summary)

        print("\n📊 RESUMO FINAL:")
        print(summary)

    return df


def _df_to_records_safe(df):
    if df is None or df.empty:
        return []

    clean_df = df.copy()

    for col in clean_df.columns:
        if pd.api.types.is_categorical_dtype(clean_df[col]):
            clean_df[col] = clean_df[col].astype(str)

    return clean_df.to_dict(orient="records")


def build_summary(df, pareto, segmentation):
    executive_kpis = build_executive_kpis(df)

    customers = executive_kpis.get("customers", {})
    revenue = executive_kpis.get("revenue", {})
    arpu = executive_kpis.get("arpu", {})
    ltv = executive_kpis.get("ltv", {})
    churn = executive_kpis.get("churn", {})
    risk = executive_kpis.get("risk", {})
    risk_distribution = risk.get("distribution", {})

    summary = {
        # Compatibilidade com frontend/API existente
        "churn_rate": churn.get("churn_rate_total", churn.get("churn_rate", 0.0)),
        "total_accounts": customers.get("total", 0),
        "total_revenue": revenue.get("total_mrr", revenue.get("mrr", 0.0)),
        "active_accounts": customers.get("active", 0),
        "churned_accounts": customers.get("churned", 0),
        "mrr_at_risk": revenue.get("mrr_at_risk", revenue.get("risk_mrr", 0.0)),
        "revenue_churn": revenue.get("revenue_churn", 0.0),
        "arpu": arpu.get("total", 0.0),
        "ltv": ltv.get("total", 0.0),
        "high_risk_accounts": risk.get("high_risk_accounts", risk.get("high_risk_active_accounts", 0)),
        "medium_risk_accounts": risk_distribution.get("medium", 0),
        "low_risk_accounts": risk_distribution.get("low", 0),

        # Novos KPIs
        "inactive_accounts": customers.get("inactive", 0),

        "total_mrr": revenue.get("total_mrr", 0.0),
        "active_mrr": revenue.get("active_mrr", 0.0),
        "inactive_mrr": revenue.get("inactive_mrr", 0.0),
        "risk_mrr": revenue.get("risk_mrr", revenue.get("mrr_at_risk", 0.0)),

        "arpu_total": arpu.get("total", 0.0),
        "arpu_active": arpu.get("active", 0.0),
        "arpu_inactive": arpu.get("inactive", 0.0),
        "arpu_risk": arpu.get("risk", 0.0),

        "ltv_total": ltv.get("total", 0.0),
        "ltv_active": ltv.get("active", 0.0),
        "ltv_inactive": ltv.get("inactive", 0.0),
        "ltv_risk": ltv.get("risk", 0.0),

        "churn_rate_total": churn.get("churn_rate_total", churn.get("churn_rate", 0.0)),

        "risk_distribution": {
            "high": risk_distribution.get("high", 0),
            "medium": risk_distribution.get("medium", 0),
            "low": risk_distribution.get("low", 0),
        },

        "pareto": _df_to_records_safe(pareto),
        "segmentation": _df_to_records_safe(segmentation),

        "executive": executive_kpis,
    }

    return summary


if __name__ == "__main__":
    df = get_full_dataset(run_analysis=True)

    print("\n🔍 Preview do dataset:")
    print(df.head())

    print("\n📌 Colunas do dataset analítico:")
    print(df.columns.tolist())

    _, pareto_summary = pareto_analysis(df)
    revenue_summary = revenue_segmentation_executive(df)

    summary = build_summary(df, pareto_summary, revenue_summary)

    print("\n📊 Summary final para API:")
    print(summary)