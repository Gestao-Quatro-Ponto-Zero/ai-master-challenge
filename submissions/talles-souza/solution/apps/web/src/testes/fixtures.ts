/** Fixtures dos testes: deals, itens, base e um cliente falso com a mesma interface do real. */
import type { Organizacao, Perfil } from '@lead-scorer/dominio/organizacao';
import type { Deal, RespostaResumo } from '@lead-scorer/dominio/pipeline';
import {
  politicaProvisoria,
  textosDaTela,
  type Fila,
  type ItemFila,
} from '@lead-scorer/dominio/priorizacao';
import { metodoProvisorio, type Bloco } from '@lead-scorer/dominio/qualificacao';
import type { Avaliacao } from '@lead-scorer/dominio/score';
import type { Base, Dependencias } from '../app/contexto';
import {
  criarRepositorioNavegador,
  SEM_REGISTROS_REMOTOS,
  type ClienteResiliente,
  type Modo,
} from '../infra';

export function deal(over: Partial<Deal> = {}): Deal {
  return {
    id: 'AAAA0001',
    vendedor: 'Ana Vendas',
    manager: 'Marcos Gestor',
    regiao: 'West',
    produto: 'GTX Pro',
    serie: 'GTX',
    precoTabela: 4821,
    conta: 'Acme',
    setor: 'tecnologia',
    funcionarios: 4540,
    receitaConta: 1000,
    empresaMae: null,
    estagio: 'Engaging',
    dataEngajamento: '2017-11-01',
    dataFechamento: null,
    valorFechamento: null,
    aberto: true,
    idadeDias: 40,
    duracaoDias: null,
    lacunas: [],
    ...over,
  };
}

export function avaliacao(d: Deal, over: Partial<Avaliacao> = {}): Avaliacao {
  return {
    dealId: d.id,
    situacao: d.idadeDias === null ? 'prospeccao' : 'na_janela',
    idadeDias: d.idadeDias,
    emJogo: d.precoTabela,
    esperado: d.idadeDias === null ? null : 0.3 * d.precoTabela,
    score: null,
    qualidade: null,
    posicao: null,
    chance: null,
    fatos: [
      {
        id: 'idade',
        rotulo: 'Idade',
        valor: d.idadeDias,
        detalhe: 'aberto há ' + d.idadeDias + ' d',
      },
      {
        id: 'em_jogo',
        rotulo: 'Preço de tabela',
        valor: d.precoTabela,
        detalhe: d.produto + ': preço de tabela US$ 4.821',
      },
    ],
    contexto: [d.conta ? 'conta de 4.540 funcionários' : 'sem dado de conta'],
    explicacao: 'aberto há ' + d.idadeDias + ' d',
    referencia: '2017-12-31',
    maxJanelaDias: 138,
    ...over,
  };
}

export function item(
  bloco: Bloco,
  over: Partial<ItemFila> = {},
  dealOver: Partial<Deal> = {},
): ItemFila {
  const d = deal(dealOver);
  const semData = d.idadeDias === null;
  const blocoFinal: Bloco = semData ? 'sem_inicio' : bloco;
  const acao = politicaProvisoria.textos.grupos[blocoFinal].acao;
  return {
    deal: d,
    avaliacao: avaliacao(d),
    bloco: blocoFinal,
    faixa: semData ? 'Aborde primeiro' : '41 a 60 dias',
    indicador: {
      score: semData ? null : 80,
      qualidade: semData
        ? { score: null, base: null, temIdade: false, ajustes: [] }
        : { score: 80, base: 80, temIdade: true, ajustes: [] },
      emJogo: d.produto + ' · US$ 4.821 em jogo',
      porqueScore: [
        semData
          ? 'Responda as perguntas para pontuar.'
          : 'Aberto há ' +
            d.idadeDias +
            ' dias: 30% dos negócios com essa idade fecharam (a melhor faixa fecha 52%).',
        'Na sua lista: 3º de 11 (o grupo, depois o que há a ganhar).',
      ],
      posicao: { k: 3, n: 11 },
      posicaoTexto: 'Na sua lista: 3º de 11 (o grupo, depois o que há a ganhar).',
      chance: semData ? null : 0.3,
      chanceTexto: semData
        ? 'Chance de fechar em 3 meses: sem dado (ainda sem primeira conversa).'
        : 'Chance de fechar em 3 meses: 30%',
      parcelas: semData
        ? []
        : [
            {
              fator: 'idade',
              pontos: 3,
              noScore: true,
              texto: '+3 · Idade: 45 dias (41 a 50 dias)',
            },
            {
              fator: 'setor',
              pontos: 0,
              noScore: false,
              texto: 'Setor: 0 · não muda a chance no histórico',
            },
          ],
      taxa: semData ? null : 0.3,
      n: semData ? null : 120,
      faixa: semData ? null : '41 a 50 dias',
      numero: semData ? 'Score —' : 'Score 80',
      rotulo: 'se o negócio é bom: a idade e as suas respostas',
      motivo: semData
        ? 'Responda as perguntas para pontuar.'
        : 'Aberto há ' +
          d.idadeDias +
          ' dias: 30% dos negócios com essa idade fecharam (a melhor faixa fecha 52%).',
      porque: semData
        ? 'Ainda sem primeira conversa. US$ 4.821 em jogo: comece por este.'
        : 'Aberto há ' + d.idadeDias + ' dias. Nessa idade, só 30% fecharam.',
      receita: semData
        ? 'Sem data de início: não dá pra estimar.'
        : 'Deve render cerca de US$ 1.446 em 3 meses (estimativa pela chance).',
      preco: 'Preço de tabela: US$ 4.821',
    },
    pendentes: [],
    respostas: [],
    proximaAcao: {
      tipo: semData
        ? 'qualificar'
        : bloco === 'nutricao'
          ? 'encaminhar_para_nutricao'
          : bloco === 'foque_agora'
            ? 'avancar_hoje'
            : 'manter_ritmo',
      texto: acao,
      perguntaId: null,
    },
    decisao: null,
    porque: 'Aberto há ' + d.idadeDias + ' dias.',
    ...over,
  };
}

