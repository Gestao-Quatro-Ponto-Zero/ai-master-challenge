"""Cenários de capacidade para uma única tarefa, triagem assistida."""

from dataclasses import asdict, dataclass, replace
from math import isfinite


@dataclass(frozen=True)
class Scenario:
    volume: float = 2500
    elegibilidade: float = 0.50
    cobertura: float = 0.60
    adesao: float = 0.80
    antes_min: float = 4.0
    depois_min: float = 1.5
    revisao_min: float = 0.50
    retrabalho_taxa: float = 0.05
    retrabalho_min: float = 4.0
    hora_brl: float = 60
    ia_mensal_brl: float = 0
    infra_mensal_brl: float = 0
    manutencao_mensal_brl: float = 150
    implantacao_brl: float = 1500
    conversao_caixa: float = 0


FRACTIONS = frozenset(
    {"elegibilidade", "cobertura", "adesao", "retrabalho_taxa", "conversao_caixa"}
)
BASE = Scenario()
SCENARIOS = {
    "Conservador": replace(
        BASE, elegibilidade=0.35, cobertura=0.40, adesao=0.60, revisao_min=1.0, retrabalho_taxa=0.15
    ),
    "Base": BASE,
    "Otimista": replace(
        BASE,
        elegibilidade=0.65,
        cobertura=0.75,
        adesao=0.90,
        revisao_min=0.30,
        retrabalho_taxa=0.03,
    ),
}


def calculate(scenario: Scenario) -> dict:
    s = scenario
    for field, value in asdict(s).items():
        if not isfinite(value) or value < 0 or (field in FRACTIONS and value > 1):
            raise ValueError(f"Premissa fora do intervalo válido: {field}.")
    processed = s.volume * s.elegibilidade * s.cobertura * s.adesao
    after = s.depois_min + s.revisao_min + s.retrabalho_taxa * s.retrabalho_min
    net_hours = processed * (s.antes_min - after) / 60
    recurring = s.ia_mensal_brl + s.infra_mensal_brl + s.manutencao_mensal_brl
    capacity = net_hours * s.hora_brl
    financial = max(capacity, 0) * s.conversao_caixa - recurring
    cost_12m = recurring * 12 + s.implantacao_brl
    return {
        "processados_mes": processed,
        "min_depois_com_revisao_e_retrabalho": after,
        "horas_liquidas_mes": net_hours,
        "valor_capacidade_mes": capacity,
        "custo_recorrente_mes": recurring,
        "valor_liquido_capacidade_mes": capacity - recurring,
        "caixa_liquido_mes": financial,
        "caixa_liquido_12m": financial * 12 - s.implantacao_brl,
        "roi_financeiro_12m": (financial * 12 - s.implantacao_brl) / cost_12m if cost_12m else None,
        "payback_meses": s.implantacao_brl / financial if financial > 0 else None,
    }
