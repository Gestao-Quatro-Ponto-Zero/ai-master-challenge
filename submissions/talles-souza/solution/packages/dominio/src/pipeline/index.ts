/**
 * Contexto `pipeline`: carrega e valida o `deals.json` gerado por `data/preparar_dados.py`,
 * expõe os deals, a idade, a janela em que ganhos fecham e as lacunas do dataset.
 * O arquivo também traz o time de vendas inteiro (formato 2), inclusive quem não tem negócio.
 * Contrato público: só o que está exportado aqui (e em ./http).
 */
import { z } from 'zod';
import { falha, ok, type Resultado } from '../compartilhado';

export * from './http';

/** Versão do formato do `deals.json` (2 = com o time de vendas); o loader recusa outra. */
export const FORMATO_DEALS = 2 as const;

/** Estágio do deal no CRM. */
export type Estagio = 'Prospecting' | 'Engaging' | 'Won' | 'Lost';

/** Lacunas e correções que o `preparar_dados.py` marcou no deal. */
export type Lacuna = 'sem_conta' | 'sem_engage_date' | 'produto_normalizado' | 'setor_normalizado';

/** Um deal do CRM, já com as 4 tabelas juntas. Datas em ISO `AAAA-MM-DD`. */
export interface Deal {
  id: string;
  vendedor: string;
  manager: string;
  regiao: string;
  produto: string;
  serie: string;
  /** Preço de tabela do produto (US$). */
  precoTabela: number;
  conta: string | null;
  setor: string | null;
  funcionarios: number | null;
  receitaConta: number | null;
  /** Empresa-mãe da conta (`subsidiary_of`); null sem conta ou conta independente. */
  empresaMae: string | null;
  estagio: Estagio;
  dataEngajamento: string | null;
  dataFechamento: string | null;
  valorFechamento: number | null;
  aberto: boolean;
  /** Dias entre o engajamento e a data de referência; só nos abertos com engajamento. */
  idadeDias: number | null;
  /** Dias entre engajamento e fechamento; só nos fechados. */
  duracaoDias: number | null;
  lacunas: Lacuna[];
}

/** Um vendedor do time (de `sales_teams.csv`), com ou sem negócio. */
export interface MembroDoTime {
  nome: string;
  manager: string;
  regiao: string;
}

/** Um produto do catálogo, com o preço de tabela. */
export interface Produto {
  nome: string;
  serie: string;
  precoTabela: number;
}

/** Uma conta (cliente) com os dados de porte que o CRM traz. */
export interface Conta {
  nome: string;
  setor: string;
  funcionarios: number;
  receita: number;
  /** Empresa-mãe (`subsidiary_of`); null se a conta é independente. */
  empresaMae: string | null;
}

/** Janela medida nos ganhos: quanto tempo deals ganhos levaram para fechar. */
export interface Janela {
  /** "Hoje" do dataset: o último `close_date` (premissa declarada). */
  referencia: string;
  ganhos: number;
  p50Dias: number;
  p95Dias: number;
  maxDias: number;
}

/** Onde um deal aberto está em relação à janela dos ganhos. */
export type SituacaoJanela = 'prospeccao' | 'na_janela' | 'perto_do_limite' | 'alem_da_janela';

/** O pipeline carregado e validado. */
export interface Pipeline {
  formato: typeof FORMATO_DEALS;
  referencia: string;
  deals: Deal[];
  abertos: Deal[];
  /** O time de vendas inteiro, em ordem de nome (os 35, inclusive os sem negócio). */
  time: MembroDoTime[];
  janela: Janela;
  catalogo: Produto[];
  contas: Conta[];
  lacunas: Record<Lacuna, number>;
}

/** Entrada da tela "Novo lead": um lead sem histórico no CRM. */
export interface NovoLead {
  vendedor: string;
  produto: string;
  conta?: string | undefined;
  /** ISO `AAAA-MM-DD`; sem ela o lead entra como Prospecting, sem idade. */
  dataEngajamento?: string | undefined;
}

const DATA_ISO = /^\d{4}-\d{2}-\d{2}$/;
const dataIso = z.string().regex(DATA_ISO);
const textoNulo = z.string().nullable();
const numeroNulo = z.number().nullable();

