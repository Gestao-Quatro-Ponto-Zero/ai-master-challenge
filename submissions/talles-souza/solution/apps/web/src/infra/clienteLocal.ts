/**
 * Modo local: o navegador baixa `/dados/deals.json` e o `.sha256`, confere o checksum, valida o
 * schema e roda os mesmos casos de uso do domínio que a API roda. Carrega uma vez só.
 */
import { criarServicos, type ServicosLeadScorer } from '@lead-scorer/dominio/aplicacao';
import { conferirChecksum, lerPipeline } from '@lead-scorer/dominio/pipeline';
import { OPERACOES, type ClienteLeadScorer } from './cliente';
import { ErroCliente } from './erros';

export interface OpcoesClienteLocal {
  /** Pasta dos dados, servida pela web. */
  base?: string;
  fetch?: typeof fetch;
}

export interface ClienteLocal extends ClienteLeadScorer {
  /** Carrega e confere os dados (a primeira operação também faz isso). */
  carregar(): Promise<ServicosLeadScorer>;
}

/** Cria o cliente local. */
export function criarClienteLocal(opcoes: OpcoesClienteLocal = {}): ClienteLocal {
  const base = opcoes.base ?? '/dados/';
  const buscar = opcoes.fetch ?? ((...a: Parameters<typeof fetch>) => globalThis.fetch(...a));
  let carregando: Promise<ServicosLeadScorer> | null = null;

  async function carregarDeVerdade(): Promise<ServicosLeadScorer> {
    const [rDados, rHash] = await Promise.all([
      buscar(base + 'deals.json'),
      buscar(base + 'deals.json.sha256'),
    ]);
    if (!rDados.ok || !rHash.ok) {
      throw new ErroCliente(
        'dados',
        'Os dados do modo local não estão disponíveis (' +
          rDados.status +
          '/' +
          rHash.status +
          ').',
      );
    }
    const bytes = new Uint8Array(await rDados.arrayBuffer());
    const conferido = await conferirChecksum(bytes, await rHash.text());
    if (!conferido.ok)
      throw new ErroCliente('dados', conferido.erro.mensagem, { codigo: conferido.erro.codigo });
    let bruto: unknown;
    try {
      bruto = JSON.parse(new TextDecoder().decode(bytes));
    } catch {
      throw new ErroCliente('dados', 'O deals.json não é um JSON válido.');
    }
    const pipeline = lerPipeline(bruto);
    if (!pipeline.ok)
      throw new ErroCliente('dados', pipeline.erro.mensagem, { codigo: pipeline.erro.codigo });
    return criarServicos({ pipeline: pipeline.valor, checksum: conferido.valor });
  }

  function carregar(): Promise<ServicosLeadScorer> {
    if (!carregando) {
      carregando = carregarDeVerdade().catch((e: unknown) => {
        carregando = null; // deixa tentar de novo na próxima operação
        throw e;
      });
    }
    return carregando;
  }

  const cliente = { carregar } as ClienteLocal;
  for (const op of OPERACOES) {
    (cliente as unknown as Record<string, (...a: unknown[]) => Promise<unknown>>)[op] = async (
      ...args
    ) => {
      const servicos = await carregar();
      return (servicos[op] as (...a: unknown[]) => unknown)(...args);
    };
  }
  return cliente;
}
