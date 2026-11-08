import type { BandKey, PriorityLabel, ReasonDirection } from '../api/types';

export const DEFAULT_ACCENT = '#1D4E89';

export function accentSoft(accent: string): string {
  const hex = accent.replace('#', '');
  const rgb =
    hex.length === 6
      ? [parseInt(hex.slice(0, 2), 16), parseInt(hex.slice(2, 4), 16), parseInt(hex.slice(4, 6), 16)]
      : [11, 107, 99];
  return `rgba(${rgb.join(',')},0.10)`;
}

export interface BandStyle {
  label: string;
  bg: string;
  fg: string;
  ring: string;
  edge: string;
}

export function bandStyle(band: BandKey, accent: string): BandStyle {
  const styles: Record<BandKey, BandStyle> = {
    focus: { label: 'Foco', bg: accentSoft(accent), fg: accent, ring: accent, edge: accent },
    stale_risk: { label: 'Decidir agora', bg: '#FFF1D6', fg: '#8A4B00', ring: '#C77A12', edge: '#C77A12' },
    follow_up: { label: 'Seguir', bg: '#EAEEF3', fg: '#3B4656', ring: '#6B7686', edge: '#B8C0CC' },
    low: { label: 'Baixa prioridade', bg: '#F0F2F5', fg: '#566070', ring: '#A3ACB8', edge: '#D5DAE1' },
    review: { label: 'Revisar', bg: '#FCE8E6', fg: '#9B2C2C', ring: '#C0504D', edge: '#C0504D' },
    prospecting: { label: 'Prospecção', bg: '#EBEAFB', fg: '#3F3A8F', ring: '#6B66C9', edge: '#6B66C9' },
  };
  return styles[band];
}

export interface PriorityStyle {
  label: '' | 'Alta' | 'Média' | 'Baixa';
  fg: string;
  bar1: string;
  bar2: string;
  bar3: string;
}

/** Só traduz o texto de prioridade da API em cores; não decide nível nenhum. */
export function priorityStyle(level: PriorityLabel | null, accent: string): PriorityStyle {
  const off = '#D5DAE1';
  if (level === 'Alta') return { label: 'Alta', fg: accent, bar1: accent, bar2: accent, bar3: accent };
  if (level === 'Média') return { label: 'Média', fg: '#3B4656', bar1: '#3B4656', bar2: '#3B4656', bar3: off };
  if (level === 'Baixa') return { label: 'Baixa', fg: '#566070', bar1: '#7A8494', bar2: off, bar3: off };
  return { label: '', fg: '#5B6472', bar1: off, bar2: off, bar3: off };
}

export interface ReasonStyle {
  sym: string;
  fg: string;
  bg: string;
}

export function reasonStyle(direction: ReasonDirection): ReasonStyle {
  const styles: Record<ReasonDirection, ReasonStyle> = {
    pos: { sym: '+', fg: '#1E6B45', bg: 'rgba(30,107,69,0.10)' },
    neg: { sym: '−', fg: '#9B2C2C', bg: '#FCE8E6' },
    neu: { sym: '•', fg: '#4A5565', bg: '#EAEEF3' },
    warn: { sym: '!', fg: '#8A4B00', bg: '#FFF1D6' },
  };
  return styles[direction];
}

/** Cor de cada faixa de tempo no funil (só apresentação): azul, azul, âmbar, vermelho. Posição = ordem das colunas da API. */
const HEAT_RGB: [number, number, number][] = [
  [29, 78, 137],
  [29, 78, 137],
  [199, 122, 18],
  [192, 79, 77],
];

function heatRgb(column: number): [number, number, number] {
  return HEAT_RGB[Math.min(Math.max(column, 0), HEAT_RGB.length - 1)];
}

/** Fundo e texto de uma célula do heatmap. `ratio` (0–1) é a intensidade relativa ao maior valor. */
export function heatStyle(column: number, ratio: number): { bg: string; fg: string } {
  const r = Math.min(1, Math.max(0, ratio));
  if (r === 0) return { bg: '#F4F6F9', fg: '#8A93A1' };
  return { bg: `rgba(${heatRgb(column).join(',')},${(0.12 + r * 0.78).toFixed(2)})`, fg: r > 0.55 ? '#FFFFFF' : '#0F1B2D' };
}

/** Tom claro de uma faixa de tempo, para a régua do detalhe. */
export function heatTint(column: number): string {
  return `rgba(${heatRgb(column).join(',')},0.28)`;
}
