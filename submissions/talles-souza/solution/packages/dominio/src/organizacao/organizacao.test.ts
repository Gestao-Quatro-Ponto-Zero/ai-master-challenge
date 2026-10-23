import { describe, expect, it } from 'vitest';
import type { Deal, MembroDoTime } from '../pipeline';
import { aplicarFiltro, filtrarTime, filtroDoPerfil, montarOrganizacao } from './index';

const deal = (vendedor: string, manager: string, regiao: string, aberto: boolean) =>
  ({ vendedor, manager, regiao, aberto }) as Deal;

const deals = [
  deal('Zeca', 'Mara', 'West', true),
  deal('Ana', 'Mara', 'West', false),
  deal('Ana', 'Mara', 'West', true),
  deal('Bruno', 'Celso', 'East', true),
];

const time: MembroDoTime[] = [
  { nome: 'Zeca', manager: 'Mara', regiao: 'West' },
  { nome: 'Ana', manager: 'Mara', regiao: 'West' },
  { nome: 'Bruno', manager: 'Celso', regiao: 'East' },
  { nome: 'Dora', manager: 'Lia', regiao: 'Central' },
];

describe('montarOrganizacao', () => {
  it('lista o time inteiro em ordem de nome, com os abertos de cada um (0 para quem não tem negócio)', () => {
    expect(montarOrganizacao(time, deals)).toEqual({
      vendedores: [
        { nome: 'Ana', manager: 'Mara', regiao: 'West', abertos: 1 },
        { nome: 'Bruno', manager: 'Celso', regiao: 'East', abertos: 1 },
        { nome: 'Dora', manager: 'Lia', regiao: 'Central', abertos: 0 },
        { nome: 'Zeca', manager: 'Mara', regiao: 'West', abertos: 1 },
      ],
      managers: [
        { nome: 'Celso', regiao: 'East', vendedores: ['Bruno'] },
        { nome: 'Lia', regiao: 'Central', vendedores: ['Dora'] },
        { nome: 'Mara', regiao: 'West', vendedores: ['Ana', 'Zeca'] },
      ],
      regioes: ['Central', 'East', 'West'],
    });
  });
});

describe('filtroDoPerfil e aplicarFiltro', () => {
  it('cada perfil vira um filtro; "todos" não filtra', () => {
    expect(filtroDoPerfil({ tipo: 'vendedor', nome: 'Ana' })).toEqual({ vendedor: 'Ana' });
    expect(filtroDoPerfil({ tipo: 'manager', nome: 'Mara' })).toEqual({ manager: 'Mara' });
    expect(filtroDoPerfil({ tipo: 'todos' })).toEqual({});
  });

  it('campos ausentes não filtram; presentes combinam', () => {
    expect(aplicarFiltro(deals, {})).toHaveLength(4);
    expect(aplicarFiltro(deals, { manager: 'Mara' })).toHaveLength(3);
    expect(aplicarFiltro(deals, { manager: 'Mara', vendedor: 'Ana' })).toHaveLength(2);
    expect(aplicarFiltro(deals, { regiao: 'Central' })).toHaveLength(0);
  });

  it('filtrarTime: o time que o filtro alcança, inclusive quem não tem negócio', () => {
    expect(filtrarTime(time, {})).toHaveLength(4);
    expect(filtrarTime(time, { regiao: 'Central' }).map((v) => v.nome)).toEqual(['Dora']);
    expect(filtrarTime(time, { manager: 'Mara' }).map((v) => v.nome)).toEqual(['Zeca', 'Ana']);
    expect(filtrarTime(time, { manager: 'Mara', vendedor: 'Bruno' })).toEqual([]);
  });
});
