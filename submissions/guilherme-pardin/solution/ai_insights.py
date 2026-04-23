import hashlib
import json

# ── Default models ───────────────────────────────────────────────────────────
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
GEMINI_MODEL    = "gemini-2.0-flash-lite"
OPENAI_MODEL    = "gpt-4o-mini"

# ── In-process cache (lives for the duration of the Streamlit server process)
_cache: dict[str, object] = {}


# ── Cache key helpers ────────────────────────────────────────────────────────

def _make_key(row_dict: dict, provider: str) -> str:
    content = json.dumps(
        {k: str(v) for k, v in row_dict.items()
         if k in ["opportunity_id", "account", "deal_stage", "score",
                  "tier", "sector", "sales_agent", "effective_value"]},
        sort_keys=True,
    ) + provider
    return hashlib.md5(content.encode()).hexdigest()


def _make_chat_key(messages: list[dict], pipeline_context: str, provider: str) -> str:
    content = json.dumps(messages, sort_keys=True) + pipeline_context[:500] + provider
    return hashlib.md5(content.encode()).hexdigest()


def _make_summary_key(stats: dict, provider: str) -> str:
    content = json.dumps({k: str(v) for k, v in stats.items()}, sort_keys=True) + provider
    return hashlib.md5(content.encode()).hexdigest()


# ── Internal call helpers ────────────────────────────────────────────────────

def _call_single(prompt: str, system: str, api_key: str, provider: str,
                 max_tokens: int = 512) -> str:
    """Single-turn generation — returns raw text."""
    if "Anthropic" in provider:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
    elif "OpenAI" in provider:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt},
            ],
        )
        return response.choices[0].message.content.strip()
    else:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=max_tokens,
            ),
        )
        return response.text.strip()


def _call_chat(messages: list[dict], system: str, api_key: str,
               provider: str, max_tokens: int = 1024) -> str:
    """Multi-turn chat — returns assistant reply text."""
    if "Anthropic" in provider:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        )
        return response.content[0].text.strip()
    elif "OpenAI" in provider:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        # Prepend system message then pass the full history as-is
        openai_messages = [{"role": "system", "content": system}] + messages
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            max_tokens=max_tokens,
            messages=openai_messages,
        )
        return response.choices[0].message.content.strip()
    else:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key)
        # Convert Anthropic format → Gemini: "assistant" → "model"
        gemini_history = [
            types.Content(
                role="model" if m["role"] == "assistant" else "user",
                parts=[types.Part(text=m["content"])],
            )
            for m in messages[:-1]
        ]
        chat = client.chats.create(
            model=GEMINI_MODEL,
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=max_tokens,
            ),
            history=gemini_history,
        )
        return chat.send_message(messages[-1]["content"]).text.strip()


# ── get_recommendation ───────────────────────────────────────────────────────

def get_recommendation(row, breakdown: dict,
                       api_key: str = "", provider: str = "Anthropic") -> dict:
    fallback = {
        "urgency": "media",
        "main_risk": "Não foi possível obter análise da IA.",
        "next_action": "Revisar o deal manualmente e definir próximo passo.",
        "why_score": "Score calculado com base nas 6 features do modelo de regras.",
    }
    if not api_key:
        return fallback

    row_dict = row if isinstance(row, dict) else row.to_dict()
    cache_key = _make_key(row_dict, provider)
    if cache_key in _cache:
        return _cache[cache_key]

    try:
        breakdown_text = "\n".join(
            f"  - {label}: {pts} pts" for label, pts in breakdown.items()
        )
        prompt = f"""Analise esta oportunidade de vendas e responda SOMENTE com JSON válido, sem markdown.

DADOS DO DEAL:
- ID: {row_dict.get('opportunity_id', 'N/A')}
- Conta: {row_dict.get('account', 'N/A')}
- Vendedor: {row_dict.get('sales_agent', 'N/A')}
- Produto: {row_dict.get('product', 'N/A')} (série: {row_dict.get('series', 'N/A')})
- Estágio: {row_dict.get('deal_stage', 'N/A')}
- Valor esperado: R$ {float(row_dict.get('effective_value', 0)):,.0f}
- Setor da conta: {row_dict.get('sector', 'N/A')}
- Receita da conta: US$ {float(row_dict.get('revenue', 0)):,.1f}M
- Funcionários: {int(row_dict.get('employees', 0))}
- Região: {row_dict.get('regional_office', 'N/A')}
- Score total: {row_dict.get('score', 'N/A')} / 100  |  Tier: {row_dict.get('tier', 'N/A')}

BREAKDOWN DO SCORE:
{breakdown_text}

Retorne EXATAMENTE este JSON (sem markdown, sem ```):
{{
  "urgency": "alta" | "media" | "baixa",
  "main_risk": "1 frase com dado concreto sobre o maior risco deste deal",
  "next_action": "1 ação específica para hoje ou amanhã",
  "why_score": "1 frase conectando os dados ao score obtido"
}}"""

        system = (
            "Você é um assistente de RevOps especializado em pipeline B2B. "
            "Responda em português."
        )
        raw = _call_single(prompt, system, api_key, provider, max_tokens=512)
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

def chat_completion(messages: list[dict], pipeline_context: str,
                    api_key: str = "", provider: str = "Anthropic") -> str:
    if not messages or not api_key:
        return "Nenhuma mensagem para processar." if not messages else "Chave de API não fornecida."

    cache_key = _make_chat_key(messages, pipeline_context, provider)
    if cache_key in _cache:
        return _cache[cache_key]

    system = (
        "Você é um assistente de vendas especialista em análise de pipeline. "
        "Responda sempre de forma direta e acionável. "
        "Use os dados reais do pipeline fornecidos. "
        "Cite números e deals específicos nas respostas. "
        "Nunca invente dados que não estejam no contexto.\n\n"
        f"PIPELINE ATUAL DO VENDEDOR (top 50 por score):\n{pipeline_context}"
    )

    try:
        result = _call_chat(messages, system, api_key, provider, max_tokens=1024)
        _cache[cache_key] = result
        return result
    except Exception as e:
        return f"Erro ao consultar a IA: {e}"


# ── get_executive_summary ────────────────────────────────────────────────────

def get_executive_summary(stats: dict,
                          api_key: str = "", provider: str = "Anthropic") -> str:
    if not api_key:
        return "Chave de API não fornecida."

    cache_key = _make_summary_key(stats, provider)
    if cache_key in _cache:
        return _cache[cache_key]

    prompt = f"""Analise este pipeline de vendas e gere um resumo executivo em 4 bullets curtos e diretos:

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

    system = (
        "Você é um analista de RevOps especialista em pipeline B2B. "
        "Seja direto e objetivo. Responda em português."
    )

    try:
        result = _call_single(prompt, system, api_key, provider, max_tokens=512)
        _cache[cache_key] = result
        return result
    except Exception as e:
        return f"Erro ao gerar resumo: {e}"
