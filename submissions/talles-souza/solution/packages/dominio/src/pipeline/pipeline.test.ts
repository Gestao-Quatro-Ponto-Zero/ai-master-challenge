import { describe, expect, it } from 'vitest';
import {
  calcularJanela,
  conferirChecksum,
  criarDealDeLead,
  lerPipeline,
  sha256Hex,
  situacaoNaJanela,
  type Deal,
  type Janela,
  type Pipeline,
} from './index';

function bruto(parcial: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    opportunity_id: 'AAAA0001',
    sales_agent: 'Ana Lima',
    product: 'GTX Pro',
    account: 'Acme',
    deal_stage: 'Won',
    engage_date: '2017-01-01',
    close_date: '2017-02-10',
    close_value: 4800,
    produto_normalizado: false,
    manager: 'Bia Souza',
    regional_office: 'West',
    sector: 'retail',
    year_established: 2001,
    revenue: 718.62,
    employees: 4540,
    office_location: 'United States',
    subsidiary_of: null,
    setor_normalizado: false,
    series: 'GTX',
    sales_price: 4821,
    aberto: false,
    idade_dias: null,
    duracao_dias: 40,
    sem_conta: false,
    sem_engage_date: false,
    ...parcial,
  };
}

/** O time do arquivo: cada vendedor que aparece nos deals, com o manager e a região dele. */
function timeDe(deals: Record<string, unknown>[]) {
  const porNome = new Map<string, Record<string, unknown>>();
  for (const d of deals) {
    porNome.set(String(d.sales_agent), {
      sales_agent: d.sales_agent,
      manager: d.manager,
      regional_office: d.regional_office,
    });
  }
  return [...porNome.values()];
}

function arquivo(deals: Record<string, unknown>[], extra: Record<string, unknown> = {}) {
  return {
    formato: 2,
    referencia: '2017-12-31',
    total: deals.length,
    vendedores: timeDe(deals),
    deals,
    ...extra,
  };
}

function pipelineDe(deals: Record<string, unknown>[]): Pipeline {
  const lido = lerPipeline(arquivo(deals));
  if (!lido.ok) throw new Error(lido.erro.mensagem);
  return lido.valor;
}

const aberto = (id: string, idade: number | null, extra: Record<string, unknown> = {}) =>
  bruto({
    opportunity_id: id,
    deal_stage: idade === null ? 'Prospecting' : 'Engaging',
    engage_date: idade === null ? null : '2017-10-01',
    close_date: null,
    close_value: null,
    aberto: true,
    idade_dias: idade,
    duracao_dias: null,
    sem_engage_date: idade === null,
    ...extra,
  });

const BOM = String.fromCharCode(0xfeff);

