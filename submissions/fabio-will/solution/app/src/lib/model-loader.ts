import meta from '@/data/model-meta.json'
import { Router, type RouterModel } from './router'

export const MODEL_URL = meta.file
export const MODEL_BYTES = meta.bytes

export class ModelIntegrityError extends Error {}

const toHex = (buf: ArrayBuffer): string => Array.from(new Uint8Array(buf), (b) => b.toString(16).padStart(2, '0')).join('')

const isNumberArray = (v: unknown, len?: number): v is number[] =>
  Array.isArray(v) && (len === undefined || v.length === len) && v.every((x) => typeof x === 'number' && Number.isFinite(x))

/** Structural check so a malformed or hostile file fails loudly instead of producing silent nonsense. */
export function assertRouterModel(m: unknown): asserts m is RouterModel {
  const r = m as Partial<RouterModel> | null
  const ok =
    !!r &&
    r.version === 1 &&
    Array.isArray(r.classes) &&
    r.classes.length > 1 &&
    r.classes.every((c) => typeof c === 'string') &&
    Array.isArray(r.terms) &&
    r.terms.every((t) => typeof t === 'string') &&
    isNumberArray(r.idf, r.terms.length) &&
    Array.isArray(r.coef) &&
    r.coef.length === r.classes.length &&
    r.coef.every((row) => isNumberArray(row, r.terms!.length)) &&
    isNumberArray(r.intercept, r.classes.length) &&
    !!r.policy &&
    [r.policy.t_auto, r.policy.t_assist, r.policy.vocab_floor, r.policy.coherence_floor, r.policy.sensitive_mass, r.policy.segment_sensitive].every(
      (x) => typeof x === 'number' && x >= 0 && x <= 1,
    ) &&
    Number.isInteger(r.policy.segment_words) &&
    r.policy.segment_words >= 2
  if (!ok) throw new ModelIntegrityError('router model failed structural validation')
}

/** Fetches the model once per page session, verifies its SHA-256 against the build pin, then validates its shape. */
export async function fetchRouter(url = MODEL_URL, expectedSha256 = meta.sha256): Promise<Router> {
  const res = await fetch(url, { credentials: 'omit' })
  if (!res.ok) throw new Error(`model fetch failed: HTTP ${res.status}`)
  const bytes = await res.arrayBuffer()
  if (!globalThis.crypto?.subtle) throw new ModelIntegrityError('WebCrypto unavailable: refusing an unverified model')
  const digest = toHex(await crypto.subtle.digest('SHA-256', bytes))
  if (digest !== expectedSha256) throw new ModelIntegrityError(`model hash mismatch: ${digest}`)
  const model: unknown = JSON.parse(new TextDecoder().decode(bytes))
  assertRouterModel(model)
  return new Router(model)
}

let pending: Promise<Router> | null = null

/** Shared across client navigations: going back to the tester does not download or parse the model again. */
export function loadRouter(): Promise<Router> {
  pending ??= fetchRouter().catch((e: unknown) => {
    pending = null
    throw e
  })
  return pending
}
