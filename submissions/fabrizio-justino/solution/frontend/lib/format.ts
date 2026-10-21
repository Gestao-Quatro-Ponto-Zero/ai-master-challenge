import type { Acao, Pilar, Severidade } from "./api"

export const usd = (v: number) => `US$ ${Math.round(v).toLocaleString("pt-BR")}`
// null = chance não disponível (Prospecting, sem data de engajamento)
export const pct = (v: number | null | undefined) => (v === null || v === undefined ? "n/d" : `${Math.round(v * 100)}%`)

// Faixa de incerteza (Wilson 95%). No platô da calibração ela é estreita de verdade
// (milhares de deals por faixa) — mostra "±<1 p.p." em vez de "40%–40%".
export function faixa(min: number | null, max: number | null): string | null {
  if (min === null || max === null) return null
  if (Math.round(max * 100) - Math.round(min * 100) < 1) return "±<1 p.p."
  return `${Math.round(min * 100)}%–${Math.round(max * 100)}%`
}
export const dataBr = (iso: string) => iso.split("-").reverse().join("/")

export const ORDEM_ACOES: Acao[] = ["Atacar agora", "Nutrir", "Primeiro contato", "Requalificar", "Encerrar", "Baixa prioridade"]

// Cada ação tem uma cor fixa em toda a interface (badge, cards de resumo, detalhe)
export const ESTILO_ACAO: Record<Acao, { badge: string; card: string; descricao: string }> = {
  "Atacar agora": {
    badge: "bg-emerald-500/15 text-emerald-700 ring-emerald-500/30 dark:text-emerald-300",
    card: "border-emerald-500/40",
    descricao: "Melhor chance no prazo e valor alto — foco da semana",
  },
  Nutrir: {
    badge: "bg-sky-500/15 text-sky-700 ring-sky-500/30 dark:text-sky-300",
    card: "border-sky-500/40",
    descricao: "Bom potencial, ainda amadurecendo",
  },
  "Primeiro contato": {
    badge: "bg-violet-500/15 text-violet-700 ring-violet-500/30 dark:text-violet-300",
    card: "border-violet-500/40",
    descricao: "Ainda em Prospecting — o ciclo só começa no 1º contato",
  },
  Requalificar: {
    badge: "bg-amber-500/15 text-amber-700 ring-amber-500/30 dark:text-amber-300",
    card: "border-amber-500/40",
    descricao: "Chance zero como está: se o cliente confirmar, encerre e reabra como novo",
  },
  Encerrar: {
    badge: "bg-rose-500/15 text-rose-700 ring-rose-500/30 dark:text-rose-300",
    card: "border-rose-500/40",
    descricao: "Fora do ciclo e de baixo valor — limpe do pipeline",
  },
  "Baixa prioridade": {
    badge: "bg-muted text-muted-foreground ring-border",
    card: "border-border",
    descricao: "Pouco valor ou sem engajamento ainda",
  },
}

export const ESTILO_SEVERIDADE: Record<Severidade, { rotulo: string; classe: string }> = {
  critico: { rotulo: "Crítico", classe: "bg-rose-500/15 text-rose-700 ring-rose-500/30 dark:text-rose-300" },
  atencao: { rotulo: "Atenção", classe: "bg-amber-500/15 text-amber-700 ring-amber-500/30 dark:text-amber-300" },
  lembrete: { rotulo: "Lembrete", classe: "bg-sky-500/15 text-sky-700 ring-sky-500/30 dark:text-sky-300" },
}

export const NOME_PILAR: Record<Pilar, string> = {
  chance: "Chance de ganhar no prazo",
  valor: "Valor do deal",
  dados: "Engajamento e dados",
}

// Cor do score pela AÇÃO (os cortes são percentis por data — ver config.PERCENTIL_*)
const COR_SCORE: Record<Acao, string> = {
  "Atacar agora": "bg-emerald-600 text-white",
  Nutrir: "bg-sky-600 text-white",
  "Primeiro contato": "bg-violet-500 text-white",
  Requalificar: "bg-amber-500 text-white",
  Encerrar: "bg-rose-500 text-white",
  "Baixa prioridade": "bg-muted-foreground/60 text-white",
}
export const corScore = (acao: Acao) => COR_SCORE[acao]

export const xVezes = (v: number | null | undefined) => (v === null || v === undefined ? "—" : `${v.toFixed(1)}×`)