describe('lerPipeline', () => {
  it('monta deals em camelCase, abertos, catálogo, contas e lacunas', () => {
    const semConta = {
      account: null,
      sector: null,
      revenue: null,
      employees: null,
      sem_conta: true,
    };
    const p = pipelineDe([
      bruto(),
      aberto('AAAA0002', 40),
      aberto('AAAA0003', null, {
        ...semConta,
        product: 'MG Special',
        sales_price: 55,
        series: 'MG',
      }),
    ]);
    expect(p.deals).toHaveLength(3);
    expect(p.abertos.map((d) => d.id)).toEqual(['AAAA0002', 'AAAA0003']);
    expect(p.deals[0]).toMatchObject({
      id: 'AAAA0001',
      vendedor: 'Ana Lima',
      regiao: 'West',
      precoTabela: 4821,
      funcionarios: 4540,
    });
    expect(p.catalogo).toEqual([
      { nome: 'GTX Pro', serie: 'GTX', precoTabela: 4821 },
      { nome: 'MG Special', serie: 'MG', precoTabela: 55 },
    ]);
    expect(p.contas).toEqual([
      { nome: 'Acme', setor: 'retail', funcionarios: 4540, receita: 718.62, empresaMae: null },
    ]);
    expect(p.lacunas).toEqual({
      sem_conta: 1,
      sem_engage_date: 1,
      produto_normalizado: 0,
      setor_normalizado: 0,
    });
    expect(p.deals[2]?.lacunas).toEqual(['sem_conta', 'sem_engage_date']);
  });

  it('recusa outro formato (o 1, sem o time, inclusive)', () => {
    const lido = lerPipeline(arquivo([bruto()], { formato: 1 }));
    expect(lido.ok ? null : lido.erro.codigo).toBe('formato_invalido');
  });

  it('o time vem do arquivo, inclusive quem não tem negócio; vendedor fora do time é recusado', () => {
    const comSemNegocio = lerPipeline(
      arquivo([bruto()], {
        vendedores: [
          { sales_agent: 'Zoe Sem Negocio', manager: 'Bia Souza', regional_office: 'West' },
          { sales_agent: 'Ana Lima', manager: 'Bia Souza', regional_office: 'West' },
        ],
      }),
    );
    if (!comSemNegocio.ok) throw new Error(comSemNegocio.erro.mensagem);
    expect(comSemNegocio.valor.time.map((v) => v.nome)).toEqual(['Ana Lima', 'Zoe Sem Negocio']);
    const fora = lerPipeline(
      arquivo([bruto()], {
        vendedores: [{ sales_agent: 'Outra', manager: 'Bia Souza', regional_office: 'West' }],
      }),
    );
    expect(fora.ok ? null : fora.erro.codigo).toBe('dados_invalidos');
    const semTime = lerPipeline(arquivo([bruto()], { vendedores: [] }));
    expect(semTime.ok ? null : semTime.erro.codigo).toBe('dados_invalidos');
  });

  it('recusa campo faltando, tipo errado e total que não bate', () => {
    const semCampo = bruto();
    delete semCampo.sales_price;
    for (const entrada of [
      arquivo([semCampo]),
      arquivo([bruto({ idade_dias: '40' })]),
      arquivo([bruto({ deal_stage: 'Open' })]),
      arquivo([bruto()], { total: 2 }),
      'não é json de deals',
    ]) {
      const lido = lerPipeline(entrada);
      expect(lido.ok ? null : lido.erro.codigo).toBe('dados_invalidos');
    }
  });
});

describe('calcularJanela e situacaoNaJanela', () => {
  const ganhos = [10, 20, 30, 40, 100].map((dur) => ({ estagio: 'Won', duracaoDias: dur }) as Deal);
  const perdido = { estagio: 'Lost', duracaoDias: 500 } as Deal;

  it('p50 e p95 por interpolação linear e o máximo, só nos ganhos', () => {
    expect(calcularJanela([...ganhos, perdido], '2017-12-31')).toEqual({
      referencia: '2017-12-31',
      ganhos: 5,
      p50Dias: 30,
      p95Dias: 88,
      maxDias: 100,
    });
  });

  it('sem ganhos, a janela fica zerada', () => {
    expect(calcularJanela([perdido], '2017-12-31')).toMatchObject({
      ganhos: 0,
      p50Dias: 0,
      p95Dias: 0,
      maxDias: 0,
    });
  });

  it('sem idade = prospecção; até p95 = na janela; até o máximo = perto do limite; além', () => {
    const janela: Janela = {
      referencia: '2017-12-31',
      ganhos: 5,
      p50Dias: 57,
      p95Dias: 116,
      maxDias: 138,
    };
    const comIdade = (idadeDias: number | null) => ({ idadeDias }) as Deal;
    expect(situacaoNaJanela(comIdade(null), janela)).toBe('prospeccao');
    expect(situacaoNaJanela(comIdade(116), janela)).toBe('na_janela');
    expect(situacaoNaJanela(comIdade(117), janela)).toBe('perto_do_limite');
    expect(situacaoNaJanela(comIdade(138), janela)).toBe('perto_do_limite');
    expect(situacaoNaJanela(comIdade(139), janela)).toBe('alem_da_janela');
  });
});

