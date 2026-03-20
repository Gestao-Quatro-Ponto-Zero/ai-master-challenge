import type { DiagnosticOverview, Bottleneck, ChannelStats, TypeStats } from '@/types'

export interface InsightsPayload {
  overview: DiagnosticOverview
  bottlenecks: Bottleneck[]
  channelStats: ChannelStats[]
  typeStats: TypeStats[]
}

// ── In-memory cache ───────────────────────────────────────────────────────────

const TTL_MS = 60 * 60 * 1000 // 1 hour

interface CacheEntry { insights: string[]; at: number }
const cache = new Map<string, CacheEntry>()

function cacheKey(payload: InsightsPayload): string {
  const { overview, bottlenecks } = payload
  return [
    overview.totalTickets,
    overview.backlogRate,
    overview.avgResolutionHours,
    overview.avgCsat,
    bottlenecks[0]?.channel,
    bottlenecks[0]?.avgHours,
  ].join('|')
}

// ── Main function ─────────────────────────────────────────────────────────────

/** Generates 4 diagnostic insights from real data via OpenRouter.
 *  Results are cached in memory for 1 hour.
 *  Falls back to data-derived text if no API key is set or the call fails. */
export async function generateInsights(payload: InsightsPayload): Promise<string[]> {
  const key = cacheKey(payload)
  const cached = cache.get(key)
  if (cached && Date.now() - cached.at < TTL_MS) return cached.insights
  const apiKey = process.env.OPENROUTER_API_KEY
  if (!apiKey) {
    const result = fallbackInsights(payload)
    cache.set(key, { insights: result, at: Date.now() })
    return result
  }

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
        'X-Title': 'Support Triage - AI Master Challenge',
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

    // Strip markdown code fences if the model wrapped the JSON
    const cleaned = raw.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/, '').trim()
    const parsed = JSON.parse(cleaned)
    if (Array.isArray(parsed) && parsed.length > 0) {
      cache.set(key, { insights: parsed, at: Date.now() })
      return parsed as string[]
    }

    const fallback = fallbackInsights(payload)
    cache.set(key, { insights: fallback, at: Date.now() })
    return fallback
  } catch (err) {
    console.error('[insights] failed', err)
    const fallback = fallbackInsights(payload)
    cache.set(key, { insights: fallback, at: Date.now() })
    return fallback
  }
}

// ── Proposal sections ─────────────────────────────────────────────────────────

export interface AutomationItem {
  title: string
  reason: string
  automate: boolean
}

export interface ProposalSections {
  automationItems: AutomationItem[]
  limitations: string[]
}

const proposalCache = new Map<string, { data: ProposalSections; at: number }>()

export async function generateProposal(payload: InsightsPayload): Promise<ProposalSections> {
  const key = 'proposal|' + cacheKey(payload)
  const cached = proposalCache.get(key)
  if (cached && Date.now() - cached.at < TTL_MS) return cached.data

  const apiKey = process.env.OPENROUTER_API_KEY
  if (!apiKey) {
    const data = fallbackProposal(payload)
    proposalCache.set(key, { data, at: Date.now() })
    return data
  }

  const { overview, bottlenecks, channelStats, typeStats } = payload

  const dataSummary = JSON.stringify({
    totalTickets:       overview.totalTickets,
    backlogRate:        overview.backlogRate,
    avgResolutionHours: overview.avgResolutionHours,
    avgCsat:            overview.avgCsat,
    top5Bottlenecks:    bottlenecks.slice(0, 5),
    channelStats,
    typeStats,
  })

  const prompt = `Você é um consultor de operações analisando dados reais de suporte ao cliente.
Com base nos dados abaixo, gere:

1. Uma lista de 4-5 itens do que AUTOMATIZAR com IA (baseado no que os dados indicam — gargalos, volumes altos, padrões repetitivos)
2. Uma lista de 4-5 itens do que NÃO automatizar (onde os dados mostram risco, variabilidade ou necessidade de julgamento humano)
3. Uma lista de 3-4 limitações honestas desta análise (baseado na qualidade e características dos dados)

Responda APENAS com JSON válido, sem texto extra:
{
  "automationItems": [
    { "title": "...", "reason": "...", "automate": true },
    { "title": "...", "reason": "...", "automate": false }
  ],
  "limitations": ["...", "..."]
}

Dados:
${dataSummary}`

  try {
    const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://github.com/bubex/ai-master-challenge',
        'X-Title': 'Support Triage - AI Master Challenge',
      },
      body: JSON.stringify({
        model: 'anthropic/claude-haiku-4-5',
        max_tokens: 800,
        messages: [{ role: 'user', content: prompt }],
      }),
    })

    if (!res.ok) {
      console.error('[proposal] OpenRouter error', res.status)
      const data = fallbackProposal(payload)
      proposalCache.set(key, { data, at: Date.now() })
      return data
    }

    const response = await res.json()
    const raw = response.choices?.[0]?.message?.content?.trim()
    if (!raw) {
      const data = fallbackProposal(payload)
      proposalCache.set(key, { data, at: Date.now() })
      return data
    }

    const cleaned = raw.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/, '').trim()
    const parsed = JSON.parse(cleaned) as ProposalSections

    if (parsed.automationItems?.length && parsed.limitations?.length) {
      proposalCache.set(key, { data: parsed, at: Date.now() })
      return parsed
    }

    const data = fallbackProposal(payload)
    proposalCache.set(key, { data, at: Date.now() })
    return data
  } catch (err) {
    console.error('[proposal] failed', err)
    const data = fallbackProposal(payload)
    proposalCache.set(key, { data, at: Date.now() })
    return data
  }
}

function fallbackProposal({ overview, bottlenecks, typeStats }: InsightsPayload): ProposalSections {
  const worst = bottlenecks[0]
  const highVolumeType = typeStats.sort((a, b) => b.total - a.total)[0]

  return {
    automationItems: [
      { title: 'Classificação e roteamento', reason: `${highVolumeType?.type || 'Tickets'} representam o maior volume — critério claro e alto grau de repetição.`, automate: true },
      { title: 'Triagem de prioridade inicial', reason: 'Urgência detectável por palavras-chave; erro tem baixo custo imediato.', automate: true },
      { title: `Gargalo ${worst?.channel} + ${worst?.type}`, reason: `${worst?.n} tickets com ${worst?.avgHours}h médios — candidato prioritário à automação.`, automate: true },
      { title: 'Tickets com carga emocional alta', reason: 'Frustração e raiva exigem empatia humana — IA piora o atendimento.', automate: false },
      { title: 'Decisões de cancelamento/reembolso', reason: 'Impacto financeiro direto — requer autorização humana.', automate: false },
      { title: 'Resposta final ao cliente', reason: 'IA sugere, mas humano sempre revisa antes de enviar.', automate: false },
    ],
    limitations: [
      `Backlog de ${overview.backlogRate}% sugere sub-dimensionamento da equipe — automação ajuda, mas não resolve o problema estrutural.`,
      'Dataset sintético com timestamps agrupados em uma única data — impossível analisar tendências temporais ou sazonalidade.',
      'CSAT uniforme (~3.0 em todos os segmentos) indica dado gerado artificialmente; em produção a variação seria mais reveladora.',
      'ROI estimado não considera custo de implementação, treinamento ou manutenção do modelo de classificação.',
    ],
  }
}

// ── Insights fallback ─────────────────────────────────────────────────────────

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
