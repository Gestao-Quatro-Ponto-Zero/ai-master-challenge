"""Engine de copy de follow-up em 3 tons com CTA explicito."""
from __future__ import annotations

from typing import Any

from sales_hooks import get_next_best_action, get_sales_hooks


TONES = ("consultivo", "direto", "provocativo elegante")


def _safe(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def _lead_context(lead_profile: dict[str, Any]) -> dict[str, str]:
    return {
        "lead_id": _safe(lead_profile.get("lead_id"), "lead_sem_id"),
        "lead_name": _safe(lead_profile.get("lead_name"), "sua conta"),
        "owner": _safe(lead_profile.get("owner"), "time comercial"),
        "product": _safe(lead_profile.get("product"), "solucao"),
        "deal_stage": _safe(lead_profile.get("deal_stage"), "pipeline"),
        "segment": _safe(lead_profile.get("segment"), "seu segmento"),
        "disc": _safe(lead_profile.get("disc_profile"), "indefinido"),
        "rationale": _safe(lead_profile.get("disc_rationale"), "avaliacao comportamental em aberto"),
    }


def _copy_templates(ctx: dict[str, str]) -> list[dict[str, str]]:
    """Gera 3 copies entre 60-120 palavras, sempre com CTA explicito."""
    consultivo = {
        "tone": "consultivo",
        "subject": f"{ctx['lead_name']}: proximo passo para avancar com seguranca",
        "text": (
            f"Oi, tudo bem? Revendo o contexto de {ctx['lead_name']}, vi que estamos em {ctx['deal_stage']} com foco em "
            f"{ctx['product']}. Minha leitura e que faz sentido avancar com um passo simples e objetivo, sem aumentar risco de execucao. "
            f"Pelo perfil observado ({ctx['disc']}), vale priorizar clareza de resultado e criterio de decisao. "
            "Se fizer sentido, eu te proponho uma conversa de 15 minutos para alinhar escopo, indicador principal e prazo de validacao. "
            "Podemos agendar ainda hoje para destravar esse proximo passo?"
        ),
    }
    direto = {
        "tone": "direto",
        "subject": f"{ctx['lead_name']}: vamos fechar o proximo passo hoje?",
        "text": (
            f"Quero te ajudar a tirar {ctx['lead_name']} da inercia no estagio {ctx['deal_stage']}. "
            f"Temos um caminho pratico para avancar com {ctx['product']} sem complicacao: definir objetivo, responsavel e data de execucao. "
            "Nao precisa de reuniao longa. Em 15 minutos fechamos um plano de acao claro para a semana, com criterio de sucesso combinado. "
            "Se topar, te envio duas opcoes de horario agora e ja deixamos o proximo passo confirmado. Pode ser?"
        ),
    }
    provocativo = {
        "tone": "provocativo elegante",
        "subject": f"{ctx['lead_name']}: custo de esperar mais uma semana",
        "text": (
            f"Uma pergunta franca: quanto custa para {ctx['lead_name']} manter o status atual por mais uma semana? "
            f"Pelo momento do deal em {ctx['deal_stage']}, adiar decisao tende a aumentar retrabalho e reduzir previsibilidade de resultado. "
            f"A oportunidade aqui nao e fazer mais uma reuniao, e sim decidir um experimento curto com {ctx['product']} e metrica objetiva. "
            "Se voce concordar, eu preparo um plano de 2 semanas com criterio de validacao e te apresento em 15 minutos. "
            "Faz sentido alinharmos isso hoje?"
        ),
    }
    return [consultivo, direto, provocativo]


def _validate_copies(copies: list[dict[str, str]]) -> list[dict[str, str]]:
    """Assegura 3 tons unicos, CTA explicito e tamanho adequado."""
    out: list[dict[str, str]] = []
    for idx, c in enumerate(copies):
        tone = c.get("tone", TONES[idx])
        text = c.get("text", "")
        subject = c.get("subject", "")

        if "?" not in text:
            text = text.rstrip(".") + ". Podemos combinar o proximo passo hoje?"

        words = text.split()
        if len(words) < 60:
            text += " Minha sugestao e fechar ja uma data de revisao para garantir ritmo e previsibilidade do avanc o comercial."
        if len(text.split()) > 120:
            text = " ".join(text.split()[:120])

        out.append({"tone": tone, "text": text, "subject": subject})

    # fallback defensivo para garantir contrato de 3 tons
    existing_tones = {i["tone"] for i in out}
    for tone in TONES:
        if tone not in existing_tones:
            out.append(
                {
                    "tone": tone,
                    "subject": f"Follow-up {tone}",
                    "text": "Vamos alinhar um proximo passo objetivo ainda esta semana?",
                }
            )
    return out[:3]


def generate_followup_package(lead_profile: dict[str, Any]) -> dict[str, Any]:
    """Gera pacote completo: 3 copies, hooks e next best action."""
    ctx = _lead_context(lead_profile)

    critical_missing = []
    if ctx["lead_id"] == "lead_sem_id":
        critical_missing.append("lead_id")
    if ctx["lead_name"] == "sua conta":
        critical_missing.append("lead_name")

    if critical_missing:
        fallback_text = (
            "Estou acompanhando seu contexto e quero propor um proximo passo simples para avancarmos com seguranca. "
            "Podemos marcar 15 minutos para validar prioridade, criterio de sucesso e data de execucao ainda nesta semana?"
        )
        copies = [
            {"tone": "consultivo", "subject": "Alinhamento rapido de proximo passo", "text": fallback_text},
            {"tone": "direto", "subject": "Confirmamos o proximo passo hoje?", "text": fallback_text},
            {"tone": "provocativo elegante", "subject": "Custo de adiar a decisao", "text": fallback_text},
        ]
    else:
        copies = _copy_templates(ctx)

    copies = _validate_copies(copies)
    hooks = get_sales_hooks(lead_profile)
    next_action = get_next_best_action(lead_profile, hooks)

    return {
        "lead_id": ctx["lead_id"],
        "disc_profile": _safe(lead_profile.get("disc_profile"), "indefinido"),
        "copies": copies,
        "sales_hooks": hooks,
        "next_best_action": next_action,
    }
