import { describe, expect, it } from 'vitest';
import { compararNaLista, posicionar, valorNaLista, type EntradaDaLista } from './posicao';

const e = (
  id: string,
  esperado: number | null,
  emJogo: number,
  idadeDias: number | null = esperado === null ? null : 10,
  grupo = 0,
): EntradaDaLista => ({ id, grupo, esperado, emJogo, idadeDias });

describe('posicionar (a posição na ordem da tela do vendedor: por onde começar, não o score)', () => {
  it('dentro do grupo, pelo valor esperado', () => {
    const p = posicionar([
      e('C', 100, 1000),
      e('A', 900, 1000),
      e('D', 10, 1000),
      e('B', 500, 1000),
    ]);
    expect([...p.entries()].map(([id, x]) => [id, x.k])).toEqual([
      ['A', 1],
      ['B', 2],
      ['C', 3],
      ['D', 4],
    ]);
    expect(p.get('A')).toEqual({ k: 1, n: 4, pelo: 'esperado' });
  });

  it('o grupo vem antes do valor: um caro do grupo de baixo não passa um barato do grupo de cima', () => {
    // o caso Zane Levy: GTK 500 na Nutrição (chance 7%) contra um negócio vivo barato no Foque
    const p = posicionar([
      e('gtk-nutricao', 0.07 * 26768, 26768, 120, 3),
      e('vivo-foque', 0.4 * 550, 550, 45, 0),
      e('sem-data', null, 4821, null, 2),
    ]);
    expect(p.get('vivo-foque')).toMatchObject({ k: 1 });
    expect(p.get('sem-data')).toMatchObject({ k: 2, pelo: 'preco' });
    expect(p.get('gtk-nutricao')).toMatchObject({ k: 3 });
  });

  it('empate no valor esperado: o de preço maior fica na frente', () => {
    const p = posicionar([e('barato', 500, 1000), e('caro', 500, 5000)]);
    expect(p.get('caro')?.k).toBe(1);
    expect(p.get('barato')?.k).toBe(2);
  });

  it('empate completo (mesmo grupo, valor e preço): o mais novo na frente, depois o id; cada um com o seu número', () => {
    const p = posicionar([
      e('B', 300, 1000, 20),
      e('A', 300, 1000, 20),
      e('N', 300, 1000, 5),
      e('Z', 100, 1000),
    ]);
    expect([...p.entries()].map(([id, x]) => [id, x.k])).toEqual([
      ['N', 1],
      ['A', 2],
      ['B', 3],
      ['Z', 4],
    ]);
  });

  it('sem data de início: entra só pelo preço dentro do grupo dele e diz isso', () => {
    expect(valorNaLista(e('S', null, 4821))).toBe(4821);
    const p = posicionar([e('sem', null, 4821), e('outro', null, 550), e('maior', null, 26768)]);
    expect([...p.entries()].map(([id, x]) => [id, x.k, x.pelo])).toEqual([
      ['maior', 1, 'preco'],
      ['sem', 2, 'preco'],
      ['outro', 3, 'preco'],
    ]);
  });

  it('lista de 1 negócio = 1º de 1; lista vazia = nada a mostrar', () => {
    expect(posicionar([e('só', 0.4, 55)]).get('só')).toEqual({ k: 1, n: 1, pelo: 'esperado' });
    expect(posicionar([]).size).toBe(0);
  });

  it('a ordem de entrada não muda nada, e as posições vão de 1 a n sem repetir', () => {
    const lista = [
      e('A', 10, 55),
      e('B', 300, 550),
      e('C', null, 4821, null, 2),
      e('D', 300, 550, 10, 1),
    ];
    const ida = posicionar(lista);
    const volta = posicionar([...lista].reverse());
    expect([...volta.entries()].sort()).toEqual([...ida.entries()].sort());
    expect([...ida.values()].map((x) => x.k).sort()).toEqual([1, 2, 3, 4]);
  });

  it('compararNaLista: negativo quando o primeiro vem antes; 0 só para o mesmo negócio', () => {
    expect(compararNaLista(e('A', 9, 10), e('B', 1, 10))).toBeLessThan(0);
    expect(compararNaLista(e('A', 1, 10), e('B', 1, 20))).toBeGreaterThan(0);
    expect(compararNaLista(e('A', 1, 10), e('B', 1, 10))).toBeLessThan(0);
    expect(compararNaLista(e('A', 1, 10), e('A', 1, 10))).toBe(0);
    // o grupo decide antes do valor
    expect(compararNaLista(e('A', 1, 10, 10, 0), e('B', 999, 9999, 10, 3))).toBeLessThan(0);
  });
});
