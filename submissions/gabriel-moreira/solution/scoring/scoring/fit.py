"""Fit histórico do vendedor por produto e por setor — workload-fit spec,
Requirement "Fit histórico do vendedor por produto e por setor".

Encolhimento hierárquico em dois níveis (vendedor -> escritório -> global),
com `k_fit` de política (design.md, D3):

    fit_produto(v, p) = (n_vp x taxa_vp + k_fit x prior_esc_p) / (n_vp + k_fit)
    prior_esc_p        = (n_ep x taxa_ep + k_fit x taxa_global_p) / (n_ep + k_fit)

Idem para setor, trocando produto por setor. Sempre sobre
`fechados_calibracao` (denominador `Won + Lost`) — nunca sobre oportunidades
abertas. Fit de setor é reportado como indisponível (`None`), nunca
substituído por zero, média global ou fit de produto, quando a oportunidade
não tem conta vinculada.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import constants
from .carga import CargaVendedorEstado
from .repository import Dataset
from .shrinkage import GroupCounts, LevelStats, level_stats, product_group_counts


def _group_counts(df: pd.DataFrame, key_cols: list[str]) -> dict:
    """Contagem n/vitórias por chave (tupla ou escalar), sobre um DataFrame
    já restrito a fechados (Won/Lost)."""
    groups: dict = {}
    for key, sub in df.groupby(key_cols):
        n = len(sub)
        wins = int((sub["deal_stage"] == "Won").sum())
        groups[key] = GroupCounts(n=n, wins=wins)
    return groups


def _sector_counts(df: pd.DataFrame, key_cols: list[str]) -> dict:
    return _group_counts(df.dropna(subset=["sector"]), key_cols)


@dataclass(frozen=True)
class FitContext:
    """Pré-computado uma vez sobre `fechados_calibracao` — reutilizado
    para todo par (vendedor, oportunidade)."""

    vendor_office: dict[str, str]
    vendor_product: dict[tuple[str, str], GroupCounts]
    vendor_sector: dict[tuple[str, str], GroupCounts]
    office_product: dict[tuple[str, str], GroupCounts]
    office_sector: dict[tuple[str, str], GroupCounts]
    global_product: dict[str, GroupCounts]
    global_sector: dict[str, GroupCounts]


def build_fit_context(dataset: Dataset, closed: pd.DataFrame) -> FitContext:
    """`closed` é `pipeline.fechados_calibracao(dataset)` — passado pelo
    chamador para evitar recomputar o filtro em todo lugar que precisa dele."""
    vendor_office = (
        dataset.pipeline[["sales_agent", "regional_office"]]
        .dropna(subset=["regional_office"])
        .drop_duplicates(subset="sales_agent")
        .set_index("sales_agent")["regional_office"]
        .to_dict()
    )

    return FitContext(
        vendor_office=vendor_office,
        vendor_product=_group_counts(closed, ["sales_agent", "product"]),
        vendor_sector=_sector_counts(closed, ["sales_agent", "sector"]),
        office_product=_group_counts(closed, ["regional_office", "product"]),
        office_sector=_sector_counts(closed, ["regional_office", "sector"]),
        global_product=product_group_counts(closed),
        global_sector=_sector_counts(closed, ["sector"]),
    )


def _shrink(n: int, rate: float, k: float, prior: float) -> float:
    if n == 0 or k == float("inf"):
        return prior
    return (n * rate + k * prior) / (n + k)


@dataclass(frozen=True)
class FitValue:
    """Fit encolhido de um vendedor numa dimensão (produto ou setor),
    junto do suporte amostral que o sustenta — a contagem de negócios
    fechados na célula vendedor x dimensão, ANTES do encolhimento
    (Requirement "Fit histórico do vendedor por produto e por setor")."""

    valor: float
    n: int


def _fit_generico(
    vendor: str,
    dim_key: str,
    vendor_office: dict[str, str],
    vendor_counts: dict[tuple[str, str], GroupCounts],
    office_counts: dict[tuple[str, str], GroupCounts],
    global_counts: dict[str, GroupCounts],
    k: float,
) -> FitValue | None:
    office = vendor_office.get(vendor)
    if office is None:
        return None

    taxa_global = global_counts.get(dim_key)
    taxa_global_valor = taxa_global.rate if taxa_global is not None else constants.GLOBAL_WIN_RATE_CALIBRACAO

    oe = office_counts.get((office, dim_key))
    n_oe = oe.n if oe is not None else 0
    rate_oe = oe.rate if oe is not None else 0.0
    prior_escritorio = _shrink(n_oe, rate_oe, k, taxa_global_valor)

    ve = vendor_counts.get((vendor, dim_key))
    n_ve = ve.n if ve is not None else 0
    rate_ve = ve.rate if ve is not None else 0.0
    valor = _shrink(n_ve, rate_ve, k, prior_escritorio)

    return FitValue(valor=valor, n=n_ve)


def fit_produto(ctx: FitContext, vendor: str, product: str, k: float = constants.K_FIT) -> FitValue | None:
    return _fit_generico(
        vendor, product, ctx.vendor_office, ctx.vendor_product, ctx.office_product, ctx.global_product, k
    )


def fit_setor(
    ctx: FitContext, vendor: str, sector: str | None, k: float = constants.K_FIT
) -> FitValue | None:
    """`None` — indisponível — quando o setor é desconhecido (oportunidade
    sem conta vinculada). Nunca substituído por zero, prior global ou
    fit de produto (Requirement "Fit histórico do vendedor por produto e
    por setor")."""
    if sector is None or (isinstance(sector, float) and sector != sector):
        return None
    return _fit_generico(
        vendor, sector, ctx.vendor_office, ctx.vendor_sector, ctx.office_sector, ctx.global_sector, k
    )


def derive_k_fit(
    ctx: FitContext, level: str, global_win_rate: float = constants.GLOBAL_WIN_RATE_CALIBRACAO
) -> LevelStats:
    """Reproduz a derivação de k por variância em excesso para o
    encolhimento do fit (mesma técnica de `shrinkage.level_stats`,
    aplicada ao nível vendedor x produto ou vendedor x setor) — usada só
    pela validação (task 3.3/8.4), nunca pelo motor de scoring, que usa
    `constants.K_FIT` congelado por política."""
    groups = ctx.vendor_product if level == "produto" else ctx.vendor_sector
    return level_stats(groups, global_win_rate)


# ---------------------------------------------------------------------------
# Sugestão de redistribuição — workload-fit spec, Requirement "Sugestão de
# vendedor para redistribuição"; design.md, D5/D6.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Candidato:
    """Um candidato elegível, ranqueado para uma oportunidade específica."""

    sales_agent: str
    fit_produto: FitValue
    fit_setor: FitValue | None
    folga: float
    rank: float


def vendors_with_history(ctx: FitContext) -> set[str]:
    """Vendedores com ao menos um negócio fechado — os únicos elegíveis a
    candidato (D6: os 5 vendedores de `sales_teams` sem nenhuma
    oportunidade registrada nunca são sugeridos, por não haver base para
    afirmar fit)."""
    return {vendor for vendor, _dim in ctx.vendor_product}


def _folga(media_escritorio: float, contagem: int) -> float:
    if media_escritorio <= 0:
        return 0.0
    return max(0.0, (media_escritorio - contagem) / media_escritorio)


def _fit_combinado(fit_p: FitValue, fit_s: FitValue | None) -> float:
    """fit(c) = fit_produto(c) quando o setor é indisponível; caso
    contrário, 0,6 x fit_produto(c) + 0,4 x fit_setor(c) (design.md, D5)."""
    if fit_s is None:
        return fit_p.valor
    return constants.FIT_PESO_PRODUTO * fit_p.valor + constants.FIT_PESO_SETOR * fit_s.valor


def eligible_pool(
    ctx: FitContext,
    carga_by_agent_estado: dict[tuple[str, str], CargaVendedorEstado],
    current_agent: str,
    office: str,
    estado: str,
) -> list[str]:
    """Mesmo escritório, com histórico de negócios fechados, não
    sobrecarregado no ESTADO da oportunidade, diferente do vendedor atual.
    Um candidato sem entrada em `carga_by_agent_estado` para este ESTADO
    (nunca teve oportunidade aberta ali) tem carga zero por definição —
    nunca sobrecarregado."""
    com_historico = vendors_with_history(ctx)
    pool = []
    for candidate, cand_office in ctx.vendor_office.items():
        if cand_office != office or candidate == current_agent:
            continue
        if candidate not in com_historico:
            continue
        item = carga_by_agent_estado.get((candidate, estado))
        if item is not None and item.sobrecarregado:
            continue
        pool.append(candidate)
    return sorted(pool)


def suggest_candidate(
    ctx: FitContext,
    carga_by_agent_estado: dict[tuple[str, str], CargaVendedorEstado],
    current_agent: str,
    office: str,
    estado: str,
    product: str,
    sector: str | None,
) -> Candidato | None:
    """Sugere o melhor candidato à redistribuição para uma oportunidade de
    vendedor sobrecarregado, combinando folga de carga com fit — nunca
    cruza escritório, nunca sugere vendedor sobrecarregado ou sem
    histórico. `None` quando o pool de elegíveis esgota (Requirement
    "Sugestão de vendedor para redistribuição")."""
    atual = carga_by_agent_estado.get((current_agent, estado))
    media_escritorio = atual.media_escritorio if atual is not None else 0.0

    pool = eligible_pool(ctx, carga_by_agent_estado, current_agent, office, estado)
    if not pool:
        return None

    brutos = []
    for candidate in pool:
        fp = fit_produto(ctx, candidate, product)
        fs = fit_setor(ctx, candidate, sector)
        item = carga_by_agent_estado.get((candidate, estado))
        contagem = item.contagem if item is not None else 0
        folga = _folga(media_escritorio, contagem)
        fit_valor = _fit_combinado(fp, fs)
        brutos.append((candidate, fp, fs, folga, fit_valor))

    valores_fit = [b[4] for b in brutos]
    lo, hi = min(valores_fit), max(valores_fit)

    def _normaliza(v: float) -> float:
        return (v - lo) / (hi - lo) if hi > lo else 0.5

    candidatos = [
        Candidato(
            sales_agent=candidate,
            fit_produto=fp,
            fit_setor=fs,
            folga=folga,
            rank=constants.RANK_PESO_FOLGA * folga + constants.RANK_PESO_FIT * _normaliza(fit_valor),
        )
        for candidate, fp, fs, folga, fit_valor in brutos
    ]
    candidatos.sort(key=lambda c: (-c.rank, c.sales_agent))
    return candidatos[0]
