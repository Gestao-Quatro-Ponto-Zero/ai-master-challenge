"""Carga e normalização dos 4 CSVs do CRM num único DataFrame de pipeline."""
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

# O pipeline grava "GTXPro" e a tabela de produtos "GTX Pro" — sem isso o join perde
# ~1.500 deals (achado na EDA, ver docs/PROCESS_LOG.md).
_ALIAS_PRODUTO = {"GTXPro": "GTX Pro"}

STAGES_ABERTOS = ("Prospecting", "Engaging")
STAGES_FECHADOS = ("Won", "Lost")


@dataclass
class Dados:
    pipeline: pd.DataFrame      # todas as oportunidades, já com produto/time/conta
    times: pd.DataFrame         # sales_teams.csv
    data_referencia: pd.Timestamp

    @property
    def fechados(self) -> pd.DataFrame:
        return self.pipeline[self.pipeline.deal_stage.isin(STAGES_FECHADOS)]

    @property
    def abertos(self) -> pd.DataFrame:
        return self.pipeline[self.pipeline.deal_stage.isin(STAGES_ABERTOS)]


def carregar(data_dir: Path, data_referencia: str | None = None) -> Dados:
    contas = pd.read_csv(data_dir / "accounts.csv")
    produtos = pd.read_csv(data_dir / "products.csv")
    times = pd.read_csv(data_dir / "sales_teams.csv")
    pipeline = pd.read_csv(data_dir / "sales_pipeline.csv", parse_dates=["engage_date", "close_date"])

    pipeline["product"] = pipeline["product"].replace(_ALIAS_PRODUTO)
    pipeline = (
        pipeline.merge(produtos, on="product", how="left")
        .merge(times, on="sales_agent", how="left")
        .merge(contas, on="account", how="left")
    )

    # Duração só existe pra deal fechado; idade (dias desde o engajamento até "hoje")
    # é calculada no scoring, que é quem conhece a data de referência em uso.
    pipeline["duracao_dias"] = (pipeline.close_date - pipeline.engage_date).dt.days
    pipeline["ganhou"] = (pipeline.deal_stage == "Won").astype(int)

    ref = pd.Timestamp(data_referencia) if data_referencia else pipeline.close_date.max()
    return snapshot(Dados(pipeline=pipeline, times=times, data_referencia=pipeline.close_date.max()), ref)


def snapshot(dados: Dados, t: pd.Timestamp) -> Dados:
    """Reconstrói o pipeline como ele estava no fim do dia `t`.

    Deals engajados até t e fechados DEPOIS de t voltam a ser 'Engaging' (sem
    close_date/close_value — o vendedor não sabia o desfecho). O desfecho verdadeiro
    fica em `resultado_real`, usado só pelo backtest de calibração. Prospecting não
    tem data nenhuma no dataset, então só existe no snapshot da data final.

    É isso que permite medir o score sem vazar o futuro: benchmarks calculados só
    com o que já tinha fechado em t, aplicados aos deals abertos em t."""
    p = dados.pipeline
    t = pd.Timestamp(t)
    fim_dataset = p.close_date.max()
    fechado = p.close_date <= t
    aberto = (p.engage_date <= t) & ~fechado
    prospecting = p.engage_date.isna() & (t >= fim_dataset)

    snap = p[fechado | aberto | prospecting].copy()
    snap["resultado_real"] = snap.deal_stage
    reabrir = aberto[snap.index]
    snap.loc[reabrir, "deal_stage"] = "Engaging"
    snap.loc[reabrir, ["close_date", "close_value", "duracao_dias"]] = None
    snap.loc[reabrir, "ganhou"] = 0
    return Dados(pipeline=snap, times=dados.times, data_referencia=t)
