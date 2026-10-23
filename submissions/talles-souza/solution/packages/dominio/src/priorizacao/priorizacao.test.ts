import { describe, expect, it } from 'vitest';
import type { Deal, Janela } from '../pipeline';
import { metodoAtivo, responder, type RespostasDoDeal } from '../qualificacao';
import { qualidadeDoDado, type Avaliacao, type ParcelaDoScore } from '../score';
import {
  classificar,
  emPorcento,
  GRUPOS,
  montarFila,
  politicaAtiva,
  politicaProvisoria,
  posicionarNaTela,
  preencher,
  textosDaTela,
  validarPolitica,
  type PoliticaPriorizacao,
} from './index';

const AGORA = '2017-12-31T12:00:00Z';
const janela: Janela = {
  referencia: '2017-12-31',
  ganhos: 100,
  p50Dias: 57,
  p95Dias: 116,
  maxDias: 138,
};

function caso(id: string, idadeDias: number | null, emJogo = 1000, taxa: number | null = 0.5) {
  const deal = { id, produto: 'GTX Pro', idadeDias } as Deal;
  const avaliacao: Avaliacao = {
    dealId: id,
    situacao: idadeDias === null ? 'prospeccao' : idadeDias > 138 ? 'alem_da_janela' : 'na_janela',
    idadeDias,
    emJogo,
    esperado: idadeDias === null || taxa === null ? null : taxa * emJogo,
    score: null,
    // a melhor faixa do caso fecha 50%: taxa 0,5 = parte do dado 100
    qualidade:
      idadeDias === null || taxa === null
        ? null
        : qualidadeDoDado(taxa, [0.5, taxa], { taxa, faixas: [0.5, taxa] }),
    posicao: null,
    chance: idadeDias === null ? null : { faixa: 'x', taxa, n: 100 },
    fatos: [],
    contexto: [],
    explicacao: '',
    referencia: '2017-12-31',
    maxJanelaDias: 138,
  };
  return { deal, avaliacao };
}

function classificarCaso(
  id: string,
  idade: number | null,
  respostas: RespostasDoDeal | null = null,
  emJogo = 1000,
) {
  const { deal, avaliacao } = caso(id, idade, emJogo);
  return classificar(deal, avaliacao, politicaAtiva, metodoAtivo, respostas);
}

function respostasDe(id: string, pares: [string, 'sim' | 'nao'][]): RespostasDoDeal {
  let atual: RespostasDoDeal | null = null;
  for (const [pergunta, valor] of pares) {
    const r = responder(atual, id, metodoAtivo, pergunta, valor, AGORA);
    if (!r.ok) throw new Error(r.erro.mensagem);
    atual = r.valor;
  }
  if (!atual) throw new Error('sem respostas');
  return atual;
}

describe('validarPolitica', () => {
  it('a política em uso passa, com Siga até 40, Foque até 60 e Nutrição acima', () => {
    expect(validarPolitica(politicaProvisoria).ok).toBe(true);
    expect(politicaAtiva.faixas.map((f) => [f.bloco, f.ateDias])).toEqual([
      ['siga_no_ritmo', 40],
      ['foque_agora', 60],
      ['nutricao', null],
    ]);
  });

  it('recusa faixas fora de ordem, última com teto e bloco inválido', () => {
    const fora = structuredClone(politicaProvisoria);
    fora.faixas[1]!.ateDias = 30;
    const comTeto = structuredClone(politicaProvisoria);
    comTeto.faixas[2]!.ateDias = 200;
    const chanceComTeto = structuredClone(politicaProvisoria);
    chanceComTeto.chance.faixas = [{ ateDias: 10 }];
    const bloco = structuredClone(politicaProvisoria) as unknown as { faixas: { bloco: string }[] };
    bloco.faixas[0]!.bloco = 'pare_de_gastar_tempo';
    for (const p of [fora, comTeto, chanceComTeto, bloco]) {
      const lido = validarPolitica(p);
      expect(lido.ok ? null : lido.erro.codigo).toBe('politica_invalida');
    }
  });
});

