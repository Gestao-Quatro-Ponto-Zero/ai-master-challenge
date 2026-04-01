import { supabase } from './supabase'

// URL da API — aponta para o domínio público da API no EasyPanel
export const API_BASE = 'https://caseg4-api.t3xbnj.easypanel.host'

async function getToken(): Promise<string> {
  const { data } = await supabase.auth.getSession()
  return data.session?.access_token || ''
}

async function apiFetch(path: string, options: RequestInit = {}) {
  const token = await getToken()
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Erro na API')
  }
  return res.json()
}

export const api = {
  init: () => apiFetch('/api/init'),

  getDealExplanation: (dealId: number) =>
    apiFetch(`/api/deals/${dealId}/explain`),

  getDealAIAnalysis: (dealId: number) =>
    apiFetch(`/api/deals/${dealId}/ai-analysis`, { method: 'POST' }),

  createDeal: (data: {
    sales_agent_id: number
    product_id: number
    account_id: number
    deal_stage: string
    engage_date?: string
  }) =>
    apiFetch('/api/deals', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  classifyDeal: (dealId: number, deal_stage: string, close_value: number = 0) =>
    apiFetch(`/api/deals/${dealId}/classify`, {
      method: 'PATCH',
      body: JSON.stringify({ deal_stage, close_value }),
    }),

  getOptions: () => apiFetch('/api/options'),

  chat: (messages: { role: string; content: string }[]) =>
    apiFetch('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ messages }),
    }),
}
