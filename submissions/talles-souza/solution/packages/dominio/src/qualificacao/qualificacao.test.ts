import { describe, expect, it } from 'vitest';
import {
  criarRepositorioEmMemoria,
  decidir,
  decidirEmLote,
  mesclarRegistros,
  montarRegistros,
  metodoAtivo,
  metodoProvisorio,
  perguntasPendentes,
  responder,
  validarMetodo,
  validarRespostas,
  type MetodoQualificacao,
} from './index';

const AGORA = '2017-12-31T12:00:00Z';
const copia = (): MetodoQualificacao => structuredClone(metodoProvisorio);

describe('validarMetodo', () => {
  it('o método em uso (BANT) passa, com os critérios T, B, A, N e compromisso', () => {
    const lido = validarMetodo(metodoAtivo);
    expect(lido.ok).toBe(true);
    expect(metodoAtivo.criterios.map((c) => c.id)).toEqual(['T', 'B', 'A', 'N', 'compromisso']);
    expect(metodoAtivo.criterios.filter((c) => c.origem === 'dado').map((c) => c.id)).toEqual([
      'T',
      'B',
    ]);
    expect(metodoAtivo.perguntas.every((p) => p.acaoSeNao)).toBe(true);
  });

  it('recusa pergunta repetida, aplicaEm vazio, efeito sobre o bloco e critério sem pergunta', () => {
    const repetida = copia();
    repetida.perguntas.push(structuredClone(repetida.perguntas[0]!));
    const vazia = copia();
    vazia.perguntas[0]!.aplicaEm = [];
    // nenhuma resposta muda o bloco: o schema recusa um efeito `mover`, mesmo para bloco válido
    const comEfeito = copia() as unknown as { perguntas: { seSim: unknown }[] };
    comEfeito.perguntas[0]!.seSim = { tipo: 'mover', para: 'nutricao', motivo: 'x' };
    const criterioSolto = copia();
    criterioSolto.criterios[2]!.perguntaId = 'nao_existe';
    for (const m of [repetida, vazia, comEfeito, criterioSolto]) {
      const lido = validarMetodo(m);
      expect(lido.ok ? null : lido.erro.codigo).toBe('metodo_invalido');
    }
  });
});

describe('responder e validarRespostas', () => {
  it('registra a resposta e troca a anterior da mesma pergunta', () => {
    const r1 = responder(null, 'AAAA0001', metodoAtivo, 'decisor', 'nao', AGORA);
    if (!r1.ok) throw new Error(r1.erro.mensagem);
    const r2 = responder(r1.valor, 'AAAA0001', metodoAtivo, 'decisor', 'sim', AGORA);
    if (!r2.ok) throw new Error(r2.erro.mensagem);
    expect(r2.valor.respostas).toEqual([
      { perguntaId: 'decisor', valor: 'sim', respondidoEm: AGORA },
    ]);
    expect(r2.valor).toMatchObject({
      formato: 1,
      dealId: 'AAAA0001',
      metodoId: metodoAtivo.id,
      decisao: null,
    });
    expect(validarRespostas(r2.valor).ok).toBe(true);
  });

  it('recusa pergunta que não existe no método', () => {
    const lido = responder(null, 'AAAA0001', metodoAtivo, 'orcamento', 'sim', AGORA);
    expect(lido.ok ? null : lido.erro.codigo).toBe('pergunta_inexistente');
  });

  it('respostas de outro deal começam do zero', () => {
    const r1 = responder(null, 'AAAA0001', metodoAtivo, 'decisor', 'nao', AGORA);
    if (!r1.ok) throw new Error(r1.erro.mensagem);
    const r2 = responder(r1.valor, 'AAAA0002', metodoAtivo, 'dor', 'sim', AGORA);
    expect(r2.ok && r2.valor.respostas.map((r) => r.perguntaId)).toEqual(['dor']);
  });

  it('validarRespostas recusa formato errado', () => {
    const lido = validarRespostas({
      formato: 2,
      dealId: 'X',
      metodoId: 'm',
      respostas: [],
      decisao: null,
    });
    expect(lido.ok ? null : lido.erro.codigo).toBe('respostas_invalidas');
  });
});

