"""
scoring/factors.py
------------------
Cada fator de scoring é uma função isolada que recebe:
  - deal: pd.Series  (uma linha do pipeline enriquecido)
  - metrics: dict    (métricas históricas calculadas pelo loader)

E retorna um dict com:
  - points: float  (pontos ganhos, 0 até max_points do fator)
  - max_points: int
  - label: str     (nome amigável do fator)
  - reason: str    (explicação em linguagem natural para o vendedor)
  - signal: str    ("positive" | "warning" | "neutral")

Isso garante que o scoring engine e o explainer possam consumir
os fatores de forma uniforme, e que adicionar um novo fator
seja só criar uma nova função.
"""

import numpy as np
import pandas as pd
from typing import Any


# ---------------------------------------------------------------------------
# Tipo de retorno de cada fator
# ---------------------------------------------------------------------------

def _factor_result(
    points: float,
    max_points: int,
    label: str,
    reason: str,
    signal: str = "neutral",
) -> dict:
    return {
        "points": round(max(0.0, min(float(points), float(max_points))), 1),
        "max_points": max_points,
        "label": label,
        "reason": reason,
        "signal": signal,  # "positive" | "warning" | "neutral"
    }


# ---------------------------------------------------------------------------
# FATOR 1 — Stage Score (0–25 pts)
# Engaging está mais perto do fechamento. Prospecting ainda é incerto.
# ---------------------------------------------------------------------------

def factor_stage(deal: pd.Series, metrics: dict) -> dict:
    stage = deal.get("deal_stage", "")

    if stage == "Engaging":
        return _factor_result(
            points=25, max_points=25,
            label="Stage: Engaging",
            reason="Deal em fase de negociação ativa — alta probabilidade de fechamento próximo.",
            signal="positive",
        )
    elif stage == "Prospecting":
        return _factor_result(
            points=10, max_points=25,
            label="Stage: Prospecting",
            reason="Deal ainda em prospecção — potencial, mas precisa avançar de fase.",
            signal="neutral",
        )
    else:
        return _factor_result(
            points=0, max_points=25,
            label=f"Stage: {stage}",
            reason=f"Stage '{stage}' não contribui para o score.",
            signal="neutral",
        )


# ---------------------------------------------------------------------------
# FATOR 2 — Velocity Score (0–25 pts)
# Compara tempo no pipeline vs. média histórica de Won deals do mesmo produto.
# Deals "vencidos" (muito acima da média) recebem penalidade forte.
# Deals rápidos recebem bônus.
# ---------------------------------------------------------------------------

def factor_velocity(deal: pd.Series, metrics: dict) -> dict:
    days = deal.get("days_in_pipeline", 0)
    product = deal.get("product", "")
    sector = deal.get("sector", "")

    # Benchmark: preferir por produto, fallback por setor, fallback global
    product_vel = metrics.get("product_velocity", {}).get(product)
    sector_avg  = metrics.get("sector_avg_days", {}).get(sector)

    if product_vel and product_vel.get("avg_days"):
        avg_days = product_vel["avg_days"]
        std_days = product_vel.get("std_days", avg_days * 0.3)
        benchmark_source = f"produto {product}"
    elif sector_avg:
        avg_days = sector_avg
        std_days = avg_days * 0.3
        benchmark_source = f"setor {sector}"
    else:
        avg_days = 30  # fallback razoável
        std_days = 10
        benchmark_source = "média geral"

    avg_days = max(avg_days, 1)
    ratio = days / avg_days  # 1.0 = exatamente na média

    if ratio <= 0.5:
        # Muito rápido — deal quente
        points = 25
        reason = (
            f"Deal muito rápido: {days}d no pipeline (média {benchmark_source}: {avg_days:.0f}d). "
            "Momentum positivo — priorize para fechar logo."
        )
        signal = "positive"
    elif ratio <= 0.85:
        points = 20
        reason = (
            f"Velocidade boa: {days}d no pipeline (média {benchmark_source}: {avg_days:.0f}d). "
            "Deal dentro do ritmo esperado."
        )
        signal = "positive"
    elif ratio <= 1.2:
        points = 15
        reason = (
            f"Velocidade normal: {days}d no pipeline (média {benchmark_source}: {avg_days:.0f}d)."
        )
        signal = "neutral"
    elif ratio <= 1.8:
        points = 8
        reason = (
            f"⚠ Deal esfriando: {days}d no pipeline, acima da média de {avg_days:.0f}d ({benchmark_source}). "
            "Contato proativo pode reativar."
        )
        signal = "warning"
    else:
        # Muito acima da média — deal possivelmente estagnado
        points = 2
        reason = (
            f"🚨 Deal parado há {days}d — {ratio:.1f}x acima da média de {avg_days:.0f}d ({benchmark_source}). "
            "Alta chance de esfriar. Ação urgente ou reclassifique."
        )
        signal = "warning"

    return _factor_result(points=points, max_points=25, label="Velocidade no pipeline", reason=reason, signal=signal)


