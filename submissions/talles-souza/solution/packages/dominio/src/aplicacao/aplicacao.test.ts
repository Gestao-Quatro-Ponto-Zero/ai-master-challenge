/// <reference types="node" />
// Casos de uso e troca de config: outra política e outro método mudam blocos, pendentes e fila
// sem tocar no motor.
import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { lerPipeline, type Pipeline } from '../pipeline';
import { politicaProvisoria, validarPolitica, type PoliticaPriorizacao } from '../priorizacao';
import {
  metodoProvisorio,
  responder,
  validarMetodo,
  type MetodoQualificacao,
} from '../qualificacao';
import { criarServicos } from './index';

const lido = lerPipeline(
  JSON.parse(readFileSync(new URL('../../../../data/deals.json', import.meta.url), 'utf8')),
);
if (!lido.ok) throw new Error(lido.erro.mensagem);
const pipeline: Pipeline = lido.valor;
const AGORA = '2017-12-31T12:00:00Z';

/** Política alternativa só do teste: Siga até 45, Foque até 90. */
const politica4590: PoliticaPriorizacao = {
  ...structuredClone(politicaProvisoria),
  id: 'politica-teste-45-90',
  faixas: [
    { bloco: 'siga_no_ritmo', ateDias: 45, rotulo: 'até 45 dias', porque: 'teste' },
    { bloco: 'foque_agora', ateDias: 90, rotulo: '46 a 90 dias', porque: 'teste' },
    { bloco: 'nutricao', ateDias: null, rotulo: 'acima de 90 dias', porque: 'teste' },
  ],
};

/** Método alternativo só do teste: outras perguntas, aplicadas em Siga no ritmo. */
const metodoAlternativo: MetodoQualificacao = {
  id: 'metodo-teste-alternativo',
  nome: 'Teste',
  versao: '0.0.1',
  provisorio: true,
  aviso: null,
  criterios: [],
  fontes: [],
  perguntas: [
    {
      id: 'pediu_proposta',
      rotulo: 'Pediu proposta',
      pergunta: 'O cliente pediu proposta?',
      aplicaEm: ['siga_no_ritmo'],
      acaoSeNao: 'Pergunte o que falta para o cliente pedir a proposta.',
      referencias: [],
      porque: 'teste',
    },
  ],
};

describe('troca de config (sem tocar no motor)', () => {
  it('os configs alternativos são válidos', () => {
    expect(validarPolitica(politica4590).ok).toBe(true);
    expect(validarMetodo(metodoAlternativo).ok).toBe(true);
  });

  it('outra política muda os blocos da fila real', () => {
    const padrao = criarServicos({ pipeline, checksum: 'x' }).fila({ filtro: {}, respostas: [] });
    const outra = criarServicos({ pipeline, checksum: 'x', politica: politica4590 }).fila({
      filtro: {},
      respostas: [],
    });
    if (!padrao.ok || !outra.ok) throw new Error('fila');
    const abertosComIdade = pipeline.abertos.filter((d) => d.idadeDias !== null);
    const esperado = (de: number, ate: number) =>
      abertosComIdade.filter((d) => (d.idadeDias as number) >= de && (d.idadeDias as number) <= ate)
        .length;
    expect(outra.valor.contadores.porBloco.foque_agora).toBe(esperado(46, 90));
    expect(outra.valor.contadores.porBloco.siga_no_ritmo).toBe(esperado(0, 45));
    expect(outra.valor.contadores.porBloco.foque_agora).not.toBe(
      padrao.valor.contadores.porBloco.foque_agora,
    );
    expect(outra.valor.contadores.total).toBe(padrao.valor.contadores.total);
  });

  it('outro método muda pendentes e a ação, nunca o bloco', () => {
    const servicos = criarServicos({ pipeline, checksum: 'x', metodo: metodoAlternativo });
    const umSiga = pipeline.abertos.find((d) => d.idadeDias !== null && d.idadeDias <= 40);
    if (!umSiga) throw new Error('sem deal em Siga');
    const antes = servicos.item({ dealId: umSiga.id });
    expect(antes.ok && antes.valor.pendentes.map((p) => p.id)).toEqual(['pediu_proposta']);
    const nao = responder(null, umSiga.id, metodoAlternativo, 'pediu_proposta', 'nao', AGORA);
    if (!nao.ok) throw new Error(nao.erro.mensagem);
    const depois = servicos.item({ dealId: umSiga.id, respostas: nao.valor });
    expect(depois.ok && depois.valor.bloco).toBe('siga_no_ritmo');
    expect(depois.ok && depois.valor.proximaAcao.texto).toBe(
      'Pergunte o que falta para o cliente pedir a proposta.',
    );
  });

  it('nenhuma resposta muda o grupo: "Não" (ou "Sim") nas 3 perguntas de todos os abertos', () => {
    const servicos = criarServicos({ pipeline, checksum: 'x' });
    const semResposta = servicos.fila({ filtro: {}, respostas: [] });
    if (!semResposta.ok) throw new Error('fila');
    const grupoDe = (f: typeof semResposta.valor) =>
      new Map(
        Object.values(f.blocos)
          .flat()
          .map((i) => [i.deal.id, i.bloco]),
      );
    const antes = grupoDe(semResposta.valor);
    for (const valor of ['nao', 'sim'] as const) {
      const respostas = pipeline.abertos.map((d) => {
        let r = null;
        for (const p of metodoProvisorio.perguntas) {
          const novo = responder(r, d.id, metodoProvisorio, p.id, valor, AGORA);
          if (!novo.ok) throw new Error(novo.erro.mensagem);
          r = novo.valor;
        }
        return r!;
      });
      const com = servicos.fila({ filtro: {}, respostas });
      if (!com.ok) throw new Error('fila');
      expect(com.valor.contadores).toEqual(semResposta.valor.contadores);
      const depois = grupoDe(com.valor);
      for (const [id, grupo] of antes) expect(depois.get(id)).toBe(grupo);
    }
  });

  it('o método padrão (BANT) não move bloco: só troca a ação', () => {
    const servicos = criarServicos({ pipeline, checksum: 'x' });
    const umFoque = pipeline.abertos.find(
      (d) => d.idadeDias !== null && d.idadeDias > 40 && d.idadeDias <= 60,
    );
    if (!umFoque) throw new Error('sem deal em Foque');
    const r = responder(null, umFoque.id, metodoProvisorio, 'decisor', 'nao', AGORA);
    if (!r.ok) throw new Error(r.erro.mensagem);
    const item = servicos.item({ dealId: umFoque.id, respostas: r.valor });
    if (!item.ok) throw new Error(item.erro.mensagem);
    expect(item.valor.bloco).toBe('foque_agora');
    expect(item.valor.proximaAcao.texto).toBe(
      'Descubra quem decide a compra e marque uma conversa com essa pessoa.',
    );
  });
});

