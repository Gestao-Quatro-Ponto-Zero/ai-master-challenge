/**
 * Rotas do contexto `qualificacao`: o método em uso e as respostas e decisões do vendedor,
 * guardadas no armazém do servidor (o banco compartilhado ou a memória do processo). A regra
 * (motivo obrigatório ao contestar, lote sem repetição) é do domínio; aqui só se confere que o
 * negócio existe, se grava e se devolve o estado atual.
 */
import { Hono } from 'hono';
import type { ServicosLeadScorer } from '@lead-scorer/dominio/aplicacao';
import { filtroSchema, type Filtro } from '@lead-scorer/dominio/organizacao';
import type { Deal } from '@lead-scorer/dominio/pipeline';
import {
  decidir,
  decidirEmLote,
  montarRegistros,
  pedidoDecidirLoteSchema,
  pedidoDecidirSchema,
  pedidoResponderSchema,
  ROTA_DECIDIR,
  ROTA_DECIDIR_LOTE,
  ROTA_METODO,
  ROTA_REGISTROS,
  ROTA_RESPONDER,
  type LinhaDecisao,
  type RespostaLote,
  type RespostaRegistros,
  type RespostasDoDeal,
} from '@lead-scorer/dominio/qualificacao';
import { erroDoDominio, ErroHttp, lerJson, validar } from '../infra/erros';
import type { ArmazemRegistros } from './armazem';

/** O que as rotas de gravação precisam além dos serviços. */
export interface DepsRegistros {
  armazem: ArmazemRegistros;
  /** ISO 8601 de agora (a data de cada resposta e decisão é do servidor). */
  agoraIso: () => string;
}

function dealOu404(servicos: ServicosLeadScorer, id: string): Deal {
  const deal = servicos.deal(id);
  if (!deal)
    throw new ErroHttp(404, {
      codigo: 'deal_nao_encontrado',
      mensagem: 'Nenhum negócio com esse id.',
    });
  return deal;
}

/**
 * `GET /api/qualificacao/metodo`; `GET /api/qualificacao/registros`; `POST
 * /api/qualificacao/responder`, `/decidir` e `/decidir-lote`.
 */
export function rotasQualificacao(servicos: ServicosLeadScorer, deps: DepsRegistros): Hono {
  const app = new Hono();
  const { armazem, agoraIso } = deps;

  async function registrosDe(ids: ReadonlySet<string> | null): Promise<RespostasDoDeal[]> {
    const linhas = await armazem.listar();
    const doFiltro = <T extends { dealId: string }>(l: T[]) =>
      ids === null ? l : l.filter((x) => ids.has(x.dealId));
    return montarRegistros(
      doFiltro(linhas.respostas),
      doFiltro(linhas.decisoes),
      servicos.metodo().id,
    );
  }

  async function registroDe(dealId: string): Promise<RespostasDoDeal | null> {
    const [r] = await registrosDe(new Set([dealId]));
    return r ?? null;
  }

  app.get(ROTA_METODO, (c) => c.json(servicos.metodo()));

  app.get(ROTA_REGISTROS, async (c) => {
    const filtro = validar(filtroSchema, c.req.query());
    const semFiltro = !filtro.vendedor && !filtro.manager && !filtro.regiao;
    const registros = await registrosDe(semFiltro ? null : idsDoFiltro(servicos, filtro));
    // o tipo é lido depois da consulta: se o banco falhou agora, a resposta já diz "memoria"
    const corpo: RespostaRegistros = { armazenamento: armazem.tipo(), registros };
    return c.json(corpo);
  });

  app.post(ROTA_RESPONDER, async (c) => {
    const pedido = validar(pedidoResponderSchema, await lerJson(c));
    const deal = dealOu404(servicos, pedido.dealId);
    if (!servicos.metodo().perguntas.some((p) => p.id === pedido.perguntaId)) {
      throw new ErroHttp(400, {
        codigo: 'pergunta_inexistente',
        mensagem: 'Essa pergunta não existe no método em uso.',
      });
    }
    await armazem.gravarResposta({
      dealId: deal.id,
      vendedor: deal.vendedor,
      perguntaId: pedido.perguntaId,
      valor: pedido.valor,
      em: agoraIso(),
    });
    return c.json(await registroDe(deal.id));
  });

  app.post(ROTA_DECIDIR, async (c) => {
    const pedido = validar(pedidoDecidirSchema, await lerJson(c));
    const deal = dealOu404(servicos, pedido.dealId);
    const r = decidir(null, deal.id, servicos.metodo(), pedido, agoraIso());
    if (!r.ok) throw erroDoDominio(r.erro);
    const decisao = r.valor.decisao;
    if (decisao)
      await armazem.gravarDecisoes([{ dealId: deal.id, vendedor: deal.vendedor, ...decisao }]);
    return c.json(await registroDe(deal.id));
  });

  app.post(ROTA_DECIDIR_LOTE, async (c) => {
    const pedido = validar(pedidoDecidirLoteSchema, await lerJson(c));
    const deals = pedido.dealIds.map((id) => dealOu404(servicos, id));
    const r = decidirEmLote(() => null, pedido.dealIds, servicos.metodo(), pedido, agoraIso());
    if (!r.ok) throw erroDoDominio(r.erro);
    const linhas: LinhaDecisao[] = r.valor.flatMap((reg, i) =>
      reg.decisao
        ? [{ dealId: reg.dealId, vendedor: deals[i]?.vendedor ?? '', ...reg.decisao }]
        : [],
    );
    await armazem.gravarDecisoes(linhas);
    const corpo: RespostaLote = {
      armazenamento: armazem.tipo(),
      registros: linhas.length,
      em: linhas[0]?.em ?? agoraIso(),
    };
    return c.json(corpo);
  });

  return app;
}

/** Os ids dos negócios (abertos ou não) que entram no filtro. */
function idsDoFiltro(servicos: ServicosLeadScorer, filtro: Filtro): Set<string> {
  const ids = new Set<string>();
  let deslocamento = 0;
  for (;;) {
    const pagina = servicos.deals({ ...filtro, limite: 2500, deslocamento });
    for (const d of pagina.deals) ids.add(d.id);
    deslocamento += pagina.deals.length;
    if (pagina.deals.length === 0 || deslocamento >= pagina.total) return ids;
  }
}
