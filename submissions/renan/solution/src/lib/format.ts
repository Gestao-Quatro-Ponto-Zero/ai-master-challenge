const usdFormatter = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

/** US$ 18.948 */
export const usd = (value: number) => usdFormatter.format(value).replace(/\s/, " ");

/** 71% (ou 70,8% com `digits`) */
export const pct = (ratio: number, digits = 0) =>
  `${(ratio * 100).toLocaleString("pt-BR", { minimumFractionDigits: digits, maximumFractionDigits: digits })}%`;

/** +7,5 pp / −0,2 pp */
export const points = (pp: number) => {
  const abs = Math.abs(pp).toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  return `${pp < 0 ? "−" : "+"}${abs} pp`;
};

export const count = (n: number) => n.toLocaleString("pt-BR");

/** 2017-12-31 → 31/12/2017 */
export const dateBr = (iso: string) => iso.split("-").reverse().join("/");

/** US$ 3,2 mi / US$ 184 mil */
export const usdCompact = (value: number) => {
  if (value >= 1_000_000) return `US$\u00a0${(value / 1_000_000).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}\u00a0mi`;
  if (value >= 1_000) return `US$\u00a0${Math.round(value / 1_000).toLocaleString("pt-BR")}\u00a0mil`;
  return usd(value);
};
