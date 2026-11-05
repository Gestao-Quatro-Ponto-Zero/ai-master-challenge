const usd = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
  minimumFractionDigits: 0,
});
const num = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 });

/** US$ 4.386 (sem centavos) */
export function formatUSD(v: number | null | undefined): string {
  if (v == null || Number.isNaN(v)) return "—";
  return usd.format(v).replace(/\u00a0/g, " ");
}

/** US$ 505 mil / US$ 1,2 mi */
export function formatUSDCompact(v: number | null | undefined): string {
  if (v == null) return "—";
  if (Math.abs(v) >= 1_000_000)
    return `US$ ${(v / 1_000_000).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} mi`;
  if (Math.abs(v) >= 10_000) return `US$ ${num.format(Math.round(v / 1000))} mil`;
  return formatUSD(v);
}

export function formatNumber(v: number | null | undefined): string {
  return v == null ? "—" : num.format(v);
}

/** 0.712 -> "71%" */
export function formatPct(p: number | null | undefined): string {
  return p == null ? "—" : `${Math.round(p * 100)}%`;
}

/** "2017-12-31" -> "31/12/2017" (sem fuso horário) */
export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const [y, m, d] = iso.slice(0, 10).split("-");
  return `${d}/${m}/${y}`;
}

export function formatPrazo(dias: number | null | undefined): string {
  if (dias == null) return "";
  if (dias <= 0) return "hoje";
  return dias === 1 ? "falta 1 dia" : `faltam ${dias} dias`;
}
