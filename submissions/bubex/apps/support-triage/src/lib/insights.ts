import type { DiagnosticOverview, Bottleneck, ChannelStats, TypeStats } from '@/types'

export interface InsightsPayload {
  overview: DiagnosticOverview
  bottlenecks: Bottleneck[]
  channelStats: ChannelStats[]
  typeStats: TypeStats[]
}

/** Generates 4 diagnostic insights from real data via OpenRouter.
 *  Falls back to data-derived text if no API key is set or the call fails. */
export async function generateInsights(payload: InsightsPayload): Promise<string[]> {
  const apiKey = process.env.OPENROUTER_API_KEY
  if (!apiKey) return fallbackInsights(payload)

  const { overview, bottlenecks, channelStats, typeStats } = payload

  const dataSummary = JSON.stringify({
    totalTickets:       overview.totalTickets,
    backlogRate:        overview.backlogRate,
    openTickets:        overview.openTickets,
    pendingTickets:     overview.pendingTickets,
    closedTickets:      overview.closedTickets,
    avgResolutionHours: overview.avgResolutionHours,
    avgCsat:            overview.avgCsat,
    top5Bottlenecks:    bottlenecks.slice(0, 5),
    channelStats,
    typeStats,
  })

  const prompt = `Você é um analista de operações de suporte ao cliente. Analise os dados abaixo e gere exatamente 4 achados (insights) relevantes para um gestor de operações.

Regras:
- Cada achado deve ser uma frase objetiva com os números reais dos dados
- Destaque o que é crítico, surpreendente ou acionável
- Não repita os mesmos números em achados diferentes
- Responda APENAS com um array JSON de 4 strings, sem texto extra

Dados:
${dataSummary}`

  try {
    const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://github.com/bubex/ai-master-challenge',
        'X-Title': 'Support Triage — AI Master Challenge',
      },
      body: JSON.stringify({
        model: 'anthropic/claude-haiku-4-5',
        max_tokens: 600,
        messages: [{ role: 'user', content: prompt }],
      }),
    })

    if (!res.ok) {
      console.error('[insights] OpenRouter error', res.status)
      return fallbackInsights(payload)
    }

    const data = await res.json()
    const raw = data.choices?.[0]?.message?.content?.trim()
    if (!raw) return fallbackInsights(payload)

    const parsed = JSON.parse(raw)
    if (Array.isArray(parsed) && parsed.length > 0) return parsed as string[]

    return fallbackInsights(payload)
  } catch (err) {
    console.error('[insights] failed', err)
    return fallbackInsights(payload)
  }
}

/** Data-driven fallback — all values come from the actual payload, no hardcoding. */
function fallbackInsights({ overview, bottlenecks, channelStats }: InsightsPayload): string[] {
  const worst = bottlenecks[0]
  const bestCh  = [...channelStats].sort((a, b) => b.avgCsat - a.avgCsat)[0]
  const worstCh = [...channelStats].sort((a, b) => a.avgCsat - b.avgCsat)[0]
  const bestChPct = overview.totalTickets > 0
    ? Math.round((channelStats.find(c => c.channel === bestCh?.channel)?.total ?? 0) / overview.totalTickets * 100)
    : 0

  return [
    `${overview.backlogRate}% dos tickets não estão resolvidos — ${overview.openTickets} abertos e ${overview.pendingTickets} aguardando resposta, superando os ${overview.closedTickets} fechados.`,
    `CSAT médio de ${overview.avgCsat}/5 está abaixo do benchmark de 3.5. O canal mais crítico é ${worstCh?.channel} (${worstCh?.avgCsat}) e o melhor é ${bestCh?.channel} (${bestCh?.avgCsat}).`,
    worst
      ? `Pior gargalo: ${worst.channel} + ${worst.type} com ${worst.avgHours}h de resolução média em ${worst.n} tickets — ${(((worst.avgHours - overview.avgResolutionHours) / overview.avgResolutionHours) * 100).toFixed(0)}% acima da média geral.`
      : `Tempo médio de resolução é ${overview.avgResolutionHours}h nos tickets fechados.`,
    `${bestCh?.channel} tem o melhor CSAT (${bestCh?.avgCsat}) mas representa apenas ${bestChPct}% do volume total — potencial de escala subutilizado.`,
  ]
}