export function fila(blocos: Partial<Record<Bloco, ItemFila[]>>, promovidos = 0): Fila {
  const b: Record<Bloco, ItemFila[]> = {
    foque_agora: blocos.foque_agora ?? [],
    siga_no_ritmo: blocos.siga_no_ritmo ?? [],
    nutricao: blocos.nutricao ?? [],
    sem_inicio: blocos.sem_inicio ?? [],
  };
  return {
    blocos: b,
    promovidos,
    contadores: {
      total: Object.values(b).flat().length,
      porBloco: {
        foque_agora: b.foque_agora.length,
        siga_no_ritmo: b.siga_no_ritmo.length,
        nutricao: b.nutricao.length,
        sem_inicio: b.sem_inicio.length,
      },
      alemDaJanela: 0,
    },
    receita: {
      total: Object.values(b)
        .flat()
        .reduce((s, i) => s + (i.avaliacao.esperado ?? 0), 0),
      semEstimativa: b.sem_inicio.length,
    },
  };
}

export const organizacao: Organizacao = {
  vendedores: [
    {
      nome: 'Ana Vendas',
      manager: 'Marcos Gestor',
      regiao: 'West',
      abertos: 4,
      grupos: { foque_agora: 1, siga_no_ritmo: 1, nutricao: 1, sem_inicio: 1 },
    },
    {
      nome: 'Bruno Campo',
      manager: 'Marcos Gestor',
      regiao: 'West',
      abertos: 2,
      grupos: { foque_agora: 2, siga_no_ritmo: 0, nutricao: 0, sem_inicio: 0 },
    },
  ],
  managers: [{ nome: 'Marcos Gestor', regiao: 'West', vendedores: ['Ana Vendas', 'Bruno Campo'] }],
  regioes: ['West'],
};

export const resumo: RespostaResumo = {
  formato: 2,
  referencia: '2017-12-31',
  total: 10,
  abertos: 6,
  janela: { referencia: '2017-12-31', ganhos: 4, p50Dias: 57, p95Dias: 116, maxDias: 138 },
  lacunas: { sem_conta: 1, sem_engage_date: 1, produto_normalizado: 0, setor_normalizado: 0 },
  catalogo: [{ nome: 'GTX Pro', serie: 'GTX', precoTabela: 4821 }],
  contas: [
    { nome: 'Acme', setor: 'tecnologia', funcionarios: 4540, receita: 1000, empresaMae: null },
  ],
  checksum: 'abc',
};

export const base: Base = {
  politica: politicaProvisoria,
  metodo: metodoProvisorio,
  organizacao,
  resumo,
  textos: textosDaTela(politicaProvisoria, resumo.janela),
};

type Ops = Omit<ClienteResiliente, 'modo' | 'assinar' | 'sondar'>;

/** Cliente falso: cada operação pode ser trocada; o padrão devolve a base e uma fila vazia. */
export function clienteFalso(over: Partial<Ops> = {}, modo: Modo = 'api'): ClienteResiliente {
  const nao = () => Promise.reject(new Error('não usado no teste'));
  return {
    modo: () => modo,
    assinar: () => () => {},
    sondar: async () => modo,
    resumo: async () => resumo,
    deals: nao,
    deal: nao,
    organizacao: async () => organizacao,
    metodo: async () => metodoProvisorio,
    politica: async () => politicaProvisoria,
    textos: async () => base.textos,
    chance: nao,
    pontos: nao,
    motor: nao,
    avaliar: nao,
    item: nao,
    fila: async () => ({ ok: true, valor: fila({}) }),
    painel: nao,
    ...over,
  };
}

/** Dependências de teste; por padrão o vendedor já escolheu quem é ("Ana Vendas"). */
export function dependencias(
  cliente: ClienteResiliente,
  perfilGuardado: Perfil | null = { tipo: 'vendedor', nome: 'Ana Vendas' },
): Dependencias {
  let perfil = perfilGuardado;
  return {
    cliente,
    repositorio: criarRepositorioNavegador(null),
    registros: SEM_REGISTROS_REMOTOS,
    agoraIso: () => '2026-10-22T12:00:00.000Z',
    perfil: {
      ler: () => perfil,
      salvar: (p) => {
        perfil = p;
      },
    },
    comissao: comissaoEmMemoria(),
  };
}

/** Comissão guardada em memória (o padrão dos testes: começa vazia). */
export function comissaoEmMemoria(inicial: number | null = null): Dependencias['comissao'] {
  let atual = inicial;
  return {
    ler: () => atual,
    salvar: (p) => {
      atual = p;
    },
  };
}