describe('classificar', () => {
  it('põe no bloco pela idade, nos limites inclusivos', () => {
    expect(classificarCaso('A', 40).bloco).toBe('siga_no_ritmo');
    expect(classificarCaso('B', 41).bloco).toBe('foque_agora');
    expect(classificarCaso('C', 60).bloco).toBe('foque_agora');
    expect(classificarCaso('D', 61).bloco).toBe('nutricao');
  });

  it('com o motor e a posição: "Score {qualidade}", o valor à parte, o porquê com a posição, a chance e a conta por fator', () => {
    const { deal, avaliacao } = caso('S', 45, 4821);
    // as chances do motor (conversão razão) e o que fechou no replay, como nos dados de 31/12/2017
    const qualidade = qualidadeDoDado(0.313, [0.467, 0.516, 0.313, 0.006], {
      taxa: 0.323,
      faixas: [0.498, 0.517, 0.323, 0],
    });
    const parcela = (
      fator: ParcelaDoScore['fator'],
      rotulo: string,
      pontos: number,
      motivo: ParcelaDoScore['motivo'],
      valor: string | null,
      faixa: string | null = valor,
    ): ParcelaDoScore => ({ fator, rotulo, valor, faixa, pontos, noScore: true, motivo });
    const comScore = (principal: ParcelaDoScore | null, parcelas: ParcelaDoScore[]) =>
      classificar(
        deal,
        {
          ...avaliacao,
          score: { score: 37, chance: 0.37, pontos: -3, parcelas, principal },
          qualidade,
          posicao: { k: 3, n: 10, pelo: 'esperado' },
          esperado: 0.37 * 4821,
        },
        politicaAtiva,
        metodoAtivo,
        null,
      ).indicador;
    const idade = parcela('idade', 'Idade', -3, 'pontua', '45 dias', '41 a 50 dias');
    const setor = { ...parcela('setor', 'Setor', 0, 'fora_do_score', 'retail'), noScore: false };
    const pelaIdade = comScore(idade, [idade, setor]);
    const motivo =
      'Aberto há 45 dias: 32% dos negócios com essa idade fecharam (a melhor faixa fecha 52%).';
    expect(pelaIdade).toMatchObject({
      // round(100 × 0,313 ÷ 0,516) = 61: a qualidade, não a posição (3º de 10)
      score: 61,
      numero: 'Score 61',
      rotulo: 'se o negócio é bom: a idade e as suas respostas',
      emJogo: 'GTX Pro · US$ 4.821 em jogo',
      posicao: { k: 3, n: 10 },
      posicaoTexto: 'Na sua lista: 3º de 10 (o grupo, depois o que há a ganhar).',
      porqueScore: [motivo, 'Na sua lista: 3º de 10 (o grupo, depois o que há a ganhar).'],
      chance: 0.37,
      chanceTexto: 'Chance de fechar em 3 meses: 37%',
      receita: 'Deve render cerca de US$ 1.784 em 3 meses (estimativa pela chance).',
      motivo,
      porque:
        'Aberto há 45 dias. Nessa idade, só 50% fecharam. Daqui pra frente a chance cai rápido.',
    });
    expect(pelaIdade.parcelas).toEqual([
      { fator: 'idade', pontos: -3, noScore: true, texto: '−3 · Idade: 45 dias (41 a 50 dias)' },
      {
        fator: 'setor',
        pontos: 0,
        noScore: false,
        texto: 'Setor: 0 · não muda a chance no histórico',
      },
    ]);
    const produto = parcela('produto', 'Produto', 4, 'pontua', 'MG Special');
    expect(comScore(produto, [produto]).parcelas[0]?.texto).toBe('+4 · Produto: MG Special');
    // a linha do porquê não muda com o fator que mais mexeu na chance
    expect(comScore(produto, [produto]).motivo).toBe(pelaIdade.motivo);
  });

  it('fora de uma lista, o score existe (é a qualidade); sem posição no porquê; a chance, a receita e o preço', () => {
    const item = classificarCaso('B', 45, null, 4821);
    expect(item.indicador).toMatchObject({
      score: 100,
      numero: 'Score 100',
      posicao: null,
      posicaoTexto: '',
      porqueScore: [
        'Aberto há 45 dias: 50% dos negócios com essa idade fecharam (a melhor faixa fecha 50%).',
      ],
      chance: 0.5,
      chanceTexto: 'Chance de fechar em 3 meses: 50%',
      receita: 'Deve render cerca de US$ 2.411 em 3 meses (estimativa pela chance).',
      preco: 'Preço de tabela: US$ 4.821',
    });
    expect(item.porque).toBe(item.indicador.porque);
    // nenhum da faixa fechou: score 0, a receita esperada é zero e a frase diz isso sem número
    const { deal, avaliacao } = caso('Z0', 120, 4821, 0);
    const zero = classificar(deal, avaliacao, politicaAtiva, metodoAtivo, null).indicador;
    expect(zero.score).toBe(0);
    expect(zero.receita).toBe('Pela chance, quase nada deve render.');
    expect(zero.motivo).toBe(
      'Aberto há 120 dias: 0% dos negócios com essa idade fecharam (a melhor faixa fecha 50%).',
    );
    expect(classificarCaso('SD', null).indicador.receita).toBe(
      'Sem data de início: não dá pra estimar.',
    );
    const m = caso('E', 75, 1000, 0.067);
    expect(classificar(m.deal, m.avaliacao, politicaAtiva, metodoAtivo, null).porque).toBe(
      'Aberto há 75 dias. Nessa idade, só 7% fecharam.',
    );
    expect(classificarCaso('F', 300).porque).toBe(
      'Aberto há 300 dias. Nenhum negócio com mais de 90 dias fechou neste histórico.',
    );
    expect(emPorcento(0.003)).toBe('menos de 1');
    expect(emPorcento(0)).toBe('0');
  });

  it('sem data: grupo "Aborde primeiro", entra pelo preço, ação de qualificar', () => {
    const item = classificarCaso('G', null);
    expect(item).toMatchObject({ bloco: 'sem_inicio', faixa: 'Aborde primeiro' });
    // as três perguntas valem no bloco próprio
    expect(item.pendentes.map((p) => p.id)).toEqual(['decisor', 'dor', 'proximo_passo']);
    expect(item.indicador).toMatchObject({
      score: null,
      chance: null,
      chanceTexto: 'Chance de fechar em 3 meses: sem dado (ainda sem primeira conversa).',
      numero: 'Score —',
      emJogo: 'GTX Pro · US$ 1.000 em jogo',
      motivo: 'Responda as perguntas para pontuar.',
      porqueScore: ['Responda as perguntas para pontuar.'],
      porque: 'Ainda sem primeira conversa. US$ 1.000 em jogo: comece por este.',
    });
    // primeiro da lista e ainda sem score: a posição não vira score
    const { deal, avaliacao } = caso('G2', null);
    const naLista = classificar(
      deal,
      { ...avaliacao, posicao: { k: 1, n: 4, pelo: 'preco' } },
      politicaAtiva,
      metodoAtivo,
      null,
    ).indicador;
    expect(naLista).toMatchObject({
      score: null,
      numero: 'Score —',
      parcelas: [],
      porqueScore: [
        'Responda as perguntas para pontuar.',
        'Na sua lista: 1º de 4 (o grupo, depois o que há a ganhar).',
      ],
    });
    expect(item.proximaAcao).toEqual({
      tipo: 'qualificar',
      texto:
        'Faça a primeira conversa: descubra quem decide e qual problema o cliente quer resolver.',
      perguntaId: null,
    });
  });

  it('a ação de cada grupo vem do config; Nutrição é encaminhar', () => {
    expect(classificarCaso('A', 10).proximaAcao).toEqual({
      tipo: 'manter_ritmo',
      texto: 'Marque a próxima conversa com data.',
      perguntaId: null,
    });
    expect(classificarCaso('B', 50).proximaAcao.tipo).toBe('avancar_hoje');
    expect(classificarCaso('D', 90).proximaAcao).toEqual({
      tipo: 'encaminhar_para_nutricao',
      texto: 'Encaminhar para nutrição',
      perguntaId: null,
    });
  });

  it('resposta "não" troca a ação pela frase da pergunta (a primeira na ordem do método), sem mudar o bloco', () => {
    const item = classificarCaso(
      'B',
      50,
      respostasDe('B', [
        ['proximo_passo', 'nao'],
        ['dor', 'nao'],
      ]),
    );
    expect(item.bloco).toBe('foque_agora');
    expect(item.proximaAcao).toEqual({
      tipo: 'avancar_hoje',
      texto:
        'Pergunte qual problema o cliente quer resolver e confirme com ele que o produto resolve. Sem isso, nada do que você falar vai importar.',
      perguntaId: 'dor',
    });
    expect(item.pendentes.map((p) => p.id)).toEqual(['decisor']);
    const sim = classificarCaso('B', 50, respostasDe('B', [['dor', 'sim']]));
    expect(sim.proximaAcao.perguntaId).toBeNull();
  });

  it('em Nutrição, a ação continua encaminhar mesmo com resposta "não"', () => {
    const item = classificarCaso('D', 90, respostasDe('D', [['dor', 'nao']]));
    expect(item.proximaAcao.tipo).toBe('encaminhar_para_nutricao');
  });

  it('respostas de outro deal são ignoradas; a decisão do vendedor vem junto', () => {
    expect(
      classificarCaso('B', 50, respostasDe('X', [['dor', 'nao']])).proximaAcao.perguntaId,
    ).toBeNull();
    const comDecisao: RespostasDoDeal = {
      ...respostasDe('D', [['dor', 'sim']]),
      decisao: { acao: 'encaminhar_para_nutricao', aceita: true, motivo: null, em: AGORA },
    };
    expect(classificarCaso('D', 90, comDecisao).decisao?.acao).toBe('encaminhar_para_nutricao');
  });
});

