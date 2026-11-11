import docs from "@/app/como-foi-feito/_content/docs.generated.json"

/**
 * Conteúdo gerado dos .md do repositório (ADRs, judgment log, process log) por
 * app/como-foi-feito/_content/generate.mjs. Import em tempo de build: funciona na Vercel com root em solution/app.
 */
export interface Adr {
  number: string
  title: string
  status: string
  statusKind: "aceita" | "proposta" | "rejeitada" | "outra"
  date: string | null
  origin: string | null
  originKind: "daniel" | "daniel_ia" | "ia_daniel" | "ia"
  summary: string | null
  /** Caminho do .md no repositório (só referência; o repositório é privado). */
  file: string
  /** Documento completo em HTML, gerado no build a partir do .md. */
  html: string
}

export interface JudgmentEntry {
  n: number
  date: string
  type: string
  what: string
  who: string
  result: string
}

export interface SessionEntry {
  name: string
  date: string | null
  harness: string | null
  duration: string | null
}

export const content = docs as {
  adrs: Adr[]
  judgment: JudgmentEntry[]
  judgmentHtml: string
  sessions: SessionEntry[]
}

export const isAiError = (j: JudgmentEntry) => /^IA errou/i.test(j.type)
export const isHumanJudgment = (j: JudgmentEntry) => /^Julgamento humano/i.test(j.type)
export const adrByNumber = (n: string) => content.adrs.find((a) => a.number === n)
