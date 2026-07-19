# -*- coding: utf-8 -*-
"""FASE 3 — Modelo de ROI / quantificação de desperdício.

Fonte única do modelo econômico — consumida pelo notebook de diagnóstico
(FASE 3), pela matriz de automação (FASE 4, que importa DEFLECTION_BY_TYPE)
e pelo ROI Simulator do protótipo Streamlit (FASE 6, sliders).

Todas as constantes são PREMISSAS DECLARADAS do autor (ordem de grandeza de
mercado, sem fonte única auditável), com faixa low/base/high para análise de
sensibilidade. Nenhum valor vem de medição nos dados — os tempos do Dataset 1
são sintéticos (D-005). Fórmulas e limitações: docs/diagnostic_report.md (§P3).

Estrutura do modelo (sem dupla contagem: assistência só incide sobre as horas
dos tickets NÃO defletidos; ordem deflexão → assistência coberta por teste):

    horas_ano       = Σ_tipo volume_anual(tipo) × aht_min(tipo) / 60
    fte             = horas_ano / horas_produtivas_fte_ano
    custo_ano       = horas_ano × custo_hora
    economia_bruta  = (horas defletidas + horas reduzidas por assistência) × custo_hora   [regime]
    economia_ano1   = economia_bruta × ramp_up_ano1
    custo_sol_ano1  = volume_anual × custo_run_por_ticket
    roi_ano1        = (economia_ano1 − custo_sol_ano1) / custo_sol_ano1
    roi_regime      = (economia_bruta − custo_run_anual) / custo_run_anual              [ano 2+]
    payback_meses   = 0 quando o líquido do ano 1 é positivo; caso contrário, nunca

IMPORTANTE — economia de FTE é LIBERAÇÃO DE CAPACIDADE, não corte automático
de custo: a captura exige decisão de realocação (ex.: apontar a capacidade
liberada para os 33,3% de tickets sem primeira resposta — amarração P1↔P3).
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.data_prep import (
    AGENT_COST_BRL_PER_HOUR,
    AHT_MIN_BY_CHANNEL,
    TICKETS_PER_YEAR,
)

# ===========================================================================
# Premissas do modelo (low / base / high)
# ===========================================================================

#: Horas produtivas de 1 FTE de suporte por ano. Derivação da premissa base:
#: ~21 dias úteis/mês × 8h = ~168h presenciais/mês; ocupação efetiva ~83%
#: (pausas, treinamento, reuniões, absenteísmo) → ~140 h produtivas/mês × 12.
FTE_PRODUCTIVE_HOURS_YEAR: dict[str, float] = {
    "low": 1_560.0,   # 130 h/mês (ocupação menor)
    "base": 1_680.0,  # 140 h/mês
    "high": 1_800.0,  # 150 h/mês (ocupação agressiva)
}

#: Volume anual de tickets. Base = 30.000 (declarado no brief — D-001);
#: faixa ±20% para sensibilidade. O cenário "8.469 as-is" (amostra sem
#: anualizar) é reportado à parte no diagnóstico.
TICKETS_PER_YEAR_RANGE: dict[str, float] = {
    "low": 24_000.0,
    "base": float(TICKETS_PER_YEAR),
    "high": 36_000.0,
}

#: Fração de tickets DEFLETIDOS por tipo (resolvidos sem agente: self-service,
#: FAQ dinâmico, resposta automática com confiança alta). Taxas LÍQUIDAS de
#: escalação — ticket defletido que volta à fila conta como não-defletido.
#: PREMISSAS PROVISÓRIAS a ratificar na FASE 4 (que importa estas constantes)
#: e a validar em piloto. Mini-racional por tipo (critérios da FASE 4 —
#: repetitividade, previsibilidade, risco, julgamento humano):
#: - Product inquiry 50/65/80: informacional, alta repetição, risco baixo;
#:   o high de 80% supõe base de conhecimento madura (não usar como headline).
#: - Billing inquiry 30/45/60: consultas padronizáveis; disputas exigem humano.
#: - Refund request 20/35/50: status e política padrão automatizáveis;
#:   exceções e valores altos exigem julgamento.
#: - Cancellation request 15/25/40: processamento automatizável, mas retenção
#:   é conversa humana de alto valor.
#: - Technical issue 10/20/30: diagnóstico exige contexto; IA atua mais como
#:   assistência do que deflexão.
DEFLECTION_BY_TYPE: dict[str, dict[str, float]] = {
    "Product inquiry": {"low": 0.50, "base": 0.65, "high": 0.80},
    "Billing inquiry": {"low": 0.30, "base": 0.45, "high": 0.60},
    "Refund request": {"low": 0.20, "base": 0.35, "high": 0.50},
    "Cancellation request": {"low": 0.15, "base": 0.25, "high": 0.40},
    "Technical issue": {"low": 0.10, "base": 0.20, "high": 0.30},
}

#: Redução de AHT nos tickets NÃO defletidos, via copilot do agente
#: (classificação/roteamento, resposta sugerida, contexto, tickets similares).
ASSIST_AHT_REDUCTION: dict[str, float] = {"low": 0.10, "base": 0.20, "high": 0.30}

#: Fração da economia de regime capturada no ANO 1 (curva de adoção/ajuste:
#: implantação faseada, tuning de confiança, treinamento do time).
RAMP_UP_YEAR1: dict[str, float] = {"low": 0.50, "base": 0.65, "high": 0.80}

#: Custo da solução de IA.
#: - Implantação incremental: R$ 0 em todos os cenários. A construção é interna,
#:   executada pelo AI Master já no headcount; esta é uma premissa fixa do caso,
#:   não uma dimensão de sensibilidade (D-019, decisão final do autor).
#: - Run por ticket: ESCOPO DECLARADO = tokens de LLM + plataforma + sustentação
#:   (curadoria de conteúdo, manutenção de prompts, monitoramento). Aplica-se a
#:   TODOS os tickets do ano — a IA toca 100% deles (triagem/classificação),
#:   incluindo tentativas de deflexão que falham e escalam para humano.
SOLUTION_IMPL_COST_BRL: dict[str, float] = {"low": 0.0, "base": 0.0, "high": 0.0}
SOLUTION_RUN_COST_PER_TICKET_BRL: dict[str, float] = {"low": 0.50, "base": 1.00, "high": 2.00}


# ===========================================================================
# Modelo
# ===========================================================================

@dataclass
class RoiScenario:
    """Resultado de um cenário (unidades explícitas nos nomes)."""
    scenario: str
    tickets_year: float
    hours_year: float
    fte: float
    cost_year_brl: float
    deflected_tickets: float
    deflected_hours: float
    assist_hours: float
    hours_saved: float          # regime (taxa anual cheia)
    fte_saved: float            # capacidade liberada, não corte automático
    gross_savings_brl: float    # regime
    savings_year1_brl: float    # regime × ramp-up
    solution_cost_year1_brl: float
    net_savings_year1_brl: float
    roi_year1: float
    run_cost_year_brl: float
    net_savings_steady_brl: float   # ano 2+ (sem implantação, sem ramp)
    roi_steady: float
    payback_months: float

    def as_dict(self) -> dict:
        return self.__dict__.copy()


def _premises(scenario: str, overrides: dict) -> dict:
    """Resolve todas as premissas de um cenário, com overrides individuais
    (contrato dos sliders do ROI Simulator e do tornado)."""
    s = scenario
    p = {
        "tickets_year": TICKETS_PER_YEAR_RANGE[s],
        "agent_cost_hour": AGENT_COST_BRL_PER_HOUR[s],
        "deflection_by_type": {t: v[s] for t, v in DEFLECTION_BY_TYPE.items()},
        "assist_reduction": ASSIST_AHT_REDUCTION[s],
        "ramp_up_year1": RAMP_UP_YEAR1[s],
        "fte_hours_year": FTE_PRODUCTIVE_HOURS_YEAR[s],
        "impl_cost": SOLUTION_IMPL_COST_BRL[s],
        "run_cost_per_ticket": SOLUTION_RUN_COST_PER_TICKET_BRL[s],
        "aht_scenario": s,
    }
    unknown = set(overrides) - set(p)
    if unknown:
        raise ValueError(f"overrides desconhecidos (contrato dos sliders): {sorted(unknown)}")
    p.update({k: v for k, v in overrides.items() if v is not None})
    return p


def roi_scenario(d1: pd.DataFrame, scenario: str = "base", **overrides) -> RoiScenario:
    """Computa um cenário completo do modelo de ROI.

    ``scenario`` fixa o nível ('low'/'base'/'high') de TODAS as premissas;
    overrides nomeados (ver ``_premises``) permitem variar uma premissa por
    vez. Para cenários de NEGÓCIO coerentes (conservador/otimista, em que
    premissas de economia e de custo variam em direções opostas), use
    ``roi_business_scenario``.
    """
    p = _premises(scenario, overrides)

    # AHT low/high aplicado como razão sobre o base, preservando o mix por tipo
    aht_ratio = (
        sum(v[p["aht_scenario"]] for v in AHT_MIN_BY_CHANNEL.values())
        / sum(v["base"] for v in AHT_MIN_BY_CHANNEL.values())
    )
    by_type = d1.groupby("Ticket Type", observed=True).agg(
        n_sample=("Ticket ID", "count"),
        aht_min=("est_handle_minutes", "mean"),
    )
    factor = p["tickets_year"] / len(d1)
    by_type["tickets_year"] = by_type["n_sample"] * factor
    by_type["aht_min"] = by_type["aht_min"] * aht_ratio
    by_type["hours_year"] = by_type["tickets_year"] * by_type["aht_min"] / 60.0

    hours_year = float(by_type["hours_year"].sum())
    fte = hours_year / p["fte_hours_year"]
    cost_year = hours_year * p["agent_cost_hour"]

    # Alavanca 1 — deflexão (líquida de escalação)
    defl = pd.Series(p["deflection_by_type"]).reindex(by_type.index).fillna(0.0)
    by_type["deflected_tickets"] = by_type["tickets_year"] * defl
    by_type["deflected_hours"] = by_type["hours_year"] * defl
    # Alavanca 2 — assistência: APENAS sobre as horas não defletidas
    by_type["assist_hours"] = (by_type["hours_year"] - by_type["deflected_hours"]) * p["assist_reduction"]

    deflected_tickets = float(by_type["deflected_tickets"].sum())
    deflected_hours = float(by_type["deflected_hours"].sum())
    assist_hours = float(by_type["assist_hours"].sum())
    hours_saved = deflected_hours + assist_hours
    gross_savings = hours_saved * p["agent_cost_hour"]

    run_cost_year = p["tickets_year"] * p["run_cost_per_ticket"]
    savings_y1 = gross_savings * p["ramp_up_year1"]
    solution_cost_y1 = p["impl_cost"] + run_cost_year
    net_y1 = savings_y1 - solution_cost_y1
    roi_y1 = net_y1 / solution_cost_y1 if solution_cost_y1 > 0 else float("inf")

    net_steady = gross_savings - run_cost_year
    roi_steady = net_steady / run_cost_year if run_cost_year > 0 else float("inf")

    monthly_net_y1 = (savings_y1 - run_cost_year) / 12.0
    payback = p["impl_cost"] / monthly_net_y1 if monthly_net_y1 > 0 else float("inf")

    return RoiScenario(
        scenario=scenario,
        tickets_year=p["tickets_year"],
        hours_year=hours_year,
        fte=fte,
        cost_year_brl=cost_year,
        deflected_tickets=deflected_tickets,
        deflected_hours=deflected_hours,
        assist_hours=assist_hours,
        hours_saved=hours_saved,
        fte_saved=hours_saved / p["fte_hours_year"],
        gross_savings_brl=gross_savings,
        savings_year1_brl=savings_y1,
        solution_cost_year1_brl=solution_cost_y1,
        net_savings_year1_brl=net_y1,
        roi_year1=roi_y1,
        run_cost_year_brl=run_cost_year,
        net_savings_steady_brl=net_steady,
        roi_steady=roi_steady,
        payback_months=payback,
    )


#: Cenários de NEGÓCIO coerentes: no conservador, premissas de economia no
#: low E custos no high (e vice-versa) — diferente de roi_scenario('low'),
#: que coloca TODAS as premissas no mesmo nível (útil para sensibilidade,
#: incoerente como cenário de decisão).
BUSINESS_SCENARIOS: dict[str, dict[str, str]] = {
    "conservador": {"savings": "low", "costs": "high"},
    "base": {"savings": "base", "costs": "base"},
    "otimista": {"savings": "high", "costs": "low"},
}


def roi_business_scenario(d1: pd.DataFrame, name: str) -> RoiScenario:
    """Cenário de decisão: economia e custo recorrente variam em direções opostas.

    O custo incremental de implantação permanece fixo em R$ 0 em todos os
    cenários; apenas o custo recorrente por ticket varia no eixo de custos.
    """
    cfg = BUSINESS_SCENARIOS[name]
    sv, ct = cfg["savings"], cfg["costs"]
    r = roi_scenario(
        d1, "base",
        tickets_year=TICKETS_PER_YEAR_RANGE["base"],
        agent_cost_hour=AGENT_COST_BRL_PER_HOUR[sv],   # custo/h alto = mais economia
        deflection_by_type={t: v[sv] for t, v in DEFLECTION_BY_TYPE.items()},
        assist_reduction=ASSIST_AHT_REDUCTION[sv],
        ramp_up_year1=RAMP_UP_YEAR1[sv],
        fte_hours_year=FTE_PRODUCTIVE_HOURS_YEAR["base"],
        impl_cost=SOLUTION_IMPL_COST_BRL[ct],
        run_cost_per_ticket=SOLUTION_RUN_COST_PER_TICKET_BRL[ct],
        aht_scenario=sv,                                # AHT alto = mais horas = mais economia
    )
    r.scenario = name
    return r


def break_even_deflection(d1: pd.DataFrame) -> float:
    """Deflexão uniforme mínima (todas as premissas no base, assistência
    DESLIGADA) que zera a economia líquida do ano 1.

    Fórmula fechada: x = custo_solução_ano1 / (horas_ano × custo_h × ramp).
    """
    base = roi_scenario(
        d1, "base",
        deflection_by_type={t: 0.0 for t in DEFLECTION_BY_TYPE},
        assist_reduction=0.0,
    )
    denom = base.hours_year * AGENT_COST_BRL_PER_HOUR["base"] * RAMP_UP_YEAR1["base"]
    return base.solution_cost_year1_brl / denom


def workload_by_segment(
    d1: pd.DataFrame,
    by: list[str] | None = None,
    tickets_per_year: float = float(TICKETS_PER_YEAR),
) -> pd.DataFrame:
    """Carga anualizada por segmento (cenário base): volume, horas, custo."""
    by = by or ["Ticket Channel", "Ticket Type"]
    g = d1.groupby(by, observed=True).agg(
        n_sample=("Ticket ID", "count"),
        aht_min=("est_handle_minutes", "mean"),
    ).reset_index()
    factor = tickets_per_year / len(d1)
    g["tickets_year"] = g["n_sample"] * factor
    g["hours_year"] = g["tickets_year"] * g["aht_min"] / 60.0
    g["cost_year_brl"] = g["hours_year"] * AGENT_COST_BRL_PER_HOUR["base"]
    return g.sort_values("hours_year", ascending=False).reset_index(drop=True)


def sensitivity_tornado(d1: pd.DataFrame) -> pd.DataFrame:
    """Sensibilidade one-at-a-time: varia UMA premissa low↔high com as demais
    no base. Métrica primária: economia LÍQUIDA do ano 1 (R$) — ROI% explode
    com denominador pequeno e distorce a leitura visual.

    Agrupamento declarado: AHTs dos 4 canais movem juntos; deflexões dos 5
    tipos movem juntas (barras por-tipo seriam ilegíveis e as premissas
    compartilham o mesmo racional de origem).
    """
    base = roi_scenario(d1, "base")
    variations: dict[str, dict[str, dict]] = {
        "Deflexão por tipo (conjunta)": {
            "low": {"deflection_by_type": {t: v["low"] for t, v in DEFLECTION_BY_TYPE.items()}},
            "high": {"deflection_by_type": {t: v["high"] for t, v in DEFLECTION_BY_TYPE.items()}},
        },
        "AHT por canal (conjunto)": {
            "low": {"aht_scenario": "low"}, "high": {"aht_scenario": "high"},
        },
        "Custo/hora do agente": {
            "low": {"agent_cost_hour": AGENT_COST_BRL_PER_HOUR["low"]},
            "high": {"agent_cost_hour": AGENT_COST_BRL_PER_HOUR["high"]},
        },
        "Volume anual (±20%)": {
            "low": {"tickets_year": TICKETS_PER_YEAR_RANGE["low"]},
            "high": {"tickets_year": TICKETS_PER_YEAR_RANGE["high"]},
        },
        "Redução de AHT (assistência)": {
            "low": {"assist_reduction": ASSIST_AHT_REDUCTION["low"]},
            "high": {"assist_reduction": ASSIST_AHT_REDUCTION["high"]},
        },
        "Ramp-up ano 1": {
            "low": {"ramp_up_year1": RAMP_UP_YEAR1["low"]},
            "high": {"ramp_up_year1": RAMP_UP_YEAR1["high"]},
        },
        "Custo por ticket (run)": {
            "low": {"run_cost_per_ticket": SOLUTION_RUN_COST_PER_TICKET_BRL["low"]},
            "high": {"run_cost_per_ticket": SOLUTION_RUN_COST_PER_TICKET_BRL["high"]},
        },
    }
    rows = []
    for name, sides in variations.items():
        vals = {side: roi_scenario(d1, "base", **ov).net_savings_year1_brl
                for side, ov in sides.items()}
        rows.append({
            "premissa": name,
            "net_low": vals["low"],
            "net_high": vals["high"],
            "net_base": base.net_savings_year1_brl,
            "amplitude": abs(vals["high"] - vals["low"]),
        })
    return pd.DataFrame(rows).sort_values("amplitude", ascending=False).reset_index(drop=True)