describe('o score com as respostas do vendedor', () => {
  const score = (
    id: string,
    idade: number | null,
    pares: [string, 'sim' | 'nao'][],
    taxa = 0.5,
  ) => {
    const { deal, avaliacao } = caso(id, idade, 1000, taxa);
    const r = pares.length ? respostasDe(id, pares) : null;
    return classificar(deal, avaliacao, politicaAtiva, metodoAtivo, r).indicador;
  };

  it('"Sim" soma 10, "Não" tira 15, sem resposta não muda; uma linha por resposta no porquê', () => {
    // taxa 0,25 contra a melhor 0,5: parte do dado 50
    expect(score('B', 50, [], 0.25).score).toBe(50);
    expect(score('B', 50, [['decisor', 'sim']], 0.25).score).toBe(60);
    expect(score('B', 50, [['decisor', 'nao']], 0.25).score).toBe(35);
    const tres = score(
      'B',
      50,
      [
        ['proximo_passo', 'sim'],
        ['decisor', 'sim'],
        ['dor', 'nao'],
      ],
      0.25,
    );
    expect(tres.score).toBe(55);
    // na ordem do método, com o rótulo de cada resposta
    expect(tres.porqueScore.slice(1)).toEqual([
      'Decisor confirmado: +10',
      'Problema não confirmado pelo cliente: −15',
      'Próxima conversa com data: +10',
    ]);
  });

  it('limite de 0 a 100', () => {
    expect(
      score('S', 20, [
        ['decisor', 'sim'],
        ['dor', 'sim'],
      ]).score,
    ).toBe(100);
    const quase = score(
      'N',
      55,
      [
        ['decisor', 'nao'],
        ['dor', 'nao'],
        ['proximo_passo', 'nao'],
      ],
      0.1,
    );
    expect(quase.score).toBe(0);
  });

  it('sem data e sem resposta = "Score —"; com resposta, parte de 50', () => {
    expect(score('G', null, [])).toMatchObject({ score: null, numero: 'Score —' });
    const comSim = score('G', null, [['decisor', 'sim']]);
    expect(comSim).toMatchObject({ score: 60, numero: 'Score 60' });
    expect(comSim.porqueScore).toEqual([
      'Ainda sem primeira conversa: sem idade, o score parte de 50 e muda só com as suas respostas.',
      'Decisor confirmado: +10',
    ]);
    expect(score('G', null, [['dor', 'nao']]).score).toBe(35);
  });

  it('o preço não entra: o mesmo negócio com outro preço tem o mesmo score', () => {
    const barato = classificarCaso('P', 45, respostasDe('P', [['decisor', 'sim']]), 55);
    const caro = classificarCaso('P', 45, respostasDe('P', [['decisor', 'sim']]), 26768);
    expect(caro.indicador.score).toBe(barato.indicador.score);
    expect(caro.indicador.emJogo).toBe('GTX Pro · US$ 26.768 em jogo');
  });

  it('em Nutrição as perguntas não valem: resposta guardada não mexe no score', () => {
    const sem = score('D', 90, [], 0.05);
    expect(sem.score).toBe(10);
    expect(
      score(
        'D',
        90,
        [
          ['decisor', 'sim'],
          ['dor', 'sim'],
        ],
        0.05,
      ).score,
    ).toBe(10);
  });

  it('respostas de outro negócio não mexem no score; o bloco não muda com o score', () => {
    const { deal, avaliacao } = caso('B', 50, 1000, 0.25);
    const outro = classificar(
      deal,
      avaliacao,
      politicaAtiva,
      metodoAtivo,
      respostasDe('X', [['decisor', 'sim']]),
    );
    expect(outro.indicador.score).toBe(50);
    expect(score('B', 50, [['decisor', 'sim']], 0.25)).toMatchObject({ score: 60 });
    expect(classificarCaso('B', 50, respostasDe('B', [['decisor', 'nao']])).bloco).toBe(
      'foque_agora',
    );
  });

  it('pesos de outro config mudam o score (os pesos são heurística, ficam no config)', () => {
    const { deal, avaliacao } = caso('B', 50, 1000, 0.25);
    const r = respostasDe('B', [['decisor', 'sim']]);
    const outro = classificar(deal, avaliacao, politicaAtiva, metodoAtivo, r, {
      porSim: 20,
      porNao: -5,
      semDataBase: 40,
    });
    expect(outro.indicador.score).toBe(70);
  });
});

