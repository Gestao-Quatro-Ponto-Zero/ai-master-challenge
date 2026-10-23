/**
 * Contraste WCAG: os pares texto/fundo que a interface usa (nomes dos tokens `--ls-color-*`).
 * O teste calcula cada par a partir de `tokens.css` e exige 4,5:1 (AA para texto normal).
 * O ouro só aparece como texto sobre o navy; sobre o claro ele é borda ou acento.
 */
export interface ParDeTexto {
  texto: string;
  fundo: string;
  onde: string;
}

export const PARES_DE_TEXTO: readonly ParDeTexto[] = [
  { texto: 'navy-ink', fundo: 'offwhite', onde: 'corpo da página' },
  { texto: 'navy-ink', fundo: 'white', onde: 'cartões e painéis' },
  { texto: 'navy-scaling', fundo: 'offwhite', onde: 'texto secundário e avisos' },
  { texto: 'navy-scaling', fundo: 'white', onde: 'avisos dentro dos painéis' },
  { texto: 'text-muted', fundo: 'white', onde: 'metadados dos cartões (só sobre branco)' },
  { texto: 'navy', fundo: 'white', onde: 'botão vazado e hover do botão' },
  { texto: 'offwhite', fundo: 'navy', onde: 'topo, botão cheio' },
  { texto: 'gold', fundo: 'navy', onde: 'marca, eyebrow e itálico do título' },
  { texto: 'gold-light', fundo: 'navy', onde: 'hover da navegação' },
  { texto: 'text-on-dark-muted', fundo: 'navy', onde: 'leitura da política no topo' },
  { texto: 'white', fundo: 'clay', onde: 'etiqueta Foque agora' },
  { texto: 'white', fundo: 'navy-scaling', onde: 'etiqueta Siga no ritmo' },
  { texto: 'white', fundo: 'navy-ink', onde: 'etiqueta Nutrição' },
  { texto: 'clay', fundo: 'white', onde: 'erro e selo dentro de painel' },
  { texto: 'clay', fundo: 'offwhite', onde: 'erro e selo na página' },
  { texto: 'offwhite', fundo: 'wine', onde: 'banner do modo local' },
];

/** Luminância relativa de `#RRGGBB`. */
export function luminancia(hex: string): number {
  const m = /^#?([0-9a-f]{6})$/i.exec(hex.trim());
  if (!m?.[1]) throw new Error('cor inválida: ' + hex);
  const n = parseInt(m[1], 16);
  const canal = (c: number) => {
    const s = c / 255;
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * canal((n >> 16) & 255) + 0.7152 * canal((n >> 8) & 255) + 0.0722 * canal(n & 255);
}

/** Razão de contraste entre duas cores (1 a 21). */
export function razaoDeContraste(a: string, b: string): number {
  const [l1, l2] = [luminancia(a), luminancia(b)].sort((x, y) => y - x) as [number, number];
  return (l1 + 0.05) / (l2 + 0.05);
}
