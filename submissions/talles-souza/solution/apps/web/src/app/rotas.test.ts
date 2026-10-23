import { describe, expect, it } from 'vitest';
import { lerRota } from './rotas';

describe('rotas por hash', () => {
  it('a raiz é a segunda-feira do vendedor', () => {
    expect(lerRota('')).toEqual({ nome: 'segunda' });
    expect(lerRota('#/')).toEqual({ nome: 'segunda' });
    expect(lerRota('#')).toEqual({ nome: 'segunda' });
  });

  it('lê deal, manager, novo lead e como funciona', () => {
    expect(lerRota('#/deal/AAAA0001')).toEqual({ nome: 'deal', id: 'AAAA0001' });
    expect(lerRota('#/manager')).toEqual({ nome: 'manager' });
    expect(lerRota('#/novo-lead/')).toEqual({ nome: 'novo-lead' });
    expect(lerRota('#/como-funciona')).toEqual({ nome: 'como-funciona' });
    expect(lerRota('#/outra')).toEqual({ nome: 'nao-encontrada', caminho: '/outra' });
  });
});
