"""
DealSignal — Friction Engine + Next Best Action Engine.

Deterministic layer that classifies the dominant commercial friction of a deal
and selects the recommended next action from a fixed catalog.
The AI layer uses this output only to communicate — it does not decide.

Architecture:
  CRM data → model → rating engines → friction engine → NBA engine → AI layer
"""

# ── Friction labels (commercial, shown in UI) ─────────────────────────────────

FRICTION_LABELS: dict[str, str] = {
    "execucao": "Momento de Fechar",
    "decisao":  "Decisão Pendente",
    "urgencia": "Engajamento em Risco",
    "valor":    "Proposta de Valor",
}

# ── Friction reasons (injected into AI prompt, Portuguese) ────────────────────

_FRICTION_REASONS: dict[str, str] = {
    "execucao": "Deal bem qualificado e próximo do fechamento — foco em remover últimas barreiras operacionais.",
    "decisao":  "Deal com boa qualificação, mas com sinais de travamento no processo decisório.",
    "urgencia": "Deal com perda de engajamento — risco real de esfriamento ou abandono.",
    "valor":    "Deal ainda não convenceu sobre o valor da solução — proposta ou impacto precisam ser reforçados.",
}

# ── Action catalog ────────────────────────────────────────────────────────────

ACTION_CATALOG: dict[str, str] = {
    "confirmar_decisor":   "confirmar quem é o decisor econômico",
    "validar_orcamento":   "validar orçamento disponível",
    "confirmar_prazo":     "confirmar prazo de decisão",
    "agendar_reuniao":     "agendar próxima reunião com stakeholders",
    "enviar_proposta":     "enviar proposta comercial",
    "alinhar_criterios":   "alinhar critérios de decisão",
    "reengajar_insight":   "reengajar o cliente com novo insight",
    "explorar_impacto":    "explorar impacto do problema no negócio",
    "validar_prioridade":  "validar prioridade do projeto",
    "confirmar_aprovacao": "confirmar aprovação final",
    "negociar_condicoes":  "negociar condições comerciais",
    "avancar_assinatura":  "avançar para assinatura",
}

# ── Narrative texts (deterministic fallback) ───────────────────────────────────

_FORCE_TEXTS: dict[str, str] = {
    "Seller Power":        "forte histórico do vendedor",
    "Deal Momentum":       "bom ritmo de avanço no pipeline",
    "Product Performance": "boa aderência do produto à conta",
    "Stagnation Risk":     "ausência de sinais de estagnação",
}

_RISK_TEXTS: dict[str, str] = {
    "Seller Power":        "histórico de conversão do vendedor abaixo da média",
    "Deal Momentum":       "lentidão recente no avanço do deal",
    "Product Performance": "baixa aderência histórica do produto",
    "Stagnation Risk":     "risco elevado de inatividade",
}


# ── Friction Engine ────────────────────────────────────────────────────────────

def identify_friction(ctx: dict) -> dict:
    """
    Classifies the dominant commercial friction of a deal using a weighted
    scoring approach across 4 friction types.

    Each friction type receives a 0–1 score based on relevant signals.
    The winner is the type with the highest score.
    Confidence reflects the margin between 1st and 2nd place.

    Args:
        ctx: dict with keys:
            win_prob           (float 0–1)
            sp                 (int 0–100, Seller Power)
            dm                 (int 0–100, Deal Momentum)
            pp                 (int 0–100, Product Performance)
            stagnation_health  (int 0–100, Stagnation Risk — HIGH = good/fresh)
            is_stale           (int 0 or 1)
            seller_rank_pct    (float 0–1 or None)
            digital_maturity   (float 0–1 or None)

    Returns:
        {friction, label, confidence, reason, scores}
    """
    win_prob          = float(ctx.get("win_prob") or 0.0)
    sp                = float(ctx.get("sp") or 0)
    dm                = float(ctx.get("dm") or 0)
    pp                = float(ctx.get("pp") or 0)
    stagnation_health = float(ctx.get("stagnation_health") or 50)
    is_stale          = int(ctx.get("is_stale") or 0)

    def _b(condition: bool) -> float:
        return 1.0 if condition else 0.0

    scores: dict[str, float] = {
        # execucao: deal genuinely close to closing — strict thresholds
        "execucao": (
            0.50 * _b(win_prob >= 0.80)
            + 0.30 * _b(sp >= 70)
            + 0.20 * _b(dm >= 60)
        ),

        # decisao: well-qualified but stuck in decision process
        "decisao": (
            0.35 * _b(sp >= 60 and pp >= 55)
            + 0.40 * _b(dm < 58)
            + 0.25 * _b(0.50 <= win_prob <= 0.82)
        ),

        # urgencia: losing engagement / going stale
        "urgencia": (
            0.40 * _b(is_stale == 1)
            + 0.35 * _b(dm < 40)
            + 0.25 * _b(stagnation_health < 35)
        ),

        # valor: product or value proposition not resonating
        "valor": (
            0.50 * _b(pp < 55)
            + 0.30 * _b(win_prob < 0.58)
            + 0.20 * _b(dm >= 40)
        ),
    }

    sorted_frictions = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    winner_key, winner_score = sorted_frictions[0]
    second_score             = sorted_frictions[1][1] if len(sorted_frictions) > 1 else 0.0
    margin                   = winner_score - second_score

    confidence = "Alto" if margin >= 0.25 else ("Médio" if margin >= 0.12 else "Baixo")

    return {
        "friction":   winner_key,
        "label":      FRICTION_LABELS[winner_key],
        "confidence": confidence,
        "reason":     _FRICTION_REASONS[winner_key],
        "scores":     scores,
    }


