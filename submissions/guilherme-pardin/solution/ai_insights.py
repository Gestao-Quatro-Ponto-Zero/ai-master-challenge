import json
import anthropic


def get_recommendation(row, breakdown: dict, api_key: str, model: str = "claude-sonnet-4-20250514") -> dict:
    fallback = {
        "urgency": "media",
        "main_risk": "Não foi possível obter análise da IA.",
        "next_action": "Revisar o deal manualmente e definir próximo passo.",
        "why_score": "Score calculado com base nas 6 features do modelo de regras.",
    }

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
        # Remove markdown code fences if present
        raw = raw.replace("```json", "").replace("```", "").strip()

        result = json.loads(raw)

        # Validate required keys
        for key in ("urgency", "main_risk", "next_action", "why_score"):
            if key not in result:
                result[key] = fallback[key]

        return result

    except Exception:
        return fallback


def chat_completion(messages: list[dict], pipeline_context: str, api_key: str, model: str = "claude-sonnet-4-20250514") -> str:
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
        return response.content[0].text.strip()
    except Exception as e:
        return f"Erro ao consultar a IA: {e}"
