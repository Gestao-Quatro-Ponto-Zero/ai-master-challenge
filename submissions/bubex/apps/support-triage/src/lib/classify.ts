import Anthropic from '@anthropic-ai/sdk'
import type { ClassifyResult, ItCategory } from '@/types'

const CATEGORIES: ItCategory[] = [
  'Hardware', 'HR Support', 'Access', 'Storage',
  'Purchase', 'Internal Project', 'Administrative rights', 'Miscellaneous',
]

// Keyword fallback — triggers when no API key is set
const KEYWORD_MAP: Record<ItCategory, string[]> = {
  Hardware:                 ['laptop', 'computer', 'keyboard', 'mouse', 'monitor', 'printer', 'screen', 'device', 'hardware', 'cable'],
  'HR Support':             ['leave', 'holiday', 'vacation', 'payroll', 'salary', 'onboarding', 'offboarding', 'employee', 'hr', 'hiring', 'benefit'],
  Access:                   ['access', 'login', 'password', 'account', 'permission', 'locked', 'reset', 'credential', 'authentication', 'vpn'],
  Storage:                  ['storage', 'disk', 'drive', 'space', 'quota', 'backup', 'file', 'folder', 'cloud', 'sync'],
  Purchase:                 ['purchase', 'order', 'procurement', 'buy', 'invoice', 'vendor', 'software license', 'license', 'request'],
  'Internal Project':       ['project', 'deadline', 'sprint', 'milestone', 'task', 'jira', 'trello', 'meeting', 'requirements'],
  'Administrative rights':  ['admin', 'administrator', 'rights', 'privilege', 'sudo', 'elevated', 'policy', 'group policy'],
  Miscellaneous:            [],
}

function keywordFallback(text: string): ClassifyResult {
  const lower = text.toLowerCase()
  let best: ItCategory = 'Miscellaneous'
  let bestScore = 0

  for (const [cat, keywords] of Object.entries(KEYWORD_MAP) as [ItCategory, string[]][]) {
    if (cat === 'Miscellaneous') continue
    const score = keywords.filter(k => lower.includes(k)).length
    if (score > bestScore) { bestScore = score; best = cat }
  }

  const confidence = bestScore === 0 ? 0.3 : Math.min(0.6, 0.3 + bestScore * 0.1)

  return {
    category: best,
    confidence,
    reasoning: bestScore === 0
      ? 'Nenhum termo-chave reconhecido — classificado como Miscellaneous.'
      : `Palavras-chave reconhecidas para "${best}".`,
    suggestedPriority: 'Medium',
    shouldAutomate: ['Access', 'Storage', 'Purchase'].includes(best),
    automationReasoning: ['Access', 'Storage', 'Purchase'].includes(best)
      ? 'Categoria com critérios objetivos e alto volume — bom candidato à automação.'
      : 'Categoria requer julgamento humano ou contexto adicional.',
    mode: 'fallback',
  }
}

export async function classifyTicket(text: string): Promise<ClassifyResult> {
  const apiKey = process.env.ANTHROPIC_API_KEY
  if (!apiKey) return keywordFallback(text)

  const client = new Anthropic({ apiKey })

  try {
    const message = await client.messages.create({
      model: 'claude-haiku-4-5-20251001',
      max_tokens: 300,
      messages: [{
        role: 'user',
        content: `Você é um classificador de tickets de suporte de TI corporativo.
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
${text.slice(0, 1000)}`,
      }],
    })

    const raw = (message.content[0] as { type: string; text: string }).text.trim()
    const json = JSON.parse(raw)

    return {
      category:            json.category,
      confidence:          Number(json.confidence),
      reasoning:           json.reasoning,
      suggestedPriority:   json.suggestedPriority,
      shouldAutomate:      Boolean(json.shouldAutomate),
      automationReasoning: json.automationReasoning,
      mode:                'ai',
    }
  } catch {
    return keywordFallback(text)
  }
}
