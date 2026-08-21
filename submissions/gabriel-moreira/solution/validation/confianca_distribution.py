"""Distribuição de CONFIANÇA e das duas metades (completude, suporte) —
acompanha o artefato de validação para que uma recalibração que torne a
janela de idade (`SUPORTE_JANELA_IDADE_DIAS`) ou a saturação de suporte
(`SUPORTE_SATURACAO_N`) inadequadas fique visível, em vez de silenciosa
(Requirement "Atribuição de confiança")."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

PERCENTIS = (10, 25, 50, 75, 90, 95, 99)


@dataclass(frozen=True)
class ConfiancaDistributionReport:
    percentis_confianca: dict[int, float]
    percentis_completude: dict[int, float]
    percentis_suporte: dict[int, float]
    fracao_sem_precedente: float
    fracao_completude_governante: float
    n: int


def build_report(scored: pd.DataFrame) -> ConfiancaDistributionReport:
    governada_por_completude = scored["completude"] <= scored["suporte"]
    return ConfiancaDistributionReport(
        percentis_confianca={p: float(scored["confianca"].quantile(p / 100)) for p in PERCENTIS},
        percentis_completude={p: float(scored["completude"].quantile(p / 100)) for p in PERCENTIS},
        percentis_suporte={p: float(scored["suporte"].quantile(p / 100)) for p in PERCENTIS},
        fracao_sem_precedente=float(scored["sem_precedente"].mean()),
        fracao_completude_governante=float(governada_por_completude.mean()),
        n=int(len(scored)),
    )
