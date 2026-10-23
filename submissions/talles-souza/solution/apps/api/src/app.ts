/**
 * A API do Lead Scorer: fronteira HTTP fina sobre `@lead-scorer/dominio`. Toda regra está no
 * domínio; aqui só se valida a entrada, se protege a dependência (o cálculo) e se traduz o
 * resultado em HTTP. Tudo é injetável, então os testes chamam `app.request(...)` sem rede.
 *
 * Ordem das proteções em `/api/*`: log → cabeçalhos → CORS → rate limit → limite de payload →
 * timeout → rota. CORS vem antes do rate limit para que o navegador consiga ler o 429.
 */
import { Hono, type Context } from 'hono';
import { bodyLimit } from 'hono/body-limit';
import type { ServicosLeadScorer } from '@lead-scorer/dominio/aplicacao';
import { ipDoSocket, type ConfigApi } from './infra/config';
import { ErroHttp, responderErro } from './infra/erros';
import { criarLimitador, limiteDeTaxa } from './infra/limite-taxa';
import { cabecalhosDeSeguranca, corsRestrito, hostPermitido } from './infra/seguranca';
import { logDeRequisicao, tempoLimite } from './infra/tempo';
import { montarWeb } from './infra/web';
import { rotasOrganizacao } from './organizacao';
import { rotasPipeline } from './pipeline';
import { rotasPriorizacao } from './priorizacao';
import { criarArmazemEmMemoria, rotasQualificacao, type ArmazemRegistros } from './qualificacao';
import { rotasSaude, type InfoSaude } from './saude';
import { rotasScore } from './score';

/** Dependências do app. Só `servicos`, `saude` e `config` são obrigatórias. */
export interface DepsApp {
  /** Os casos de uso do domínio (reais ou falsos, nos testes). */
  servicos: ServicosLeadScorer;
  /** O que `GET /health` informa. */
  saude: InfoSaude;
  config: ConfigApi;
  /** Relógio em ms (rate limit e duração no log). Padrão: `Date.now`. */
  relogio?: () => number;
  /** Chave do rate limit. Padrão: IP do socket (`ipDoSocket`). */
  ipDe?: (c: Context) => string;
  /** Saída do log de requisição. Padrão: `console.log`. */
  log?: (linha: string) => void;
  /** Pasta da web construída; ausente = só API. */
  web?: { raiz: string };
  /** Onde as respostas e decisões ficam. Padrão: memória do processo (sem banco). */
  registros?: ArmazemRegistros;
}

/** Monta o app Hono com as proteções e as rotas de todos os contextos. */
export function criarApp(deps: DepsApp): Hono {
  const relogio = deps.relogio ?? Date.now;
  const log = deps.log ?? ((linha: string) => console.log(linha));
  const { config } = deps;
  const app = new Hono();

  app.use('*', logDeRequisicao(log, relogio));
  app.use('*', cabecalhosDeSeguranca());
  if (config.hostsPermitidos) app.use('*', hostPermitido(config.hostsPermitidos));
  const cors = corsRestrito(config.corsOrigens);
  app.use('/health', cors);
  app.use('/api/*', cors);
  app.use(
    '/api/*',
    limiteDeTaxa(criarLimitador(config.limiteTaxa, relogio), deps.ipDe ?? ipDoSocket),
  );
  app.use(
    '/api/*',
    bodyLimit({
      maxSize: config.payloadMaxBytes,
      onError: (c) =>
        responderErro(c, 413, {
          codigo: 'payload_grande',
          mensagem: 'O corpo passou de ' + config.payloadMaxBytes + ' bytes.',
        }),
    }),
  );
  app.use('/api/*', tempoLimite(config.tempoLimiteMs));

  app.route('/', rotasSaude(deps.saude));
  app.route('/', rotasPipeline(deps.servicos));
  app.route('/', rotasOrganizacao(deps.servicos));
  const armazem = deps.registros ?? criarArmazemEmMemoria();
  const agoraIso = () => new Date(relogio()).toISOString();
  app.route('/', rotasQualificacao(deps.servicos, { armazem, agoraIso }));
  app.route('/', rotasScore(deps.servicos));
  app.route('/', rotasPriorizacao(deps.servicos));
  if (deps.web) montarWeb(app, deps.web.raiz);

  app.notFound((c) =>
    responderErro(c, 404, { codigo: 'nao_encontrado', mensagem: 'Rota inexistente.' }),
  );
  app.onError((err, c) => {
    if (err instanceof ErroHttp) return responderErro(c, err.status, err.erro);
    log(
      'erro interno em ' +
        c.req.method +
        ' ' +
        c.req.path +
        ': ' +
        // sem quebra de linha nem texto longo: a mensagem pode carregar parte da entrada
        (err instanceof Error ? err.message : String(err)).replace(/[\r\n]+/g, ' ').slice(0, 200),
    );
    return responderErro(c, 500, {
      codigo: 'erro_interno',
      mensagem: 'Erro interno. Tente de novo.',
    });
  });
  return app;
}