describe('decidir', () => {
  it('contestar exige motivo', () => {
    const lido = decidir(
      null,
      'AAAA0001',
      metodoAtivo,
      { acao: 'avancar_hoje', aceita: false, motivo: ' ' },
      AGORA,
    );
    expect(lido.ok ? null : lido.erro.codigo).toBe('motivo_obrigatorio');
  });

  it('contestar com motivo guarda o motivo; aceitar sem motivo guarda null', () => {
    const contesta = decidir(
      null,
      'AAAA0001',
      metodoAtivo,
      { acao: 'avancar_hoje', aceita: false, motivo: 'cliente de férias' },
      AGORA,
    );
    expect(contesta.ok && contesta.valor.decisao).toEqual({
      acao: 'avancar_hoje',
      aceita: false,
      motivo: 'cliente de férias',
      em: AGORA,
    });
    const aceita = decidir(
      null,
      'AAAA0001',
      metodoAtivo,
      { acao: 'avancar_hoje', aceita: true },
      AGORA,
    );
    expect(aceita.ok && aceita.valor.decisao?.motivo).toBeNull();
  });

  it('encaminhar para nutrição fica registrado com a data e o motivo opcional', () => {
    const lido = decidir(
      null,
      'AAAA0001',
      metodoAtivo,
      { acao: 'encaminhar_para_nutricao', aceita: true, motivo: 'sem orçamento este ano' },
      AGORA,
    );
    if (!lido.ok) throw new Error(lido.erro.mensagem);
    expect(lido.valor.decisao).toEqual({
      acao: 'encaminhar_para_nutricao',
      aceita: true,
      motivo: 'sem orçamento este ano',
      em: AGORA,
    });
    expect(validarRespostas(lido.valor).ok).toBe(true);
  });

  it('a decisão preserva as respostas já dadas', () => {
    const r = responder(null, 'AAAA0001', metodoAtivo, 'dor', 'sim', AGORA);
    if (!r.ok) throw new Error(r.erro.mensagem);
    const d = decidir(
      r.valor,
      'AAAA0001',
      metodoAtivo,
      { acao: 'avancar_hoje', aceita: true },
      AGORA,
    );
    expect(d.ok && d.valor.respostas).toHaveLength(1);
  });
});

describe('perguntasPendentes', () => {
  it('só as do bloco, na ordem do config, sem as respondidas', () => {
    const r = responder(null, 'AAAA0001', metodoAtivo, 'dor', 'nao', AGORA);
    if (!r.ok) throw new Error(r.erro.mensagem);
    expect(perguntasPendentes(metodoAtivo, 'foque_agora', r.valor).map((p) => p.id)).toEqual([
      'decisor',
      'proximo_passo',
    ]);
    expect(perguntasPendentes(metodoAtivo, 'nutricao', null)).toEqual([]);
  });
});

describe('criarRepositorioEmMemoria', () => {
  it('salva, lê, lista e limpa', () => {
    const repo = criarRepositorioEmMemoria();
    const r = responder(null, 'AAAA0001', metodoAtivo, 'dor', 'sim', AGORA);
    if (!r.ok) throw new Error(r.erro.mensagem);
    repo.salvar(r.valor);
    expect(repo.ler('AAAA0001')).toEqual(r.valor);
    expect(repo.listar()).toHaveLength(1);
    repo.limpar('AAAA0001');
    expect(repo.ler('AAAA0001')).toBeNull();
  });
});

