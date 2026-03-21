import type { ChurnOverview, SegmentBreakdown, SupportComparison, ChurnReason, FeatureComparison } from '@/types'

export interface ChurnInsightsPayload {
  overview: ChurnOverview
  topIndustries: SegmentBreakdown[]
  topChannels: SegmentBreakdown[]
  topPlans: SegmentBreakdown[]
  supportAnalysis: SupportComparison
  topReasons: ChurnReason[]
  atRiskCount: number
}

export interface DiagnosticInsightsPayload {
  overview: ChurnOverview
  topFeatures: FeatureComparison[]   // sorted by |delta|
  supportAnalysis: SupportComparison
  topReasons: ChurnReason[]
  topIndustries: SegmentBreakdown[]
}

// ── Cache ─────────────────────────────────────────────────────────────────────

const TTL_MS = 24 * 60 * 60 * 1000

const insightsCache = new Map<string, { data: string[] | null; at: number }>()
const recoCache     = new Map<string, { data: RecommendationsOutput | null; at: number }>()
const diagCache     = new Map<string, { data: string[] | null; at: number }>()

const RECO_VERSION = 'v2'

function overviewKey(o: ChurnOverview): string {
  return `${o.churnRate}|${o.mrrChurned}|${o.totalAccounts}`
}

// ── Overview insights ─────────────────────────────────────────────────────────

