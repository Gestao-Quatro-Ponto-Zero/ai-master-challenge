import type { RespostasDoDeal } from '@lead-scorer/dominio/qualificacao';
import { describe, expect, it } from 'vitest';
import {
  criarRepositorioNavegador,
  lerComissao,
  lerPerfil,
  PREFIXO_RESPOSTAS,
  salvarComissao,
  salvarPerfil,
} from './repositorio';

/** Storage em memória com a interface do `localStorage`. */
function storage(inicial: Record<string, string> = {}): Storage {
  const m = new Map(Object.entries(inicial));
  return {
    get length() {
      return m.size;
    },
    key: (i) => [...m.keys()][i] ?? null,
    getItem: (k) => m.get(k) ?? null,
    setItem: (k, v) => void m.set(k, String(v)),
    removeItem: (k) => void m.delete(k),
    clear: () => m.clear(),
  };
}

const respostas: RespostasDoDeal = {
  formato: 1,
  dealId: 'AAAA0001',
  metodoId: 'metodo-provisorio-v1',
  respostas: [{ perguntaId: 'decisor', valor: 'sim', respondidoEm: '2026-10-22T12:00:00.000Z' }],
  decisao: null,
};

describe('repositório no navegador', () => {
  it('salva, lê, lista e limpa', () => {
    const repo = criarRepositorioNavegador(storage());
    repo.salvar(respostas);
    expect(repo.ler('AAAA0001')).toEqual(respostas);
    expect(repo.listar()).toEqual([respostas]);
    repo.limpar('AAAA0001');
    expect(repo.ler('AAAA0001')).toBeNull();
  });

  it('ignora JSON quebrado e formato errado, sem lançar', () => {
    const repo = criarRepositorioNavegador(
      storage({
        [PREFIXO_RESPOSTAS + 'QUEBRADO']: '{ não é json',
        [PREFIXO_RESPOSTAS + 'ERRADO01']: JSON.stringify({
          ...respostas,
          dealId: 'ERRADO01',
          formato: 2,
        }),
        [PREFIXO_RESPOSTAS + 'AAAA0001']: JSON.stringify(respostas),
        'outra-chave': 'qualquer coisa',
      }),
    );
    expect(repo.ler('QUEBRADO')).toBeNull();
    expect(repo.ler('ERRADO01')).toBeNull();
    expect(repo.listar()).toEqual([respostas]);
  });

  it('storage que lança não derruba a tela', () => {
    const quebrado = storage();
    quebrado.getItem = () => {
      throw new Error('SecurityError');
    };
    quebrado.setItem = () => {
      throw new Error('QuotaExceededError');
    };
    const repo = criarRepositorioNavegador(quebrado);
    expect(() => repo.salvar(respostas)).not.toThrow();
    expect(repo.ler('AAAA0001')).toBeNull();
    expect(repo.listar()).toEqual([]);
  });

  it('sem storage, guarda em memória', () => {
    const repo = criarRepositorioNavegador(null);
    repo.salvar(respostas);
    expect(repo.ler('AAAA0001')).toEqual(respostas);
  });

  it('o perfil volta como foi salvo e lixo vira null', () => {
    const s = storage();
    salvarPerfil({ tipo: 'vendedor', nome: 'Ana Vendas' }, s);
    expect(lerPerfil(s)).toEqual({ tipo: 'vendedor', nome: 'Ana Vendas' });
    s.setItem('lead-scorer:perfil:v1', '{"tipo":"rei"}');
    expect(lerPerfil(s)).toBeNull();
    s.setItem('lead-scorer:perfil:v1', 'xx');
    expect(lerPerfil(s)).toBeNull();
    expect(lerPerfil(null)).toBeNull();
  });
});

describe('comissão (preferência do vendedor)', () => {
  it('começa vazia, guarda o que ele digita e apaga com null', () => {
    const s = storage();
    expect(lerComissao(s)).toBeNull();
    salvarComissao(7.5, s);
    expect(lerComissao(s)).toBe(7.5);
    salvarComissao(null, s);
    expect(lerComissao(s)).toBeNull();
  });

  it('valor fora de 0 a 100 ou texto estranho vira vazio; sem storage não quebra', () => {
    const s = storage({ 'lead-scorer:comissao:v1': 'abc' });
    expect(lerComissao(s)).toBeNull();
    salvarComissao(150, s);
    expect(lerComissao(s)).toBeNull();
    salvarComissao(0, s);
    expect(lerComissao(s)).toBeNull();
    const quebrado = {
      getItem: () => {
        throw new Error('bloqueado');
      },
      setItem: () => {
        throw new Error('bloqueado');
      },
      removeItem: () => {
        throw new Error('bloqueado');
      },
    } as unknown as Storage;
    expect(lerComissao(quebrado)).toBeNull();
    expect(() => salvarComissao(5, quebrado)).not.toThrow();
    expect(lerComissao(null)).toBeNull();
  });
});
