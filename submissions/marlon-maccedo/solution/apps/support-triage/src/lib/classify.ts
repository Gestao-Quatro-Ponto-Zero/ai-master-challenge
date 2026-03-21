import type { ClassifyResult, ItCategory } from '@/types'
import { getOpenRouterApiKey } from '@/lib/env'

const CATEGORIES: ItCategory[] = [
  'Hardware', 'HR Support', 'Access', 'Storage',
  'Purchase', 'Internal Project', 'Administrative rights', 'Miscellaneous',
]

export async function classifyTicket(text: string): Promise<ClassifyResult | null> {
  const apiKey = getOpenRouterApiKey()
  if (!apiKey) return null

  const prompt = `Você é um classificador de tickets de suporte de TI corporativo.
Classifique o ticket abaixo em UMA das categorias: ${CATEGORIES.join(' | ')}

Responda APENAS com JSON válido, sem texto extra:
{
  "category": "<categoria>",
  "confidence": <0.0 a 1.0>,
  "reasoning": "<uma frase curta explicando a classificação>",
  "suggestedPriority": "Low|Medium|High|Critical",
  "shouldAutomate": <true|false>,
  "automationReasoning": "<por que pode ou não ser automatizado>"
}

Ticket:
${text.slice(0, 1000)}`

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
      max_tokens: 300,
      messages: [{ role: 'user', content: prompt }],
    }),
  })

  if (!res.ok) {
    const body = await res.text()
    throw new Error(`OpenRouter error ${res.status}: ${body}`)
  }

  const data = await res.json()
  const raw = data.choices?.[0]?.message?.content?.trim()
  if (!raw) throw new Error('Resposta vazia da API')

  const cleaned = raw.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/, '').trim()
  const json = JSON.parse(cleaned)
  return {
    category:            json.category,
    confidence:          Number(json.confidence),
    reasoning:           json.reasoning,
    suggestedPriority:   json.suggestedPriority,
    shouldAutomate:      Boolean(json.shouldAutomate),
    automationReasoning: json.automationReasoning,
    mode:                'ai',
  }
}
