import { describe, expect, it } from 'vitest';
import { ErroCliente } from './erros';
import { comRetry, esperaComJitter, RETRY_PADRAO } from './retry';

const transitorio = () => new ErroCliente('http', '503', { status: 503 });

describe('esperaComJitter', () => {
  it('fica entre 0 e min(teto, base · 2ⁿ)', () => {
    const quaseUm = () => 0.999999;
    expect(esperaComJitter(0, RETRY_PADRAO, quaseUm)).toBe(199);
    expect(esperaComJitter(1, RETRY_PADRAO, quaseUm)).toBe(399);
    expect(esperaComJitter(3, RETRY_PADRAO, quaseUm)).toBe(1599);
    expect(esperaComJitter(10, RETRY_PADRAO, quaseUm)).toBe(1999); // teto de 2 s
    expect(esperaComJitter(5, RETRY_PADRAO, () => 0)).toBe(0); // full jitter começa em zero
  });
});

describe('comRetry', () => {
  it('repete erro transitório até 3 tentativas e devolve o sucesso', async () => {
    let chamadas = 0;
    const esperas: number[] = [];
    const v = await comRetry(
      async () => {
        chamadas++;
        if (chamadas < 3) throw transitorio();
        return 'ok';
      },
      { idempotente: true, dormir: async (ms) => void esperas.push(ms), aleatorio: () => 0.5 },
    );
    expect(v).toBe('ok');
    expect(chamadas).toBe(3);
    expect(esperas).toEqual([100, 200]);
  });

  it('desiste depois da terceira tentativa', async () => {
    let chamadas = 0;
    await expect(
      comRetry(
        async () => {
          chamadas++;
          throw transitorio();
        },
        { idempotente: true, dormir: async () => {} },
      ),
    ).rejects.toMatchObject({ tipo: 'http' });
    expect(chamadas).toBe(3);
  });

  it('nunca repete erro de entrada (4xx)', async () => {
    let chamadas = 0;
    await expect(
      comRetry(
        async () => {
          chamadas++;
          throw new ErroCliente('http', '400', { status: 400, codigo: 'entrada_invalida' });
        },
        { idempotente: true, dormir: async () => {} },
      ),
    ).rejects.toBeInstanceOf(ErroCliente);
    expect(chamadas).toBe(1);
  });

  it('nunca repete operação que não é idempotente', async () => {
    let chamadas = 0;
    await expect(
      comRetry(
        async () => {
          chamadas++;
          throw transitorio();
        },
        { idempotente: false, dormir: async () => {} },
      ),
    ).rejects.toBeInstanceOf(ErroCliente);
    expect(chamadas).toBe(1);
  });

  it('respeita o Retry-After do 429 quando cabe no teto', async () => {
    const esperas: number[] = [];
    let chamadas = 0;
    await comRetry(
      async () => {
        if (chamadas++ === 0)
          throw new ErroCliente('http', '429', { status: 429, retryAfterMs: 1000 });
        return 1;
      },
      { idempotente: true, dormir: async (ms) => void esperas.push(ms), aleatorio: () => 0 },
    );
    expect(esperas).toEqual([1000]);
  });

  it('desiste na hora se o Retry-After passa do teto', async () => {
    let chamadas = 0;
    await expect(
      comRetry(
        async () => {
          chamadas++;
          throw new ErroCliente('http', '429', { status: 429, retryAfterMs: 30_000 });
        },
        { idempotente: true, dormir: async () => {} },
      ),
    ).rejects.toMatchObject({ extra: { status: 429 } });
    expect(chamadas).toBe(1);
  });

  it('trata rede e timeout como transitórios', () => {
    expect(new ErroCliente('rede', 'x').transitorio).toBe(true);
    expect(new ErroCliente('timeout', 'x').transitorio).toBe(true);
    expect(new ErroCliente('http', 'x', { status: 502 }).transitorio).toBe(true);
    expect(new ErroCliente('http', 'x', { status: 504 }).transitorio).toBe(true);
    expect(new ErroCliente('http', 'x', { status: 500 }).transitorio).toBe(false);
    expect(new ErroCliente('http', 'x', { status: 404 }).transitorio).toBe(false);
    expect(new ErroCliente('circuito_aberto', 'x').transitorio).toBe(false);
  });
});
