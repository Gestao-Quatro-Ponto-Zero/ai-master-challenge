/** Formatação pt-BR usada em todo o app. */
const nf = (opts: Intl.NumberFormatOptions) => new Intl.NumberFormat("pt-BR", opts)

export const fmt = {
  int: (n: number) => nf({ maximumFractionDigits: 0 }).format(n),
  dec: (n: number, digits = 1) => nf({ minimumFractionDigits: digits, maximumFractionDigits: digits }).format(n),
  pct: (share: number, digits = 1) => nf({ style: "percent", minimumFractionDigits: digits, maximumFractionDigits: digits }).format(share),
  brl: (n: number, digits = 0) => nf({ style: "currency", currency: "BRL", minimumFractionDigits: digits, maximumFractionDigits: digits }).format(n),
  usd: (n: number, digits = 4) => nf({ style: "currency", currency: "USD", minimumFractionDigits: digits, maximumFractionDigits: digits }).format(n),
  ms: (ms: number) => (ms >= 1000 ? `${nf({ maximumFractionDigits: 1 }).format(ms / 1000)} s` : `${Math.round(ms)} ms`),
  hours: (h: number, digits = 1) => `${nf({ maximumFractionDigits: digits }).format(h)} h`,
  /** "há 12 min", "há 3 h", "há 2 dias" */
  relative: (iso: string, now: number = Date.now()) => {
    const s = Math.max(0, Math.round((now - new Date(iso).getTime()) / 1000))
    if (s < 60) return "agora"
    if (s < 3600) return `há ${Math.round(s / 60)} min`
    if (s < 86400) return `há ${Math.round(s / 3600)} h`
    return `há ${Math.round(s / 86400)} dias`
  },
}
