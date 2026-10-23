/**
 * Carrega o `deals.json` com integridade conferida (e, com banco, os mesmos dados do banco): bytes → SHA-256 contra o `.sha256` → JSON →
 * schema do domínio (`lerPipeline`) → casos de uso (`criarServicos`). Qualquer falha devolve
 * erro; o servidor não sobe com dado adulterado, truncado ou de formato desconhecido.
 */
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { criarServicos, type ServicosLeadScorer } from '@lead-scorer/dominio/aplicacao';
import { falha, ok, type Resultado } from '@lead-scorer/dominio/compartilhado';
import { conferirChecksum, FORMATO_DEALS, lerPipeline } from '@lead-scorer/dominio/pipeline';
import { criarBanco, criarDisjuntorBanco, semQuebra, type Consultor } from './infra/banco';
import {
  criarArmazemEmMemoria,
  criarArmazemNoBanco,
  criarArmazemResiliente,
  type ArmazemRegistros,
} from './qualificacao';
import type { InfoSaude } from './saude';

/** `solution/data/deals.json`, resolvido a partir deste arquivo (não do diretório de onde se roda). */
export const CAMINHO_PADRAO_DEALS = fileURLToPath(
  new URL('../../../data/deals.json', import.meta.url),
);

/** O que o servidor precisa depois da carga. */
export interface DadosCarregados {
  servicos: ServicosLeadScorer;
  dados: InfoSaude['dados'];
}

/** Lê `caminho` e `caminho + '.sha256'`, confere e monta os serviços. */
export async function carregarDados(caminho: string): Promise<Resultado<DadosCarregados>> {
  let bytes: Uint8Array;
  let sha: string;
  try {
    bytes = new Uint8Array(await readFile(caminho));
    sha = await readFile(caminho + '.sha256', 'utf8');
  } catch (e) {
    return falha(
      'arquivo_ilegivel',
      'Não consegui ler ' + caminho + ' e o .sha256 dele: ' + (e as Error).message,
    );
  }
  const conferido = await conferirChecksum(bytes, sha);
  if (!conferido.ok) return conferido;
  let bruto: unknown;
  try {
    bruto = JSON.parse(new TextDecoder().decode(bytes));
  } catch {
    return falha('json_invalido', caminho + ' não é um JSON válido.');
  }
  const pipeline = lerPipeline(bruto);
  if (!pipeline.ok) return pipeline;
  const servicos = criarServicos({ pipeline: pipeline.valor, checksum: conferido.valor });
  return ok({
    servicos,
    dados: {
      total: pipeline.valor.deals.length,
      referencia: pipeline.valor.referencia,
      checksum: conferido.valor,
    },
  });
}

/** O que o banco guarda em `lead_scorer.metadados`, conferido contra o `deals.json` embarcado. */
interface Metadados {
  formato?: string;
  referencia?: string;
  sha256_deals_json?: string;
}

const COLUNAS_DEALS = [
  'opportunity_id',
  'sales_agent',
  'product',
  'account',
  'deal_stage',
  "to_char(engage_date, 'YYYY-MM-DD') as engage_date",
  "to_char(close_date, 'YYYY-MM-DD') as close_date",
  'close_value::float8 as close_value',
  'produto_normalizado',
  'manager',
  'regional_office',
  'sector',
  'year_established::float8 as year_established',
  'revenue::float8 as revenue',
  'employees::float8 as employees',
  'office_location',
  'subsidiary_of',
  'setor_normalizado',
  'series',
  'sales_price::float8 as sales_price',
  'aberto',
  'idade_dias::int as idade_dias',
  'duracao_dias::int as duracao_dias',
  'sem_conta',
  'sem_engage_date',
].join(', ');

/**
 * Lê os negócios e o time do banco compartilhado (schema `lead_scorer`), só se o metadado do
 * banco disser que ele foi carregado do mesmo `deals.json` embarcado (sha256 e formato iguais).
 * Depois passa pelo mesmo schema do domínio (`lerPipeline`). Erros: `metadado_divergente` e os
 * de `lerPipeline`; falha de conexão sobe como exceção (quem chama decide cair para o arquivo).
 */
