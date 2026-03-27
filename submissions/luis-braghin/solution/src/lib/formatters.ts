export function formatBRL(value: number): string {
  return "R$ " + new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 }).format(value);
}

export function formatUSD(value: number): string {
  return "$ " + new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value);
}

export function formatPercent(value: number): string {
  return (value * 100).toFixed(1) + "%";
}

export function formatPercentRaw(value: number): string {
  return value.toFixed(1) + "%";
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat("pt-BR").format(value);
}

export function formatCompact(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(0)}K`;
  return value.toString();
}

export function getCategoryColor(category: string): string {
  switch (category) {
    case "HOT": return "hsl(var(--success))";
    case "WARM": return "hsl(var(--chart-3))";
    case "COOL": return "hsl(var(--primary))";
    case "COLD": return "hsl(var(--destructive))";
    case "DEAD": return "hsl(var(--muted-foreground))";
    default: return "hsl(var(--muted-foreground))";
  }
}

export function getCategoryBadgeClasses(category: string): string {
  switch (category) {
    case "HOT": return "bg-success/10 text-success border-success/30";
    case "WARM": return "bg-warning/10 text-warning border-warning/30";
    case "COOL": return "bg-primary/10 text-primary border-primary/30";
    case "COLD": return "bg-destructive/10 text-destructive border-destructive/30";
    case "DEAD": return "bg-muted text-muted-foreground border-muted-foreground/30";
    default: return "bg-muted text-muted-foreground border-border";
  }
}
