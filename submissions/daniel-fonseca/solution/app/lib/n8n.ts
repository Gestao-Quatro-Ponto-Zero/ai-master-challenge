import "server-only"

import { env } from "@/lib/env"

export class N8nUnavailable extends Error {}

/**
 * Chama um webhook do n8n com o X-Webhook-Secret (o segredo nunca sai do servidor).
 * Lança N8nUnavailable em timeout, erro de rede ou 5xx — o chamador decide o modo offline (PRD §4.4).
 */
export async function callN8n<T>(path: "triage" | "hitl-decision", body: unknown, timeoutMs = 30_000): Promise<{ status: number; data: T }> {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), timeoutMs)
  try {
    const res = await fetch(`${env.n8nBaseUrl()}/webhook/g4-support/${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Webhook-Secret": env.n8nWebhookSecret() },
      body: JSON.stringify(body),
      signal: ctrl.signal,
      cache: "no-store",
    })
    if (res.status >= 500) throw new N8nUnavailable(`n8n respondeu ${res.status}`)
    const data = (await res.json().catch(() => ({}))) as T
    return { status: res.status, data }
  } catch (err) {
    if (err instanceof N8nUnavailable) throw err
    throw new N8nUnavailable(err instanceof Error ? err.message : "falha ao chamar o n8n")
  } finally {
    clearTimeout(timer)
  }
}
