/**
 * O banco compartilhado. Sem `DATABASE_URL`, roda só a parte de unidade, com um banco falso: o
 * SQL é só SELECT e INSERT em `lead_scorer.*`, as linhas viram o formato do domínio, o lote é um
 * INSERT só, a queda do banco cai para a memória e o metadado divergente faz usar o arquivo.
 * Com `DATABASE_URL`, roda também a integração contra o banco de verdade; as gravações ficam
 * numa transação desfeita (ROLLBACK), então nada fica no banco.
 */
import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import {
  CAMINHO_PADRAO_DEALS,
  carregarDados,
  carregarDoBanco,
  montarDependencias,
} from '../src/carregador';
import { criarBanco, criarDisjuntorBanco, type Consultor } from '../src/infra/banco';
import {
  acaoParaTexto,
  criarArmazemNoBanco,
  criarArmazemResiliente,
  textoParaAcao,
} from '../src/qualificacao';

const EM = '2026-10-22T12:00:00.000Z';
const arquivo = JSON.parse(readFileSync(CAMINHO_PADRAO_DEALS, 'utf8')) as {
  formato: number;
  referencia: string;
  vendedores: object[];
  deals: object[];
};
const checksum = readFileSync(CAMINHO_PADRAO_DEALS + '.sha256', 'utf8').slice(0, 64);

/** Banco falso: responde por trecho do SQL e grava cada chamada. */
function bancoFalso(responder: (sql: string) => object[] | Error = () => []) {
  const chamadas: { sql: string; parametros: readonly unknown[] }[] = [];
  const consultor: Consultor = {
    async consultar<T extends object>(sql: string, parametros: readonly unknown[] = []) {
      chamadas.push({ sql, parametros });
      const r = responder(sql);
      if (r instanceof Error) throw r;
      return r as T[];
    },
  };
  return { consultor, chamadas };
}

