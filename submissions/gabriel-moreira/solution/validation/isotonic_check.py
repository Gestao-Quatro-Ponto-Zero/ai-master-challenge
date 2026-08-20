"""Verificação das curvas de aging — Requirement "Verificação das curvas de
aging".

Recalcula `p_ganho(t)` e `risco(t)` a partir dos negócios fechados (não a
partir dos breakpoints congelados em `scoring.constants`) e verifica que a
suavização isotônica de `risco(t)` é não-decrescente, e que nenhum negócio
fechado excede 138 dias — a checagem roda sobre os dados carregados, não
usa 138 como constante sem verificação.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scoring import constants
from sklearn.isotonic import IsotonicRegression


@dataclass(frozen=True)
class AgingCurves:
    max_duracao_dias: int
    ts: list[int]
    p_ganho_bruto: list[float]
    p_ganho_isotonico: list[float]
    risco_bruto: list[float]
    risco_isotonico: list[float]

    @property
    def risco_monotonico(self) -> bool:
        return all(
            b >= a for a, b in zip(self.risco_isotonico, self.risco_isotonico[1:])
        )

    @property
    def censura_confirmada(self) -> bool:
        return self.max_duracao_dias <= constants.CENSURA_DIAS


def _duration_days(closed: pd.DataFrame) -> pd.Series:
    return (closed["close_date"] - closed["engage_date"]).dt.days


def recompute_curves(closed: pd.DataFrame, janela_risco: int = 30) -> AgingCurves:
    duration = _duration_days(closed)
    won = (closed["deal_stage"] == "Won").to_numpy()
    max_duracao = int(duration.max())

    ts = list(range(0, constants.CURVA_LIMITE_CONFIAVEL_DIAS + 1, 1))

    p_ganho_bruto: list[float] = []
    risco_bruto: list[float] = []
    for t in ts:
        at_risk = duration.to_numpy() >= t
        n_at_risk = int(at_risk.sum())
        if n_at_risk == 0:
            p_ganho_bruto.append(np.nan)
            risco_bruto.append(np.nan)
            continue
        p_ganho_bruto.append(float(won[at_risk].mean()))

        resolves_soon = at_risk & (duration.to_numpy() < t + janela_risco)
        risco_bruto.append(float(resolves_soon.sum() / n_at_risk))

    valid = ~np.isnan(p_ganho_bruto)
    ts_arr = np.array(ts)

    iso_p_ganho = IsotonicRegression(increasing=True, out_of_bounds="clip")
    p_ganho_iso = iso_p_ganho.fit_transform(ts_arr[valid], np.array(p_ganho_bruto)[valid])

    iso_risco = IsotonicRegression(increasing=True, out_of_bounds="clip")
    risco_iso = iso_risco.fit_transform(ts_arr[valid], np.array(risco_bruto)[valid])

    return AgingCurves(
        max_duracao_dias=max_duracao,
        ts=list(ts_arr[valid]),
        p_ganho_bruto=list(np.array(p_ganho_bruto)[valid]),
        p_ganho_isotonico=list(p_ganho_iso),
        risco_bruto=list(np.array(risco_bruto)[valid]),
        risco_isotonico=list(risco_iso),
    )
