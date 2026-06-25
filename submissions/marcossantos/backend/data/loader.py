"""
data/loader.py
--------------
Responsável por:
1. Ler os 4 CSVs do dataset CRM
2. Fazer o join das tabelas (pipeline é a tabela central)
3. Calcular métricas base derivadas dos dados históricos
   (win rates, médias de tempo, etc.) que o scoring engine vai consumir

Tudo é carregado em memória uma vez (startup) e reutilizado nas requisições.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).parent

CSV_FILES = {
    "pipeline": DATA_DIR / "sales_pipeline.csv",
    "accounts": DATA_DIR / "accounts.csv",
    "products": DATA_DIR / "products.csv",
    "teams":    DATA_DIR / "sales_teams.csv",
}

# Mapeamento de stages para valor numérico (usado no scoring)
STAGE_ORDER = {
    "Prospecting": 1,
    "Engaging":    2,
    "Won":         3,
    "Lost":        0,
}


# ---------------------------------------------------------------------------
# Classe principal
# ---------------------------------------------------------------------------

class CRMDataLoader:
    """
    Carrega e prepara todos os dados do CRM.
    Instanciada uma vez na inicialização do FastAPI (singleton via lifespan).
    """

    def __init__(self):
        self.pipeline: Optional[pd.DataFrame] = None   # tabela central enriquecida
        self.accounts: Optional[pd.DataFrame] = None
        self.products: Optional[pd.DataFrame] = None
        self.teams:    Optional[pd.DataFrame] = None

        # Métricas históricas calculadas dos dados (usadas pelo scoring engine)
        self.metrics: dict = {}

    # ------------------------------------------------------------------
    # Ponto de entrada
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Carrega tudo e prepara as métricas. Chame no startup."""
        logger.info("Carregando CSVs do CRM...")
        self._read_csvs()
        self._clean_and_join()
        self._compute_historical_metrics()
        logger.info(
            f"Dataset pronto: {len(self.pipeline)} oportunidades, "
            f"{self.pipeline['sales_agent'].nunique()} vendedores, "
            f"{self.pipeline['account'].nunique()} contas."
        )

    # ------------------------------------------------------------------
    # Leitura dos CSVs
    # ------------------------------------------------------------------

    def _read_csvs(self) -> None:
        for name, path in CSV_FILES.items():
            if not path.exists():
                raise FileNotFoundError(
                    f"Arquivo não encontrado: {path}\n"
                    f"Baixe o dataset em: https://www.kaggle.com/datasets/agungpambudi/crm-sales-predictive-analytics\n"
                    f"e coloque os CSVs na pasta /data/"
                )

        self.pipeline = pd.read_csv(CSV_FILES["pipeline"])
        self.accounts = pd.read_csv(CSV_FILES["accounts"])
        self.products = pd.read_csv(CSV_FILES["products"])
        self.teams    = pd.read_csv(CSV_FILES["teams"])

        logger.info(f"  pipeline: {len(self.pipeline)} registros")
        logger.info(f"  accounts: {len(self.accounts)} registros")
        logger.info(f"  products: {len(self.products)} registros")
        logger.info(f"  teams:    {len(self.teams)} registros")

    # ------------------------------------------------------------------
    # Limpeza e JOIN das tabelas
    # ------------------------------------------------------------------

    def _clean_and_join(self) -> None:
        """
        Faz o join de pipeline com as demais tabelas e garante tipos corretos.
        """
        df = self.pipeline.copy()

        # Normaliza nomes de colunas (lowercase, sem espaços)
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        self.accounts.columns = self.accounts.columns.str.strip().str.lower().str.replace(" ", "_")
        self.products.columns = self.products.columns.str.strip().str.lower().str.replace(" ", "_")
        self.teams.columns    = self.teams.columns.str.strip().str.lower().str.replace(" ", "_")

        # Datas
        for col in ["engage_date", "close_date"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        # Valor de fechamento — 0 pra Lost, NaN vira 0
        df["close_value"] = pd.to_numeric(df["close_value"], errors="coerce").fillna(0)

        # Stage numérico
        df["stage_order"] = df["deal_stage"].map(STAGE_ORDER).fillna(0).astype(int)

        # Join com accounts
        if "account" in df.columns and "account" in self.accounts.columns:
            df = df.merge(
                self.accounts[["account", "sector", "revenue", "employees", "office_location"]],
                on="account",
                how="left",
            )

        # Join com products
        if "product" in df.columns and "product" in self.products.columns:
            df = df.merge(
                self.products[["product", "series", "sales_price"]],
                on="product",
                how="left",
            )

        # Join com sales_teams
        if "sales_agent" in df.columns and "sales_agent" in self.teams.columns:
            df = df.merge(
                self.teams[["sales_agent", "manager", "regional_office"]],
                on="sales_agent",
                how="left",
            )

        # Dados derivados de tempo
        reference_date = df["close_date"].max()  # data mais recente no dataset como "hoje"
        if pd.isnull(reference_date):
            reference_date = pd.Timestamp.now()

        df["days_in_pipeline"] = (reference_date - df["engage_date"]).dt.days.fillna(0).astype(int)
        df["days_since_close"] = (reference_date - df["close_date"]).dt.days.fillna(0).astype(int)

        # Revenue numérico (pode vir como string com vírgulas)
        if "revenue" in df.columns:
            df["revenue"] = (
                df["revenue"]
                .astype(str)
                .str.replace(",", "")
                .str.replace("$", "")
                .str.strip()
            )
            df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce").fillna(0)

        if "employees" in df.columns:
            df["employees"] = pd.to_numeric(df["employees"], errors="coerce").fillna(0)

        self.pipeline = df

    # ------------------------------------------------------------------
    # Métricas históricas (calculadas dos deals Won/Lost)
    # ------------------------------------------------------------------

    def _compute_historical_metrics(self) -> None:
        """
        Calcula métricas agregadas dos dados históricos.
        Estas métricas são a base do scoring não-óbvio.
        """
        df = self.pipeline
        closed = df[df["deal_stage"].isin(["Won", "Lost"])].copy()
        won    = df[df["deal_stage"] == "Won"].copy()

        # --- 1. Win rate geral do dataset ---
        total_closed = len(closed)
        self.metrics["global_win_rate"] = len(won) / total_closed if total_closed > 0 else 0.5

        # --- 2. Win rate por sales_agent ---
        agent_stats = (
            closed.groupby("sales_agent")
            .apply(lambda g: (g["deal_stage"] == "Won").mean())
            .reset_index()
        )
        agent_stats.columns = ["sales_agent", "win_rate"]
        self.metrics["agent_win_rate"] = agent_stats.set_index("sales_agent")["win_rate"].to_dict()

        # --- 3. Win rate por produto ---
        product_stats = (
            closed.groupby("product")
            .apply(lambda g: (g["deal_stage"] == "Won").mean())
            .reset_index()
        )
        product_stats.columns = ["product", "win_rate"]
        self.metrics["product_win_rate"] = product_stats.set_index("product")["win_rate"].to_dict()

        # --- 4. Win rate por setor da conta ---
        if "sector" in closed.columns:
            sector_stats = (
                closed.groupby("sector")
                .apply(lambda g: (g["deal_stage"] == "Won").mean())
                .reset_index()
            )
            sector_stats.columns = ["sector", "win_rate"]
            self.metrics["sector_win_rate"] = sector_stats.set_index("sector")["win_rate"].to_dict()
        else:
            self.metrics["sector_win_rate"] = {}

        # --- 5. Tempo médio até fechar (Won) por produto ---
        # "velocity benchmark": deals mais rápidos que a média do produto têm vantagem
        if "days_in_pipeline" in won.columns and "product" in won.columns:
            product_velocity = (
                won.groupby("product")["days_in_pipeline"]
                .agg(["mean", "std"])
                .reset_index()
            )
            product_velocity.columns = ["product", "avg_days", "std_days"]
            product_velocity["std_days"] = product_velocity["std_days"].fillna(
                product_velocity["avg_days"] * 0.3
            )
            self.metrics["product_velocity"] = (
                product_velocity.set_index("product")[["avg_days", "std_days"]].to_dict("index")
            )
        else:
            self.metrics["product_velocity"] = {}

        # --- 6. Tempo médio até fechar por setor ---
        if "days_in_pipeline" in won.columns and "sector" in won.columns:
            sector_velocity = (
                won.groupby("sector")["days_in_pipeline"]
                .mean()
                .reset_index()
            )
            sector_velocity.columns = ["sector", "avg_days"]
            self.metrics["sector_avg_days"] = sector_velocity.set_index("sector")["avg_days"].to_dict()
        else:
            self.metrics["sector_avg_days"] = {}

        # --- 7. Valor médio de deals Won (para contextualizar o valor do deal) ---
        self.metrics["avg_won_value"]    = won["close_value"].mean() if len(won) > 0 else 0
        self.metrics["median_won_value"] = won["close_value"].median() if len(won) > 0 else 0

        # --- 8. Percentis de employees e revenue (para normalizar account fit) ---
        active = df[df["deal_stage"].isin(["Prospecting", "Engaging"])]
        if "employees" in df.columns:
            self.metrics["employees_p25"] = float(df["employees"].quantile(0.25))
            self.metrics["employees_p75"] = float(df["employees"].quantile(0.75))
        if "revenue" in df.columns:
            self.metrics["revenue_p25"] = float(df["revenue"].quantile(0.25))
            self.metrics["revenue_p75"] = float(df["revenue"].quantile(0.75))

        logger.info(
            f"  Métricas calculadas: "
            f"win_rate global={self.metrics['global_win_rate']:.1%}, "
            f"{len(self.metrics['agent_win_rate'])} agentes, "
            f"{len(self.metrics['product_win_rate'])} produtos"
        )

    # ------------------------------------------------------------------
    # Helpers para acesso aos dados
    # ------------------------------------------------------------------

    def get_active_pipeline(self) -> pd.DataFrame:
        """Retorna apenas deals ativos (Prospecting ou Engaging)."""
        return self.pipeline[
            self.pipeline["deal_stage"].isin(["Prospecting", "Engaging"])
        ].copy()

    def get_agents(self) -> list[dict]:
        """Lista de agentes com manager e regional_office."""
        cols = ["sales_agent", "manager", "regional_office"]
        available = [c for c in cols if c in self.pipeline.columns]
        return (
            self.pipeline[available]
            .drop_duplicates(subset=["sales_agent"])
            .sort_values("sales_agent")
            .to_dict(orient="records")
        )

    def get_deal_by_id(self, opportunity_id: str) -> Optional[pd.Series]:
        """Retorna uma oportunidade pelo ID."""
        mask = self.pipeline["opportunity_id"].astype(str) == str(opportunity_id)
        result = self.pipeline[mask]
        return result.iloc[0] if len(result) > 0 else None