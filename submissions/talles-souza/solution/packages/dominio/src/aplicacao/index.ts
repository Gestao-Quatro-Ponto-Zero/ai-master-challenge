/**
 * Composição dos contextos (não é um contexto): os casos de uso que a API expõe e que a web
 * repete no modo local. Os dois lados chamam as mesmas funções, então o resultado é o mesmo.
 */
import { falha, ok, type Resultado } from '../compartilhado';
import { aplicarFiltro, filtrarTime, montarOrganizacao, type Organizacao } from '../organizacao';
import {
  criarDealDeLead,
  type ConsultaDeals,
  type Deal,
  type NovoLead,
  type Pipeline,
  type RespostaDeals,
  type RespostaResumo,
} from '../pipeline';
import {
  classificar,
  montarFila,
  montarPainel,
  politicaAtiva,
  posicionarNaTela,
  textosDaTela,
  type Fila,
  type ItemFila,
  type Painel,
  type PedidoFila,
  type PedidoItem,
  type PoliticaPriorizacao,
  type TextosPreenchidos,
} from '../priorizacao';
import {
  metodoAtivo,
  validarRespostas,
  type MetodoQualificacao,
  type RespostasDoDeal,
} from '../qualificacao';
import {
  avaliar,
  configMotorPadrao,
  medirChance,
  medirMotor,
  medirPontos,
  type Avaliacao,
  type ChanceHistorica,
  type ConfigMotor,
  type ContextoScore,
  type MotorDePontos,
  type PedidoAvaliacao,
  type RespostaAvaliacao,
  type TabelaDePontos,
} from '../score';

export * from './http';

/** Os casos de uso do Lead Scorer. */
export interface ServicosLeadScorer {
  resumo(): RespostaResumo;
  deals(consulta: ConsultaDeals): RespostaDeals;
  deal(id: string): Deal | null;
  organizacao(): Organizacao;
  metodo(): MetodoQualificacao;
  politica(): PoliticaPriorizacao;
  /** Os textos dos grupos e os avisos, já preenchidos com os limites da política e a janela. */
  textos(): TextosPreenchidos;
  /** A chance histórica por faixa de idade (replay), da qual sai o indicador de cada negócio. */
  chance(): ChanceHistorica;
  /** A tabela de pontos por atributo (Perfil × Interesse), medida no histórico. */
  pontos(): TabelaDePontos;
  /** O motor de pontos: os fatores testados, o AUC na validação, os escolhidos e os pontos. */
  motor(): MotorDePontos;
  /** Os fatos explicados (idade, o que está em jogo, contexto). Erros: `deal_nao_encontrado`, `lead_invalido`. */
  avaliar(pedido: PedidoAvaliacao): Resultado<RespostaAvaliacao>;
  /** Um deal ou lead classificado em bloco. Erros: os de `avaliar` e `respostas_invalidas`. */
  item(pedido: PedidoItem): Resultado<ItemFila>;
  /** A segunda-feira do filtro. Erro: `respostas_invalidas`. */
  fila(pedido: PedidoFila): Resultado<Fila>;
  /** O painel "Acompanhar a equipe" do filtro (4 métricas e a linha de cada vendedor, só leitura). Erro: o da `fila`. */
  painel(pedido: PedidoFila): Resultado<Painel>;
}

/** O que `criarServicos` precisa: o pipeline validado e, se quiser, outro método ou política. */
export interface OpcoesServicos {
  pipeline: Pipeline;
  /** SHA-256 conferido do arquivo de origem. */
  checksum: string;
  /** Padrão: `metodoAtivo`. */
  metodo?: MetodoQualificacao;
  /** Padrão: `politicaAtiva`. */
  politica?: PoliticaPriorizacao;
  /** Padrão: `configMotorPadrao`. */
  configMotor?: ConfigMotor;
}

/**
 * Põe em cada avaliação a posição na lista aberta do vendedor dela (por onde começar), na ordem em
 * que a tela dele mostra os negócios: o grupo, depois o que há a ganhar. A lista é a do vendedor
 * do negócio, qualquer que seja o filtro da tela.
 */