describe('casos de uso', () => {
  const servicos = criarServicos({ pipeline, checksum: 'abc123' });

  it('resumo e deals com filtro e paginação', () => {
    expect(servicos.resumo()).toMatchObject({
      formato: 2,
      total: 8800,
      abertos: 2089,
      checksum: 'abc123',
    });
    const pagina = servicos.deals({
      regiao: 'Central',
      aberto: 'true',
      limite: 10,
      deslocamento: 5,
    });
    expect(pagina.total).toBe(908);
    expect(pagina.deals).toHaveLength(10);
    expect(pagina.deals.every((d) => d.regiao === 'Central' && d.aberto)).toBe(true);
    const ganhos = pipeline.deals.filter((d) => d.estagio === 'Won').length;
    expect(servicos.deals({ estagio: 'Won', limite: 1, deslocamento: 0 }).total).toBe(ganhos);
  });

  it('deal e avaliar: existente, inexistente e lead novo', () => {
    const id = pipeline.abertos[0]!.id;
    expect(servicos.deal(id)?.id).toBe(id);
    expect(servicos.deal('ZZZZZZZZ')).toBeNull();
    const nao = servicos.avaliar({ dealId: 'ZZZZZZZZ' });
    expect(nao.ok ? null : nao.erro.codigo).toBe('deal_nao_encontrado');
    const vendedor = pipeline.deals[0]!.vendedor;
    const lead = servicos.avaliar({
      lead: { vendedor, produto: 'GTX Pro', dataEngajamento: '2017-12-01' },
    });
    if (!lead.ok) throw new Error(lead.erro.mensagem);
    expect(lead.valor.avaliacao.idadeDias).toBe(30);
    expect(lead.valor.avaliacao.chance?.faixa).toBe('21 a 30 dias');
    const invalido = servicos.avaliar({ lead: { vendedor: 'Ninguém', produto: 'GTX Pro' } });
    expect(invalido.ok ? null : invalido.erro.codigo).toBe('lead_invalido');
  });

  it('item recusa respostas de outro deal ou de outro método', () => {
    const [a, b] = pipeline.abertos;
    const r = responder(null, b!.id, metodoProvisorio, 'dor', 'sim', AGORA);
    if (!r.ok) throw new Error(r.erro.mensagem);
    const outroDeal = servicos.item({ dealId: a!.id, respostas: r.valor });
    expect(outroDeal.ok ? null : outroDeal.erro.codigo).toBe('respostas_invalidas');
    const outroMetodo = servicos.item({
      dealId: b!.id,
      respostas: { ...r.valor, metodoId: 'outro' },
    });
    expect(outroMetodo.ok ? null : outroMetodo.erro.codigo).toBe('respostas_invalidas');
    const fila = servicos.fila({ filtro: {}, respostas: [{ ...r.valor, metodoId: 'outro' }] });
    expect(fila.ok ? null : fila.erro.codigo).toBe('respostas_invalidas');
  });

  it('item de lead novo sem data cai em "Aborde primeiro"', () => {
    const vendedor = pipeline.deals[0]!.vendedor;
    const item = servicos.item({ lead: { vendedor, produto: 'MG Special' } });
    if (!item.ok) throw new Error(item.erro.mensagem);
    expect(item.valor.bloco).toBe('sem_inicio');
    expect(item.valor.proximaAcao.tipo).toBe('qualificar');
  });

  it('organização, método, política, chance e pontos ficam disponíveis', () => {
    expect(servicos.organizacao().regioes).toEqual(['Central', 'East', 'West']);
    expect(servicos.metodo().nome).toBe('BANT');
    expect(servicos.politica().id).toBe(politicaProvisoria.id);
    expect(servicos.chance().faixas).toHaveLength(8);
    expect(servicos.pontos().atributos).toHaveLength(6);
  });
});
