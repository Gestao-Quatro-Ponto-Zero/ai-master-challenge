import hashlib
import json
import anthropic

# ── In-process cache (lives for the duration of the Streamlit server process)
_cache: dict[str, object] = {}


def _make_key(row_dict: dict, model: str) -> str:
    """Hash key for get_recommendation cache."""
    content = json.dumps(
        {
            k: str(v)
            for k, v in row_dict.items()
            if k in [
                "opportunity_id", "account", "deal_stage",
                "score", "tier", "sector", "sales_agent",
                "effective_value",
            ]
        },
        sort_keys=True,
    ) + model
    return hashlib.md5(content.encode()).hexdigest()


def _make_chat_key(messages: list[dict], pipeline_context: str, model: str) -> str:
    """Hash key for chat_completion cache."""
    content = json.dumps(messages, sort_keys=True) + pipeline_context[:500] + model
    return hashlib.md5(content.encode()).hexdigest()


def _make_summary_key(stats: dict, model: str) -> str:
    """Hash key for get_executive_summary cache."""
    content = json.dumps({k: str(v) for k, v in stats.items()}, sort_keys=True) + model
    return hashlib.md5(content.encode()).hexdigest()


# ── get_recommendation ───────────────────────────────────────────────────────

def get_recommendation(row, breakdown: dict, api_key: str, model: str = "claude-sonnet-4-20250514") -> dict:
    fallback = {
        "urgency": "media",
        "main_risk": "Não foi possível obter análise da IA.",
        "next_action": "Revisar o deal manualmente e definir próximo passo.",
        "why_score": "Score calculado com base nas 6 features do modelo de regras.",
    }

    # ── Cache check ──────────────────────────────────────────────────────────
    cache_key = _make_key(row if isinstance(row, dict) else row.to_dict(), model)
    if cache_key in _cache:
        return _cache[cache_key]

    try:
        breakdown_text = "\n".join(
            f"  - {label}: {pts} pts" for label, pts in breakdown.items()
        )

        prompt = f"""Você é um assistente de RevOps especializado em análise de pipeline de vendas B2B.

Analise esta oportunidade e responda SOMENTE com JSON válido, sem markdown, sem explicações.

DADOS DO DEAL:
- ID: {row.get('opportunity_id', 'N/A')}
- Conta: {row.get('account', 'N/A')}
- Vendedor: {row.get('sales_agent', 'N/A')}
- Produto: {row.get('product', 'N/A')} (série: {row.get('series', 'N/A')})
- Estágio: {row.get('deal_stage', 'N/A')}
- Dias no pipeline: {row.get('days_in_pipeline', 'N/A')}
- Valor esperado: R$ {float(row.get('effective_value', 0)):,.0f}
- Setor da conta: {row.get('sector', 'N/A')}
- Receita da conta: US$ {float(row.get('revenue', 0)):,.1f}M
- Funcionários: {int(row.get('employees', 0))}
- Região: {row.get('regional_office', 'N/A')}
- Manager: {row.get('manager', 'N/A')}
- Score total: {row.get('score', 'N/A')} / 100
- Tier: {row.get('tier', 'N/A')}

BREAKDOWN DO SCORE (calculado do histórico real do dataset):
{breakdown_text}

Retorne EXATAMENTE este JSON (sem markdown, sem ```):
{{
  "urgency": "alta" | "media" | "baixa",
  "main_risk": "1 frase com dado concreto sobre o maior risco deste deal",
  "next_action": "1 ação específica para hoje ou amanhã",
  "why_score": "1 frase conectando os dados ao score obtido"
}}"""

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = message.content[0].text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(raw)

        for key in ("urgency", "main_risk", "next_action", "why_score"):
            if key not in result:
                result[key] = fallback[key]

        _cache[cache_key] = result
        return result

    except Exception:
        return fallback


# ── chat_completion ──────────────────────────────────────────────────────────

def chat_completion(messages: list[dict], pipeline_context: str, api_key: str, model: str = "claude-sonnet-4-20250514") -> str:
    # ── Cache check ──────────────────────────────────────────────────────────
    cache_key = _make_chat_key(messages, pipeline_context, model)
    if cache_key in _cache:
        return _cache[cache_key]

    system_prompt = (
        "Você é um assistente de vendas especialista em análise de pipeline. "
        "Responda sempre de forma direta e acionável. "
        "Use os dados reais do pipeline fornecidos. "
        "Cite números e deals específicos nas respostas. "
        "Nunca invente dados que não estejam no contexto.\n\n"
        f"PIPELINE ATUAL DO VENDEDOR (top 50 por score):\n{pipeline_context}"
    )

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
        )
        result = response.content[0].text.strip()
        _cache[cache_key] = result
        return result
    except Exception as e:
        return f"Erro ao consultar a IA: {e}"


# ── get_executive_summary ────────────────────────────────────────────────────

def get_executive_summary(stats: dict, api_key: str, model: str = "claude-sonnet-4-20250514") -> str:
    # ── Cache check ──────────────────────────────────────────────────────────
    cache_key = _make_summary_key(stats, model)
    if cache_key in _cache:
        return _cache[cache_key]

    user_prompt = f"""Analise este pipeline de vendas e gere um resumo executivo em 4 bullets curtos e diretos:

DADOS DO PIPELINE:
- Total de deals abertos: {stats['total_deals']}
- Tier A (score ≥70): {stats['tier_a_count']} deals | R$ {stats['tier_a_value']:,.0f}
- Tier B (score 40-69): {stats['tier_b_count']} deals
- Score médio: {stats['avg_score']:.0f}/100
- Top vendedor por Tier A: {stats['top_seller']}
- Setor com mais Tier A: {stats['top_sector']}
- Mês com maior win rate histórico: {stats['best_month']} ({stats['best_wr']:.0%})
- Mês com menor win rate histórico: {stats['worst_month']} ({stats['worst_wr']:.0%})

Gere exatamente 4 bullets no formato:
- [insight acionável com número concreto]"""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=model,
            max_tokens=512,
            system=(
                "Você é um analista de RevOps especialista em pipeline B2B. "
                "Seja direto e objetivo. Responda em português."
            ),
            messages=[{"role": "user", "content": user_prompt}],
        )
        result = message.content[0].text.strip()
        _cache[cache_key] = result
        return result
    except Exception as e:
        return f"Erro ao gerar resumo: {e}"
