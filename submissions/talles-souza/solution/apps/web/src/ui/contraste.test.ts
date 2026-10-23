import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { PARES_DE_TEXTO, razaoDeContraste } from './contraste';

const TOKENS = readFileSync(
  join(dirname(fileURLToPath(import.meta.url)), '../estilo/tokens.css'),
  'utf8',
);

function cor(nome: string): string {
  const m = new RegExp('--ls-color-' + nome + ':\\s*(#[0-9A-Fa-f]{6})\\s*;').exec(TOKENS);
  if (!m?.[1]) throw new Error('token não encontrado: --ls-color-' + nome);
  return m[1];
}

describe('contraste dos pares de texto usados', () => {
  for (const par of PARES_DE_TEXTO) {
    it(par.texto + ' sobre ' + par.fundo + ' (' + par.onde + ') ≥ 4,5:1', () => {
      expect(razaoDeContraste(cor(par.texto), cor(par.fundo))).toBeGreaterThanOrEqual(4.5);
    });
  }

  it('o ouro sobre o claro reprova como texto (por isso só é borda/acento no claro)', () => {
    expect(razaoDeContraste(cor('gold'), cor('offwhite'))).toBeLessThan(4.5);
    expect(razaoDeContraste(cor('gold'), cor('white'))).toBeLessThan(4.5);
  });

  it('o cinza secundário sobre o fundo da página reprova (por isso só sobre branco)', () => {
    expect(razaoDeContraste(cor('text-muted'), cor('offwhite'))).toBeLessThan(4.5);
  });
});
