import { describe, expect, it } from 'vitest';
import { clienteFalso, resumo } from '../testes/fixtures';
import type { ClienteHttp } from './clienteHttp';
import { criarClienteResiliente, type Modo } from './clienteResiliente';
import { ErroCliente } from './erros';

function httpQue(falha: () => ErroCliente | null): ClienteHttp {
  const base = clienteFalso();
  const embrulhar =
    <A extends unknown[], R>(f: (...a: A) => Promise<R>) =>
    async (...a: A): Promise<R> => {
      const e = falha();
      if (e) throw e;
      return f(...a);
    };
  return {
    saude: embrulhar(async () => ({
      status: 'ok' as const,
      versao: '1',
      iniciadoEm: '2026-10-22T00:00:00Z',
      dados: { total: 1, referencia: '2017-12-31', checksum: 'x' },
    })),
    resumo: embrulhar(base.resumo),
    deals: embrulhar(base.deals),
    deal: embrulhar(base.deal),
    organizacao: embrulhar(base.organizacao),
    metodo: embrulhar(base.metodo),
    politica: embrulhar(base.politica),
    textos: embrulhar(base.textos),
    chance: embrulhar(base.chance),
    pontos: embrulhar(base.pontos),
    motor: embrulhar(base.motor),
    avaliar: embrulhar(base.avaliar),
    item: embrulhar(base.item),
    fila: embrulhar(base.fila),
    painel: embrulhar(base.painel),
  };
}

describe('clienteResiliente', () => {
  it('cai para o modo local quando a API some e volta quando ela responde', async () => {
    let fora = true;
    const http = httpQue(() => (fora ? new ErroCliente('circuito_aberto', 'aberto') : null));
    const local = clienteFalso({ resumo: async () => ({ ...resumo, checksum: 'local' }) });
    const c = criarClienteResiliente(http, local);
    const modos: Modo[] = [];
    c.assinar((m) => modos.push(m));

    expect(c.modo()).toBe('api');
    await expect(c.resumo()).resolves.toMatchObject({ checksum: 'local' });
    expect(c.modo()).toBe('local');

    fora = false;
    await expect(c.resumo()).resolves.toMatchObject({ checksum: 'abc' });
    expect(c.modo()).toBe('api');
    expect(modos).toEqual(['local', 'api']);
  });

  it('erro de rede depois dos retries também cai para o local', async () => {
    const c = criarClienteResiliente(
      httpQue(() => new ErroCliente('rede', 'caiu')),
      clienteFalso({ resumo: async () => ({ ...resumo, checksum: 'local' }) }),
    );
    await expect(c.resumo()).resolves.toMatchObject({ checksum: 'local' });
    expect(c.modo()).toBe('local');
  });

  it('erro de entrada não troca de modo: o pedido é que está errado', async () => {
    const c = criarClienteResiliente(
      httpQue(() => new ErroCliente('http', '400', { status: 400 })),
      clienteFalso(),
    );
    await expect(c.resumo()).rejects.toMatchObject({ extra: { status: 400 } });
    expect(c.modo()).toBe('api');
  });

  it('rota que a API não conhece (404 nao_encontrado) é respondida pelo local, sem trocar o modo', async () => {
    const c = criarClienteResiliente(
      httpQue(() => new ErroCliente('http', '404', { status: 404, codigo: 'nao_encontrado' })),
      clienteFalso({ resumo: async () => ({ ...resumo, checksum: 'local' }) }),
    );
    await expect(c.resumo()).resolves.toMatchObject({ checksum: 'local' });
    expect(c.modo()).toBe('api');
  });

  it('a sonda traz de volta para a API sem esperar uma operação', async () => {
    let fora = true;
    const c = criarClienteResiliente(
      httpQue(() => (fora ? new ErroCliente('rede', 'caiu') : null)),
      clienteFalso(),
    );
    await c.resumo();
    expect(c.modo()).toBe('local');
    await expect(c.sondar()).resolves.toBe('local');
    fora = false;
    await expect(c.sondar()).resolves.toBe('api');
  });
});
