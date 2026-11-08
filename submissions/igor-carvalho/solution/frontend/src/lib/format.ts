/** "US$ 5.482" */
export function money(n: number): string {
  return 'US$ ' + Math.round(n).toLocaleString('pt-BR');
}

/** "2017-12-31" -> "31/12/2017" */
export function formatFullDate(iso: string): string {
  const [year, month, day] = iso.split('-');
  return `${day}/${month}/${year}`;
}

/** ISO 8601 -> "07/11 10:29" */
export function formatShortDateTime(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '';
  const two = (n: number) => String(n).padStart(2, '0');
  return `${two(date.getDate())}/${two(date.getMonth() + 1)} ${two(date.getHours())}:${two(date.getMinutes())}`;
}

export function initialsOf(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join('');
}

export function daysText(days: number): string {
  return `${days} ${days === 1 ? 'dia' : 'dias'}`;
}

export function buildFooterText(args: {
  total: number;
  pageStart: number;
  shown: number;
  tab: string;
  levelLabel: string | null;
  sampleData: boolean;
}): string {
  const { total, pageStart, shown, tab, levelLabel, sampleData } = args;
  const sample = sampleData ? ' (amostra do exemplo)' : '';
  let suffix = ` deals nesta faixa${sample}`;
  if (tab === 'ev') suffix = ` deals com valor esperado, do maior para o menor${sample}`;
  else if (tab === 'all') suffix = ` deals abertos${sample}`;
  const level = levelLabel && tab !== 'review' ? ` · prioridade ${levelLabel.toLowerCase()}` : '';
  return `Mostrando ${total ? pageStart + 1 : 0}–${pageStart + shown} de ${total}${suffix}${level}`;
}

/** Chance de fechar: "70%"; abaixo de 10% mostra uma casa decimal ("6,1%"). */
export function percent(p: number): string {
  const pct = p * 100;
  return pct < 10 ? `${pct.toFixed(1).replace('.', ',')}%` : `${Math.round(pct)}%`;
}
