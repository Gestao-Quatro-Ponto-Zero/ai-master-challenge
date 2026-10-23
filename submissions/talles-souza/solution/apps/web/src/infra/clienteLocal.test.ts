// O modo local com o deals.json real: confere o checksum, valida e responde igual ao domínio direto.
import { criarServicos } from '@lead-scorer/dominio/aplicacao';
import { conferirChecksum, lerPipeline } from '@lead-scorer/dominio/pipeline';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { criarClienteLocal } from './clienteLocal';

// caminho, não URL: no ambiente jsdom o `URL` global é o do jsdom e o node:fs não o aceita
const PASTA = join(dirname(fileURLToPath(import.meta.url)), '../../../../data');
const bytes = new Uint8Array(readFileSync(join(PASTA, 'deals.json')));
const sha = readFileSync(join(PASTA, 'deals.json.sha256'), 'utf8');

function fetchDosArquivos(conteudo: Record<string, BodyInit>): typeof fetch {
  return async (url) => {
    const nome = String(url).split('/').pop() ?? '';
    const corpo = conteudo[nome];
    return corpo === undefined
      ? new Response('não achei', { status: 404 })
      : new Response(corpo, { status: 200 });
  };
}

describe('modo local com o dado real', () => {
  it('responde igual aos casos de uso do domínio', async () => {
    const local = criarClienteLocal({
      fetch: fetchDosArquivos({ 'deals.json': bytes, 'deals.json.sha256': sha }),
    });
    const conferido = await conferirChecksum(bytes, sha);
    const pipeline = lerPipeline(JSON.parse(new TextDecoder().decode(bytes)));
    if (!conferido.ok || !pipeline.ok) throw new Error('dado real inválido');
    const direto = criarServicos({ pipeline: pipeline.valor, checksum: conferido.valor });

    const resumo = await local.resumo();
    expect(resumo).toEqual(direto.resumo());
    expect(resumo.checksum).toMatch(/^[0-9a-f]{64}$/);

    const pedido = { filtro: {}, respostas: [] };
    const fila = await local.fila(pedido);
    expect(fila).toEqual(direto.fila(pedido));
    if (!fila.ok) throw new Error(fila.erro.mensagem);
    const c = fila.valor.contadores;
    expect(c.total).toBe(resumo.abertos);
    const porBloco = Object.values(c.porBloco).reduce((s, n) => s + n, 0);
    expect(porBloco).toBe(c.total);
  }, 30_000);

  it('recusa dado com checksum que não bate', async () => {
    const outro = 'f'.repeat(64) + '  deals.json\n';
    const local = criarClienteLocal({
      fetch: fetchDosArquivos({ 'deals.json': bytes, 'deals.json.sha256': outro }),
    });
    await expect(local.resumo()).rejects.toMatchObject({
      tipo: 'dados',
      extra: { codigo: 'checksum_divergente' },
    });
  });

  it('sem os arquivos, avisa que o modo local não tem dados', async () => {
    const local = criarClienteLocal({ fetch: fetchDosArquivos({}) });
    await expect(local.resumo()).rejects.toMatchObject({ tipo: 'dados' });
  });
});
