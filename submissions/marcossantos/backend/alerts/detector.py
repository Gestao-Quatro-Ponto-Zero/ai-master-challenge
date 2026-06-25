"""
alerts/detector.py
------------------
Lógica de detecção de alertas.

Cada função de detecção recebe o pipeline + métricas e retorna
uma lista de alertas candidatos. O scheduler chama todas e deduplica.

Adicionar um novo tipo de alerta = criar uma nova função _detect_*.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from .models import Alert, AlertSeverity, AlertType


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _make_id() -> str:
    return str(uuid.uuid4())[:8]


# ---------------------------------------------------------------------------
# 1. Deals parados acima da média do produto
# ---------------------------------------------------------------------------

def _detect_stale_deals(pipeline: pd.DataFrame, metrics: dict) -> list[Alert]:
    """
    Detecta deals que estão há muito tempo no pipeline comparado
    à média histórica de Won deals do mesmo produto.

    - 1.5x → warning
    - 2.0x → critical (se close_value alto) ou warning
    """
    alerts = []
    product_velocity = metrics.get("product_velocity", {})
    global_avg = 30  # fallback

    active = pipeline[pipeline["deal_stage"].isin(["Prospecting", "Engaging"])].copy()

    for _, deal in active.iterrows():
        product = deal.get("product", "")
        days    = deal.get("days_in_pipeline", 0) or 0
        value   = deal.get("close_value", 0) or 0

        vel = product_velocity.get(product)
        avg_days = vel["avg_days"] if vel else global_avg
        if not avg_days or avg_days <= 0:
            avg_days = global_avg

        ratio = days / avg_days

        if ratio < 1.5:
            continue

        account = deal.get("account", "")
        agent   = deal.get("sales_agent", "")

        # Critical: 2x acima da média E valor relevante
        if ratio >= 2.0:
            severity = AlertSeverity.critical
            alert_type = AlertType.deal_critical_stale
            title = f"Deal crítico parado — {account}"
            message = (
                f"Deal com {account} está há {int(days)} dias no pipeline "
                f"({ratio:.1f}x acima da média de {avg_days:.0f}d para '{product}'). "
                f"Risco alto de perda. Contato imediato necessário."
            )
        else:
            severity = AlertSeverity.warning if value > 0 else AlertSeverity.info
            alert_type = AlertType.deal_stale
            title = f"Deal esfriando — {account}"
            message = (
                f"Deal com {account} está há {int(days)} dias no pipeline "
                f"({ratio:.1f}x acima da média de {avg_days:.0f}d para '{product}'). "
                f"Recomenda-se contato proativo."
            )

        alerts.append(Alert(
            id=_make_id(),
            type=alert_type,
            severity=severity,
            title=title,
            message=message,
            opportunity_id=str(deal.get("opportunity_id", "")),
            account=account,
            sales_agent=agent,
            manager=deal.get("manager"),
            regional_office=deal.get("regional_office"),
            score=int(deal.get("score", 0)) if "score" in deal else None,
            close_value=float(value),
            days_in_pipeline=int(days),
            created_at=_now_iso(),
        ))

    return alerts


# ---------------------------------------------------------------------------
# 2. Deals de alto valor esfriando
# ---------------------------------------------------------------------------

def _detect_high_value_at_risk(pipeline: pd.DataFrame, metrics: dict) -> list[Alert]:
    """
    Deals cujo close_value está acima do percentil 75 dos Won deals
    e que estão esfriando (days_in_pipeline > média do produto).
    Merece alerta separado por impacto financeiro.
    """
    alerts = []
    avg_won_value = metrics.get("avg_won_value", 0)
    high_value_threshold = avg_won_value * 1.5  # 50% acima da média

    if high_value_threshold <= 0:
        return []

    product_velocity = metrics.get("product_velocity", {})
    global_avg = 30

    active = pipeline[pipeline["deal_stage"].isin(["Prospecting", "Engaging"])].copy()
    high_value = active[active["close_value"].fillna(0) >= high_value_threshold]

    for _, deal in high_value.iterrows():
        product  = deal.get("product", "")
        days     = deal.get("days_in_pipeline", 0) or 0
        value    = deal.get("close_value", 0) or 0

        vel = product_velocity.get(product)
        avg_days = vel["avg_days"] if vel else global_avg
        if not avg_days or avg_days <= 0:
            avg_days = global_avg

        # Só alerta se estiver acima da média (já capturado pelo detector geral)
        # Aqui filtramos só os de ALTO VALOR que ainda não estão critical
        ratio = days / avg_days
        if ratio < 1.2 or ratio >= 2.0:  # 2x+ já vai para deal_critical_stale
            continue

        account = deal.get("account", "")
        alerts.append(Alert(
            id=_make_id(),
            type=AlertType.high_value_at_risk,
            severity=AlertSeverity.critical,
            title=f"💰 Deal de alto valor em risco — {account}",
            message=(
                f"Deal de ${value:,.0f} com {account} está esfriando "
                f"({int(days)}d no pipeline, média: {avg_days:.0f}d). "
                f"Valor {value/avg_won_value:.1f}x acima da média dos deals fechados."
            ),
            opportunity_id=str(deal.get("opportunity_id", "")),
            account=account,
            sales_agent=deal.get("sales_agent"),
            manager=deal.get("manager"),
            regional_office=deal.get("regional_office"),
            score=int(deal.get("score", 0)) if "score" in deal else None,
            close_value=float(value),
            days_in_pipeline=int(days),
            created_at=_now_iso(),
        ))

    return alerts


# ---------------------------------------------------------------------------
# 3. Vendedor sem nenhum deal em Engaging
# ---------------------------------------------------------------------------

def _detect_no_engaging_deals(pipeline: pd.DataFrame, metrics: dict) -> list[Alert]:
    """
    Vendedores que têm deals ativos mas nenhum em Engaging.
    Indica pipeline raso — só prospecção, nada avançando.
    """
    alerts = []
    active = pipeline[pipeline["deal_stage"].isin(["Prospecting", "Engaging"])].copy()

    if "sales_agent" not in active.columns:
        return []

    for agent, group in active.groupby("sales_agent"):
        total    = len(group)
        engaging = len(group[group["deal_stage"] == "Engaging"])

        if total < 3:  # ignora vendedores com pipeline muito pequeno
            continue

        if engaging == 0:
            manager = group.iloc[0].get("manager", "")
            region  = group.iloc[0].get("regional_office", "")

            alerts.append(Alert(
                id=_make_id(),
                type=AlertType.no_engaging_deals,
                severity=AlertSeverity.warning,
                title=f"Pipeline raso — {agent}",
                message=(
                    f"{agent} tem {total} deals ativos mas nenhum em fase Engaging. "
                    f"Pipeline travado em Prospecting — ação necessária para avançar deals."
                ),
                opportunity_id=None,
                account=None,
                sales_agent=str(agent),
                manager=manager,
                regional_office=region,
                score=None,
                close_value=None,
                days_in_pipeline=None,
                created_at=_now_iso(),
            ))

    return alerts


# ---------------------------------------------------------------------------
# Orquestrador principal
# ---------------------------------------------------------------------------

def detect_all_alerts(pipeline: pd.DataFrame, metrics: dict) -> list[Alert]:
    """
    Roda todos os detectores e retorna lista consolidada de alertas,
    ordenada por severidade (critical primeiro).
    """
    all_alerts: list[Alert] = []

    detectors = [
        _detect_stale_deals,
        _detect_high_value_at_risk,
        _detect_no_engaging_deals,
    ]

    for detector in detectors:
        try:
            found = detector(pipeline, metrics)
            all_alerts.extend(found)
        except Exception as e:
            # Nunca deixa um detector quebrar o sistema inteiro
            import logging
            logging.getLogger(__name__).error(f"Detector {detector.__name__} falhou: {e}")

    # Ordena: critical > warning > info
    severity_order = {
        AlertSeverity.critical: 0,
        AlertSeverity.warning:  1,
        AlertSeverity.info:     2,
    }
    all_alerts.sort(key=lambda a: severity_order.get(a.severity, 99))

    return all_alerts
