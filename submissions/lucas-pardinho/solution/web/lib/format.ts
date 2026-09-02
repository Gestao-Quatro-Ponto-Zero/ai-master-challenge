export function formatNumber(value: number): string {
  const rounded = Math.round(value);
  const sign = rounded < 0 ? "-" : "";
  const digits = Math.abs(rounded).toString();
  return `${sign}${digits.replace(/\B(?=(\d{3})+(?!\d))/g, ".")}`;
}

export function formatCurrency(value: number): string {
  const absolute = Math.abs(value);
  if (absolute >= 1_000_000) return `US$ ${formatDecimal(value / 1_000_000)} mi`;
  if (absolute >= 1_000) return `US$ ${formatDecimal(value / 1_000)} mil`;
  return formatFullCurrency(value);
}

export function formatFullCurrency(value: number): string {
  return `US$ ${formatNumber(value)}`;
}

export function formatPercent(value: number | null): string {
  if (value === null) return "—";
  const normalized = value <= 1 ? value * 100 : value;
  return `${Math.round(normalized)}%`;
}

export function confidenceLabel(value: "high" | "medium" | "low"): string {
  return { high: "Alta", medium: "Média", low: "Baixa" }[value];
}

function formatDecimal(value: number): string {
  return value.toFixed(1).replace(".", ",");
}
