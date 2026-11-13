/**
 * Browser port of the ticket router trained in analysis/ (scikit-learn TfidfVectorizer +
 * multinomial LogisticRegression). Mirrors scikit-learn step by step so the probabilities match:
 * lowercase → token_pattern (?u)\b\w\w+\b → word 1-2 grams → sublinear tf → idf → L2 norm → softmax.
 * The parity test in tests/router.test.ts checks this against probabilities exported from Python.
 */

export type Tier = 'auto' | 'assist' | 'human'

export type Reason =
  | 'confianca_alta'
  | 'confianca_media'
  | 'confianca_baixa'
  | 'fila_privilegiada'
  | 'possivel_conteudo_sensivel'
  | 'sem_historico_parecido'
  | 'vocabulario_desconhecido'
  | 'trecho_sensivel'
  | 'sequencia_incomum'

export interface RouterModel {
  version: number
  classes: string[]
  terms: string[]
  idf: number[]
  coef: number[][]
  intercept: number[]
  ngram: [number, number]
  sublinear_tf: boolean
  policy: {
    t_auto: number
    t_assist: number
    vocab_floor: number
    coherence_floor: number
    sensitive_mass: number
    segment_words: number
    segment_sensitive: number
    never_auto: string[]
    sensitive: string[]
  }
}

export interface Decision {
  queue: string
  confidence: number
  top: { queue: string; p: number }[]
  tier: Tier
  reason: Reason
  coverage: number
  coherence: number
  segment: number
  why: { term: string; weight: number }[]
}

const TOKEN = /[\p{L}\p{N}_]{2,}/gu

export function tokenize(text: string): string[] {
  return text.toLowerCase().match(TOKEN) ?? []
}

export function ngrams(tokens: string[], [lo, hi]: [number, number]): string[] {
  const out: string[] = []
  for (let n = lo; n <= hi; n++) {
    for (let i = 0; i + n <= tokens.length; i++) out.push(tokens.slice(i, i + n).join(' '))
  }
  return out
}

/** Overlapping word windows, stride half a window; short text is one window. Mirrors segment_windows() in analysis/router.py. */
export function segmentWindows(text: string, words: number): string[] {
  const tokens = text.trim().split(/\s+/).filter(Boolean)
  if (tokens.length <= words) return [text]
  const step = Math.max(1, Math.floor(words / 2))
  const out: string[] = []
  for (let i = 0; i < tokens.length - words + step; i += step) out.push(tokens.slice(i, i + words).join(' '))
  return out
}

export class Router {
  private readonly index: Map<string, number>

  constructor(private readonly model: RouterModel) {
    this.index = new Map(model.terms.map((t, i) => [t, i]))
  }

  get policy() {
    return this.model.policy
  }

  /** Sparse L2-normalised tf-idf vector as [termIndex, value] pairs. */
  vectorize(text: string): [number, number][] {
    const counts = new Map<number, number>()
    for (const gram of ngrams(tokenize(text), this.model.ngram)) {
      const i = this.index.get(gram)
      if (i !== undefined) counts.set(i, (counts.get(i) ?? 0) + 1)
    }
    const entries: [number, number][] = []
    let norm = 0
    for (const [i, tf] of counts) {
      const w = (this.model.sublinear_tf ? 1 + Math.log(tf) : tf) * (this.model.idf[i] ?? 0)
      entries.push([i, w])
      norm += w * w
    }
    norm = Math.sqrt(norm)
    return norm > 0 ? entries.map(([i, w]) => [i, w / norm]) : entries
  }

  predictProba(text: string): number[] {
    const x = this.vectorize(text)
    const scores = this.model.coef.map((row, k) => x.reduce((s, [i, v]) => s + v * (row[i] ?? 0), this.model.intercept[k] ?? 0))
    const max = Math.max(...scores)
    const exps = scores.map((s) => Math.exp(s - max))
    const sum = exps.reduce((a, b) => a + b, 0)
    return exps.map((e) => e / sum)
  }

  /** Share of the ticket's tokens seen in training: low coverage means another language or heavy noise. */
  coverage(text: string): number {
    const toks = tokenize(text)
    if (toks.length === 0) return 0
    return toks.filter((t) => this.index.has(t)).length / toks.length
  }

  /** Share of adjacent token pairs the router knows as bigrams. Scrambled or interleaved text scores near zero. */
  coherence(text: string): number {
    const toks = tokenize(text)
    if (toks.length < 2) return 1
    let known = 0
    for (let i = 0; i + 1 < toks.length; i++) if (this.index.has(`${toks[i]} ${toks[i + 1]}`)) known++
    return known / (toks.length - 1)
  }

  /** Highest probability any short window of the ticket gives to a single sensitive queue (padding-resistant). */
  segmentSensitivity(text: string): number {
    const { classes, policy } = this.model
    const sensitive = classes.map((c, i) => (policy.sensitive.includes(c) ? i : -1)).filter((i) => i >= 0)
    let best = 0
    for (const w of segmentWindows(text, policy.segment_words)) {
      const p = this.predictProba(w)
      for (const i of sensitive) best = Math.max(best, p[i] ?? 0)
    }
    return best
  }

  decide(text: string): Decision {
    const { classes, policy } = this.model
    const proba = this.predictProba(text)
    const order = proba.map((p, k) => [p, k] as const).sort((a, b) => b[0] - a[0])
    const [conf, k] = order[0] ?? [0, 0]
    const queue = classes[k] ?? ''
    const coverage = this.coverage(text)
    const coherence = this.coherence(text)
    const segment = this.segmentSensitivity(text)
    const sensitiveMass = classes.reduce((s, c, i) => s + (policy.sensitive.includes(c) ? (proba[i] ?? 0) : 0), 0)
    const elsewhere = !policy.sensitive.includes(queue)

    // Same order as Policy.decide in analysis/router.py; the similarity guard needs the ticket index and runs server-side.
    let tier: Tier = 'human'
    let reason: Reason = 'confianca_baixa'
    if (coverage < policy.vocab_floor) {
      reason = 'vocabulario_desconhecido'
    } else if (coherence < policy.coherence_floor) {
      reason = 'sequencia_incomum'
    } else if (policy.never_auto.includes(queue) && conf >= policy.t_assist) {
      tier = 'assist'
      reason = 'fila_privilegiada'
    } else if (elsewhere && sensitiveMass >= policy.sensitive_mass && conf >= policy.t_assist) {
      tier = 'assist'
      reason = 'possivel_conteudo_sensivel'
    } else if (elsewhere && segment >= policy.segment_sensitive && conf >= policy.t_assist) {
      tier = 'assist'
      reason = 'trecho_sensivel'
    } else if (conf >= policy.t_auto) {
      tier = 'auto'
      reason = 'confianca_alta'
    } else if (conf >= policy.t_assist) {
      tier = 'assist'
      reason = 'confianca_media'
    }

    const row = this.model.coef[k] ?? []
    const why = this.vectorize(text)
      .map(([i, v]) => ({ term: this.model.terms[i] ?? '', weight: v * (row[i] ?? 0) }))
      .filter((w) => w.weight > 0)
      .sort((a, b) => b.weight - a.weight)
      .slice(0, 5)
      .map((w) => ({ term: w.term, weight: Math.round(w.weight * 1000) / 1000 }))

    return {
      queue,
      confidence: conf,
      top: order.slice(0, 3).map(([p, i]) => ({ queue: classes[i] ?? '', p })),
      tier,
      reason,
      coverage,
      coherence,
      segment,
      why,
    }
  }
}
