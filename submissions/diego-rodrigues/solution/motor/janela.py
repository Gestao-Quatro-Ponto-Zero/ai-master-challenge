"""Janela de validade de um deal: ciclo máximo e regra do prazo do trimestre."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from motor.carregar import Dados


def prazo_trimestre(serie: pd.Series) -> pd.Series:
    """Fim do trimestre seguinte ao do engajamento."""
    return (
        serie.dt.to_period("Q").dt.start_time
        + pd.offsets.QuarterBegin(2, startingMonth=1)
        - pd.Timedelta(days=1)
    )


@dataclass
class Janela:
    ciclo_max: int
    usa_prazo_trimestre: bool
    n_fechamentos: int
    fechamentos_apos_prazo: int


def aprender_janela(dados: Dados, config: dict) -> Janela:
    """Aprende a janela de validade a partir dos fechamentos conhecidos em dados."""
    fe = dados.pipeline[dados.pipeline.close_date.notna()].copy()

    ciclo_max = int((fe.close_date - fe.engage_date).dt.days.max())

    apos_prazo = int((fe.close_date > prazo_trimestre(fe.engage_date)).sum())
    usa = (
        len(fe) >= config["min_fechamentos_para_prazo"]
        and apos_prazo / len(fe) <= config["tolerancia_prazo_trimestre"]
    )

    return Janela(
        ciclo_max=ciclo_max,
        usa_prazo_trimestre=bool(usa),
        n_fechamentos=len(fe),
        fechamentos_apos_prazo=apos_prazo,
    )


def prazo_do_deal(engage_date: pd.Series, janela: Janela) -> pd.Series:
    """O menor entre engage_date + ciclo_max e o fim do trimestre seguinte (quando ativo)."""
    por_idade = engage_date + pd.Timedelta(days=janela.ciclo_max)
    if not janela.usa_prazo_trimestre:
        return por_idade
    return pd.Series(
        np.minimum(por_idade.values, prazo_trimestre(engage_date).values),
        index=engage_date.index,
    )


def estado(pipeline: pd.DataFrame, janela: Janela, hoje: pd.Timestamp) -> pd.Series:
    """Classifica cada deal aberto em 'vivo', 'vencido' ou 'sem_data'; NaN para deals fechados."""
    resultado = pd.Series(pd.NA, index=pipeline.index, dtype=object)

    ab = pipeline[pipeline.close_date.isna()]

    # sem_data: abertos sem data de engajamento
    resultado.loc[ab.index[ab.engage_date.isna()]] = "sem_data"

    # deals com data de engajamento
    com_data = ab[ab.engage_date.notna()]
    idade = (hoje - com_data.engage_date).dt.days
    prazo = prazo_do_deal(com_data.engage_date, janela)
    vivo = (idade <= janela.ciclo_max) & (prazo >= hoje)

    resultado.loc[com_data.index[vivo]] = "vivo"
    resultado.loc[com_data.index[~vivo]] = "vencido"

    return resultado
