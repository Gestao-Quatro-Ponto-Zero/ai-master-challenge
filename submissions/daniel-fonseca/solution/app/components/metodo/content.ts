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
  href: string
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
  repo: string
  adrs: Adr[]
  judgment: JudgmentEntry[]
  judgmentHref: string
  sessions: SessionEntry[]
  processLogHref: string
}

export const isAiError = (j: JudgmentEntry) => /^IA errou/i.test(j.type)
export const isHumanJudgment = (j: JudgmentEntry) => /^Julgamento humano/i.test(j.type)
export const repoHref = (path: string) => `${content.repo}/${path}`
