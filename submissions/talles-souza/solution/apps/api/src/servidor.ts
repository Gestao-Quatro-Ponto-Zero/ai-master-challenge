/**
 * Ponto de entrada do `npm start`: carrega o dado com o checksum conferido, monta o app e sobe
 * em `127.0.0.1` (só esta máquina). Com a web construída, entrega app + API na mesma porta.
 *
 * Ambiente: `PORT` (8787), `HOST` (127.0.0.1), `DEALS_PATH` (padrão `solution/data/deals.json`),
 * `SERVIR_WEB` (pasta da web construída; padrão `apps/web/dist` se existir; `0` desliga), mais os
 * da borda em `infra/config.ts`. `DATABASE_URL` (opcional): o banco compartilhado das respostas e
 * decisões (e dos negócios, se o metadado dele conferir); sem ela, `deals.json` + memória.
 * Dado que não confere ou não segue o schema: não sobe (código 1).
 */
import { serve } from '@hono/node-server';
import { existsSync, readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { criarApp } from './app';
import { CAMINHO_PADRAO_DEALS, montarDependencias } from './carregador';
import { hostsDoServidor, ipDoSocket, lerConfig } from './infra/config';

const RAIZ_SOLUCAO = fileURLToPath(new URL('../../../', import.meta.url));

function sair(mensagem: string): never {
  console.error('A API não subiu: ' + mensagem);
  process.exit(1);
}

function pastaDaWeb(): string | null {
  const pedida = process.env['SERVIR_WEB'];
  if (pedida === '0') return null;
  const raiz =
    pedida !== undefined && pedida.trim() !== ''
      ? resolve(pedida)
      : join(RAIZ_SOLUCAO, 'apps/web/dist');
  return existsSync(join(raiz, 'index.html')) ? raiz : null;
}

async function principal(): Promise<void> {
  let config;
  try {
    config = lerConfig(process.env);
  } catch (e) {
    sair((e as Error).message);
  }
  const porta = Number(process.env['PORT'] ?? 8787);
  if (!Number.isInteger(porta) || porta < 1 || porta > 65535) {
    sair('PORT inválida: ' + String(process.env['PORT']));
  }
  config = { ...config, hostsPermitidos: hostsDoServidor(porta, config.corsOrigens) };
  const caminho = process.env['DEALS_PATH']
    ? resolve(process.env['DEALS_PATH'])
    : CAMINHO_PADRAO_DEALS;
  const carga = await montarDependencias(process.env, caminho, (linha) => console.warn(linha));
  if (!carga.ok) sair(carga.erro.codigo + ': ' + carga.erro.mensagem);

  const pacote = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8')) as {
    version: string;
  };
  const raizWeb = pastaDaWeb();
  const app = criarApp({
    servicos: carga.valor.servicos,
    registros: carga.valor.registros,
    saude: {
      versao: pacote.version,
      iniciadoEm: new Date().toISOString(),
      dados: carga.valor.dados,
    },
    config,
    ipDe: ipDoSocket,
    ...(raizWeb ? { web: { raiz: raizWeb } } : {}),
  });

  const host = process.env['HOST'] ?? '127.0.0.1';
  if (host !== '127.0.0.1' && host !== 'localhost' && host !== '::1') {
    console.warn('aviso: HOST=' + host + ' expõe a API fora desta máquina; não há login.');
  }
  const servidor = serve({ fetch: app.fetch, port: porta, hostname: host }, (info) => {
    console.log(
      'Lead Scorer em http://localhost:' +
        info.port +
        (raizWeb ? ' (app + API)' : ' (só API; rode o build da web para servir o app)'),
    );
    console.log(
      'dados: ' +
        carga.valor.dados.total +
        ' deals, referência ' +
        carga.valor.dados.referencia +
        ', sha256 ' +
        carga.valor.dados.checksum.slice(0, 12) +
        '… (' +
        (carga.valor.origem === 'banco' ? 'do banco compartilhado' : 'do deals.json') +
        '); respostas e decisões: ' +
        (carga.valor.registros.tipo() === 'banco'
          ? 'banco compartilhado'
          : 'memória deste processo (sem DATABASE_URL)'),
    );
  });

  const encerrar = (sinal: string): void => {
    console.log(sinal + ': encerrando');
    servidor.close(() => void carga.valor.fechar().finally(() => process.exit(0)));
    setTimeout(() => process.exit(0), 3_000).unref();
  };
  process.on('SIGINT', () => encerrar('SIGINT'));
  process.on('SIGTERM', () => encerrar('SIGTERM'));
}

principal().catch((e: unknown) => sair(e instanceof Error ? e.message : String(e)));
