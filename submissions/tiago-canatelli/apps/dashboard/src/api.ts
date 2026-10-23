export const API_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000'

export type Row = Record<string, unknown>

export function getToken(): string {
  try { return localStorage.getItem('token') ?? '' } catch { return '' }
}
export function setToken(t: string | null) {
  try { if (t) localStorage.setItem('token', t); else localStorage.removeItem('token') } catch { /* sem storage */ }
}
const authHeader = (): Record<string, string> => (getToken() ? { authorization: `Bearer ${getToken()}` } : {})

export async function getData<T = Row>(view: string, params: Record<string, string> = {}): Promise<T[]> {
  const qs = new URLSearchParams(params).toString()
  const res = await fetch(`${API_URL}/data/${view}${qs ? `?${qs}` : ''}`, { headers: authHeader() })
  if (res.status === 401) { setToken(null); window.location.reload() }
  if (!res.ok) throw new Error(`Falha ao ler ${view} (${res.status})`)
  return res.json() as Promise<T[]>
}

function accessHeaders(): Record<string, string> {
  return { 'content-type': 'application/json', ...authHeader() }
}

export type User = { email: string; name: string; role: string; label: string; profile_slug: string | null; tabs: string[]; can_edit: boolean }

export async function me(): Promise<User | null> {
  if (!getToken()) return null
  const res = await fetch(`${API_URL}/me`, { headers: authHeader() })
  if (!res.ok) { setToken(null); return null }
  return res.json() as Promise<User>
}

export async function post<T>(path: string, body: unknown, method = 'POST'): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { method, headers: accessHeaders(), body: JSON.stringify(body) })
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}))
    throw new Error((detail as { detail?: string }).detail ?? `Erro ${res.status}`)
  }
  return res.json() as Promise<T>
}

export const usd = (v: unknown) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(Number(v ?? 0))
export const num = (v: unknown, d = 0) =>
  new Intl.NumberFormat('pt-BR', { maximumFractionDigits: d, minimumFractionDigits: d }).format(Number(v ?? 0))
export const pct = (v: unknown, d = 1) => `${num(v, d)}%`