function posicionarPorVendedor(
  abertos: readonly Deal[],
  avaliacoes: Map<string, Avaliacao>,
  classificarSem: (d: Deal, a: Avaliacao) => ItemFila,
): void {
  const listas = new Map<string, ItemFila[]>();
  for (const d of abertos) {
    const a = avaliacoes.get(d.id);
    if (!a) continue;
    listas.set(d.vendedor, [...(listas.get(d.vendedor) ?? []), classificarSem(d, a)]);
  }
  for (const lista of listas.values()) {
    const posicoes = posicionarNaTela(lista);
    for (const { avaliacao: a } of lista)
      avaliacoes.set(a.dealId, { ...a, posicao: posicoes.get(a.dealId) ?? null });
  }
}

/**
 * Conta, por vendedor, quantos abertos a tela dele mostra em cada grupo (sem respostas: nenhuma resposta muda o
 * grupo). Roda uma vez, na carga; o seletor lê daqui, sem consulta nova ao banco.
 */
function comGrupos(organizacao: Organizacao, itens: readonly ItemFila[]): Organizacao {
  const porVendedor = new Map<string, ItemFila[]>();
  for (const i of itens)
    porVendedor.set(i.deal.vendedor, [...(porVendedor.get(i.deal.vendedor) ?? []), i]);
  // a contagem é a da tela do vendedor: com o Foque vazio, o Siga dele aparece no Foque
  return {
    ...organizacao,
    vendedores: organizacao.vendedores.map((v) => ({
      ...v,
      grupos: montarFila(porVendedor.get(v.nome) ?? []).contadores.porBloco,
    })),
  };
}

/**
 * Monta os casos de uso sobre um pipeline já validado. A chance histórica (replay), a tabela de
 * pontos, o motor de pontos, as avaliações dos deals abertos e a posição de cada um na lista do
 * vendedor são calculados uma vez, na montagem; a fila só classifica.
 */