describe('criarDealDeLead', () => {
  const p = pipelineDe([bruto(), aberto('AAAA0002', 40)]);

  it('com data de engajamento: Engaging, idade até a referência, manager e região do vendedor, preço do catálogo', () => {
    const lido = criarDealDeLead(
      { vendedor: 'Ana Lima', produto: 'GTX Pro', conta: 'Acme', dataEngajamento: '2017-12-01' },
      p,
    );
    if (!lido.ok) throw new Error(lido.erro.mensagem);
    expect(lido.valor).toMatchObject({
      estagio: 'Engaging',
      idadeDias: 30,
      manager: 'Bia Souza',
      regiao: 'West',
      precoTabela: 4821,
      setor: 'retail',
      funcionarios: 4540,
      aberto: true,
      lacunas: [],
    });
    expect(lido.valor.id).toMatch(/^LEAD[0-9A-F]{8}$/);
  });

  it('sem data: Prospecting, sem idade; sem conta: lacuna, sem penalidade', () => {
    const lido = criarDealDeLead({ vendedor: 'Ana Lima', produto: 'GTX Pro' }, p);
    if (!lido.ok) throw new Error(lido.erro.mensagem);
    expect(lido.valor).toMatchObject({
      estagio: 'Prospecting',
      idadeDias: null,
      conta: null,
      lacunas: ['sem_conta', 'sem_engage_date'],
    });
  });

  it('o id é o mesmo para o mesmo lead', () => {
    const a = criarDealDeLead({ vendedor: 'Ana Lima', produto: 'GTX Pro' }, p);
    const b = criarDealDeLead({ vendedor: 'Ana Lima', produto: 'GTX Pro' }, p);
    expect(a.ok && b.ok && a.valor.id === b.valor.id).toBe(true);
  });

  it('recusa vendedor ou produto desconhecido e data depois da referência ou inexistente', () => {
    for (const lead of [
      { vendedor: 'Fulano', produto: 'GTX Pro' },
      { vendedor: 'Ana Lima', produto: 'Produto X' },
      { vendedor: 'Ana Lima', produto: 'GTX Pro', dataEngajamento: '2018-01-05' },
      { vendedor: 'Ana Lima', produto: 'GTX Pro', dataEngajamento: '2017-02-30' },
    ]) {
      const lido = criarDealDeLead(lead, p);
      expect(lido.ok ? null : lido.erro.codigo).toBe('lead_invalido');
    }
  });
});

describe('sha256Hex e conferirChecksum', () => {
  const abc = new TextEncoder().encode('abc');
  const hashAbc = 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad';

  it('calcula o SHA-256 conhecido de "abc"', async () => {
    expect(await sha256Hex(abc)).toBe(hashAbc);
  });

  it('aceita o formato do sha256sum com LF, CRLF e BOM', async () => {
    const conteudos = [
      hashAbc + '  deals.json\n',
      hashAbc.toUpperCase() + '  deals.json\r\n',
      BOM + hashAbc + '  deals.json\r\n',
    ];
    for (const conteudo of conteudos) {
      const lido = await conferirChecksum(abc, conteudo);
      expect(lido.ok ? lido.valor : lido.erro.codigo).toBe(hashAbc);
    }
  });

  it('acusa divergência e arquivo ilegível', async () => {
    const divergente = await conferirChecksum(abc, '0'.repeat(64) + '  deals.json\n');
    expect(divergente.ok ? null : divergente.erro.codigo).toBe('checksum_divergente');
    const ilegivel = await conferirChecksum(abc, 'sem hash aqui');
    expect(ilegivel.ok ? null : ilegivel.erro.codigo).toBe('checksum_ilegivel');
  });
});