describe('armazém no banco (banco falso)', () => {
  it('a ação da decisão vira texto e volta igual; texto estranho é ignorado', () => {
    expect(acaoParaTexto('encaminhar_para_nutricao', true)).toBe(
      'aceitar:encaminhar_para_nutricao',
    );
    expect(textoParaAcao('contestar:avancar_hoje')).toEqual({
      acao: 'avancar_hoje',
      aceita: false,
    });
    expect(textoParaAcao('apagar:tudo')).toBeNull();
    expect(textoParaAcao('aceitar:outra_coisa')).toBeNull();
  });

  it('lê as linhas e converte para o domínio (boolean → sim/não, data → ISO)', async () => {
    const { consultor } = bancoFalso((sql) =>
      sql.includes('from lead_scorer.respostas')
        ? [
            {
              opportunity_id: 'AAAA0001',
              sales_agent: 'Ana',
              pergunta: 'dor',
              resposta: false,
              respondido_em: new Date(EM),
            },
          ]
        : [
            {
              opportunity_id: 'AAAA0001',
              sales_agent: 'Ana',
              acao: 'contestar:avancar_hoje',
              motivo: 'cliente pediu tempo',
              decidido_em: new Date(EM),
            },
            {
              opportunity_id: 'AAAA0002',
              sales_agent: 'Ana',
              acao: 'formato-antigo',
              motivo: null,
              decidido_em: new Date(EM),
            },
          ],
    );
    const linhas = await criarArmazemNoBanco(consultor).listar();
    expect(linhas.respostas).toEqual([
      { dealId: 'AAAA0001', vendedor: 'Ana', perguntaId: 'dor', valor: 'nao', em: EM },
    ]);
    expect(linhas.decisoes).toEqual([
      {
        dealId: 'AAAA0001',
        vendedor: 'Ana',
        acao: 'avancar_hoje',
        aceita: false,
        motivo: 'cliente pediu tempo',
        em: EM,
      },
    ]);
  });

  it('grava só com INSERT em lead_scorer; o lote é um INSERT só, com a mesma data', async () => {
    const { consultor, chamadas } = bancoFalso();
    const armazem = criarArmazemNoBanco(consultor);
    await armazem.gravarResposta({
      dealId: 'AAAA0001',
      vendedor: 'Ana',
      perguntaId: 'dor',
      valor: 'sim',
      em: EM,
    });
    const lote = ['AAAA0001', 'AAAA0002', 'AAAA0003'].map((dealId) => ({
      dealId,
      vendedor: 'Ana',
      acao: 'encaminhar_para_nutricao' as const,
      aceita: true,
      motivo: null,
      em: EM,
    }));
    await armazem.gravarDecisoes(lote);
    expect(chamadas).toHaveLength(2);
    expect(chamadas[0]?.sql).toMatch(/^insert into lead_scorer\.respostas /);
    expect(chamadas[0]?.parametros).toEqual(['AAAA0001', 'Ana', 'dor', true, EM]);
    expect(chamadas[1]?.sql).toMatch(/^insert into lead_scorer\.decisoes .* unnest\(/);
    expect(chamadas[1]?.parametros).toEqual([
      ['AAAA0001', 'AAAA0002', 'AAAA0003'],
      ['Ana', 'Ana', 'Ana'],
      Array(3).fill('aceitar:encaminhar_para_nutricao'),
      [null, null, null],
      [EM, EM, EM],
    ]);
    for (const c of chamadas) {
      expect(c.sql).not.toMatch(/\b(update|delete|drop|alter|create|truncate)\b/i);
    }
  });

  it('banco fora: grava e lê na memória e diz "memoria"; o disjuntor abre depois de 3 falhas', async () => {
    let fora = true;
    let tentativas = 0;
    const { consultor } = bancoFalso(() => {
      tentativas += 1;
      return fora ? new Error('connection refused') : [];
    });
    let agora = 0;
    const disjuntor = criarDisjuntorBanco({
      falhasParaAbrir: 3,
      abertoPorMs: 30_000,
      relogio: () => agora,
    });
    const logs: string[] = [];
    const armazem = criarArmazemResiliente(criarArmazemNoBanco(consultor), disjuntor, (l) =>
      logs.push(l),
    );
    expect(armazem.tipo()).toBe('banco');
    await armazem.gravarResposta({
      dealId: 'AAAA0001',
      vendedor: 'Ana',
      perguntaId: 'dor',
      valor: 'sim',
      em: EM,
    });
    expect(armazem.tipo()).toBe('memoria');
    expect((await armazem.listar()).respostas).toHaveLength(1);
    await armazem.listar();
    expect(disjuntor.aberto()).toBe(true);
    const antes = tentativas;
    await armazem.listar(); // circuito aberto: nem tenta o banco
    expect(tentativas).toBe(antes);
    expect(logs).toHaveLength(1);
    // o banco volta e o tempo passa: a próxima tentativa fecha o circuito e junta a memória
    fora = false;
    agora = 31_000;
    const depois = await armazem.listar();
    expect(armazem.tipo()).toBe('banco');
    expect(depois.respostas).toHaveLength(1);
  });
});

describe('negócios vindos do banco (banco falso)', () => {
  const metadados = (sha: string) => [
    { chave: 'formato', valor: String(arquivo.formato) },
    { chave: 'referencia', valor: arquivo.referencia },
    { chave: 'sha256_deals_json', valor: sha },
  ];
  const responder = (sha: string) => (sql: string) =>
    sql.includes('lead_scorer.metadados')
      ? metadados(sha)
      : sql.includes('lead_scorer.vendedores')
        ? arquivo.vendedores
        : arquivo.deals;

  it('metadado igual ao deals.json embarcado: o mesmo pipeline (8.800 negócios, 35 vendedores)', async () => {
    const { consultor } = bancoFalso(responder(checksum));
    const r = await carregarDoBanco(consultor, checksum);
    if (!r.ok) throw new Error(r.erro.mensagem);
    expect(r.valor.dados).toEqual({ total: 8800, referencia: '2017-12-31', checksum });
    expect(r.valor.servicos.organizacao().vendedores).toHaveLength(35);
    const fila = r.valor.servicos.fila({ filtro: {}, respostas: [] });
    // na tela: com o Foque vazio, o Siga do vendedor sobe (3 negócios de 2 vendedores); pela idade, 30 e 27
    expect(fila.ok && fila.valor.contadores.porBloco).toEqual({
      foque_agora: 33,
      siga_no_ritmo: 24,
      nutricao: 1532,
      sem_inicio: 500,
    });
  });

  it('metadado de outro deals.json: recusa com metadado_divergente, sem ler os negócios', async () => {
    const { consultor, chamadas } = bancoFalso(responder('0'.repeat(64)));
    const r = await carregarDoBanco(consultor, checksum);
    expect(r.ok ? null : r.erro.codigo).toBe('metadado_divergente');
    expect(chamadas).toHaveLength(1);
  });

  it('sem DATABASE_URL: deals.json e respostas na memória', async () => {
    const r = await montarDependencias({}, CAMINHO_PADRAO_DEALS, () => {});
    if (!r.ok) throw new Error(r.erro.mensagem);
    expect(r.valor.origem).toBe('arquivo');
    expect(r.valor.registros.tipo()).toBe('memoria');
    expect(r.valor.dados.checksum).toBe(checksum);
  });
});

const URL_BANCO = process.env['DATABASE_URL']?.trim();

describe.skipIf(!URL_BANCO)('integração com o banco compartilhado (DATABASE_URL)', () => {
  it('lê os negócios do banco, conferidos contra o deals.json embarcado', async () => {
    const logs: string[] = [];
    const r = await montarDependencias({ DATABASE_URL: URL_BANCO }, CAMINHO_PADRAO_DEALS, (l) =>
      logs.push(l),
    );
    if (!r.ok) throw new Error(r.erro.mensagem);
    try {
      expect(
        logs,
        'recarregue lead_scorer.metadados: formato ' + arquivo.formato + ', sha256 ' + checksum,
      ).toEqual([]);
      expect(r.valor.origem).toBe('banco');
      expect(r.valor.registros.tipo()).toBe('banco');
      const doArquivo = await carregarDados(CAMINHO_PADRAO_DEALS);
      if (!doArquivo.ok) throw new Error('arquivo');
      const pedido = { filtro: {}, respostas: [] };
      expect(r.valor.servicos.fila(pedido)).toEqual(doArquivo.valor.servicos.fila(pedido));
      expect(r.valor.servicos.organizacao()).toEqual(doArquivo.valor.servicos.organizacao());
      await r.valor.registros.listar(); // o papel lê respostas e decisões
      expect(r.valor.registros.tipo()).toBe('banco');
    } finally {
      await r.valor.fechar();
    }
  }, 30_000);

  it('grava resposta e lote e lê de volta, numa transação desfeita (nada fica no banco)', async () => {
    const banco = criarBanco(URL_BANCO as string, () => {});
    try {
      const deals = await banco.consultar<{ opportunity_id: string; sales_agent: string }>(
        'select opportunity_id, sales_agent from lead_scorer.deals ' +
          'where aberto order by opportunity_id limit 3',
      );
      const [a] = deals;
      if (!a) throw new Error('sem negócio aberto no banco');
      const antes = await criarArmazemNoBanco(banco).listar();
      const lidas = await banco.transacao(
        async (tx) => {
          const armazem = criarArmazemNoBanco(tx);
          await armazem.gravarResposta({
            dealId: a.opportunity_id,
            vendedor: a.sales_agent,
            perguntaId: 'dor',
            valor: 'sim',
            em: EM,
          });
          await armazem.gravarDecisoes(
            deals.map((d) => ({
              dealId: d.opportunity_id,
              vendedor: d.sales_agent,
              acao: 'encaminhar_para_nutricao' as const,
              aceita: true,
              motivo: null,
              em: EM,
            })),
          );
          return armazem.listar();
        },
        { desfazer: true },
      );
      expect(lidas.respostas.length).toBe(antes.respostas.length + 1);
      expect(lidas.decisoes.length).toBe(antes.decisoes.length + deals.length);
      expect(lidas.decisoes.slice(-deals.length).every((d) => d.em === EM)).toBe(true);
      // ROLLBACK: o banco ficou como estava
      const depois = await criarArmazemNoBanco(banco).listar();
      expect(depois.respostas.length).toBe(antes.respostas.length);
      expect(depois.decisoes.length).toBe(antes.decisoes.length);
    } finally {
      await banco.fechar();
    }
  }, 30_000);

  it('o papel do app não altera nem apaga (UPDATE e DELETE são recusados)', async () => {
    const banco = criarBanco(URL_BANCO as string, () => {});
    try {
      for (const sql of [
        'update lead_scorer.respostas set pergunta = pergunta where false',
        'delete from lead_scorer.decisoes where false',
      ]) {
        await expect(
          banco.transacao((tx) => tx.consultar(sql), { desfazer: true }),
        ).rejects.toThrow();
      }
    } finally {
      await banco.fechar();
    }
  }, 30_000);
});