export function criarServicos(opcoes: OpcoesServicos): ServicosLeadScorer {
  const { pipeline, checksum } = opcoes;
  const metodo = opcoes.metodo ?? metodoAtivo;
  const politica = opcoes.politica ?? politicaAtiva;
  const chance = medirChance(pipeline.deals, pipeline.referencia, politica.chance);
  const pontos = medirPontos(pipeline.deals, chance);
  // as faixas de idade do motor são as da chance, para a idade falar a mesma língua nos dois
  const pontuador = medirMotor(
    pipeline.deals,
    pipeline.referencia,
    politica.chance.faixas,
    opcoes.configMotor ?? configMotorPadrao,
  );
  const textos = textosDaTela(politica, pipeline.janela);
  const contexto: ContextoScore = {
    janela: pipeline.janela,
    catalogo: pipeline.catalogo,
    contas: pipeline.contas,
    chance,
    pontuador,
  };
  const porId = new Map(pipeline.deals.map((d) => [d.id, d]));
  const avaliacoes = new Map<string, Avaliacao>(
    pipeline.abertos.map((d) => [d.id, avaliar(d, contexto)]),
  );
  // o grupo vem da idade, que nenhuma resposta muda: classificar sem respostas basta para a ordem
  const classificarSem = (d: Deal, a: Avaliacao) => classificar(d, a, politica, metodo, null);
  posicionarPorVendedor(pipeline.abertos, avaliacoes, classificarSem);
  const organizacao = comGrupos(
    montarOrganizacao(pipeline.time, pipeline.deals),
    pipeline.abertos.map((d) =>
      classificar(d, avaliacoes.get(d.id) ?? avaliar(d, contexto), politica, metodo, null),
    ),
  );

  /**
   * A avaliação de um deal aberto já vem com a posição. Um lead novo entra na lista do vendedor
   * dele só para medir a posição (a lista guardada não muda); um negócio fechado fica sem posição.
   */
  function avaliacaoDe(deal: Deal): Avaliacao {
    const pronta = avaliacoes.get(deal.id);
    if (pronta) return pronta;
    const avaliacao = avaliar(deal, contexto);
    if (!deal.aberto) return avaliacao;
    const lista = pipeline.abertos
      .filter((d) => d.vendedor === deal.vendedor)
      .flatMap((d) => {
        const a = avaliacoes.get(d.id);
        return a ? [classificarSem(d, a)] : [];
      })
      .concat(classificarSem(deal, avaliacao));
    return { ...avaliacao, posicao: posicionarNaTela(lista).get(deal.id) ?? null };
  }

  function resolver(pedido: { dealId: string } | { lead: NovoLead }): Resultado<Deal> {
    if ('dealId' in pedido) {
      const deal = porId.get(pedido.dealId);
      return deal
        ? ok(deal)
        : falha('deal_nao_encontrado', 'Deal não encontrado: ' + pedido.dealId + '.');
    }
    return criarDealDeLead(pedido.lead, pipeline);
  }

  function conferirRespostas(bruto: unknown): Resultado<RespostasDoDeal> {
    const lido = validarRespostas(bruto);
    if (!lido.ok) return lido;
    if (lido.valor.metodoId !== metodo.id) {
      return falha(
        'respostas_invalidas',
        'As respostas são do método ' +
          lido.valor.metodoId +
          '; o método ativo é ' +
          metodo.id +
          '.',
      );
    }
    return lido;
  }

  function fila(pedido: PedidoFila): Resultado<Fila> {
    const respostasPorDeal = new Map<string, RespostasDoDeal>();
    for (const bruto of pedido.respostas) {
      const lido = conferirRespostas(bruto);
      if (!lido.ok) return lido;
      respostasPorDeal.set(lido.valor.dealId, lido.valor);
    }
    const abertos = aplicarFiltro(pipeline.abertos, pedido.filtro);
    const itens = abertos.map((d) =>
      classificar(d, avaliacaoDe(d), politica, metodo, respostasPorDeal.get(d.id) ?? null),
    );
    return ok(montarFila(itens));
  }

  return {
    resumo: () => ({
      formato: pipeline.formato,
      referencia: pipeline.referencia,
      total: pipeline.deals.length,
      abertos: pipeline.abertos.length,
      janela: pipeline.janela,
      lacunas: pipeline.lacunas,
      catalogo: pipeline.catalogo,
      contas: pipeline.contas,
      checksum,
    }),

    deals: (consulta) => {
      const filtrados = aplicarFiltro(pipeline.deals, consulta).filter(
        (d) =>
          (consulta.estagio === undefined || d.estagio === consulta.estagio) &&
          (consulta.aberto === undefined || d.aberto === (consulta.aberto === 'true')),
      );
      return {
        total: filtrados.length,
        limite: consulta.limite,
        deslocamento: consulta.deslocamento,
        deals: filtrados.slice(consulta.deslocamento, consulta.deslocamento + consulta.limite),
      };
    },

    deal: (id) => porId.get(id) ?? null,
    organizacao: () => organizacao,
    metodo: () => metodo,
    politica: () => politica,
    textos: () => textos,
    chance: () => chance,
    pontos: () => pontos,
    motor: () => pontuador.motor,

    avaliar: (pedido) => {
      const deal = resolver(pedido);
      if (!deal.ok) return deal;
      return ok({ deal: deal.valor, avaliacao: avaliacaoDe(deal.valor) });
    },

    item: (pedido) => {
      const deal = resolver(pedido);
      if (!deal.ok) return deal;
      let respostas: RespostasDoDeal | null = null;
      if (pedido.respostas) {
        const lido = conferirRespostas(pedido.respostas);
        if (!lido.ok) return lido;
        if (lido.valor.dealId !== deal.valor.id) {
          return falha(
            'respostas_invalidas',
            'As respostas são do deal ' + lido.valor.dealId + ', não do ' + deal.valor.id + '.',
          );
        }
        respostas = lido.valor;
      }
      return ok(classificar(deal.valor, avaliacaoDe(deal.valor), politica, metodo, respostas));
    },

    fila,

    painel: (pedido) => {
      const f = fila(pedido);
      return f.ok
        ? ok(montarPainel(f.valor, filtrarTime(pipeline.time, pedido.filtro), metodo, politica))
        : f;
    },
  };
}
