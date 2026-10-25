"""
Actionable Commercial Explainability & Tactical Playbook Engine.

Translates mathematical score components (Survival Factor, Empirical Bayes Priors, EV Velocity)
into plain, non-black-box commercial language for sales representatives and managers:
1. Three concrete drivers of the opportunity score.
2. Recommended prescriptive next step with SLA.
3. Cold/warm outreach conversation openers and 'break-up' scripts for zombie suspects.
"""

from __future__ import annotations

from typing import Dict, List, Tuple
import pandas as pd


def generate_deal_reasons(row: pd.Series) -> Tuple[str, str, str]:
    """Generates 3 deterministic, plain-language commercial reasons for an opportunity's score."""
    cycle = float(row.get("cycle_days", 0.0))
    p_win = float(row.get("p_win", 0.5))
    ev_day = float(row.get("ev_per_day", 0.0))
    exp_val = float(row.get("expected_won_value", 0.0))
    has_acc = bool(row.get("has_account", False))
    is_ent = bool(row.get("is_enterprise_account", False))
    product = str(row.get("product", "Produto"))
    account = str(row.get("account_display", "Conta"))
    action_tier = str(row.get("action_tier", ""))

    # --- Driver 1: Pipeline Velocity & Aging Window ---
    is_zombie = bool(row.get("is_zombie_suspect", False))
    if is_zombie or "Zombie" in action_tier:
        driver_1 = f"🚨 Estagnação Crítica ({int(cycle)} dias no funil): Oportunidade ultrapassou o P95 de conversão para {product}. Prioritária para higienização."
    elif cycle <= 14:
        driver_1 = f"⚡ Prospecção Recente ({int(cycle)} dias no funil): Oportunidade em qualificação inicial. Período crítico de triagem."
    elif cycle <= 60:
        driver_1 = f"⏱️ Fase de Maturação Ativa ({int(cycle)} dias no funil): Dentro da janela áurea de conversão para {product}."
    else:
        driver_1 = f"⚠️ Ciclo Estendido ({int(cycle)} dias no funil): Negociação acima da mediana do produto. Exige revalidação de timeline."

    # --- Driver 2: Account Fit & CRM Data Completeness ---
    if not has_acc:
        driver_2 = "⚠️ Oportunidade Órfã (Sem Conta no CRM): Falta mapeamento de decisores e dados corporativos, reduzindo o score de tração."
    elif is_ent:
        driver_2 = f"🏢 Conta Enterprise ({account}): Alto faturamento/porte com orçamento corporativo robusto para {product}."
    else:
        driver_2 = f"✅ Conta Vinculada ({account}): Registro comercial ativo e perfil aderente ao histórico do portfólio."

    # --- Driver 3: Financial Yield & Expected Velocity ---
    if exp_val >= 10000:
        driver_3 = f"💎 Impacto de Receita Nobre: Contrato estimado em ${exp_val:,.0f} com rendimento esperado de ${ev_day:,.0f}/dia restante."
    elif ev_day >= 50:
        driver_3 = f"📈 Alta Eficiência Comercial: Velocidade esperada de ${ev_day:,.0f}/dia com ciclo enxuto e conversão estimada em {p_win*100:.0f}%."
    else:
        driver_3 = f"📊 Ticket de Volume (${exp_val:,.0f}): Conversão prevista de {p_win*100:.0f}%, ideal para compor meta de velocidade."

    return driver_1, driver_2, driver_3


def generate_prescriptive_action(row: pd.Series) -> Tuple[str, str, str]:
    """
    Generates:
    - Recommended next tactical step.
    - Prescriptive SLA.
    - Tactical talk track / script snippet.
    """
    action_tier = str(row.get("action_tier", ""))
    account = str(row.get("account_display", "Cliente"))
    product = str(row.get("product", "Solução"))
    has_acc = bool(row.get("has_account", False))
    exp_val = float(row.get("expected_won_value", 0.0))

    if "Zombie" in action_tier:
        next_step = "Auditoria de Encerramento (Break-up Pitch): Enviar e-mail de fechamento de arquivo para reativar resposta ou desqualificar."
        sla = "Executar nas próximas 24h"
        script = (
            f"Olá [Nome], imagino que as prioridades na {account} tenham mudado. "
            f"Como não tivemos retorno sobre o {product}, estou arquivando nosso processo por ora "
            "para não sobrecarregar sua caixa. Caso queira retomar no futuro, estou à disposição."
        )
    elif "Resgate" in action_tier:
        if exp_val >= 5000:
            next_step = "Executive Sponsor Touch: Acionar o gerente/diretor para call estratégica com o sponsor econômico do cliente."
            sla = "Ligar hoje até 17h00"
            script = (
                f"Olá [Nome], nosso diretor de soluções pediu para acompanhar pessoalmente o projeto de {product} "
                f"na {account}. Podemos reservar 15 minutos amanhã para ajustar os termos e viabilizar a implementação?"
            )
        else:
            next_step = "Diagnóstico de Objeção: Descobrir o gargalo de aprovação interna e propor condição especial limitada."
            sla = "Contato nas próximas 48h"
            script = (
                f"Olá [Nome], percebi que nosso cronograma com o {product} pausou. Qual é a principal pendência "
                "interna hoje: validação técnica ou aprovação de verba?"
            )
    else:
        # Acelerar Fechamento
        if not has_acc:
            next_step = "Qualificação Imediata + Agendamento de Demo: Enriquecer a conta no CRM e travar data de validação final."
            sla = "Ligar nas próximas 4 horas"
            script = (
                f"Olá [Nome], parabéns pelo interesse no {product}. "
                "Quero garantir que você veja a aplicação prática no seu cenário antes de fecharmos a alocação de licenças desta semana."
            )
        else:
            next_step = "Fechamento Direto / Apresentação de Proposta Final: Travar call de fechamento com decisor e envio de minuta."
            sla = "Call prioritária Hoje"
            script = (
                f"Olá [Nome], com os pontos alinhados para a {account}, já estruturei os parâmetros para liberar o {product}. "
                "Podemos assinar a formalização até sexta-feira para garantir as condições acordadas?"
            )

    return next_step, sla, script


def enrich_with_explainability(df: pd.DataFrame) -> pd.DataFrame:
    """Enriches the dataframe with all explainability and prescriptive action columns."""
    out = df.copy()

    reasons = [generate_deal_reasons(row) for _, row in out.iterrows()]
    actions = [generate_prescriptive_action(row) for _, row in out.iterrows()]

    out["driver_1"] = [r[0] for r in reasons]
    out["driver_2"] = [r[1] for r in reasons]
    out["driver_3"] = [r[2] for r in reasons]

    out["recommended_next_step"] = [a[0] for a in actions]
    out["sla_recommendation"] = [a[1] for a in actions]
    out["suggested_script"] = [a[2] for a in actions]

    return out
