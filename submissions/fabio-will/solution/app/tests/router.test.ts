import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'
import meta from '../src/data/model-meta.json'
import { Router, ngrams, segmentWindows, tokenize, type RouterModel } from '../src/lib/router'

const root = join(__dirname, '..')
const model = JSON.parse(readFileSync(join(root, 'public', meta.file), 'utf8')) as RouterModel
const fixtures = JSON.parse(readFileSync(join(root, 'tests/fixtures/parity.json'), 'utf8')) as { text: string; proba: number[]; segment: number; coherence: number }[]
const router = new Router(model)

describe('tokenizer', () => {
  it('matches scikit-learn token_pattern (2+ word chars, lowercase)', () => {
    expect(tokenize('Reset my VPN-password, a b ok!')).toEqual(['reset', 'my', 'vpn', 'password', 'ok'])
  })

  it('builds unigrams then bigrams', () => {
    expect(ngrams(['a1', 'b2', 'c3'], [1, 2])).toEqual(['a1', 'b2', 'c3', 'a1 b2', 'b2 c3'])
  })
})

describe('parity with the Python router', () => {
  it('reproduces the exported probabilities on 300 test tickets', () => {
    let maxDiff = 0
    let argmaxAgreement = 0
    for (const { text, proba } of fixtures) {
      const js = router.predictProba(text)
      js.forEach((p, i) => (maxDiff = Math.max(maxDiff, Math.abs(p - (proba[i] ?? 0)))))
      const a = js.indexOf(Math.max(...js))
      const b = proba.indexOf(Math.max(...proba))
      if (a === b) argmaxAgreement++
    }
    expect(argmaxAgreement).toBe(fixtures.length)
    expect(maxDiff).toBeLessThan(1e-3)
  })

  it('reproduces the padding and word-order guard signals', () => {
    let segDiff = 0
    let cohDiff = 0
    for (const { text, segment, coherence } of fixtures) {
      segDiff = Math.max(segDiff, Math.abs(router.segmentSensitivity(text) - segment))
      cohDiff = Math.max(cohDiff, Math.abs(router.coherence(text) - coherence))
    }
    expect(segDiff).toBeLessThan(1e-3)
    expect(cohDiff).toBeLessThan(1e-6)
  })

  it('windows overlap by half and always cover the tail', () => {
    const words = Array.from({ length: 11 }, (_, i) => `w${i}`)
    const w = segmentWindows(words.join(' '), 8)
    expect(w[0]).toBe(words.slice(0, 8).join(' '))
    expect(w.at(-1)?.split(' ').at(-1)).toBe('w10')
    expect(segmentWindows('short ticket', 8)).toEqual(['short ticket'])
  })
})

describe('routing policy', () => {
  it('sends text outside the known vocabulary to a human', () => {
    const d = router.decide('não consigo acessar minha conta, a senha expirou e o reset não chega')
    expect(d.tier).toBe('human')
    expect(d.reason).toBe('vocabulario_desconhecido')
  })

  it('never auto-routes a privileged access request', () => {
    const d = router.decide('please grant local administrator rights on my laptop to install the analysis software admin access request')
    if (d.queue === 'Administrative rights') expect(d.tier).not.toBe('auto')
  })

  it('blocks the padding attack found in the pentest', () => {
    const hr = 'question about my holiday allowance and remaining sick leave days this year'
    const padded = `${hr} laptop screen printer keyboard monitor`
    const interleaved = hr
      .split(' ')
      .map((w, i) => `${w} ${['laptop', 'screen', 'printer', 'keyboard', 'monitor'][i % 5]}`)
      .join(' ')
    for (const text of [padded, interleaved]) {
      const d = router.decide(text)
      expect(d.tier === 'auto' && d.queue !== 'HR Support').toBe(false)
    }
    expect(router.decide(interleaved).reason).toBe('sequencia_incomum')
  })

  it('returns a full decision for an empty ticket without throwing', () => {
    const d = router.decide('')
    expect(d.tier).toBe('human')
    expect(d.coverage).toBe(0)
  })

  it('explains a decision with terms that pushed the chosen queue up', () => {
    const d = router.decide('laptop screen broken keyboard not working need replacement hardware')
    expect(d.why.length).toBeGreaterThan(0)
    expect(d.why.every((w) => w.weight > 0)).toBe(true)
  })
})
