/// <reference types="node" />
// Integração com o dado real (data/deals.json): os números que a tela mostra, medidos de ponta a ponta.
import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { conferirChecksum, lerPipeline, type Pipeline } from '../pipeline';
import { GRUPOS, politicaAtiva, type Fila } from '../priorizacao';
import { chancesDaIdade, configMotorPadrao, fatoresNoCorte } from '../score';
import { metodoProvisorio, responder, type RespostasDoDeal } from '../qualificacao';
import { criarServicos } from './index';

const PASTA_DADOS = new URL('../../../../data/', import.meta.url);
const bytes = new Uint8Array(readFileSync(new URL('deals.json', PASTA_DADOS)));
const arquivoSha = readFileSync(new URL('deals.json.sha256', PASTA_DADOS), 'utf8');

function carregar(): Pipeline {
  const lido = lerPipeline(JSON.parse(new TextDecoder().decode(bytes)));
  if (!lido.ok) throw new Error(lido.erro.mensagem);
  return lido.valor;
}

describe('integração com o deals.json real', () => {
  const pipeline = carregar();
  const servicos = criarServicos({ pipeline, checksum: 'conferido-no-teste' });
  const filaDe = (filtro: { vendedor?: string; regiao?: string }): Fila => {
    const fila = servicos.fila({ filtro, respostas: [] });
    if (!fila.ok) throw new Error(fila.erro.mensagem);
    return fila.valor;
  };

  it('o checksum publicado bate com o arquivo', async () => {
    const conferido = await conferirChecksum(bytes, arquivoSha);
    expect(conferido.ok).toBe(true);
  });

  it('carrega 8.800 deals, 2.089 abertos e 7 produtos', () => {
    expect(pipeline.deals).toHaveLength(8800);
    expect(pipeline.abertos).toHaveLength(2089);
    expect(pipeline.catalogo).toHaveLength(7);
    expect(pipeline.referencia).toBe('2017-12-31');
  });

  it('mede a janela dos ganhos: p50 57, p95 116, máximo 138', () => {
    expect(pipeline.janela).toMatchObject({ p50Dias: 57, p95Dias: 116, maxDias: 138 });
  });

  it('mede a chance pelo replay de 92 dias (corte 30/09/2017)', () => {
    const chance = servicos.chance();
    expect(chance.corte).toBe('2017-09-30');
    expect(chance.populacao).toBe(2409);
    const porFaixa = Object.fromEntries(
      chance.faixas.map((f) => [f.rotulo, { n: f.n, taxa: f.taxa }]),
    );
    expect(porFaixa['41 a 50 dias']?.n).toBe(164);
    expect(porFaixa['41 a 50 dias']?.taxa).toBeCloseTo(0.323, 3);
    expect(porFaixa['51 a 60 dias']?.n).toBe(201);
    expect(porFaixa['51 a 60 dias']?.taxa).toBeCloseTo(0.219, 3);
    expect(porFaixa['61 a 90 dias']?.n).toBe(460);
    expect(porFaixa['61 a 90 dias']?.taxa).toBeCloseTo(0.067, 3);
    expect(porFaixa['acima de 90 dias']?.taxa).toBe(0);
    const ate40 = chance.faixas.filter((f) => f.ateDias !== null && f.ateDias <= 40);
    const n40 = ate40.reduce((t, f) => t + f.n, 0);
    const g40 = ate40.reduce((t, f) => t + f.ganhos, 0);
    expect(n40).toBe(859);
    expect(g40 / n40).toBeCloseTo(0.502, 3);
    // as faixas antigas, para conferir com o backtest publicado
    const somar = (de: number, ate: number) => {
      const fs = chance.faixas.filter((f) => f.de >= de && f.ateDias !== null && f.ateDias <= ate);
      return fs.reduce((t, f) => t + f.ganhos, 0) / fs.reduce((t, f) => t + f.n, 0);
    };
    expect(somar(31, 60)).toBeCloseTo(0.343, 3);
    expect(somar(0, 60)).toBeCloseTo(0.431, 3);
  });

  it('a tabela de pontos (HubSpot): taxa geral 63,2% de 6.711; o Perfil fica perto de 1,0', () => {
    const tabela = servicos.pontos();
    expect(tabela.fechados).toBe(6711);
    expect(tabela.taxaGeral).toBeCloseTo(0.632, 3);
    const faixa = (id: string) => {
      const a = tabela.atributos.find((x) => x.id === id);
      return [Number(a?.minPontos.toFixed(2)), Number(a?.maxPontos.toFixed(2))];
    };
    expect(faixa('setor')).toEqual([0.97, 1.03]);
    expect(faixa('produto')).toEqual([0.95, 1.03]);
    expect(faixa('porte')).toEqual([0.97, 1.04]);
    expect(faixa('escritorio')).toEqual([0.99, 1.01]);
    expect(faixa('vendedor')).toEqual([0.87, 1.11]);
    const porte = tabela.atributos.find((x) => x.id === 'porte')?.valores.map((v) => v.n);
    expect(porte).toEqual([1681, 1699, 1699, 1632]);
    const idade = tabela.atributos.find((x) => x.id === 'idade');
    expect(idade?.eixo).toBe('interesse');
    expect(idade?.maxPontos ?? 0).toBeGreaterThan(1.5);
  });

  it('a segunda-feira de todos (40/60): pela idade, Foque 30, Siga 27, Aborde primeiro 500, Nutrição 1.532 (1.291 além da janela); na tela, 3 do Siga sobem para o Foque', () => {
    const fila = filaDe({});
    const pelaIdade = (b: string) =>
      Object.values(fila.blocos)
        .flat()
        .filter((i) => i.bloco === b);
    expect(
      ['foque_agora', 'siga_no_ritmo', 'nutricao', 'sem_inicio'].map((b) => pelaIdade(b).length),
    ).toEqual([30, 27, 1532, 500]);
    expect(fila.contadores).toEqual({
      total: 2089,
      porBloco: { foque_agora: 33, siga_no_ritmo: 24, nutricao: 1532, sem_inicio: 500 },
      alemDaJanela: 1291,
    });
    expect(fila.promovidos).toBe(3);
  });

  it('por região, na tela: West 17/15/716/0 (3 promovidos), East 16/9/408/0, Central 0/0/408/500; o painel conta o Foque da tela', () => {
    const porRegiao = (regiao: string) => {
      const g = filaDe({ regiao }).contadores.porBloco;
      return [g.foque_agora, g.siga_no_ritmo, g.nutricao, g.sem_inicio];
    };
    expect(porRegiao('West')).toEqual([17, 15, 716, 0]);
    expect(porRegiao('East')).toEqual([16, 9, 408, 0]);
    expect(porRegiao('Central')).toEqual([0, 0, 408, 500]);
    const painel = servicos.painel({ filtro: { regiao: 'West' }, respostas: [] });
    if (!painel.ok) throw new Error(painel.erro.mensagem);
    expect(painel.valor.foqueSemConversa.foque).toBe(17);
  });

  it('Foque vazio: o Siga do vendedor sobe para o Foque, na ordem da tela (Elease Gluck: 2; Hayden Neloms: 1)', () => {
    for (const [vendedor, n] of [
      ['Elease Gluck', 2],
      ['Hayden Neloms', 1],
    ] as const) {
      const fila = filaDe({ vendedor });
      expect(fila.promovidos).toBe(n);
      expect(fila.blocos.foque_agora).toHaveLength(n);
      expect(fila.blocos.siga_no_ritmo).toHaveLength(0);
      expect(fila.blocos.foque_agora.every((i) => i.bloco === 'siga_no_ritmo')).toBe(true);
      const ks = fila.blocos.foque_agora.map((i) => i.indicador.posicao?.k ?? 0);
      expect(ks).toEqual([...ks].sort((a, b) => a - b));
    }
    // com Foque não vazio, nada muda
    const zane = filaDe({ vendedor: 'Zane Levy' });
    expect(zane.promovidos).toBe(0);
    expect(zane.blocos.foque_agora.every((i) => i.bloco === 'foque_agora')).toBe(true);
  });

  it('Central sem nenhum em Foque: o texto do grupo vazio diz a faixa', () => {
    expect(servicos.textos().grupos.foque_agora.vazio).toBe(
      'Nenhum negócio seu está entre 41 e 60 dias hoje.',
    );
    expect(servicos.textos().avisos.nutricao).toBe(
      'Nenhum negócio deste histórico fechou depois de 138 dias. Pode ser um limite dos próprios dados.',
    );
    expect(servicos.textos().grupos.nutricao.subtitulo).toBe(
      'Abertos há mais de 60 dias. Quase nenhum fechou com essa idade.',
    );
  });

  it('o time inteiro: 35 vendedores, 5 sem negócio, todos com manager e região', () => {
    const { vendedores, managers, regioes } = servicos.organizacao();
    expect(vendedores).toHaveLength(35);
    // 5 nunca tiveram negócio no histórico; outros 3 têm só negócios fechados (zero abertos)
    const comNegocio = new Set(carregar().deals.map((d) => d.vendedor));
    expect(vendedores.filter((v) => !comNegocio.has(v.nome)).map((v) => v.nome)).toEqual([
      'Carl Lin',
      'Carol Thompson',
      'Elizabeth Anderson',
      'Mei-Mei Johns',
      'Natalya Ivanova',
    ]);
    expect(vendedores.filter((v) => v.abertos === 0)).toHaveLength(8);
    expect(managers.flatMap((m) => m.vendedores).sort()).toEqual(
      vendedores.map((v) => v.nome).sort(),
    );
    expect(regioes).toEqual(['Central', 'East', 'West']);
    // a soma dos abertos por vendedor é a fila inteira
    expect(vendedores.reduce((s, v) => s + v.abertos, 0)).toBe(2089);
  });

  it('Central: Darcel Schlecht vê 111 em "Aborde primeiro", na ordem do preço, sem score até responder, antes da Nutrição', () => {
    const fila = filaDe({ vendedor: 'Darcel Schlecht' });
    expect(fila.contadores.porBloco).toMatchObject({
      foque_agora: 0,
      siga_no_ritmo: 0,
      sem_inicio: 111,
    });
    const aborde = fila.blocos.sem_inicio;
    const precos = aborde.map((i) => i.avaliacao.emJogo);
    expect(precos).toEqual([...precos].sort((a, b) => b - a));
    // sem data e sem resposta: nenhum score, "Score —" e o pedido para responder
    expect(aborde.every((i) => i.indicador.score === null)).toBe(true);
    expect(aborde[0]?.indicador.numero).toBe('Score —');
    expect(aborde[0]?.indicador.porqueScore[0]).toBe('Responda as perguntas para pontuar.');
    expect(aborde[0]?.proximaAcao.texto).toBe(
      'Faça a primeira conversa: descubra quem decide e qual problema o cliente quer resolver.',
    );
    expect(servicos.textos().grupos.sem_inicio.titulo).toBe('Aborde primeiro');
    expect(GRUPOS.indexOf('sem_inicio')).toBeLessThan(GRUPOS.indexOf('nutricao'));
  });

  it('o seletor já traz quantos abertos cada vendedor tem em cada grupo, medidos na carga', () => {
    const { vendedores } = servicos.organizacao();
    for (const v of vendedores) {
      const contagem = filaDe({ vendedor: v.nome }).contadores.porBloco;
      expect(v.grupos).toEqual(contagem);
      expect(Object.values(v.grupos ?? {}).reduce((s, n) => s + n, 0)).toBe(v.abertos);
    }
    expect(vendedores.find((v) => v.nome === 'Darcel Schlecht')?.grupos).toEqual({
      foque_agora: 0,
      siga_no_ritmo: 0,
      nutricao: 83,
      sem_inicio: 111,
    });
  });

  it('vendedor sem negócio: fila vazia, zero em todos os números', () => {
    const fila = filaDe({ vendedor: 'Carl Lin' });
    expect(fila.contadores).toEqual({
      total: 0,
      porBloco: { foque_agora: 0, siga_no_ritmo: 0, nutricao: 0, sem_inicio: 0 },
      alemDaJanela: 0,
    });
    expect(fila.receita).toEqual({ total: 0, semEstimativa: 0 });
  });

  it('por vendedor, Foque agora vai de 0 a 3', () => {
    const foques = servicos
      .organizacao()
      .vendedores.map((v) => filaDe({ vendedor: v.nome }).contadores.porBloco.foque_agora);
    expect(Math.min(...foques)).toBe(0);
    expect(Math.max(...foques)).toBe(3);
  });

  it('receita esperada: chance do motor (sem arredondar) × preço de tabela; sem data fica fora', () => {
    const fila = filaDe({});
    expect(fila.receita.semEstimativa).toBe(500);
    let soma = 0;
    for (const item of Object.values(fila.blocos).flat()) {
      const { idadeDias, esperado, emJogo, score } = item.avaliacao;
      if (idadeDias === null) {
        expect(esperado).toBeNull();
        expect(score).toBeNull();
        expect(item.indicador.receita).toBe('Sem data de início: não dá pra estimar.');
        continue;
      }
      if (score === null) throw new Error('aberto com data e sem score: ' + item.deal.id);
      expect(esperado).toBeCloseTo(score.chance * emJogo, 6);
      soma += esperado ?? 0;
      if (Math.round(esperado ?? 0) === 0)
        expect(item.indicador.receita).toBe('Pela chance, quase nada deve render.');
    }
    expect(fila.receita.total).toBeCloseTo(soma, 6);
  });

  it('motor de pontos no arquivo real: treino 1.686 abertos em 30/06, validação 2.409 em 30/09; só a idade entra', () => {
    const motor = servicos.motor();
    expect(motor.treino).toEqual({
      corte: '2017-06-30',
      ate: '2017-09-30',
      n: 1686,
      ganhos: 609,
      taxa: 609 / 1686,
    });
    expect(motor.validacao).toEqual({
      corte: '2017-09-30',
      ate: '2017-12-31',
      n: 2409,
      ganhos: 559,
      taxa: 559 / 2409,
    });
    expect(motor.fatores).toHaveLength(19);
    expect(motor.escolhidos).toEqual(['idade']);
    expect(motor.aucIdade).toBeCloseTo(0.83, 3);
    expect(motor.aucScore).toBe(motor.aucIdade);
    // nenhum outro fator sobe o AUC em 0,005 onde tem dado
    for (const f of motor.fatores.filter((x) => !x.entrou))
      expect(f.ganhoAuc ?? 0).toBeLessThan(0.005);
    // sem conta nunca fechou: os fatores de conta, medidos só onde há conta, ficam perto de 0,5
    const deConta = motor.fatores.filter((f) => f.id.startsWith('conta_') || f.id === 'setor');
    for (const f of deConta) expect(Math.abs((f.aucValidacao ?? 0.5) - 0.5)).toBeLessThan(0.05);
  });

  it('sem vazamento no arquivo real: apagar o que veio depois do corte não muda nenhum fator', () => {
    const config = configMotorPadrao;
    const faixas = politicaAtiva.chance.faixas;
    for (const corte of ['2017-06-30', '2017-09-30']) {
      const c = Date.parse(corte + 'T00:00:00Z');
      const antes = (iso: string | null) => iso !== null && Date.parse(iso + 'T00:00:00Z') <= c;
      const censurados = pipeline.deals
        .filter((d) => antes(d.dataEngajamento))
        .map((d) =>
          d.dataFechamento !== null && !antes(d.dataFechamento)
            ? {
                ...d,
                estagio: 'Engaging' as const,
                dataFechamento: null,
                valorFechamento: null,
                aberto: true,
                duracaoDias: null,
                idadeDias: null,
              }
            : d,
        );
      const completo = fatoresNoCorte(pipeline.deals, corte, faixas, config);
      expect(fatoresNoCorte(censurados, corte, faixas, config)).toEqual(completo);
      expect(completo.size).toBe(corte === '2017-06-30' ? 1686 : 2409);
    }
  });

  it('backtest da receita esperada (dentro da amostra): 2.409 abertos em 30/09/2017, previsto US$ 1.284.794 × realizado US$ 1.251.928', () => {
    const chance = servicos.chance();
    const corte = Date.parse(chance.corte + 'T00:00:00Z');
    const fim = Date.parse(chance.referencia + 'T00:00:00Z');
    const dia = (iso: string) => Date.parse(iso + 'T00:00:00Z');
    let previsto = 0;
    let realizado = 0;
    let n = 0;
    for (const d of pipeline.deals) {
      if (d.dataEngajamento === null) continue;
      const engajou = dia(d.dataEngajamento);
      const fechou = d.dataFechamento === null ? null : dia(d.dataFechamento);
      if (engajou > corte || (fechou !== null && fechou <= corte)) continue;
      const idade = Math.round((corte - engajou) / 86_400_000);
      const faixa = chance.faixas.find((f) => f.ateDias === null || idade <= f.ateDias);
      n += 1;
      previsto += (faixa?.taxa ?? 0) * d.precoTabela;
      if (d.estagio === 'Won' && fechou !== null && fechou <= fim)
        realizado += d.valorFechamento ?? 0;
    }
    expect(n).toBe(2409);
    expect(Math.round(previsto)).toBe(1284794);
    expect(Math.round(realizado)).toBe(1251928);
  });

  it('dentro de cada grupo a ordem é o valor esperado (sem data, o preço): na lista de um vendedor, a posição só cresce', () => {
    const fila = filaDe({});
    for (const bloco of ['foque_agora', 'siga_no_ritmo', 'nutricao'] as const) {
      const esperados = fila.blocos[bloco].map((i) => i.avaliacao.esperado ?? -1);
      expect(esperados).toEqual([...esperados].sort((a, b) => b - a));
    }
    const precos = fila.blocos.sem_inicio.map((i) => i.avaliacao.emJogo);
    expect(precos).toEqual([...precos].sort((a, b) => b - a));
    for (const vendedor of ['Darcel Schlecht', 'Vicki Laflamme']) {
      for (const bloco of Object.values(filaDe({ vendedor }).blocos)) {
        const ks = bloco.map((i) => i.indicador.posicao?.k ?? 0);
        expect(ks).toEqual([...ks].sort((a, b) => a - b));
      }
    }
  });

  it('o score é a qualidade, no arquivo real: Nutrição ≤ 15, Siga ≥ Foque, sem data = "—", o filtro e o preço não mudam', () => {
    const todos = Object.values(filaDe({}).blocos).flat();
    expect(todos).toHaveLength(2089);
    const doBloco = (b: string) => todos.filter((i) => i.bloco === b);
    const scores = (b: string) => doBloco(b).map((i) => i.indicador.score as number);
    // a parte do dado por faixa: 90–100 até 40 dias, 61 e 41 de 41 a 60, 15 de 61 a 90, 1 acima
    expect(Math.max(...scores('nutricao'))).toBe(15);
    expect(Math.min(...scores('nutricao'))).toBe(1);
    expect(Math.min(...scores('siga_no_ritmo'))).toBeGreaterThanOrEqual(
      Math.max(...scores('foque_agora')),
    );
    expect([...new Set(scores('foque_agora'))].sort()).toEqual([41, 61]);
    expect(Math.min(...scores('siga_no_ritmo'))).toBeGreaterThanOrEqual(90);
    expect(doBloco('sem_inicio').every((i) => i.indicador.score === null)).toBe(true);
    expect(todos.filter((i) => i.indicador.score === null)).toHaveLength(500);
    // o filtro da tela não muda o score
    const daVicki = new Map(
      Object.values(filaDe({ vendedor: 'Vicki Laflamme' }).blocos)
        .flat()
        .map((i) => [i.deal.id, i.indicador.score]),
    );
    const daRegiao = Object.values(filaDe({ regiao: 'West' }).blocos).flat();
    for (const i of daRegiao.filter((x) => x.deal.vendedor === 'Vicki Laflamme'))
      expect(i.indicador.score).toBe(daVicki.get(i.deal.id));
    // o mesmo score para a mesma idade, qualquer que seja o produto (o preço não entra)
    const porIdade = new Map<number, Set<number | null>>();
    for (const i of todos) {
      if (i.avaliacao.idadeDias === null) continue;
      const s = porIdade.get(i.avaliacao.idadeDias) ?? new Set();
      s.add(i.indicador.score);
      porIdade.set(i.avaliacao.idadeDias, s);
    }
    for (const s of porIdade.values()) expect(s.size).toBe(1);
    // a parte do dado sai das chances do motor: a melhor faixa vale 100
    const maxima = Math.max(...chancesDaIdade(servicos.motor()).map((f) => f.chance));
    for (const i of todos.slice(0, 200)) {
      const q = i.avaliacao.qualidade;
      if (q === null) continue;
      expect(q.maxima).toBe(maxima);
      expect(i.indicador.score).toBe(Math.round((100 * q.chance) / maxima));
    }
  });

  it('a posição segue a ordem da tela: em toda lista, do primeiro ao último grupo, k vai de 1 a n', () => {
    const comNegocio = [...new Set(pipeline.abertos.map((d) => d.vendedor))];
    expect(comNegocio).toHaveLength(27);
    for (const nome of comNegocio) {
      const tela = GRUPOS.flatMap((g) => filaDe({ vendedor: nome }).blocos[g]);
      expect(tela.map((i) => i.indicador.posicao?.k)).toEqual(tela.map((_, i) => i + 1));
      expect(tela.every((i) => i.indicador.posicao?.n === tela.length)).toBe(true);
    }
  });

  it('Zane Levy: o Foque agora fica no topo da tela, mas o score dele é menor que o do Siga; a Nutrição fica embaixo nos dois', () => {
    const fila = filaDe({ vendedor: 'Zane Levy' });
    const scores = (g: (typeof GRUPOS)[number]) =>
      fila.blocos[g].map((i) => i.indicador.score as number);
    expect(fila.blocos.foque_agora.length).toBeGreaterThan(0);
    // a ordem: Foque primeiro (por onde começar)
    expect(fila.blocos.foque_agora[0]?.indicador.posicao?.k).toBe(1);
    // o score: Siga (idade boa) ≥ Foque (a chance caindo) > Nutrição (parado)
    expect(Math.min(...scores('siga_no_ritmo'))).toBeGreaterThanOrEqual(
      Math.max(...scores('foque_agora')),
    );
    expect(Math.min(...scores('foque_agora'))).toBeGreaterThan(Math.max(...scores('nutricao')));
    expect(Math.max(...scores('nutricao'))).toBeLessThanOrEqual(15);
  });

  it('responder "Sim" sobe o score do negócio e não muda a ordem da tela', () => {
    const fila = filaDe({ vendedor: 'Zane Levy' });
    const alvo = fila.blocos.foque_agora[0]!;
    const sim = responder(
      null,
      alvo.deal.id,
      metodoProvisorio,
      'decisor',
      'sim',
      '2026-10-23T12:00:00Z',
    );
    if (!sim.ok) throw new Error(sim.erro.mensagem);
    const item = servicos.item({ dealId: alvo.deal.id, respostas: sim.valor });
    if (!item.ok) throw new Error(item.erro.mensagem);
    expect(item.valor.indicador.score).toBe((alvo.indicador.score as number) + 10);
    expect(item.valor.indicador.porqueScore).toContain('Decisor confirmado: +10');
    const depois = servicos.fila({ filtro: { vendedor: 'Zane Levy' }, respostas: [sim.valor] });
    if (!depois.ok) throw new Error(depois.erro.mensagem);
    const ids = (f: typeof fila) => GRUPOS.flatMap((g) => f.blocos[g].map((i) => i.deal.id));
    expect(ids(depois.valor)).toEqual(ids(fila));
  });

  it('Darcel Schlecht: o "Aborde primeiro" fica acima de toda a Nutrição na tela, com o porquê de começar por ele', () => {
    const fila = filaDe({ vendedor: 'Darcel Schlecht' });
    const k = (g: (typeof GRUPOS)[number]) =>
      fila.blocos[g].map((i) => i.indicador.posicao?.k as number);
    expect(Math.max(...k('sem_inicio'))).toBeLessThan(Math.min(...k('nutricao')));
    const primeiro = fila.blocos.sem_inicio[0];
    expect(primeiro?.porque).toBe(
      'Ainda sem primeira conversa. US$ ' +
        new Intl.NumberFormat('pt-BR').format(primeiro?.avaliacao.emJogo ?? 0) +
        ' em jogo: comece por este.',
    );
    expect(fila.blocos.sem_inicio.every((i) => !i.porque.includes('não dá pra estimar'))).toBe(
      true,
    );
  });

  const painelDe = (
    filtro: { vendedor?: string; regiao?: string },
    respostas: RespostasDoDeal[] = [],
  ) => {
    const r = servicos.painel({ filtro, respostas });
    if (!r.ok) throw new Error(r.erro.mensagem);
    return r.valor;
  };
  const emJogoDe = (itens: readonly { avaliacao: { emJogo: number } }[]) => ({
    n: itens.length,
    valor: itens.reduce((s, i) => s + i.avaliacao.emJogo, 0),
  });

  it('painel sem filtro: as 4 métricas, com o Foque da tela (Siga promovido) e o preço em jogo', () => {
    const p = painelDe({});
    const fila = filaDe({});
    expect(p.total).toBe(2089);
    expect(p.receita).toBeCloseTo(fila.receita.total, 6);
    expect(Math.round(p.receita)).toBe(69395);
    // o Foque agora da tela: 30 pela idade + 3 do Siga promovidos; sem resposta, todos sem "Sim"
    expect(p.foqueSemConversa).toMatchObject({ n: 33, foque: 33, sim: 0, nao: 0, semResposta: 33 });
    expect(p.foqueSemConversa.valor).toBeCloseTo(emJogoDe(fila.blocos.foque_agora).valor, 6);
    expect(p.foqueSemConversa.valor).toBe(67896);
    expect(p.parado).toEqual(emJogoDe(fila.blocos.nutricao));
    expect(p.parado).toEqual({ n: 1532, valor: 3779334 });
    expect(p.limiteParadoDias).toBe(60);
    expect(p.semInicio).toEqual(emJogoDe(fila.blocos.sem_inicio));
    expect(p.semInicio).toEqual({ n: 500, valor: 1073986 });
    // as perguntas valem fora da Nutrição: 2.089 − 1.532
    expect(p.respostas).toMatchObject({ n: 0, base: 557 });
  });

  it('painel por vendedor: os 35 aparecem, cada linha bate com a fila dele, a soma é o time e quem não tem negócio fica com zero', () => {
    const p = painelDe({});
    expect(p.vendedores).toHaveLength(35);
    for (const linha of p.vendedores) {
      const fila = filaDe({ vendedor: linha.vendedor });
      expect(linha.total).toBe(fila.contadores.total);
      expect(linha.receita).toBeCloseTo(fila.receita.total, 6);
      expect(linha.foqueSemConversa.n).toBe(fila.blocos.foque_agora.length);
      expect(linha.foqueSemConversa.valor).toBeCloseTo(emJogoDe(fila.blocos.foque_agora).valor, 6);
      expect(linha.parado).toEqual(emJogoDe(fila.blocos.nutricao));
      expect(linha.semInicio).toEqual(emJogoDe(fila.blocos.sem_inicio));
    }
    const soma = (f: (l: (typeof p.vendedores)[number]) => number) =>
      p.vendedores.reduce((s, l) => s + f(l), 0);
    expect(soma((l) => l.total)).toBe(p.total);
    expect(soma((l) => l.receita)).toBeCloseTo(p.receita, 4);
    expect(soma((l) => l.foqueSemConversa.n)).toBe(p.foqueSemConversa.n);
    expect(soma((l) => l.foqueSemConversa.valor)).toBeCloseTo(p.foqueSemConversa.valor, 4);
    expect(soma((l) => l.parado.valor)).toBe(p.parado.valor);
    expect(soma((l) => l.semInicio.valor)).toBe(p.semInicio.valor);
    // ordem: do que mais tem Foque sem próxima conversa para o que menos tem
    const ns = p.vendedores.map((l) => l.foqueSemConversa.n);
    expect(ns).toEqual([...ns].sort((a, b) => b - a));
    // quem não tem negócio aberto aparece com zero em tudo
    const semNegocio = servicos
      .organizacao()
      .vendedores.filter((v) => v.abertos === 0)
      .map((v) => v.nome);
    expect(semNegocio.length).toBeGreaterThan(0);
    for (const nome of semNegocio) {
      expect(p.vendedores.find((l) => l.vendedor === nome)).toMatchObject({
        total: 0,
        receita: 0,
        foqueSemConversa: { n: 0, valor: 0 },
        parado: { n: 0, valor: 0 },
        semInicio: { n: 0, valor: 0 },
        respostas: { n: 0, base: 0 },
      });
      expect(painelDe({ vendedor: nome })).toMatchObject({
        total: 0,
        receita: 0,
        foqueSemConversa: { n: 0, valor: 0 },
        parado: { n: 0, valor: 0 },
        semInicio: { n: 0, valor: 0 },
      });
    }
  });

  it('painel: as respostas mudam a métrica 2 e a coluna de respostas; o filtro por região muda os números', () => {
    const foque = filaDe({}).blocos.foque_agora;
    let completo: RespostasDoDeal | null = null;
    for (const [pergunta, valor] of [
      ['decisor', 'sim'],
      ['dor', 'sim'],
      ['proximo_passo', 'nao'],
    ] as const) {
      const r = responder(
        completo,
        foque[0]!.deal.id,
        metodoProvisorio,
        pergunta,
        valor,
        '2026-10-22T12:00:00Z',
      );
      if (!r.ok) throw new Error(r.erro.mensagem);
      completo = r.valor;
    }
    const sim = responder(
      null,
      foque[1]!.deal.id,
      metodoProvisorio,
      'proximo_passo',
      'sim',
      '2026-10-22T12:00:00Z',
    );
    if (!sim.ok || !completo) throw new Error('x');
    const antes = painelDe({});
    const p = painelDe({}, [completo, sim.valor]);
    // o "Sim" tira o negócio da métrica 2 (com o preço dele); o "Não" continua contando
    expect(p.foqueSemConversa).toMatchObject({ n: 32, foque: 33, sim: 1, nao: 1, semResposta: 31 });
    expect(p.foqueSemConversa.valor).toBeCloseTo(
      antes.foqueSemConversa.valor - foque[1]!.avaliacao.emJogo,
      6,
    );
    expect(p.respostas).toMatchObject({ n: 2, base: 557 });
    const doVendedor = p.vendedores.find((l) => l.vendedor === foque[1]!.deal.vendedor);
    expect(doVendedor?.respostas.n).toBeGreaterThan(0);
    // as respostas não mudam a receita, o parado nem os sem primeira conversa
    expect([p.receita, p.parado, p.semInicio]).toEqual([
      antes.receita,
      antes.parado,
      antes.semInicio,
    ]);

    // o filtro por região muda os números e a tabela traz só os vendedores dela
    const central = painelDe({ regiao: 'Central' });
    expect(central.total).toBe(908);
    expect(central.foqueSemConversa.n).toBe(0);
    expect(central.semInicio.n).toBe(500);
    const west = painelDe({ regiao: 'West' });
    expect(Math.round(west.receita)).toBe(38435);
    expect(west.foqueSemConversa).toMatchObject({ n: 17, valor: 36502, foque: 17 });
    expect(west.parado).toEqual({ n: 716, valor: 1935958 });
    expect(west.semInicio).toEqual({ n: 0, valor: 0 });
    expect(west.vendedores).toHaveLength(12);
    expect(west.receita).toBeLessThan(antes.receita);
    expect(west.receita).toBeCloseTo(filaDe({ regiao: 'West' }).receita.total, 6);
    const doTime = pipeline.time.filter((v) => v.regiao === 'West').map((v) => v.nome);
    expect(west.vendedores.map((l) => l.vendedor).sort()).toEqual([...doTime].sort());
    expect(
      west.vendedores.every((l) =>
        antes.vendedores.some((t) => t.vendedor === l.vendedor && t.parado.n === l.parado.n),
      ),
    ).toBe(true);
  });

  it('cada negócio mostra um indicador calculado e a ação do grupo', () => {
    const fila = filaDe({});
    const foque = fila.blocos.foque_agora[0];
    expect(foque?.indicador.numero).toMatch(/^Score \d{1,3}$/);
    expect(foque?.indicador.numero).toBe('Score ' + foque?.indicador.score);
    expect(foque?.indicador.rotulo).toBe('se o negócio é bom: a idade e as suas respostas');
    expect(foque?.indicador.emJogo).toMatch(/^[\w ]+ · US\$ [\d.]+ em jogo$/);
    expect(foque?.indicador.motivo).toMatch(
      /^Aberto há \d+ dias: \d+% dos negócios com essa idade fecharam \(a melhor faixa fecha 52%\)\.$/,
    );
    expect(foque?.indicador.posicaoTexto).toMatch(
      /^Na sua lista: \d+º de \d+ \(o grupo, depois o que há a ganhar\)\.$/,
    );
    expect(foque?.indicador.porqueScore).toEqual([
      foque?.indicador.motivo,
      foque?.indicador.posicaoTexto,
    ]);
    expect(foque?.indicador.chanceTexto).toMatch(/^Chance de fechar em 3 meses: \d+%$/);
    expect(foque?.indicador.parcelas[0]?.texto).toMatch(/^[+−]\d+ · Idade: \d+ dias \(/);
    expect(foque?.indicador.parcelas.find((p) => p.fator === 'setor')?.texto).toMatch(
      /^Setor: 0 · /,
    );
    expect(foque?.indicador.receita).toMatch(
      /^Deve render cerca de US\$ [\d.]+ em 3 meses \(estimativa pela chance\)\.$/,
    );
    expect(foque?.indicador.preco).toMatch(/^Preço de tabela: US\$ [\d.]+$/);
    expect(foque?.porque).toContain('Daqui pra frente a chance cai rápido.');
    expect(foque?.proximaAcao).toEqual({
      tipo: 'avancar_hoje',
      texto: 'A chance está caindo: marque a próxima conversa esta semana.',
      perguntaId: null,
    });
    const nutricao = fila.blocos.nutricao[0];
    expect(nutricao?.proximaAcao.tipo).toBe('encaminhar_para_nutricao');
    expect(nutricao?.proximaAcao.texto).toBe('Encaminhar para nutrição');
    expect(fila.blocos.sem_inicio).toHaveLength(500);
    expect(fila.blocos.siga_no_ritmo.every((i) => i.avaliacao.idadeDias !== null)).toBe(true);
    const semData = fila.blocos.sem_inicio[0];
    expect(semData?.indicador.chance).toBeNull();
    expect(semData?.indicador.motivo).toBe('Responda as perguntas para pontuar.');
    expect(semData?.indicador.score).toBeNull();
    expect(semData?.indicador.numero).toBe('Score —');
    expect(semData?.proximaAcao.tipo).toBe('qualificar');
  });

  it('de 61 a 90 dias a chance e a frase concordam: abaixo de 10%', () => {
    const itens = Object.values(filaDe({}).blocos).flat();
    const item = itens.find(
      (i) => (i.avaliacao.idadeDias ?? 0) > 60 && (i.avaliacao.idadeDias ?? 0) <= 90,
    );
    expect(item?.indicador.chance).toBeLessThan(0.1);
    expect(item?.porque).toBe(
      'Aberto há ' + item?.avaliacao.idadeDias + ' dias. Nessa idade, só 7% fecharam.',
    );
  });

  it('nenhum texto da fila usa "deal", "morto" ou "encerrar"', () => {
    const fila = filaDe({});
    for (const item of Object.values(fila.blocos).flat()) {
      const textos = [
        item.porque,
        item.proximaAcao.texto,
        item.indicador.motivo,
        item.indicador.numero,
        item.indicador.receita,
        item.indicador.posicaoTexto,
        item.indicador.chanceTexto,
        item.indicador.emJogo,
        ...item.indicador.porqueScore,
      ];
      for (const t of textos) expect(t).not.toMatch(/\bdeals?\b|morto|encerr|em 10\b|em cada 10/i);
    }
  });
});