describe('montarFila', () => {
  it('ordena pelo valor esperado (sem data, só o preço), depois preço, idade e id', () => {
    const fila = montarFila([
      classificarCaso('C', 20, null, 500),
      classificarCaso('B', 30, null, 1000),
      classificarCaso('A', 10, null, 1000),
      classificarCaso('Z', null, null, 1000),
      classificarCaso('Y', null, null, 1000),
      classificarCaso('X', null, null, 3000),
      classificarCaso('F', 50),
    ]);
    expect(fila.blocos.siga_no_ritmo.map((i) => i.deal.id)).toEqual(['A', 'B', 'C']);
    expect(fila.blocos.sem_inicio.map((i) => i.deal.id)).toEqual(['X', 'Y', 'Z']);
  });

  it('Foque vazio + 2 no Siga: o Foque mostra os 2, pelo valor esperado, e o Siga fica vazio', () => {
    const fila = montarFila([
      classificarCaso('S1', 20, null, 500),
      classificarCaso('S2', 10, null, 4821),
      classificarCaso('N1', 200),
    ]);
    expect(fila.blocos.foque_agora.map((i) => i.deal.id)).toEqual(['S2', 'S1']);
    expect(fila.blocos.siga_no_ritmo).toEqual([]);
    expect(fila.promovidos).toBe(2);
    expect(fila.contadores.porBloco).toMatchObject({ foque_agora: 2, siga_no_ritmo: 0 });
    // o grupo da idade e a ação continuam os do Siga
    expect(fila.blocos.foque_agora.map((i) => i.bloco)).toEqual(['siga_no_ritmo', 'siga_no_ritmo']);
    expect(fila.blocos.foque_agora[0]?.proximaAcao.texto).toBe(
      'Marque a próxima conversa com data.',
    );
  });

  it('Foque com 1: o Siga mantém os seus', () => {
    const fila = montarFila([
      classificarCaso('F1', 50),
      classificarCaso('S1', 20),
      classificarCaso('S2', 10),
    ]);
    expect(fila.blocos.foque_agora.map((i) => i.deal.id)).toEqual(['F1']);
    expect(fila.blocos.siga_no_ritmo).toHaveLength(2);
    expect(fila.promovidos).toBe(0);
  });

  it('a promoção é por vendedor: quem tem Foque não promove; quem não tem, promove', () => {
    const doVendedor = (id: string, idade: number, vendedor: string) => {
      const { deal, avaliacao } = caso(id, idade);
      return classificar({ ...deal, vendedor }, avaliacao, politicaAtiva, metodoAtivo, null);
    };
    const fila = montarFila([
      doVendedor('A-F', 50, 'Ana'),
      doVendedor('A-S', 10, 'Ana'),
      doVendedor('B-S', 10, 'Bruno'),
    ]);
    expect(fila.blocos.foque_agora.map((i) => i.deal.id).sort()).toEqual(['A-F', 'B-S']);
    expect(fila.blocos.siga_no_ritmo.map((i) => i.deal.id)).toEqual(['A-S']);
    expect(fila.promovidos).toBe(1);
  });

  it('a posição é a ordem da tela: grupo primeiro (Foque, Siga, Aborde, Nutrição), depois o valor; o score não segue a posição', () => {
    // a Nutrição tem o produto mais caro; mesmo assim fica no fim, como na tela
    const itens = [
      classificarCaso('N-caro', 120, null, 26768),
      classificarCaso('S', 20, null, 550),
      classificarCaso('F', 50, null, 550),
      classificarCaso('A', null, null, 4821),
    ];
    const p = posicionarNaTela(itens);
    expect(['F', 'S', 'A', 'N-caro'].map((id) => p.get(id)?.k)).toEqual([1, 2, 3, 4]);
    // o score é a qualidade de cada um, qualquer que seja a posição
    const m = caso('F2', 50, 550, 0.25);
    const foque = classificar(m.deal, m.avaliacao, politicaAtiva, metodoAtivo, null);
    const siga = classificarCaso('S2', 20, null, 550);
    expect(posicionarNaTela([foque, siga]).get('F2')?.k).toBe(1);
    expect([foque.indicador.score, siga.indicador.score]).toEqual([50, 100]);
    // a mesma ordem da fila
    const fila = montarFila(
      itens.map((i) => ({
        ...i,
        avaliacao: { ...i.avaliacao, posicao: p.get(i.deal.id) ?? null },
      })),
    );
    const tela = GRUPOS.flatMap((g) => fila.blocos[g].map((i) => i.deal.id));
    expect(tela).toEqual(['F', 'S', 'A', 'N-caro']);
  });

  it('a posição segue a promoção: Foque vazio, o Siga vem primeiro; lista de 1 = 1º de 1', () => {
    const p = posicionarNaTela([
      classificarCaso('A', null, null, 26768),
      classificarCaso('S', 10, null, 55),
      classificarCaso('N', 200, null, 26768),
    ]);
    expect(['S', 'A', 'N'].map((id) => p.get(id)?.k)).toEqual([1, 2, 3]);
    expect(posicionarNaTela([classificarCaso('só', 200)]).get('só')).toMatchObject({ k: 1, n: 1 });
    expect(posicionarNaTela([]).size).toBe(0);
  });

  it('conta os blocos: sem data de início fica no bloco próprio, separado do Siga', () => {
    const fila = montarFila([
      classificarCaso('A', 10),
      classificarCaso('B', 50),
      classificarCaso('C', 200),
      classificarCaso('D', null),
    ]);
    expect(fila.contadores).toEqual({
      total: 4,
      porBloco: { foque_agora: 1, siga_no_ritmo: 1, nutricao: 1, sem_inicio: 1 },
      alemDaJanela: 1,
    });
  });
});

