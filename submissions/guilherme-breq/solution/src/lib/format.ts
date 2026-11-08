const MONTHS = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];

/** "2017-12-31" → "31 dez 2017" (sem depender do fuso do navegador). */
export function formatDate(iso: string): string {
  const [y, m, d] = iso.split("-").map(Number);
  return `${d} ${MONTHS[m - 1]} ${y}`;
}

const compact = new Intl.NumberFormat("pt-BR", { notation: "compact", maximumFractionDigits: 1 });
export const formatCompactUSD = (v: number) => `US$ ${compact.format(v)}`;
export const formatInt = (v: number) => new Intl.NumberFormat("pt-BR").format(v);
export const formatPct = (p: number) => `${Math.round(p * 100)}%`;

export function firstName(full: string): string {
  return full.split(" ")[0];
}