# ---------------------------------------------------------------------------
# FATOR 3 — Account Fit (0–20 pts)
# Porte da conta (employees + revenue) vs. perfil histórico de contas que fecham.
# Contas grandes tendem a gerar deals maiores e mais sólidos.
# ---------------------------------------------------------------------------

def factor_account_fit(deal: pd.Series, metrics: dict) -> dict:
    employees = deal.get("employees", 0) or 0
    revenue   = deal.get("revenue", 0) or 0
    sector    = deal.get("sector", "")

    emp_p25 = metrics.get("employees_p25", 100)
    emp_p75 = metrics.get("employees_p75", 1000)
    rev_p25 = metrics.get("revenue_p25", 1_000_000)
    rev_p75 = metrics.get("revenue_p75", 50_000_000)

    # Score de porte: 0 a 10 pts por employees, 0 a 10 pts por revenue
    def bracket_score(value, p25, p75, max_pts=10):
        if value >= p75:
            return max_pts
        elif value >= p25:
            # linear entre p25 e p75
            return max_pts * 0.5 + (max_pts * 0.5) * (value - p25) / (p75 - p25)
        else:
            return max_pts * 0.5 * (value / p25) if p25 > 0 else 0

    emp_score = bracket_score(employees, emp_p25, emp_p75)
    rev_score = bracket_score(revenue, rev_p25, rev_p75)
    total = emp_score + rev_score

    # Bônus de setor: setor com win_rate acima da média global recebe +3
    sector_wr = metrics.get("sector_win_rate", {}).get(sector, metrics.get("global_win_rate", 0.5))
    global_wr = metrics.get("global_win_rate", 0.5)
    sector_bonus = 0
    sector_note = ""
    if sector_wr > global_wr * 1.1:
        sector_bonus = 3
        sector_note = f" Setor '{sector}' tem win rate acima da média ({sector_wr:.0%} vs {global_wr:.0%} global)."

    total = min(total + sector_bonus, 20)

    if total >= 15:
        signal = "positive"
        qual = "grande porte"
    elif total >= 8:
        signal = "neutral"
        qual = "porte médio"
    else:
        signal = "neutral"
        qual = "porte menor"

    reason = (
        f"Conta de {qual}: {int(employees):,} funcionários, receita ${revenue:,.0f}.{sector_note}"
    )

    return _factor_result(points=total, max_points=20, label="Fit da conta", reason=reason, signal=signal)


# ---------------------------------------------------------------------------
# FATOR 4 — Product Win Rate (0–15 pts)
# Win rate histórico do produto neste contexto.
# Feature não-óbvia: produtos têm taxas de conversão muito diferentes.
# ---------------------------------------------------------------------------

def factor_product_win_rate(deal: pd.Series, metrics: dict) -> dict:
    product    = deal.get("product", "")
    sales_price = deal.get("sales_price", 0) or 0

    product_wr = metrics.get("product_win_rate", {}).get(product)
    global_wr  = metrics.get("global_win_rate", 0.5)

    if product_wr is None:
        return _factor_result(
            points=7, max_points=15,
            label="Win rate do produto",
            reason=f"Sem histórico suficiente para o produto '{product}'.",
            signal="neutral",
        )

    # Normaliza: produto com WR igual à média global = 7.5pts (meio do range)
    # WR máximo histórico → 15pts, WR zero → 0pts
    ratio = product_wr / global_wr if global_wr > 0 else 1.0
    points = 15 * min(ratio / 2.0, 1.0)  # ratio 2x = max

    if product_wr >= global_wr * 1.2:
        signal = "positive"
        qual = "alta conversão"
    elif product_wr >= global_wr * 0.8:
        signal = "neutral"
        qual = "conversão média"
    else:
        signal = "warning"
        qual = "conversão abaixo da média"

    reason = (
        f"Produto '{product}' tem {qual}: win rate histórico de {product_wr:.0%} "
        f"(média geral: {global_wr:.0%})."
    )
    if sales_price > 0:
        reason += f" Preço de tabela: ${sales_price:,.0f}."

    return _factor_result(points=points, max_points=15, label="Win rate do produto", reason=reason, signal=signal)


# ---------------------------------------------------------------------------
# FATOR 5 — Agent Performance (0–15 pts)
# Win rate histórico do vendedor responsável.
# Feature não-óbvia: vendedor experiente no tipo de deal aumenta probabilidade real.
# ---------------------------------------------------------------------------