/** Returns 4 AI-generated insights or null when no API key. */
export async function generateInsights(payload: ChurnInsightsPayload): Promise<string[] | null> {
  const key = overviewKey(payload.overview) + '|' + payload.topIndustries[0]?.segment
  const apiKey = process.env.OPENROUTER_API_KEY
  const hit = insightsCache.get(key)
  if (hit && Date.now() - hit.at < TTL_MS) {
    if (hit.data !== null) return hit.data
    // Não reutilizar cache de "sem resultado" se a chave foi configurada depois (evita 24h de banner falso)
    if (!apiKey) return null
  }

  if (!apiKey) {
    return null
  }

  const dataSummary = JSON.stringify({
    churnRate:                  payload.overview.churnRate,
    totalAccounts:              payload.overview.totalAccounts,
    churnedAccounts:            payload.overview.churnedAccounts,
    mrrChurned:                 payload.overview.mrrChurned,
    mrrRetained:                payload.overview.mrrRetained,
    avgMrrChurned:              payload.overview.avgMrrChurned,
    avgMrrRetained:             payload.overview.avgMrrRetained,
    topChurnIndustry:           payload.topIndustries[0],
    topChurnChannel:            payload.topChannels[0],
    topChurnPlan:               payload.topPlans[0],
    supportTicketsChurned:      payload.supportAnalysis.avgTicketsChurned,
    supportTicketsRetained:     payload.supportAnalysis.avgTicketsRetained,
    escalationRateChurned:      payload.supportAnalysis.escalationRateChurned,
    escalationRateRetained:     payload.supportAnalysis.escalationRateRetained,
    topChurnReason:             payload.topReasons[0]?.reasonCode,
    topChurnReasonPct:          payload.topReasons[0]?.pct,
    atRiskRetainedAccounts:     payload.atRiskCount,
  })

  const prompt = `Você é um analista de negócios SaaS. Analise os dados de churn abaixo e gere exatamente 4 achados relevantes para o CEO.

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

// ── Diagnostic insights ───────────────────────────────────────────────────────

/** Returns 3 AI-generated diagnostic findings or null when no API key. */
export async function generateDiagnosticInsights(payload: DiagnosticInsightsPayload): Promise<string[] | null> {
  const key = `diag|${overviewKey(payload.overview)}|${payload.topFeatures[0]?.feature}`
  const apiKey = process.env.OPENROUTER_API_KEY
  const hit = diagCache.get(key)
  if (hit && Date.now() - hit.at < TTL_MS) {
    if (hit.data !== null) return hit.data
    if (!apiKey) return null
  }

  if (!apiKey) {
    return null
  }

  const dataSummary = JSON.stringify({
    churnRate:                   payload.overview.churnRate,
    topFeaturesByDelta:          payload.topFeatures.slice(0, 5),
    supportAvgTicketsChurned:    payload.supportAnalysis.avgTicketsChurned,
    supportAvgTicketsRetained:   payload.supportAnalysis.avgTicketsRetained,
    supportResolutionChurned:    payload.supportAnalysis.avgResolutionHoursChurned,
    supportResolutionRetained:   payload.supportAnalysis.avgResolutionHoursRetained,
    escalationRateChurned:       payload.supportAnalysis.escalationRateChurned,
    escalationRateRetained:      payload.supportAnalysis.escalationRateRetained,
    topChurnReasons:             payload.topReasons.slice(0, 3),
    topChurnIndustry:            payload.topIndustries[0],
  })

  const prompt = `Você é um analista de dados SaaS. Com base nos dados abaixo, gere exatamente 3 achados sobre as CAUSAS RAIZ do churn.

Regras:
- Use APENAS os números presentes nos dados
- Mostre contrastes entre churned vs retidos quando relevante
- Destaque padrões de uso de features e suporte
- Responda APENAS com um array JSON de 3 strings, sem texto extra

Dados:
${dataSummary}`

  const result = await callOpenRouter(prompt, 500)
  diagCache.set(key, { data: result, at: Date.now() })
  return result
}

// ── Recommendations ───────────────────────────────────────────────────────────

export interface RecommendationItem {
  priority: number
  segment: string
  action: string
  mrrImpact: string
  effort: 'baixo' | 'médio' | 'alto'
}

export interface RecommendationsOutput {
  actions: RecommendationItem[]
  notToDo: string[]
}

/** Returns AI-generated recommendations or null when no API key. */
export async function generateRecommendations(payload: ChurnInsightsPayload): Promise<RecommendationsOutput | null> {
  const key = `reco|${RECO_VERSION}|${overviewKey(payload.overview)}|${payload.topChannels[0]?.segment}`
  const apiKey = process.env.OPENROUTER_API_KEY
  const hit = recoCache.get(key)
  if (hit && Date.now() - hit.at < TTL_MS) {
    if (hit.data !== null) return hit.data
    if (!apiKey) return null
  }

  if (!apiKey) {
    return null
  }

  const dataSummary = JSON.stringify({
    churnRate:          payload.overview.churnRate,
    mrrChurned:         payload.overview.mrrChurned,
    worstIndustry:      payload.topIndustries[0],
    worstChannel:       payload.topChannels[0],
    worstPlan:          payload.topPlans[0],
    topChurnReason:     payload.topReasons[0],
    escalationChurned:  payload.supportAnalysis.escalationRateChurned,
    escalationRetained: payload.supportAnalysis.escalationRateRetained,
    atRiskAccounts:     payload.atRiskCount,
    mrrRetained:        payload.overview.mrrRetained,
  })

  const prompt = `Você é um consultor de retenção SaaS. Com base nos dados reais de churn abaixo, gere:
- 5 ações concretas de retenção priorizadas por impacto (priority 1 = maior impacto)
- 3 armadilhas a evitar ("o que NÃO fazer")

Responda APENAS com JSON válido, sem texto extra:
{"actions":[{"priority":1,"segment":"...","action":"...","mrrImpact":"...","effort":"baixo|médio|alto"}],"notToDo":["...","...","..."]}

Mantenha cada campo curto (máx 20 palavras). Use os números dos dados para justificar. Dados:
${dataSummary}`

  try {
    const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://github.com/marlon-maccedo/ai-master-challenge',
        'X-Title': 'Churn Dashboard - AI Master Challenge',
      },
      body: JSON.stringify({
        model: 'anthropic/claude-haiku-4-5',
        max_tokens: 1200,
        messages: [{ role: 'user', content: prompt }],
      }),
    })

    if (!res.ok) {
      console.error('[churn-reco] OpenRouter error', res.status)
      recoCache.set(key, { data: null, at: Date.now() })
      return null
    }

    const response = await res.json()
    const raw = response.choices?.[0]?.message?.content?.trim()
    if (!raw) { recoCache.set(key, { data: null, at: Date.now() }); return null }

    const cleaned = raw.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/, '').trim()
    const parsed = JSON.parse(cleaned) as RecommendationsOutput

    if (parsed.actions?.length && parsed.notToDo?.length) {
      recoCache.set(key, { data: parsed, at: Date.now() })
      return parsed
    }

    recoCache.set(key, { data: null, at: Date.now() })
    return null
  } catch (err) {
    console.error('[churn-reco] failed', err)
    recoCache.set(key, { data: null, at: Date.now() })
    return null
  }
}

// ── Shared OpenRouter helper ──────────────────────────────────────────────────

async function callOpenRouter(prompt: string, maxTokens: number): Promise<string[] | null> {
  const apiKey = process.env.OPENROUTER_API_KEY
  if (!apiKey) return null

  try {
    const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://github.com/marlon-maccedo/ai-master-challenge',
        'X-Title': 'Churn Dashboard - AI Master Challenge',
      },
      body: JSON.stringify({
        model: 'anthropic/claude-haiku-4-5',
        max_tokens: maxTokens,
        messages: [{ role: 'user', content: prompt }],
      }),
    })

    if (!res.ok) {
      console.error('[churn-insights] OpenRouter error', res.status)
      return null
    }

    const data = await res.json()
    const raw  = data.choices?.[0]?.message?.content?.trim()
    if (!raw) return null

    const cleaned = raw.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/, '').trim()
    const parsed  = JSON.parse(cleaned)
    return Array.isArray(parsed) && parsed.length > 0 ? (parsed as string[]) : null
  } catch (err) {
    console.error('[churn-insights] failed', err)
    return null
  }
}
