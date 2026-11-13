import { createHash } from 'node:crypto'
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { afterEach, describe, expect, it, vi } from 'vitest'
import meta from '../src/data/model-meta.json'
import { ModelIntegrityError, assertRouterModel, fetchRouter } from '../src/lib/model-loader'

const bytes = readFileSync(join(__dirname, '..', 'public', meta.file))
const sha = (b: Uint8Array | string) => createHash('sha256').update(b).digest('hex')
const serve = (body: BodyInit, status = 200) => vi.stubGlobal('fetch', vi.fn(async () => new Response(body, { status })))

afterEach(() => vi.unstubAllGlobals())

describe('model integrity pin', () => {
  it('the pinned hash matches the shipped model', () => {
    expect(sha(bytes)).toBe(meta.sha256)
    expect(bytes.length).toBe(meta.bytes)
  })

  it('loads and routes with the genuine file', async () => {
    serve(bytes)
    const router = await fetchRouter()
    expect(router.decide('laptop screen broken need replacement').queue).toBe('Hardware')
  })

  it('refuses a model with a single byte changed', async () => {
    const tampered = Buffer.from(bytes)
    tampered[tampered.length - 3] = tampered[tampered.length - 3]! ^ 1
    serve(tampered)
    await expect(fetchRouter()).rejects.toBeInstanceOf(ModelIntegrityError)
  })

  it('refuses a policy rewritten to automate everything', async () => {
    const hostile = JSON.stringify({ ...JSON.parse(bytes.toString('utf8')), policy: { t_auto: 0, t_assist: 0, vocab_floor: 0, coherence_floor: 0, sensitive_mass: 1, segment_words: 8, segment_sensitive: 1, never_auto: [], sensitive: [] } })
    serve(hostile)
    await expect(fetchRouter()).rejects.toBeInstanceOf(ModelIntegrityError)
  })

  it('reports a network failure as a plain error, not as tampering', async () => {
    serve('nope', 503)
    await expect(fetchRouter()).rejects.not.toBeInstanceOf(ModelIntegrityError)
  })
})

describe('structural validation', () => {
  it('rejects malformed shapes even when the hash would be accepted', () => {
    const base = JSON.parse(bytes.toString('utf8'))
    expect(() => assertRouterModel(null)).toThrow(ModelIntegrityError)
    expect(() => assertRouterModel({ ...base, coef: [[1]] })).toThrow(ModelIntegrityError)
    expect(() => assertRouterModel({ ...base, idf: base.idf.slice(1) })).toThrow(ModelIntegrityError)
    expect(() => assertRouterModel({ ...base, policy: { ...base.policy, t_auto: 7 } })).toThrow(ModelIntegrityError)
    expect(() => assertRouterModel({ ...base, intercept: base.intercept.map(() => Number.NaN) })).toThrow(ModelIntegrityError)
    expect(() => assertRouterModel(base)).not.toThrow()
  })

  it('a valid hash on a malformed file still fails', async () => {
    const malformed = JSON.stringify({ version: 1, classes: ['a'] })
    serve(malformed)
    await expect(fetchRouter(meta.file, sha(malformed))).rejects.toBeInstanceOf(ModelIntegrityError)
  })
})
