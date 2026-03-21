import type { SocialOverview, PlatformEngagement, SponsorComparison } from '@/types'

export interface SocialInsightsPayload {
  overview: SocialOverview
  topPlatform: PlatformEngagement
  sponsorship: SponsorComparison
  bestCreatorTier: string
}

export interface StrategyRecommendation {
  priority: number
  platform: string
  action: string
  kpiImpact: string
  effort: 'baixo' | 'médio' | 'alto'
}

export interface StrategyOutput {
  recommendations: StrategyRecommendation[]
  notToDo: string[]
}

// ── Cache ─────────────────────────────────────────────────────────────────────

const TTL_MS = 24 * 60 * 60 * 1000

const insightsCache = new Map<string, { data: string[] | null; at: number }>()
const strategyCache = new Map<string, { data: StrategyOutput | null; at: number }>()

const STRATEGY_VERSION = 'v1'

function overviewKey(o: SocialOverview): string {
  return `${o.totalPosts}|${o.avgEngagementRate}`
}

// ── OpenRouter helper ─────────────────────────────────────────────────────────

async function callOpenRouter(prompt: string, maxTokens: number): Promise<string[] | null> {
  const apiKey = process.env.OPENROUTER_API_KEY
  if (!apiKey) return null

  try {
    const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://github.com/bubex/ai-master-challenge',
        'X-Title': 'Social Dashboard - AI Master Challenge',
      },
      body: JSON.stringify({
        model: 'anthropic/claude-haiku-4-5',
        max_tokens: maxTokens,
        messages: [{ role: 'user', content: prompt }],
      }),
    })

    if (!res.ok) {
      console.error('[social-insights] OpenRouter error', res.status)
      return null
    }

    const data = await res.json()
    const raw  = data.choices?.[0]?.message?.content?.trim()
    if (!raw) return null

    const cleaned = raw.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/, '').trim()
    const parsed  = JSON.parse(cleaned)
    return Array.isArray(parsed) && parsed.length > 0 ? (parsed as string[]) : null
  } catch (err) {
    console.error('[social-insights] failed', err)
    return null
  }
}

// ── Overview insights ─────────────────────────────────────────────────────────

/** Returns 4 AI-generated insights or null when no API key. */
export async function generateOverviewInsights(payload: SocialInsightsPayload): Promise<string[] | null> {
  const key = overviewKey(payload.overview) + '|' + payload.topPlatform.platform
  const hit = insightsCache.get(key)
  if (hit && Date.now() - hit.at < TTL_MS) return hit.data

  const apiKey = process.env.OPENROUTER_API_KEY
  if (!apiKey) {
    insightsCache.set(key, { data: null, at: Date.now() })
    return null
  }

  const dataSummary = JSON.stringify({
    totalPosts:              payload.overview.totalPosts,
    totalViews:              payload.overview.totalViews,
    avgEngagementRatePct:    payload.overview.avgEngagementRate,
    sponsoredCount:          payload.overview.sponsoredCount,
    organicCount:            payload.overview.organicCount,
    sponsoredPct:            Math.round(payload.overview.sponsoredCount / payload.overview.totalPosts * 100),
    topPlatform:             payload.topPlatform.platform,
    topPlatformEngagement:   payload.topPlatform.avgEngagementRate,
    sponsoredEngagement:     payload.sponsorship.avgEngagementSponsored,
    organicEngagement:       payload.sponsorship.avgEngagementOrganic,
    bestCreatorTier:         payload.bestCreatorTier,
  })

  const prompt = `Você é um analista de social media. Analise os dados abaixo e gere exatamente 4 achados relevantes para um gerente de marketing.

Regras:
- Cada achado deve ser uma frase objetiva com os números reais dos dados
- Destaque o que é crítico, surpreendente ou acionável
- Não repita os mesmos números em achados diferentes
- Responda APENAS com um array JSON de 4 strings, sem texto extra

Dados:
${dataSummary}`

  const result = await callOpenRouter(prompt, 600)
  insightsCache.set(key, { data: result, at: Date.now() })
  return result
}

// ── Strategy recommendations ──────────────────────────────────────────────────

/** Returns AI-generated strategy or null when no API key. */
export async function generateStrategyRecommendations(payload: SocialInsightsPayload): Promise<StrategyOutput | null> {
  const key = `strat|${STRATEGY_VERSION}|${overviewKey(payload.overview)}|${payload.topPlatform.platform}`
  const hit = strategyCache.get(key)
  if (hit && Date.now() - hit.at < TTL_MS) return hit.data

  const apiKey = process.env.OPENROUTER_API_KEY
  if (!apiKey) {
    strategyCache.set(key, { data: null, at: Date.now() })
    return null
  }

  const dataSummary = JSON.stringify({
    totalPosts:            payload.overview.totalPosts,
    avgEngagementRatePct:  payload.overview.avgEngagementRate,
    sponsoredPct:          Math.round(payload.overview.sponsoredCount / payload.overview.totalPosts * 100),
    topPlatform:           payload.topPlatform.platform,
    topPlatformEngagement: payload.topPlatform.avgEngagementRate,
    sponsoredEngagement:   payload.sponsorship.avgEngagementSponsored,
    organicEngagement:     payload.sponsorship.avgEngagementOrganic,
    bestCreatorTier:       payload.bestCreatorTier,
  })

  const prompt = `Você é um estrategista de social media. Com base nos dados reais abaixo, gere:
- 5 recomendações concretas priorizadas por impacto (priority 1 = maior impacto)
- 3 armadilhas a evitar ("o que NÃO fazer")

Responda APENAS com JSON válido, sem texto extra:
{"recommendations":[{"priority":1,"platform":"...","action":"...","kpiImpact":"...","effort":"baixo|médio|alto"}],"notToDo":["...","...","..."]}

Mantenha cada campo curto (máx 20 palavras). Use os números dos dados para justificar. Dados:
${dataSummary}`

  try {
    const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://github.com/bubex/ai-master-challenge',
        'X-Title': 'Social Dashboard - AI Master Challenge',
      },
      body: JSON.stringify({
        model: 'anthropic/claude-haiku-4-5',
        max_tokens: 1200,
        messages: [{ role: 'user', content: prompt }],
      }),
    })

    if (!res.ok) {
      console.error('[social-strategy] OpenRouter error', res.status)
      strategyCache.set(key, { data: null, at: Date.now() })
      return null
    }

    const response = await res.json()
    const raw = response.choices?.[0]?.message?.content?.trim()
    if (!raw) { strategyCache.set(key, { data: null, at: Date.now() }); return null }

    const cleaned = raw.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/, '').trim()
    const parsed = JSON.parse(cleaned) as StrategyOutput

    if (parsed.recommendations?.length && parsed.notToDo?.length) {
      strategyCache.set(key, { data: parsed, at: Date.now() })
      return parsed
    }

    strategyCache.set(key, { data: null, at: Date.now() })
    return null
  } catch (err) {
    console.error('[social-strategy] failed', err)
    strategyCache.set(key, { data: null, at: Date.now() })
    return null
  }
}
