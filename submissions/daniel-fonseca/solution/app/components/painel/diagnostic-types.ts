/** Formatos que o servidor monta para os gráficos do Painel › Diagnóstico (PRD §4.1). */

export type MetricKey = "pct_open" | "pct_pending" | "hours" | "csat"
export type DimensionKey = "canal" | "prioridade" | "tipo" | "assunto" | "produto"
export type Interval = [number, number]

export interface GroupStat {
  value: string
  n: number
  nClosed: number
  nCoherent: number
  pct_open: number
  pct_open_ci: Interval
  pct_pending: number
  pct_pending_ci: Interval
  hours: number
  hours_ci: Interval
  csat: number
  csat_ci: Interval
  /** agrupa os produtos fora dos 10 maiores */
  isOther?: boolean
  otherCount?: number
}

export interface TestResult {
  p: number
  significant: boolean
  test: string
}

export interface DimensionData {
  key: DimensionKey
  label: string
  /** "Os canais", "As prioridades"… */
  subject: string
  groups: GroupStat[]
  tests: Record<MetricKey, TestResult | null>
  /** produto: total de grupos antes do corte em 10 + Outros */
  totalGroups: number
}

export interface Overall {
  pct_open: number
  pct_pending: number
  hours: number
  csat: number
}

export const METRICS: { key: MetricKey; label: string; short: string }[] = [
  { key: "pct_open", label: "% sem 1ª resposta", short: "sem 1ª resposta" },
  { key: "pct_pending", label: "% aguardando cliente", short: "aguardando cliente" },
  { key: "hours", label: "Tempo até resolução", short: "horas (mediana)" },
  { key: "csat", label: "CSAT", short: "CSAT médio" },
]

export const DIMENSIONS: { key: DimensionKey; label: string; subject: string }[] = [
  { key: "canal", label: "Canal", subject: "Os canais" },
  { key: "prioridade", label: "Prioridade", subject: "As prioridades" },
  { key: "tipo", label: "Tipo", subject: "Os tipos de ticket" },
  { key: "assunto", label: "Assunto", subject: "Os assuntos" },
  { key: "produto", label: "Produto", subject: "Os produtos" },
]