describe('GRUPOS', () => {
  it('a ordem da tela vai do que mais precisa do vendedor ao que menos precisa: Nutrição por último', () => {
    expect(GRUPOS).toEqual(['foque_agora', 'siga_no_ritmo', 'sem_inicio', 'nutricao']);
  });
});

describe('textos', () => {
  it('nenhum texto da interface (política e método) fala em revisitar, requalificar, "pare de gastar", "Vale US$", pesos provisórios ou encerrar', () => {
    const todos = JSON.stringify(politicaAtiva.textos) + JSON.stringify(metodoAtivo.perguntas);
    for (const proibido of [
      /revisit/i,
      /requalific/i,
      /pare de gastar/i,
      /Vale US/i,
      /pesos provis/i,
      /encerr/i,
      /em 10\b/,
      /em cada 10/,
    ]) {
      expect(todos).not.toMatch(proibido);
    }
    // nº 59: a frase do "Não" na próxima conversa
    expect(metodoAtivo.perguntas.find((p) => p.id === 'proximo_passo')?.acaoSeNao).toBe(
      'Proponha uma data agora. Sem data marcada, a chance continua caindo.',
    );
  });

  it('preencher troca as chaves conhecidas e deixa as outras', () => {
    expect(preencher('{a} e {b}', { a: 1 })).toBe('1 e {b}');
  });

  it('textosDaTela preenche os limites da política e a janela', () => {
    const t = textosDaTela(politicaAtiva, janela);
    expect(t.grupos.foque_agora.vazio).toBe('Nenhum negócio seu está entre 41 e 60 dias hoje.');
    expect(t.grupos.siga_no_ritmo.vazio).toBe('Nenhum negócio seu está entre 0 e 40 dias hoje.');
    expect(t.grupos.nutricao.subtitulo).toBe(
      'Abertos há mais de 60 dias. Quase nenhum fechou com essa idade.',
    );
    expect(t.avisos.referencia).toBe('Dados até 31/12/2017. As idades são contadas até essa data.');
  });

  it('os limites dos textos acompanham uma política com outras faixas', () => {
    const outra: PoliticaPriorizacao = structuredClone(politicaProvisoria);
    outra.faixas[0]!.ateDias = 30;
    outra.faixas[1]!.ateDias = 45;
    expect(textosDaTela(outra, janela).grupos.foque_agora.vazio).toBe(
      'Nenhum negócio seu está entre 31 e 45 dias hoje.',
    );
  });
});