export async function carregarDoBanco(
  banco: Consultor,
  checksumEmbarcado: string,
): Promise<Resultado<DadosCarregados>> {
  const linhas = await banco.consultar<{ chave: string; valor: string }>(
    'select chave, valor from lead_scorer.metadados',
  );
  const meta: Metadados = Object.fromEntries(linhas.map((l) => [l.chave, l.valor]));
  if (meta.sha256_deals_json !== checksumEmbarcado || meta.formato !== String(FORMATO_DEALS)) {
    return falha(
      'metadado_divergente',
      'O banco foi carregado de outro deals.json (formato ' +
        String(meta.formato) +
        ', sha256 ' +
        String(meta.sha256_deals_json).slice(0, 12) +
        '…); o embarcado é o formato ' +
        FORMATO_DEALS +
        ', sha256 ' +
        checksumEmbarcado.slice(0, 12) +
        '….',
    );
  }
  const [deals, vendedores] = await Promise.all([
    banco.consultar('select ' + COLUNAS_DEALS + ' from lead_scorer.deals order by opportunity_id'),
    banco.consultar(
      'select sales_agent, manager, regional_office from lead_scorer.vendedores order by sales_agent',
    ),
  ]);
  const pipeline = lerPipeline({
    formato: FORMATO_DEALS,
    referencia: meta.referencia,
    total: deals.length,
    vendedores,
    deals,
  });
  if (!pipeline.ok) return pipeline;
  return ok({
    servicos: criarServicos({ pipeline: pipeline.valor, checksum: checksumEmbarcado }),
    dados: {
      total: pipeline.valor.deals.length,
      referencia: pipeline.valor.referencia,
      checksum: checksumEmbarcado,
    },
  });
}

/** O que o servidor (e a função serverless) precisa para montar o app. */
export interface Montagem extends DadosCarregados {
  registros: ArmazemRegistros;
  /** De onde vieram os negócios: o banco (conferido) ou o `deals.json` embarcado. */
  origem: 'banco' | 'arquivo';
  /** Fecha a conexão com o banco, se houver. */
  fechar(): Promise<void>;
}

/**
 * Monta os dados e o armazém das respostas. Sem `DATABASE_URL`: o `deals.json` e a memória do
 * processo. Com ela: os negócios do banco, se o metadado conferir com o `deals.json` (senão, o
 * arquivo, com aviso no log), e as respostas e decisões no banco, com disjuntor e queda para a
 * memória. O `deals.json` é sempre conferido primeiro: sem ele válido, nada sobe.
 */
export async function montarDependencias(
  env: Record<string, string | undefined>,
  caminhoDeals: string,
  log: (linha: string) => void,
): Promise<Resultado<Montagem>> {
  const arquivo = await carregarDados(caminhoDeals);
  if (!arquivo.ok) return arquivo;
  const url = env['DATABASE_URL']?.trim();
  if (!url) {
    return ok({
      ...arquivo.valor,
      registros: criarArmazemEmMemoria(),
      origem: 'arquivo',
      fechar: async () => {},
    });
  }
  const banco = criarBanco(url, log);
  const disjuntor = criarDisjuntorBanco();
  const registros = criarArmazemResiliente(criarArmazemNoBanco(banco), disjuntor, log);
  const comBanco = { registros, fechar: () => banco.fechar() };
  try {
    const doBanco = await disjuntor.executar(() =>
      carregarDoBanco(banco, arquivo.valor.dados.checksum),
    );
    if (doBanco.ok) return ok({ ...doBanco.valor, ...comBanco, origem: 'banco' });
    log('banco: ' + doBanco.erro.codigo + ': ' + doBanco.erro.mensagem + ' Usando o deals.json.');
  } catch (e) {
    log(
      'banco: não deu para ler os negócios: ' +
        semQuebra((e as Error).message) +
        '. Usando o deals.json.',
    );
  }
  return ok({ ...arquivo.valor, ...comBanco, origem: 'arquivo' });
}
