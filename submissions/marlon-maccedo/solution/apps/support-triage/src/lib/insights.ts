import type { DiagnosticOverview, Bottleneck, ChannelStats, TypeStats } from '@/types'
import { getOpenRouterApiKey } from '@/lib/env'

export interface InsightsPayload {
  overview: DiagnosticOverview
  bottlenecks: Bottleneck[]
  channelStats: ChannelStats[]
  typeStats: TypeStats[]
}

// ── In-memory cache ───────────────────────────────────────────────────────────

const TTL_MS = 24 * 60 * 60 * 1000 // 24 hours

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
 *  Results are cached in memory for 24 hours. Returns null when no API key. */
export async function generateInsights(payload: InsightsPayload): Promise<string[] | null> {
  const key = cacheKey(payload)
  const cached = cache.get(key)
  if (cached && Date.now() - cached.at < TTL_MS) return cached.insights

  const apiKey = getOpenRouterApiKey()
  if (!apiKey) return null

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

  const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
      'HTTP-Referer': 'https://github.com/marlon-maccedo/ai-master-challenge',
      'X-Title': 'Support Triage - AI Master Challenge',
    },
    body: JSON.stringify({
      model: 'anthropic/claude-haiku-4-5',
      max_tokens: 600,
      messages: [{ role: 'user', content: prompt }],
    }),
  })

  if (!res.ok) return null

  let data: { choices?: Array<{ message?: { content?: string } }> }
  try {
    data = await res.json()
  } catch {
    return null
  }
  const raw = data.choices?.[0]?.message?.content?.trim()
  if (!raw) return null

  const cleaned = raw.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/, '').trim()
  let parsed: unknown
  try {
    parsed = JSON.parse(cleaned)
  } catch {
    return null
  }
  if (!Array.isArray(parsed) || parsed.length === 0) return null

  cache.set(key, { insights: parsed as string[], at: Date.now() })
  return parsed as string[]
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
// cache bust: bump this string when the prompt changes to force regeneration
const PROPOSAL_PROMPT_VERSION = 'v2'

export async function generateProposal(payload: InsightsPayload): Promise<ProposalSections | null> {
  const key = `proposal|${PROPOSAL_PROMPT_VERSION}|` + cacheKey(payload)
  const cached = proposalCache.get(key)
  if (cached && Date.now() - cached.at < TTL_MS) return cached.data

  const apiKey = getOpenRouterApiKey()
  if (!apiKey) return null

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
Com base nos dados abaixo, gere exatamente:
- 3 itens para AUTOMATIZAR (automate: true)
- 3 itens para NÃO automatizar (automate: false)
- 3 limitações honestas desta análise

Responda APENAS com JSON válido, sem texto extra, sem markdown:
{"automationItems":[{"title":"...","reason":"...","automate":true},{"title":"...","reason":"...","automate":false}],"limitations":["...","...","..."]}

Mantenha "reason" e "title" curtos (máx 15 palavras cada). Dados:
${dataSummary}`

  const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
      'HTTP-Referer': 'https://github.com/marlon-maccedo/ai-master-challenge',
      'X-Title': 'Support Triage - AI Master Challenge',
    },
    body: JSON.stringify({
      model: 'anthropic/claude-haiku-4-5',
      max_tokens: 1200,
      messages: [{ role: 'user', content: prompt }],
    }),
  })

  if (!res.ok) return null

  let response: { choices?: Array<{ message?: { content?: string } }> }
  try {
    response = await res.json()
  } catch {
    return null
  }
  const raw = response.choices?.[0]?.message?.content?.trim()
  if (!raw) return null

  const cleaned = raw.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/, '').trim()
  let parsed: ProposalSections
  try {
    parsed = JSON.parse(cleaned) as ProposalSections
  } catch {
    return null
  }

  if (!parsed.automationItems?.length || !parsed.limitations?.length) {
    return null
  }

  proposalCache.set(key, { data: parsed, at: Date.now() })
  return parsed
}