def factor_agent_performance(deal: pd.Series, metrics: dict) -> dict:
    agent     = deal.get("sales_agent", "")
    global_wr = metrics.get("global_win_rate", 0.5)

    agent_wr = metrics.get("agent_win_rate", {}).get(agent)

    if agent_wr is None:
        return _factor_result(
            points=7, max_points=15,
            label="Performance do vendedor",
            reason=f"Sem histórico suficiente para o vendedor '{agent}'.",
            signal="neutral",
        )

    ratio = agent_wr / global_wr if global_wr > 0 else 1.0
    points = 15 * min(ratio / 2.0, 1.0)

    if agent_wr >= global_wr * 1.2:
        signal = "positive"
        qual = "alta performance"
        adj = "acima da média"
    elif agent_wr >= global_wr * 0.8:
        signal = "neutral"
        qual = "performance regular"
        adj = "próximo da média"
    else:
        signal = "warning"
        qual = "performance abaixo"
        adj = "abaixo da média"

    reason = (
        f"Vendedor '{agent}' tem {qual}: win rate de {agent_wr:.0%} "
        f"({adj} — média geral: {global_wr:.0%})."
    )

    return _factor_result(points=points, max_points=15, label="Performance do vendedor", reason=reason, signal=signal)

# ---------------------------------------------------------------------------
# FATOR 6 — Notes Activity (0–10 pts, pode ser negativo até -8)
# Atividade de notas registradas pelo vendedor no deal.
# Feature não-óbvia: deals com contato recente documentado têm
# probabilidade de fechamento maior — o vendedor está engajado.
#
# Pontuação:
#   +10  → nota nos últimos 2 dias   (deal muito ativo)
#   + 7  → nota nos últimos 5 dias   (ativo)
#   + 3  → nota nos últimos 10 dias  (razoável)
#   + 0  → sem notas                 (neutro — não penaliza deals novos)
#   - 5  → sem nota há 10–20 dias em deal Engaging (esquecido)
#   - 8  → sem nota há 20+ dias em deal Engaging   (abandonado)
# ---------------------------------------------------------------------------

def factor_notes_activity(deal: pd.Series, metrics: dict) -> dict:
    opportunity_id = str(deal.get("opportunity_id", ""))
    stage          = deal.get("deal_stage", "")

    # Importa aqui para evitar circular import no topo do módulo
    try:
        from notes.store import get_days_since_last_note
        days_since = get_days_since_last_note(opportunity_id)
    except Exception:
        days_since = None

    # Sem notas
    if days_since is None:
        # Penaliza deals em Engaging sem nenhuma nota há muito tempo
        days_in_pipe = deal.get("days_in_pipeline", 0) or 0
        if stage == "Engaging" and days_in_pipe >= 20:
            return _factor_result(
                points=0, max_points=10,
                label="Atividade de contato",
                reason=(
                    f"Nenhuma nota registrada neste deal há {days_in_pipe} dias em Engaging. "
                    "Documente o próximo contato para manter o histórico."
                ),
                signal="warning",
            )
        return _factor_result(
            points=5, max_points=10,
            label="Atividade de contato",
            reason="Sem notas registradas ainda. Adicione uma nota após o próximo contato.",
            signal="neutral",
        )

    # Com notas — classifica por recência
    if days_since <= 2:
        points = 10
        signal = "positive"
        reason = f"✓ Contato recente: nota registrada há {days_since}d. Deal ativo e bem acompanhado."
    elif days_since <= 5:
        points = 7
        signal = "positive"
        reason = f"Última nota há {days_since} dias. Bom ritmo de acompanhamento."
    elif days_since <= 10:
        points = 3
        signal = "neutral"
        reason = f"Última nota há {days_since} dias. Considere um novo contato em breve."
    elif days_since <= 20:
        # Penalidade leve para Engaging, neutro para Prospecting
        if stage == "Engaging":
            points = 0
            signal = "warning"
            reason = (
                f"⚠ Última nota há {days_since} dias em fase Engaging. "
                "Deal pode estar esfriando — agende um follow-up."
            )
        else:
            points = 1
            signal = "neutral"
            reason = f"Última nota há {days_since} dias."
    else:
        # 20+ dias sem nota em Engaging = penalidade forte
        if stage == "Engaging":
            points = 0
            signal = "warning"
            reason = (
                f"🚨 Sem nota há {days_since} dias em Engaging. "
                "Deal possivelmente abandonado. Reative o contato ou reclassifique."
            )
        else:
            points = 0
            signal = "warning"
            reason = f"Sem nota há {days_since} dias. Verifique o status deste deal."

    return _factor_result(
        points=points, max_points=10,
        label="Atividade de contato",
        reason=reason,
        signal=signal,
    )