describe('decidirEmLote', () => {
  const nada = () => null;
  it('um registro por negócio, com a mesma data e o mesmo motivo', () => {
    const r = decidirEmLote(
      nada,
      ['AAAA0001', 'AAAA0002', 'AAAA0003'],
      metodoAtivo,
      { acao: 'encaminhar_para_nutricao', aceita: true },
      AGORA,
    );
    if (!r.ok) throw new Error(r.erro.mensagem);
    expect(r.valor.map((x) => x.dealId)).toEqual(['AAAA0001', 'AAAA0002', 'AAAA0003']);
    for (const x of r.valor) {
      expect(x.decisao).toEqual({
        acao: 'encaminhar_para_nutricao',
        aceita: true,
        motivo: null,
        em: AGORA,
      });
    }
  });

  it('mantém as respostas que cada negócio já tinha', () => {
    const antes = responder(null, 'AAAA0001', metodoAtivo, 'dor', 'sim', AGORA);
    if (!antes.ok) throw new Error('x');
    const r = decidirEmLote(
      (id) => (id === 'AAAA0001' ? antes.valor : null),
      ['AAAA0001'],
      metodoAtivo,
      { acao: 'encaminhar_para_nutricao', aceita: true },
      AGORA,
    );
    expect(r.ok && r.valor[0]?.respostas).toEqual(antes.valor.respostas);
  });

  it('recusa lote vazio, negócio repetido e contestação sem motivo', () => {
    const decisao = { acao: 'encaminhar_para_nutricao' as const, aceita: true };
    const vazio = decidirEmLote(nada, [], metodoAtivo, decisao, AGORA);
    expect(vazio.ok ? null : vazio.erro.codigo).toBe('lote_vazio');
    const repetido = decidirEmLote(nada, ['AAAA0001', 'AAAA0001'], metodoAtivo, decisao, AGORA);
    expect(repetido.ok ? null : repetido.erro.codigo).toBe('lote_repetido');
    const semMotivo = decidirEmLote(
      nada,
      ['AAAA0001'],
      metodoAtivo,
      { ...decisao, aceita: false },
      AGORA,
    );
    expect(semMotivo.ok ? null : semMotivo.erro.codigo).toBe('motivo_obrigatorio');
  });
});

describe('montarRegistros e mesclarRegistros', () => {
  const T1 = '2026-10-22T10:00:00.000Z';
  const T2 = '2026-10-22T11:00:00.000Z';
  it('por pergunta vale a resposta mais recente; a decisão também', () => {
    const regs = montarRegistros(
      [
        { dealId: 'B', vendedor: 'v', perguntaId: 'dor', valor: 'nao', em: T2 },
        { dealId: 'B', vendedor: 'v', perguntaId: 'dor', valor: 'sim', em: T1 },
        { dealId: 'A', vendedor: 'v', perguntaId: 'decisor', valor: 'sim', em: T1 },
      ],
      [
        { dealId: 'B', vendedor: 'v', acao: 'manter_ritmo', aceita: true, motivo: null, em: T1 },
        {
          dealId: 'B',
          vendedor: 'v',
          acao: 'manter_ritmo',
          aceita: false,
          motivo: 'cliente pediu tempo',
          em: T2,
        },
      ],
      metodoAtivo.id,
    );
    expect(regs.map((r) => r.dealId)).toEqual(['A', 'B']);
    expect(regs[1]?.respostas).toEqual([{ perguntaId: 'dor', valor: 'nao', respondidoEm: T2 }]);
    expect(regs[1]?.decisao).toMatchObject({ aceita: false, motivo: 'cliente pediu tempo' });
    for (const r of regs) expect(validarRespostas(r).ok).toBe(true);
  });

  it('mesclar o do navegador com o do servidor fica com o mais recente de cada pergunta', () => {
    const local = responder(null, 'A', metodoAtivo, 'dor', 'sim', T2);
    const servidor = responder(null, 'A', metodoAtivo, 'dor', 'nao', T1);
    if (!local.ok || !servidor.ok) throw new Error('x');
    const comDecisao = decidir(
      servidor.valor,
      'A',
      metodoAtivo,
      { acao: 'manter_ritmo', aceita: true },
      T1,
    );
    if (!comDecisao.ok) throw new Error('x');
    const junto = mesclarRegistros(local.valor, comDecisao.valor);
    expect(junto.respostas).toEqual([{ perguntaId: 'dor', valor: 'sim', respondidoEm: T2 }]);
    expect(junto.decisao?.em).toBe(T1);
  });
});
