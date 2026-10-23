import { describe, expect, it } from 'vitest';
import type { Deal, Janela } from '../pipeline';
import { avaliar, chanceDaIdade, medirChance, medirPontos, type ContextoScore } from './index';

const janela: Janela = {
  referencia: '2017-12-31',
  ganhos: 100,
  p50Dias: 57,
  p95Dias: 116,
  maxDias: 138,
};

function deal(parcial: Partial<Deal>): Deal {
  return {
    id: 'AAAA0001',
    vendedor: 'Ana',
    manager: 'Mara',
    regiao: 'West',
    produto: 'GTX Pro',
    serie: 'GTX',
    precoTabela: 4821,
    conta: 'Acme',
    setor: 'retail',
    funcionarios: 4540,
    receitaConta: 700,
    empresaMae: null,
    estagio: 'Engaging',
    dataEngajamento: '2017-11-21',
    dataFechamento: null,
    valorFechamento: null,
    aberto: true,
    idadeDias: 40,
    duracaoDias: null,
    lacunas: [],
    ...parcial,
  };
}

const contexto: ContextoScore = {
  janela,
  catalogo: [{ nome: 'GTX Pro', serie: 'GTX', precoTabela: 4821 }],
  contas: [],
};

describe('avaliar', () => {
  it('explica a idade contra a janela e o preço de tabela, com números da janela', () => {
    const a = avaliar(deal({}), contexto);
    expect(a.situacao).toBe('na_janela');
    expect(a.emJogo).toBe(4821);
    expect(a.fatos).toEqual([
      {
        id: 'idade',
        rotulo: 'Idade',
        valor: 40,
        detalhe: 'aberto há 40 d; 95% dos ganhos fecharam em até 116 d',
      },
      {
        id: 'em_jogo',
        rotulo: 'Preço de tabela',
        valor: 4821,
        detalhe: 'GTX Pro: preço de tabela US$ 4.821',
      },
    ]);
    expect(a.contexto).toEqual(['conta Acme', 'conta de 4.540 funcionários', 'setor retail']);
    expect(a.explicacao).toBe(
      'Aberto há 40 d; 95% dos ganhos fecharam em até 116 d. GTX Pro: preço de tabela US$ 4.821.',
    );
    // sem replay no contexto, não há chance nem receita esperada
    expect(a).toMatchObject({
      referencia: '2017-12-31',
      maxJanelaDias: 138,
      chance: null,
      esperado: null,
    });
  });

  it('perto do limite e além da janela citam o máximo', () => {
    expect(avaliar(deal({ idadeDias: 120 }), contexto).fatos[0]?.detalhe).toContain(
      'o mais longo levou 138 d',
    );
    expect(avaliar(deal({ idadeDias: 300 }), contexto).fatos[0]?.detalhe).toBe(
      'aberto há 300 d; nenhum ganho deste histórico levou mais de 138 d',
    );
  });

  it('prospecção não tem idade; sem conta é "sem dado", não penalidade', () => {
    const a = avaliar(
      deal({
        idadeDias: null,
        dataEngajamento: null,
        conta: null,
        setor: null,
        funcionarios: null,
      }),
      contexto,
    );
    expect(a.situacao).toBe('prospeccao');
    expect(a.fatos[0]?.detalhe).toBe('em prospecção, ainda sem data de engajamento');
    expect(a.contexto).toEqual(['sem dado de conta']);
    expect(a.emJogo).toBe(4821);
  });
});

