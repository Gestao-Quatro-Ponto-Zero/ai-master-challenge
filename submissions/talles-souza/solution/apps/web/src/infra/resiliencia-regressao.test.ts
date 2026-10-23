/**
 * Casos de borda da resiliência: requisição atrasada não mexe no disjuntor nem no modo, o
 * timeout cobre o corpo da resposta, erro 5xx manda para o modo local sem retry e 404 de rota
 * ausente não vira "negócio inexistente".
 */
import { describe, expect, it } from 'vitest';
import { lerRota } from '../app/rotas';
import { clienteFalso, resumo } from '../testes/fixtures';
import { criarClienteHttp, type ClienteHttp } from './clienteHttp';
import { criarClienteResiliente } from './clienteResiliente';
import { criarDisjuntor } from './disjuntor';
import { ErroCliente } from './erros';
import type { Temporizador } from './tempo';

const semEspera = { dormir: async () => {}, aleatorio: () => 0 };
const rede = () => new ErroCliente('rede', 'caiu');

function adiado<T>() {
  let resolver!: (v: T) => void;
  let rejeitar!: (e: unknown) => void;
  const promessa = new Promise<T>((ok, nao) => {
    resolver = ok;
    rejeitar = nao;
  });
  return { promessa, resolver, rejeitar };
}

/** HTTP falso a partir das fixtures, com `saude` (o resiliente precisa dela para sondar). */
function httpFalso(): ClienteHttp {
  return { ...clienteFalso(), saude: async () => ({}) } as unknown as ClienteHttp;
}

describe('disjuntor: só o resultado da geração atual muda o estado', () => {
  it('um sucesso atrasado, de antes da abertura, não fecha o circuito', async () => {
    const d = criarDisjuntor(undefined, () => 1_000);
    const lenta = adiado<string>();
    const emVoo = d.executar(() => lenta.promessa);
    for (let i = 0; i < 3; i++) {
      await expect(d.executar(() => Promise.reject(rede()))).rejects.toBeDefined();
    }
    expect(d.estado()).toBe('aberto');
    lenta.resolver('tarde');
    await expect(emVoo).resolves.toBe('tarde');
    expect(d.estado()).toBe('aberto');
  });

  it('uma falha atrasada não estende a janela aberta', async () => {
    let t = 1_000;
    const d = criarDisjuntor({ falhasParaAbrir: 3, abertoMs: 15_000 }, () => t);
    const lenta = adiado<string>();
    const emVoo = d.executar(() => lenta.promessa);
    for (let i = 0; i < 3; i++) {
      await expect(d.executar(() => Promise.reject(rede()))).rejects.toBeDefined();
    }
    t += 14_000;
    lenta.rejeitar(rede());
    await expect(emVoo).rejects.toBeDefined();
    t += 1_000;
    expect(d.estado()).toBe('meio_aberto');
  });

  it('erro 500 conta como falha do servidor', async () => {
    const d = criarDisjuntor(undefined, () => 0);
    const quinhentos = () => Promise.reject(new ErroCliente('http', '500', { status: 500 }));
    for (let i = 0; i < 3; i++) await expect(d.executar(quinhentos)).rejects.toBeDefined();
    expect(d.estado()).toBe('aberto');
  });
});

describe('clienteHttp: prazo e 404', () => {
  it('o timeout cobre o corpo: o cabeçalho chega, o corpo trava, e vale o timeout', async () => {
    const pendentes: Array<() => void> = [];
    const tempo: Temporizador = {
      definir(fn) {
        pendentes.push(fn);
        return pendentes.length;
      },
      limpar() {},
    };
    const c = criarClienteHttp({
      ...semEspera,
      temporizador: tempo,
      retry: { tentativas: 1, baseMs: 1, tetoMs: 1 },
      fetch: async (_url, init) => {
        const corpo = new ReadableStream<Uint8Array>({
          start(controle) {
            init?.signal?.addEventListener('abort', () =>
              controle.error(new DOMException('abortado', 'AbortError')),
            );
          },
        });
        // o prazo estoura depois que o cabeçalho já chegou
        queueMicrotask(() => pendentes.forEach((fn) => fn()));
        return new Response(corpo, {
          status: 200,
          headers: { 'content-type': 'application/json' },
        });
      },
    });
    await expect(c.politica()).rejects.toMatchObject({ tipo: 'timeout' });
  });

  it('404 de rota ausente não vira "negócio inexistente"', async () => {
    const corpo = (codigo: string) =>
      new Response(JSON.stringify({ erro: { codigo, mensagem: 'x' } }), { status: 404 });
    const ausente = criarClienteHttp({ ...semEspera, fetch: async () => corpo('nao_encontrado') });
    await expect(ausente.deal('AAAA1111')).rejects.toMatchObject({
      tipo: 'http',
      extra: { status: 404, codigo: 'nao_encontrado' },
    });
    const inexistente = criarClienteHttp({
      ...semEspera,
      fetch: async () => corpo('deal_nao_encontrado'),
    });
    await expect(inexistente.deal('AAAA1111')).resolves.toBeNull();
  });
});

describe('clienteResiliente: ordem das chamadas e 5xx', () => {
  const local = () => clienteFalso({ resumo: async () => ({ ...resumo, checksum: 'local' }) });

  it('erro 500 responde pelo modo local', async () => {
    const http = httpFalso();
    http.resumo = () => Promise.reject(new ErroCliente('http', '500', { status: 500 }));
    const c = criarClienteResiliente(http, local());
    await expect(c.resumo()).resolves.toMatchObject({ checksum: 'local' });
    expect(c.modo()).toBe('local');
  });

  it('um sucesso atrasado, de antes da queda, não volta o modo para api', async () => {
    const lenta = adiado<typeof resumo>();
    let chamada = 0;
    const http = httpFalso();
    http.resumo = () => (++chamada === 1 ? lenta.promessa : Promise.reject(rede()));
    const c = criarClienteResiliente(http, local());
    const primeira = c.resumo();
    await expect(c.resumo()).resolves.toMatchObject({ checksum: 'local' });
    expect(c.modo()).toBe('local');
    lenta.resolver(resumo);
    await primeira;
    expect(c.modo()).toBe('local');
  });
});

describe('rotas', () => {
  it('um "%" malformado no link do negócio não derruba o app', () => {
    expect(lerRota('#/deal/%E0%A4%A')).toMatchObject({ nome: 'nao-encontrada' });
  });
});
