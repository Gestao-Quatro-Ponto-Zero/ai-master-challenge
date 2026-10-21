"""Orquestra tudo que a API precisa para UMA data de referência: snapshot do pipeline,
benchmarks, score + probabilidade calibrada, métricas, alertas, emergência e cross-sell.

A data é selecionável (qualquer segunda-feira do histórico, ou a data final) — é
isso que permite ver o modo emergência funcionando: na data final do dataset
(31/12/2017) o trimestre fecha no mesmo dia, mas em 04/12/2017 faltam 27 dias.
Cada data é calculada uma vez e fica em cache."""
import logging
import time
from dataclasses import dataclass

import pandas as pd

from . import alertas, config, crosssell, emergencia, metricas
from .calibracao import Backtest, Calibracao, calibrar
from .dados import Dados, snapshot
from .metricas import Trimestre
from .scoring import Benchmarks, calcular_benchmarks, pontuar

logger = logging.getLogger("lead_scorer")


def registros(df: pd.DataFrame) -> list[dict]:
    """DataFrame → lista de dicts JSON-safe (NaN/pd.NA viram None)."""
    if df is None or df.empty:
        return []
    return df.astype(object).where(df.notna(), None).to_dict("records")


@dataclass
class Visao:
    data: pd.Timestamp
    dados: Dados
    bm: Benchmarks
    deals: pd.DataFrame        # deals abertos pontuados, com coluna 'alertas'
    metricas: pd.DataFrame     # 1 linha por vendedor
    trimestre: Trimestre
    cross_sell: pd.DataFrame
    calibracao: Calibracao     # rolling-origin: só o que se sabia nesta data
    cortes: dict               # score mínimo de "Atacar agora" / "Nutrir" nesta data


class Motor:
    def __init__(self, base: Dados):
        self.base = base
        self.data_final = base.pipeline.close_date.max()
        inicio = time.perf_counter()
        self.backtest: Backtest = calibrar(base)
        # Calibração da data final (a mais completa) — usada no /saude e como referência
        self.calibracao: Calibracao = self.backtest.para_data(self.data_final)
        logger.info("Backtest: %d observações, AUC %.3f na data final (%.1fs)",
                    self.calibracao.n_observacoes, self.calibracao.auc, time.perf_counter() - inicio)
        self._cache: dict[str, Visao] = {}

    def datas_disponiveis(self) -> list[pd.Timestamp]:
        """Segundas-feiras desde o primeiro mês com histórico + a data final."""
        primeiro = self.base.pipeline.close_date.min() + pd.offsets.MonthBegin(1)
        segundas = list(pd.date_range(primeiro, self.data_final, freq="W-MON"))
        return segundas + ([self.data_final] if self.data_final not in segundas else [])

    def _pontuar_em(self, t: pd.Timestamp) -> tuple[Dados, Benchmarks, pd.DataFrame]:
        snap = snapshot(self.base, t)
        bm = calcular_benchmarks(snap)
        return snap, bm, pontuar(snap, bm, self.backtest.para_data(t))

    def visao(self, data: str | None = None) -> Visao:
        t = pd.Timestamp(data or config.DATA_REFERENCIA or self.data_final).normalize()
        chave = t.date().isoformat()
        if chave in self._cache:
            return self._cache[chave]
        if t > self.data_final or t < self.datas_disponiveis()[0]:
            raise ValueError(f"Data fora do histórico disponível ({self.datas_disponiveis()[0].date()} a {self.data_final.date()}).")

        inicio = time.perf_counter()
        snap, bm, deals = self._pontuar_em(t)
        _, _, deals_antes = self._pontuar_em(t - pd.Timedelta(days=config.DIAS_COMPARACAO_SCORE))
        tri = metricas.trimestre(t)
        met = metricas.calcular(snap, deals, bm)

        ctx = {
            "valor_relevante": float(deals.valor.quantile(config.QUANTIL_VALOR_RELEVANTE)) if len(deals) else 0.0,
            "resgate": emergencia.ids_resgate_por_vendedor(deals, met, tri),
            "esfriando": emergencia.deals_esfriando(deals, deals_antes, bm),
            "data_fim_trimestre": tri.fim.strftime("%d/%m"),
        }
        listas = [alertas.gerar_alertas_deal(d, bm, ctx) for d in registros(deals)]
        alertas.aplicar_teto_criticos(listas)
        deals["alertas"] = listas

        cortes = deals.attrs.get("cortes", {})
        v = Visao(t, snap, bm, deals, met, tri, crosssell.sugerir(snap, deals), self.backtest.para_data(t), cortes)
        self._cache[chave] = v
        logger.info("Visão %s: %d deals abertos (%.1fs)", chave, len(deals), time.perf_counter() - inicio)
        return v
