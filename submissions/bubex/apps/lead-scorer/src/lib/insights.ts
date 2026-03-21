import type { Deal } from '@/types'

// ── Cache ─────────────────────────────────────────────────────────────────────

const TTL_MS = 24 * 60 * 60 * 1000
const actionCache = new Map<string, { data: string[] | null; at: number }>()

// ── Fallback determinístico (sem API key) ─────────────────────────────────────

function fallbackActions(deal: Deal): string[] {
  const actions: string[] = []

  if (deal.score >= 70 && deal.score_time < 0) {
    actions.push('Deal quente mas envelhecendo — agendar call esta semana antes de perder mais pontos de aging')
  } else if (deal.score >= 70 && deal.score_time === 0) {
    actions.push('Prioridade máxima — enviar proposta formal se ainda não enviada')
  }

  if (deal.deal_stage === 'Prospecting' && deal.score >= 50) {
    actions.push('Mover para Engaging — agendar reunião de descoberta para recuperar 15 pontos de stage')
  }

  if (deal.score_account >= 14 && deal.score_stage === 15) {
    actions.push('Conta de alto valor ainda em Prospecting — envolver AE senior para acelerar o avanço de stage')
  }

  if (deal.days_in_pipeline > 200 && deal.score < 40) {
    actions.push('Deal frio e envelhecido — reavaliar viabilidade ou encerrar para limpar o pipeline')
  }

  if (actions.length === 0) {
    actions.push(`Score ${deal.score} — acompanhar com cadência quinzenal até mudança de stage ou aging crítico`)
  }

  return actions
}

// ── Geração via LLM ───────────────────────────────────────────────────────────

/** Returns action suggestions (string[]) or null when no API key — in that case use fallback. */
export async function generateDealAction(deal: Deal): Promise<{ actions: string[]; fromLLM: boolean }> {
  const cacheKey = deal.opportunity_id
  const hit = actionCache.get(cacheKey)
  if (hit && Date.now() - hit.at < TTL_MS) {
    return { actions: hit.data ?? fallbackActions(deal), fromLLM: hit.data !== null }
  }

  const apiKey = process.env.OPENROUTER_API_KEY
  if (!apiKey) {
    actionCache.set(cacheKey, { data: null, at: Date.now() })
    return { actions: fallbackActions(deal), fromLLM: false }
  }

  const payload = JSON.stringify({
    stage:         deal.deal_stage,
    score:         deal.score,
    score_stage:   deal.score_stage,
    score_value:   deal.score_value,
    score_account: deal.score_account,
    score_time:    deal.score_time,
    score_series:  deal.score_series,
    score_agent:   deal.score_agent,
    days_in_pipeline: deal.days_in_pipeline,
    account:       deal.account,
    sector:        deal.sector,
    win_rate_pct:  deal.win_rate_pct,
    product:       deal.product,
    series:        deal.series,
    sales_price:   deal.sales_price,
  })

  const prompt = `Você é um coach de vendas B2B. Analise o deal abaixo e sugira exatamente 2 ações concretas para o vendedor fechar essa oportunidade.

Regras:
- Cada ação deve ser uma instrução direta (verbo no imperativo)
- Use os dados do deal para justificar brevemente (máx 15 palavras por ação)
- Foco no que o vendedor pode fazer hoje ou esta semana
- Responda APENAS com um array JSON de 2 strings, sem texto extra

Deal:
${payload}`

  try {
    const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://github.com/bubex/ai-master-challenge',
        'X-Title': 'Lead Scorer - AI Master Challenge',
      },
      body: JSON.stringify({
        model: 'anthropic/claude-haiku-4-5',
        max_tokens: 300,
        messages: [{ role: 'user', content: prompt }],
      }),
    })

    if (!res.ok) {
      console.error('[lead-insights] OpenRouter error', res.status)
      actionCache.set(cacheKey, { data: null, at: Date.now() })
      return { actions: fallbackActions(deal), fromLLM: false }
    }

    const data = await res.json()
    const raw = data.choices?.[0]?.message?.content?.trim()
    if (!raw) {
      actionCache.set(cacheKey, { data: null, at: Date.now() })
      return { actions: fallbackActions(deal), fromLLM: false }
    }

    const cleaned = raw.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/, '').trim()
    const parsed = JSON.parse(cleaned)
    const actions = Array.isArray(parsed) && parsed.length > 0 ? (parsed as string[]) : null

    actionCache.set(cacheKey, { data: actions, at: Date.now() })
    return { actions: actions ?? fallbackActions(deal), fromLLM: actions !== null }
  } catch (err) {
    console.error('[lead-insights] failed', err)
    actionCache.set(cacheKey, { data: null, at: Date.now() })
    return { actions: fallbackActions(deal), fromLLM: false }
  }
}