const dealBrutoSchema = z.object({
  opportunity_id: z.string().min(1),
  sales_agent: z.string().min(1),
  product: z.string().min(1),
  account: textoNulo,
  deal_stage: z.enum(['Prospecting', 'Engaging', 'Won', 'Lost']),
  engage_date: dataIso.nullable(),
  close_date: dataIso.nullable(),
  close_value: numeroNulo,
  produto_normalizado: z.boolean(),
  manager: z.string().min(1),
  regional_office: z.string().min(1),
  sector: textoNulo,
  year_established: numeroNulo,
  revenue: numeroNulo,
  employees: numeroNulo,
  office_location: textoNulo,
  subsidiary_of: textoNulo,
  setor_normalizado: z.boolean(),
  series: z.string().min(1),
  sales_price: z.number(),
  aberto: z.boolean(),
  idade_dias: z.number().int().nullable(),
  duracao_dias: z.number().int().nullable(),
  sem_conta: z.boolean(),
  sem_engage_date: z.boolean(),
});
type DealBruto = z.infer<typeof dealBrutoSchema>;

const arquivoSchema = z.object({
  formato: z.number(),
  referencia: dataIso,
  total: z.number().int().min(0),
  vendedores: z
    .array(
      z.strictObject({
        sales_agent: z.string().min(1),
        manager: z.string().min(1),
        regional_office: z.string().min(1),
      }),
    )
    .min(1),
  deals: z.array(dealBrutoSchema),
});

function paraDeal(b: DealBruto): Deal {
  const lacunas: Lacuna[] = [];
  if (b.sem_conta) lacunas.push('sem_conta');
  if (b.sem_engage_date) lacunas.push('sem_engage_date');
  if (b.produto_normalizado) lacunas.push('produto_normalizado');
  if (b.setor_normalizado) lacunas.push('setor_normalizado');
  return {
    id: b.opportunity_id,
    vendedor: b.sales_agent,
    manager: b.manager,
    regiao: b.regional_office,
    produto: b.product,
    serie: b.series,
    precoTabela: b.sales_price,
    conta: b.account,
    setor: b.sector,
    funcionarios: b.employees,
    receitaConta: b.revenue,
    empresaMae: b.subsidiary_of,
    estagio: b.deal_stage,
    dataEngajamento: b.engage_date,
    dataFechamento: b.close_date,
    valorFechamento: b.close_value,
    aberto: b.aberto,
    idadeDias: b.idade_dias,
    duracaoDias: b.duracao_dias,
    lacunas,
  };
}

function porNome<T extends { nome: string }>(a: T, b: T): number {
  return a.nome.localeCompare(b.nome, 'pt-BR');
}

function montarCatalogo(deals: readonly Deal[]): Produto[] {
  const produtos = new Map<string, Produto>();
  for (const d of deals) {
    if (!produtos.has(d.produto))
      produtos.set(d.produto, { nome: d.produto, serie: d.serie, precoTabela: d.precoTabela });
  }
  return [...produtos.values()].sort(porNome);
}

function montarContas(deals: readonly Deal[]): Conta[] {
  const contas = new Map<string, Conta>();
  for (const d of deals) {
    if (d.conta === null || contas.has(d.conta)) continue;
    if (d.setor === null || d.funcionarios === null || d.receitaConta === null) continue;
    contas.set(d.conta, {
      nome: d.conta,
      setor: d.setor,
      funcionarios: d.funcionarios,
      receita: d.receitaConta,
      empresaMae: d.empresaMae,
    });
  }
  return [...contas.values()].sort(porNome);
}

function contarLacunas(deals: readonly Deal[]): Record<Lacuna, number> {
  const contagem: Record<Lacuna, number> = {
    sem_conta: 0,
    sem_engage_date: 0,
    produto_normalizado: 0,
    setor_normalizado: 0,
  };
  for (const d of deals) for (const l of d.lacunas) contagem[l] += 1;
  return contagem;
}

/**
 * Valida o JSON bruto do `deals.json` (schema + formato) e monta o Pipeline.
 * Erros: `dados_invalidos` (campo faltando, tipo errado, total que não bate, vendedor fora do
 * time, vendedor repetido) e `formato_invalido`.
 */
