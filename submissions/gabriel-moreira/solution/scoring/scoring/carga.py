"""Carga por vendedor e ESTADO, contra a média do escritório regional —
workload-fit spec, Requirements "Carga por vendedor e estado contra a
média do escritório" e "Detecção de sobrecarga".

"Estado" aqui é o ESTADO do funil (`prioritize`/`acompanhar`/`qualificar`),
não geografia. `revisao_lote` é excluído de toda contagem de carga — é um
backlog de higiene de dados, não carga de trabalho atribuível — mas um
vendedor cujas únicas oportunidades abertas estão em `revisao_lote` ainda
conta para o denominador da média do escritório (ele tem oportunidade
aberta no funil; só não tem carga *contável* em nenhum ESTADO trabalhável).
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import constants

# Os três ESTADOs trabalháveis — a única superfície onde "carga" existe.
CARGA_ESTADOS: tuple[str, ...] = tuple(e for e in constants.ESTADOS if e != "revisao_lote")


@dataclass(frozen=True)
class CargaVendedorEstado:
    """Carga de um vendedor num ESTADO, contra a média do próprio
    escritório regional naquele ESTADO."""

    sales_agent: str
    regional_office: str
    estado: str
    contagem: int
    media_escritorio: float
    razao: float | None  # None quando a média do escritório é 0
    sobrecarregado: bool


def _office_by_agent(scored: pd.DataFrame) -> pd.Series:
    """Escritório regional de cada vendedor — do vendedor dono da
    oportunidade (`sales_teams`, via a coluna já unida `regional_office`),
    nunca inferido de conta, produto ou localização do cliente."""
    return (
        scored[["sales_agent", "regional_office"]]
        .dropna(subset=["regional_office"])
        .drop_duplicates(subset="sales_agent")
        .set_index("sales_agent")["regional_office"]
    )


def compute_carga(scored: pd.DataFrame) -> list[CargaVendedorEstado]:
    """Calcula a carga de todo (vendedor, ESTADO) com escritório conhecido.

    `scored` é o funil aberto pontuado (todas as 4 chaves de ESTADO
    presentes) — a mesma estrutura de `pipeline.score_open_pipeline`. A
    média do escritório usa todos os vendedores do escritório com ao menos
    uma oportunidade aberta no funil (qualquer ESTADO, incluindo
    `revisao_lote`) — excluir os que têm zero no ESTADO avaliado inflaria
    a média (Requirement "Carga por vendedor e estado contra a média do
    escritório").
    """
    office_by_agent = _office_by_agent(scored)
    vendedores_por_escritorio: dict[str, list[str]] = {}
    for agent, office in office_by_agent.items():
        vendedores_por_escritorio.setdefault(office, []).append(agent)

    contabilizavel = scored[scored["estado"].isin(CARGA_ESTADOS)]
    contagens = (
        contabilizavel.groupby(["sales_agent", "estado"]).size().to_dict()
    )

    resultados: list[CargaVendedorEstado] = []
    for office, agentes in vendedores_por_escritorio.items():
        n_agentes = len(agentes)
        for estado in CARGA_ESTADOS:
            total_estado = sum(contagens.get((agente, estado), 0) for agente in agentes)
            media = total_estado / n_agentes if n_agentes else 0.0
            for agente in agentes:
                contagem = contagens.get((agente, estado), 0)
                razao = (contagem / media) if media > 0 else None
                sobrecarregado = (
                    media > 0
                    and contagem >= constants.CARGA_RAZAO_SOBRECARGA * media
                    and contagem >= constants.CARGA_PISO_SOBRECARGA
                )
                resultados.append(
                    CargaVendedorEstado(
                        sales_agent=agente,
                        regional_office=office,
                        estado=estado,
                        contagem=contagem,
                        media_escritorio=media,
                        razao=razao,
                        sobrecarregado=sobrecarregado,
                    )
                )
    return resultados


def overloaded_pairs(carga: list[CargaVendedorEstado]) -> list[CargaVendedorEstado]:
    return [c for c in carga if c.sobrecarregado]


def is_overloaded(
    carga: list[CargaVendedorEstado], sales_agent: str, estado: str
) -> bool:
    return any(
        c.sales_agent == sales_agent and c.estado == estado and c.sobrecarregado
        for c in carga
    )


def deal_pertence_a_sobrecarregado(
    carga_by_key: dict[tuple[str, str], CargaVendedorEstado], sales_agent: str, estado: str
) -> bool:
    """Uma oportunidade pertence a vendedor sobrecarregado quando o par
    (vendedor da oportunidade, ESTADO da oportunidade) está sobrecarregado
    (Requirement "Detecção de sobrecarga")."""
    item = carga_by_key.get((sales_agent, estado))
    return item is not None and item.sobrecarregado


def index_by_agent_estado(
    carga: list[CargaVendedorEstado],
) -> dict[tuple[str, str], CargaVendedorEstado]:
    return {(c.sales_agent, c.estado): c for c in carga}


def annotate_sobrecarga(
    scored: pd.DataFrame, carga_by_agent_estado: dict[tuple[str, str], CargaVendedorEstado]
) -> pd.Series:
    """Sinalizador booleano de sobrecarga por linha — Requirement
    "Sinalizador de sobrecarga na listagem de oportunidades". `revisao_lote`
    nunca está sobrecarregado (não tem entrada no índice)."""
    return pd.Series(
        [
            deal_pertence_a_sobrecarregado(carga_by_agent_estado, agent, estado)
            for agent, estado in zip(scored["sales_agent"], scored["estado"])
        ],
        index=scored.index,
    )
