"""Auditoria do denominador das taxas de vitória — Requirement "Auditoria
do denominador das taxas de vitória".

Verifica, em todo artefato de análise que publique taxa de vitória, que o
denominador é `Won + Lost` e que nenhuma oportunidade em `Engaging` ou
`Prospecting` participa dele.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class DenominatorAuditResult:
    nome_artefato: str
    n_linhas: int
    denominador_correto: bool
    taxa_consistente: bool

    @property
    def aprovado(self) -> bool:
        return self.denominador_correto and self.taxa_consistente


def audit(df: pd.DataFrame, nome_artefato: str) -> DenominatorAuditResult:
    denominador_correto = bool((df["Fechados"] == df["Won"] + df["Lost"]).all())

    com_fechados = df[df["Fechados"] > 0]
    esperado = (com_fechados["Won"] / com_fechados["Fechados"] * 100).round(2)
    taxa_consistente = bool((com_fechados["Taxa Vitória %"].round(2) == esperado).all())

    return DenominatorAuditResult(
        nome_artefato=nome_artefato,
        n_linhas=len(df),
        denominador_correto=denominador_correto,
        taxa_consistente=taxa_consistente,
    )