export function lerPipeline(bruto: unknown): Resultado<Pipeline> {
  const lido = arquivoSchema.safeParse(bruto);
  if (!lido.success) {
    const detalhes = lido.error.issues
      .slice(0, 20)
      .map((i) => ({ caminho: i.path.join('.'), mensagem: i.message }));
    return falha('dados_invalidos', 'O deals.json não segue o formato esperado.', detalhes);
  }
  const arquivo = lido.data;
  if (arquivo.formato !== FORMATO_DEALS) {
    return falha(
      'formato_invalido',
      'O deals.json está no formato ' +
        arquivo.formato +
        '; este sistema lê o formato ' +
        FORMATO_DEALS +
        '.',
    );
  }
  if (arquivo.total !== arquivo.deals.length) {
    return falha(
      'dados_invalidos',
      'O deals.json declara ' + arquivo.total + ' deals e traz ' + arquivo.deals.length + '.',
    );
  }
  const time: MembroDoTime[] = arquivo.vendedores
    .map((v) => ({ nome: v.sales_agent, manager: v.manager, regiao: v.regional_office }))
    .sort(porNome);
  const nomes = new Set(time.map((v) => v.nome));
  if (nomes.size !== time.length)
    return falha('dados_invalidos', 'O deals.json repete um vendedor no time.');
  const deals = arquivo.deals.map(paraDeal);
  const fora = deals.find((d) => !nomes.has(d.vendedor));
  if (fora)
    return falha(
      'dados_invalidos',
      'O negócio ' + fora.id + ' é de um vendedor fora do time: ' + fora.vendedor + '.',
    );
  return ok({
    formato: FORMATO_DEALS,
    referencia: arquivo.referencia,
    deals,
    abertos: deals.filter((d) => d.aberto),
    time,
    janela: calcularJanela(deals, arquivo.referencia),
    catalogo: montarCatalogo(deals),
    contas: montarContas(deals),
    lacunas: contarLacunas(deals),
  });
}

/** Percentil por interpolação linear entre os vizinhos (o padrão do numpy). */
function percentil(ordenados: readonly number[], p: number): number {
  if (ordenados.length === 0) return 0;
  const h = (ordenados.length - 1) * p;
  const baixo = Math.floor(h);
  const alto = Math.min(baixo + 1, ordenados.length - 1);
  const a = ordenados[baixo] ?? 0;
  const b = ordenados[alto] ?? a;
  return a + (h - baixo) * (b - a);
}

/** Mede a janela dos ganhos (p50, p95, máximo da duração) a partir dos deals Won. */
export function calcularJanela(deals: readonly Deal[], referencia: string): Janela {
  const duracoes = deals
    .filter((d) => d.estagio === 'Won' && d.duracaoDias !== null)
    .map((d) => d.duracaoDias as number)
    .sort((a, b) => a - b);
  return {
    referencia,
    ganhos: duracoes.length,
    p50Dias: Math.round(percentil(duracoes, 0.5)),
    p95Dias: Math.round(percentil(duracoes, 0.95)),
    maxDias: duracoes[duracoes.length - 1] ?? 0,
  };
}

/** Classifica um deal aberto contra a janela: sem idade = prospecção; até p95 = na janela; até o máximo = perto do limite; além. */
export function situacaoNaJanela(deal: Deal, janela: Janela): SituacaoJanela {
  if (deal.idadeDias === null) return 'prospeccao';
  if (deal.idadeDias <= janela.p95Dias) return 'na_janela';
  if (deal.idadeDias <= janela.maxDias) return 'perto_do_limite';
  return 'alem_da_janela';
}

const DIA_MS = 86_400_000;

/** Milissegundos UTC de uma data ISO `AAAA-MM-DD` válida no calendário; null se não for. */
function diaUtc(iso: string): number | null {
  if (!DATA_ISO.test(iso)) return null;
  const t = Date.parse(iso + 'T00:00:00Z');
  if (Number.isNaN(t) || new Date(t).toISOString().slice(0, 10) !== iso) return null;
  return t;
}

/** Hash curto e estável (FNV-1a de 32 bits) para dar ao lead novo um id reproduzível. */
function idDoLead(lead: NovoLead): string {
  const chave = [lead.vendedor, lead.produto, lead.conta ?? '', lead.dataEngajamento ?? ''].join(
    '|',
  );
  let h = 0x811c9dc5;
  for (let i = 0; i < chave.length; i++) {
    h ^= chave.charCodeAt(i);
    h = Math.imul(h, 0x01000193) >>> 0;
  }
  return 'LEAD' + h.toString(16).toUpperCase().padStart(8, '0');
}

/**
 * Monta um Deal a partir de um lead novo (o vendedor precisa estar no time e o produto no
 * catálogo). O manager e a região vêm do time; o preço, do catálogo. Com `dataEngajamento` o lead entra
 * como Engaging, com a idade até a referência; sem ela, como Prospecting, sem idade. O id é
 * estável para o mesmo lead (`LEAD` + 8 dígitos hexadecimais), para as respostas se ligarem a ele.
 * Erro: `lead_invalido`.
 */
