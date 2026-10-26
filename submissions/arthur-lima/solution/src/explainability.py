"""
Commercial Explainability & Operational Playbook Generator.

Translates the separated statistical estimates (`p_win_90d`, `ev_90d`) and
operational governance flags (`crm_hygiene_status`, `is_stale_p95`, `override_disposition`)
into clear, non-black-box explanations and suggested commercial actions.
"""

from __future__ import annotations

from typing import Tuple
import pandas as pd


def generate_deal_reasons(row: pd.Series) -> Tuple[str, str, str]:
    """
    Generates 3 transparent drivers strictly aligned with the underlying columns:
    - Driver 1: Empirical 90-day conversion signal by deal age (`cycle_days`, `p_win_90d`).
    - Driver 2: Expected 90-day revenue (`ev_90d = p_win_90d * expected_won_value`).
    - Driver 3: CRM data hygiene (`has_account`) & active field overrides (kept separate from `p_win_90d`).
    """
    cycle = float(row.get("cycle_days", 0.0))
    p_win = float(row.get("p_win_90d", 0.35))
    ev_90d = float(row.get("ev_90d", 0.0))
    exp_val = float(row.get("expected_won_value", 0.0))
    has_acc = bool(row.get("has_account", False))
    is_stale = bool(row.get("is_stale_p95", False))
    med_cycle = float(row.get("product_median_cycle", 57.0))
    product = str(row.get("product", "Produto"))
    account = str(row.get("account_display", "Conta"))
    override_disp = str(row.get("override_disposition", "none"))
    override_reason = str(row.get("override_reason", ""))

    # Driver 1: Empirical Age Signal (90-day horizon)
    if is_stale:
        driver_1 = (
            f"📉 Estagnação Acima do P95 ({int(cycle)}d no funil): Em coortes históricas, "
            f"negócios nessa faixa convertem apenas {p_win*100:.1f}% nos próximos 90 dias."
        )
    elif cycle <= med_cycle:
        driver_1 = (
            f"⏱️ Janela Ativa ({int(cycle)}d no funil, mediana {int(med_cycle)}d): "
            f"Taxa empírica de conversão em 90 dias estimada em {p_win*100:.1f}%."
        )
    else:
        driver_1 = (
            f"⚠️ Ciclo Estendido ({int(cycle)}d no funil, acima da mediana de {int(med_cycle)}d): "
            f"Conversão empírica em 90 dias estimada em {p_win*100:.1f}%."
        )

    # Driver 2: Expected 90-Day Revenue
    driver_2 = (
        f"💵 Receita Esperada em 90d (${ev_90d:,.0f}): Produto {product} com ticket mediano "
        f"histórico de ${exp_val:,.0f} ponderado pela chance empírica de fechamento no trimestre."
    )

    # Driver 3: CRM Hygiene & Field Override Governance (explicitly separate from probability)
    if override_disp != "none":
        driver_3 = (
            f"🔄 Override Manual Ativo ({override_disp.upper()}): Posição na fila ajustada pelo "
            f"vendedor ({override_reason or 'contexto de campo'}), preservando P(90d) original para auditoria."
        )
    elif not has_acc:
        driver_3 = (
            "⚠️ Pendência de Higiene Cadastral: Negócio sem conta vinculada no CRM. "
            "Exige enriquecimento cadastral antes do fechamento (sem penalidade arbitrária em P_90d)."
        )
    else:
        driver_3 = (
            f"✅ Cadastro Completo ({account}): Conta vinculada no CRM, apta para "
            "formalização contratual sem bloqueio cadastral."
        )

    return driver_1, driver_2, driver_3


def generate_prescriptive_action(row: pd.Series) -> Tuple[str, str, str]:
    """
    Generates operational workflow suggestions (heuristic playbook, explicitly non-causal):
    - Recommended next step
    - Suggested SLA window
    - Outreach / follow-up template
    """
    action_tier = str(row.get("action_tier", ""))
    account = str(row.get("account_display", "Cliente"))
    product = str(row.get("product", "Solução"))
    has_acc = bool(row.get("has_account", False))
    exp_val = float(row.get("expected_won_value", 0.0))

    if "Desqualificado" in action_tier:
        next_step = "Manter arquivado fora da fila ativa; formalizar baixa como Lost no CRM se confirmado."
        sla = "Sem ação ativa"
        script = (
            f"Registro interno: oportunidade de {product} ({account}) marcada para baixa "
            "conforme contexto de campo do vendedor."
        )
    elif "Pausado" in action_tier:
        next_step = "Manter em acompanhamento passivo até a data acordada de retomada de orçamento."
        sla = "Revisar no próximo ciclo quinzenal"
        script = (
            f"Olá [Nome], conforme alinhamos sobre o {product}, deixei nosso ponto de retorno "
            "agendado para reavaliarmos assim que a janela orçamentária reabrir."
        )
    elif "Higienizar" in action_tier:
        next_step = (
            "Triagem de Encerramento (Break-up): Solicitar confirmação objetiva de interesse "
            "ou dar baixa como Lost para limpar o backlog em Engaging."
        )
        sla = "Triar em até 48h"
        script = (
            f"Olá [Nome], como não tivemos avanço recente sobre o {product}, vou encerrar "
            "nosso acompanhamento ativo por ora. Caso o projeto volte à pauta, basta me acionar."
        )
    elif "Gargalo" in action_tier:
        if exp_val >= 4000:
            next_step = (
                "Destravamento Executivo: Mapear bloqueio de aprovação junto ao decisor econômico "
                + ("e vincular conta no CRM." if not has_acc else "com apoio da gerência.")
            )
            sla = "Contato em até 24h"
        else:
            next_step = (
                "Revalidação de Escopo e Prazo: Confirmar data real de decisão ou encerrar pendência."
            )
            sla = "Contato em até 48h"
        script = (
            f"Olá [Nome], gostaria de validar se ainda faz sentido mantermos o cronograma do {product} "
            "para este trimestre ou se existe alguma pendência técnica/comercial que possamos destravar."
        )
    else:
        # Active window or manually promoted
        prefix = "Vincular conta no CRM + " if not has_acc else ""
        next_step = (
            f"{prefix}Avançar Fechamento: Validar proposta comercial e definir data de decisão."
        )
        sla = "Prioridade do dia"
        script = (
            f"Olá [Nome], dando sequência à avaliação do {product}, já consolidei os termos "
            "comerciais para validarmos os próximos passos de implantação."
        )

    return next_step, sla, script


def enrich_with_explainability(df: pd.DataFrame) -> pd.DataFrame:
    """Enriches scored deals with deterministic explainability and workflow suggestions."""
    out = df.copy()
    if len(out) == 0:
        for col in [
            "driver_1",
            "driver_2",
            "driver_3",
            "recommended_next_step",
            "sla_recommendation",
            "suggested_script",
        ]:
            out[col] = pd.Series(dtype=str)
        return out

    reasons = [generate_deal_reasons(row) for _, row in out.iterrows()]
    actions = [generate_prescriptive_action(row) for _, row in out.iterrows()]

    out["driver_1"] = [r[0] for r in reasons]
    out["driver_2"] = [r[1] for r in reasons]
    out["driver_3"] = [r[2] for r in reasons]

    out["recommended_next_step"] = [a[0] for a in actions]
    out["sla_recommendation"] = [a[1] for a in actions]
    out["suggested_script"] = [a[2] for a in actions]

    return out