describe('medirChance', () => {
  // referência 31/12; corte (−92 d) = 30/09
  const replay = [
    deal({ id: 'A', dataEngajamento: '2017-09-25', dataFechamento: '2017-11-01', estagio: 'Won' }), // 5 d no corte, ganhou
    deal({ id: 'B', dataEngajamento: '2017-09-25', dataFechamento: '2017-11-01', estagio: 'Lost' }), // 5 d, perdeu
    deal({ id: 'C', dataEngajamento: '2017-08-01', dataFechamento: null, estagio: 'Engaging' }), // 60 d, segue aberto
    deal({ id: 'D', dataEngajamento: '2017-08-01', dataFechamento: '2017-09-01', estagio: 'Won' }), // fechou antes do corte: fora
    deal({ id: 'E', dataEngajamento: '2017-10-05', dataFechamento: null, estagio: 'Engaging' }), // engajou depois do corte: fora
    deal({ id: 'F', dataEngajamento: null, estagio: 'Prospecting' }), // sem data: fora
    deal({ id: 'G', dataEngajamento: '2017-01-01', dataFechamento: '2018-01-10', estagio: 'Won' }), // ganhou depois da referência
  ];
  const chance = medirChance(replay, '2017-12-31', {
    corteDias: 92,
    faixas: [{ ateDias: 10 }, { ateDias: 60 }, { ateDias: null }],
  });

  it('pega os abertos no corte, mede a idade no corte e conta ganhos até a referência', () => {
    expect(chance).toMatchObject({ corte: '2017-09-30', populacao: 4, ganhos: 1, taxaGeral: 0.25 });
    expect(chance.faixas).toEqual([
      { de: 0, ateDias: 10, rotulo: '0 a 10 dias', n: 2, ganhos: 1, taxa: 0.5 },
      { de: 11, ateDias: 60, rotulo: '11 a 60 dias', n: 1, ganhos: 0, taxa: 0 },
      { de: 61, ateDias: null, rotulo: 'acima de 60 dias', n: 1, ganhos: 0, taxa: 0 },
    ]);
  });

  it('chanceDaIdade dá a faixa da idade de hoje', () => {
    expect(chanceDaIdade(chance, 7)).toEqual({ faixa: '0 a 10 dias', taxa: 0.5, n: 2 });
    expect(chanceDaIdade(chance, 400)?.taxa).toBe(0);
    expect(chanceDaIdade(chance, null)).toBeNull();
  });

  it('avaliar usa a chance do contexto', () => {
    const avaliacao = avaliar(deal({ idadeDias: 7 }), { ...contexto, chance });
    expect(avaliacao.chance?.taxa).toBe(0.5);
    // a posição só existe dentro da lista do vendedor (criarServicos)
    expect(avaliacao.posicao).toBeNull();
  });
});

describe('medirPontos', () => {
  const fechado = (id: string, estagio: 'Won' | 'Lost', setor: string, receitaConta: number) =>
    deal({ id, estagio, setor, receitaConta, aberto: false, dataFechamento: '2017-06-01' });
  const deals = [
    fechado('1', 'Won', 'retail', 100),
    fechado('2', 'Won', 'retail', 200),
    fechado('3', 'Lost', 'finance', 300),
    fechado('4', 'Won', 'finance', 400),
    deal({ id: '5' }), // aberto: fora da tabela
  ];
  const chance = medirChance([], '2017-12-31', { corteDias: 92, faixas: [{ ateDias: null }] });
  const tabela = medirPontos(deals, chance);

  it('taxa geral dos fechados e pontos = taxa do valor ÷ taxa geral', () => {
    expect(tabela.fechados).toBe(4);
    expect(tabela.taxaGeral).toBe(0.75);
    const setor = tabela.atributos.find((a) => a.id === 'setor');
    expect(setor?.valores).toEqual([
      { valor: 'finance', n: 2, ganhos: 1, taxa: 0.5, pontos: 0.5 / 0.75 },
      { valor: 'retail', n: 2, ganhos: 2, taxa: 1, pontos: 1 / 0.75 },
    ]);
    expect(setor?.minPontos).toBeCloseTo(0.667, 3);
    expect(setor?.maxPontos).toBeCloseTo(1.333, 3);
  });

  it('porte em quartis de receita, na ordem do menor para o maior', () => {
    const porte = tabela.atributos.find((a) => a.id === 'porte');
    expect(porte?.valores.map((v) => [v.valor, v.n])).toEqual([
      ['Q1 menor', 1],
      ['Q2', 1],
      ['Q3', 1],
      ['Q4 maior', 1],
    ]);
  });

  it('traz os eixos Perfil (5 atributos) e Interesse (idade)', () => {
    expect(tabela.atributos.map((a) => [a.id, a.eixo])).toEqual([
      ['setor', 'perfil'],
      ['produto', 'perfil'],
      ['porte', 'perfil'],
      ['escritorio', 'perfil'],
      ['vendedor', 'perfil'],
      ['idade', 'interesse'],
    ]);
  });
});