export function criarDealDeLead(lead: NovoLead, pipeline: Pipeline): Resultado<Deal> {
  const membro = pipeline.time.find((v) => v.nome === lead.vendedor);
  const doVendedor = membro && {
    vendedor: membro.nome,
    manager: membro.manager,
    regiao: membro.regiao,
  };
  if (!doVendedor) return falha('lead_invalido', 'Vendedor não encontrado: ' + lead.vendedor + '.');
  const produto = pipeline.catalogo.find((p) => p.nome === lead.produto);
  if (!produto) return falha('lead_invalido', 'Produto fora do catálogo: ' + lead.produto + '.');

  let idadeDias: number | null = null;
  if (lead.dataEngajamento !== undefined) {
    const engajamento = diaUtc(lead.dataEngajamento);
    const referencia = diaUtc(pipeline.referencia);
    if (engajamento === null || referencia === null) {
      return falha('lead_invalido', 'Data de engajamento inválida: ' + lead.dataEngajamento + '.');
    }
    if (engajamento > referencia) {
      return falha(
        'lead_invalido',
        'A data de engajamento (' +
          lead.dataEngajamento +
          ') é depois de hoje no dataset (' +
          pipeline.referencia +
          ').',
      );
    }
    idadeDias = Math.round((referencia - engajamento) / DIA_MS);
  }

  const nomeConta = lead.conta?.trim() ? lead.conta.trim() : null;
  const conta = nomeConta === null ? undefined : pipeline.contas.find((c) => c.nome === nomeConta);
  const lacunas: Lacuna[] = [];
  if (nomeConta === null) lacunas.push('sem_conta');
  if (idadeDias === null) lacunas.push('sem_engage_date');

  return ok({
    id: idDoLead(lead),
    vendedor: doVendedor.vendedor,
    manager: doVendedor.manager,
    regiao: doVendedor.regiao,
    produto: produto.nome,
    serie: produto.serie,
    precoTabela: produto.precoTabela,
    conta: nomeConta,
    setor: conta?.setor ?? null,
    funcionarios: conta?.funcionarios ?? null,
    receitaConta: conta?.receita ?? null,
    empresaMae: conta?.empresaMae ?? null,
    estagio: idadeDias === null ? 'Prospecting' : 'Engaging',
    dataEngajamento: idadeDias === null ? null : (lead.dataEngajamento ?? null),
    dataFechamento: null,
    valorFechamento: null,
    aberto: true,
    idadeDias,
    duracaoDias: null,
    lacunas,
  });
}

/** SHA-256 em hexadecimal, pela Web Crypto (existe no Node 22 e nos navegadores). */
export async function sha256Hex(bytes: Uint8Array): Promise<string> {
  const resumo = await globalThis.crypto.subtle.digest('SHA-256', new Uint8Array(bytes));
  return [...new Uint8Array(resumo)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

/**
 * Confere os bytes do `deals.json` contra o conteúdo do `deals.json.sha256`
 * (formato do `sha256sum`: `<hex>  deals.json`, com LF ou CRLF). Devolve o hash conferido.
 * Erros: `checksum_ilegivel` (arquivo fora do formato), `checksum_divergente` e
 * `checksum_indisponivel` (sem Web Crypto: página servida por HTTP fora de localhost).
 */
export async function conferirChecksum(
  bytes: Uint8Array,
  arquivoSha256: string,
): Promise<Resultado<string>> {
  // trim() também tira o BOM (U+FEFF) de um arquivo salvo por editor no Windows
  const linha = arquivoSha256.trim().split(/\r?\n/)[0]?.trim() ?? '';
  const casou = /^([0-9a-fA-F]{64})(?:\s+\*?\S.*)?$/.exec(linha);
  if (!casou?.[1])
    return falha('checksum_ilegivel', 'O arquivo de checksum não está no formato do sha256sum.');
  const esperado = casou[1].toLowerCase();
  // a Web Crypto só existe em contexto seguro (HTTPS ou localhost) no navegador
  if (!globalThis.crypto?.subtle) {
    return falha(
      'checksum_indisponivel',
      'Este navegador não confere o checksum fora de HTTPS ou localhost.',
    );
  }
  const calculado = await sha256Hex(bytes);
  if (calculado !== esperado) {
    return falha('checksum_divergente', 'O deals.json não bate com o checksum publicado.', {
      esperado,
      calculado,
    });
  }
  return ok(calculado);
}