# ── Next Best Action Engine ───────────────────────────────────────────────────

def choose_next_action(friction: str, ctx: dict) -> dict:
    """
    Selects the recommended next action from the fixed catalog based on
    the dominant friction and secondary deal signals.

    The action is NEVER generated by AI — it comes from ACTION_CATALOG only.

    Args:
        friction: one of "execucao" | "decisao" | "urgencia" | "valor"
        ctx:      same dict as identify_friction

    Returns:
        {"action_key": str, "action_text": str}
    """
    win_prob         = float(ctx.get("win_prob") or 0.0)
    is_stale         = int(ctx.get("is_stale") or 0)
    seller_rank_pct  = ctx.get("seller_rank_pct")
    digital_maturity = ctx.get("digital_maturity")

    if friction == "execucao":
        if win_prob >= 0.85:
            key = "avancar_assinatura"
        elif win_prob >= 0.70:
            key = "confirmar_aprovacao"
        else:
            key = "negociar_condicoes"

    elif friction == "decisao":
        if seller_rank_pct is not None and float(seller_rank_pct) >= 0.65:
            key = "alinhar_criterios"
        else:
            key = "confirmar_decisor"

    elif friction == "urgencia":
        key = "reengajar_insight" if is_stale == 1 else "explorar_impacto"

    else:  # valor
        if digital_maturity is not None and float(digital_maturity) < 0.45:
            key = "explorar_impacto"
        elif win_prob >= 0.50:
            key = "enviar_proposta"
        else:
            key = "validar_prioridade"

    return {"action_key": key, "action_text": ACTION_CATALOG[key]}


# ── AI Prompt Builder ─────────────────────────────────────────────────────────

def build_nba_prompt(ctx: dict, friction_payload: dict, action_payload: dict) -> str:
    """
    Builds the LLM prompt for the AI insight layer.

    The action (Próximo passo) is passed as a hard constraint —
    the AI writes only Observação and Leitura.
    """
    from app.ui.formatters import format_currency

    sp               = int(ctx.get("sp") or 0)
    dm               = int(ctx.get("dm") or 0)
    pp               = int(ctx.get("pp") or 0)
    stagnation       = int(ctx.get("stagnation_health") or 50)
    action_text      = action_payload["action_text"]
    friction_reason  = friction_payload["reason"]
    similar_count    = ctx.get("similar_count", 0)
    win_rate_similar = ctx.get("win_rate_similar", 0.0)
    top_positive     = ctx.get("top_positive", "—")
    top_risk         = ctx.get("top_risk", "—")

    seller_line = ""
    if ctx.get("seller_win_rate") is not None and ctx.get("seller_rank_pct") is not None:
        top_pct = (1 - float(ctx["seller_rank_pct"])) * 100
        seller_line = (
            f"Vendedor: {ctx.get('sales_agent', '—')} "
            f"({float(ctx['seller_win_rate']):.0%} conversão, top {top_pct:.0f}%)\n"
        )

    product_line = ""
    if ctx.get("product_win_rate") is not None:
        product_line = f"Produto: {float(ctx['product_win_rate']):.0%} conversão histórica\n"

    history_block = ""
    if similar_count >= 15:
        history_block = (
            f"Deals similares: {similar_count} | "
            f"Taxa de fechamento: {float(win_rate_similar):.0%}\n\n"
        )

    value_str = format_currency(ctx.get("effective_value"))

    return (
        "Você é o DealSignal AI, assistente de inteligência de vendas.\n\n"
        f"Deal: {ctx.get('product', '—')} | {value_str} | {ctx.get('deal_stage', '—')}\n"
        + seller_line
        + product_line
        + f"Motores: Vendedor={sp} | Momento={dm} | Produto={pp} | Estagnação={stagnation}\n\n"
        f"Diagnóstico do sistema: {friction_reason}\n"
        + history_block
        + f"Fatores positivos: {top_positive}\n"
        f"Fatores de risco: {top_risk}\n\n"
        f'O sistema já determinou o próximo passo: "{action_text}"\n'
        "Escreva APENAS Observação e Leitura. NÃO altere o próximo passo.\n\n"
        "Responda EXATAMENTE neste formato:\n\n"
        "Observação\n"
        "• [máx 10 palavras]\n"
        "• [máx 10 palavras]\n\n"
        f"Próximo passo\n"
        f"{action_text}\n\n"
        "Leitura\n"
        "[1 frase ≤ 20 palavras explicando o que está acontecendo]\n\n"
        "Regras: linguagem comercial simples. Sem termos de ML. "
        "Sem repetir probabilidade numérica. Sem \"priorize este deal\"."
    )


# ── Deal Narrative (deterministic) ───────────────────────────────────────────

def build_deal_narrative(ctx: dict, friction_payload: dict) -> str:
    """
    Generates a short deal narrative using only rule-based logic.
    Never calls the AI — always deterministic.

    Returns 1–2 sentences describing the deal's main strength and main risk.
    """
    engine_scores = ctx.get("engine_scores", {})
    if not engine_scores:
        return "Dados insuficientes para gerar narrativa do deal."

    strongest = max(engine_scores.items(), key=lambda x: x[1])[0]
    weakest   = min(engine_scores.items(), key=lambda x: x[1])[0]

    force = _FORCE_TEXTS.get(strongest, "sinais positivos no pipeline")
    risk  = _RISK_TEXTS.get(weakest, "fatores de atenção identificados")

    if strongest == weakest:
        return f"Este deal apresenta {force}."

    return f"Este deal apresenta {force}. O principal risco está no {risk}."
