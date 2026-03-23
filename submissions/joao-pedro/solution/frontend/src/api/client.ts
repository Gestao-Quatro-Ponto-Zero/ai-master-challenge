export const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8001'

export async function apiFetch<T>(path: string, params?: Record<string, unknown>): Promise<T> {
  const url = new URL(`${API_BASE}${path}`)

  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null && value !== '') {
        url.searchParams.set(key, String(value))
      }
    }
  }

  const res = await fetch(url.toString())
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${await res.text()}`)
  }
  return res.json() as Promise<T>
}
