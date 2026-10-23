import { describe, expect, it } from 'vitest';
import { criarDisjuntor } from './disjuntor';
import { ErroCliente } from './erros';

const falhar = () => Promise.reject(new ErroCliente('rede', 'caiu'));
const passar = () => Promise.resolve('ok');

function relogio() {
  let t = 1_000;
  return { agora: () => t, andar: (ms: number) => void (t += ms) };
}

describe('disjuntor', () => {
  it('abre depois de 3 falhas transitórias seguidas e recusa sem chamar', async () => {
    const r = relogio();
    const d = criarDisjuntor(undefined, r.agora);
    for (let i = 0; i < 3; i++)
      await expect(d.executar(falhar)).rejects.toMatchObject({ tipo: 'rede' });
    expect(d.estado()).toBe('aberto');
    let chamou = false;
    await expect(
      d.executar(async () => {
        chamou = true;
        return 1;
      }),
    ).rejects.toMatchObject({ tipo: 'circuito_aberto' });
    expect(chamou).toBe(false);
  });

  it('um sucesso no meio zera a contagem', async () => {
    const d = criarDisjuntor(undefined, relogio().agora);
    await expect(d.executar(falhar)).rejects.toBeDefined();
    await expect(d.executar(falhar)).rejects.toBeDefined();
    await d.executar(passar);
    await expect(d.executar(falhar)).rejects.toBeDefined();
    expect(d.estado()).toBe('fechado');
  });

  it('erro de entrada não conta como falha', async () => {
    const d = criarDisjuntor(undefined, relogio().agora);
    const entrada = () => Promise.reject(new ErroCliente('http', '400', { status: 400 }));
    for (let i = 0; i < 5; i++) await expect(d.executar(entrada)).rejects.toBeDefined();
    expect(d.estado()).toBe('fechado');
  });

  it('depois de 15 s deixa 1 sonda: sucesso fecha', async () => {
    const r = relogio();
    const d = criarDisjuntor(undefined, r.agora);
    for (let i = 0; i < 3; i++) await expect(d.executar(falhar)).rejects.toBeDefined();
    r.andar(14_999);
    expect(d.estado()).toBe('aberto');
    r.andar(1);
    expect(d.estado()).toBe('meio_aberto');
    await expect(d.executar(passar)).resolves.toBe('ok');
    expect(d.estado()).toBe('fechado');
  });

  it('a sonda que falha reabre por mais 15 s', async () => {
    const r = relogio();
    const d = criarDisjuntor(undefined, r.agora);
    for (let i = 0; i < 3; i++) await expect(d.executar(falhar)).rejects.toBeDefined();
    r.andar(15_000);
    await expect(d.executar(falhar)).rejects.toMatchObject({ tipo: 'rede' });
    expect(d.estado()).toBe('aberto');
    r.andar(10_000);
    expect(d.estado()).toBe('aberto');
    r.andar(5_000);
    expect(d.estado()).toBe('meio_aberto');
  });

  it('no meio-aberto só passa uma sonda por vez', async () => {
    const r = relogio();
    const d = criarDisjuntor(undefined, r.agora);
    for (let i = 0; i < 3; i++) await expect(d.executar(falhar)).rejects.toBeDefined();
    r.andar(15_000);
    let soltar: (v: string) => void = () => {};
    const sonda = d.executar(() => new Promise<string>((res) => (soltar = res)));
    await expect(d.executar(passar)).rejects.toMatchObject({ tipo: 'circuito_aberto' });
    soltar('ok');
    await expect(sonda).resolves.toBe('ok');
    expect(d.estado()).toBe('fechado');
  });
});
