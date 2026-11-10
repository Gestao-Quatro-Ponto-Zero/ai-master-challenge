import "server-only";
// Acesso ao banco (Supabase). A chave service_role só existe aqui, no servidor, lida do ambiente.
// Leitura: views e tabelas. Escrita: SÓ pelas functions do banco (rpc), que registram o contexto
// (usuário + correlation_id) e passam pela auditoria. Nada de insert/update direto em tabela.
import { AsyncLocalStorage } from "node:async_hooks";
import { randomUUID } from "node:crypto";
import { createClient, type SupabaseClient } from "@supabase/supabase-js";

export type CodigoErro = "GS400" | "GS401" | "GS403" | "GS404" | "GS405" | "GS409" | "GS422" | "GS429" | "GS503";

/** Erro de regra, já em frase simples para a tela. */
export class ErroCRM extends Error {
  constructor(public codigo: CodigoErro, mensagem: string, public detalhe?: Record<string, unknown>) {
    super(mensagem);
  }
}

/** O banco não respondeu (rede, tempo esgotado, projeto pausado). As leituras caem na reserva em arquivo. */
export class BancoFora extends Error {}

const TEMPO_LIMITE_MS = 12_000;
const PAUSA_APOS_FALHA_MS = 15_000;
const g = globalThis as unknown as { __g4Banco?: SupabaseClient; __g4BancoForaAte?: number };

export function bancoConfigurado(): boolean {
  return !!process.env.SUPABASE_URL && !!process.env.SUPABASE_SERVICE_ROLE_KEY;
}

/** Banco configurado e sem falha recente. Depois de uma falha, o app usa a reserva por alguns segundos. */
export function bancoAtivo(): boolean {
  return bancoConfigurado() && Date.now() >= (g.__g4BancoForaAte ?? 0);
}

export function estadoBanco(): "ok" | "indisponivel" | "nao_configurado" {
  return !bancoConfigurado() ? "nao_configurado" : bancoAtivo() ? "ok" : "indisponivel";
}

export function banco(): SupabaseClient {
  if (!bancoConfigurado()) throw new BancoFora("banco não configurado");
  g.__g4Banco ??= createClient(process.env.SUPABASE_URL as string, process.env.SUPABASE_SERVICE_ROLE_KEY as string, {
    auth: { persistSession: false, autoRefreshToken: false },
    global: { fetch: (url, init) => fetch(url, { ...init, cache: "no-store", signal: AbortSignal.timeout(TEMPO_LIMITE_MS) }) },
  });
  return g.__g4Banco;
}

interface ErroPostgrest {
  code?: string;
  message?: string;
  details?: string | null;
}

const FRASES: Partial<Record<CodigoErro, string>> = {
  GS401: "Escolha um perfil antes de alterar dados.",
  GS405: "Apagar dados não é permitido neste sistema.",
};

/** Traduz o erro do banco: GSxxx vira frase simples; o resto conta como banco fora. */
function traduzir(e: ErroPostgrest): Error {
  const codigo = e.code ?? "";
  if (/^GS\d{3}$/.test(codigo)) {
    let detalhe: Record<string, unknown> | undefined;
    try {
      detalhe = e.details ? (JSON.parse(e.details) as Record<string, unknown>) : undefined;
    } catch {
      detalhe = undefined;
    }
    let frase = FRASES[codigo as CodigoErro] ?? e.message ?? "Não foi possível concluir.";
    if (codigo === "GS409" && detalhe?.alterado_por) frase = `Este deal foi alterado por ${String(detalhe.alterado_por)}. Recarregue para ver a versão atual.`;
    return new ErroCRM(codigo as CodigoErro, frase, detalhe);
  }
  // 23xxx: o banco recusou por integridade (chave, check). Não é queda do banco.
  if (/^23/.test(codigo)) return new ErroCRM("GS422", "Não foi possível salvar: os dados não são aceitos. Confira os campos e tente de novo.");
  g.__g4BancoForaAte = Date.now() + PAUSA_APOS_FALHA_MS;
  console.error(JSON.stringify({ momento: new Date().toISOString(), nivel: "erro", banco: "indisponivel", codigo: codigo || "rede" }));
  return new BancoFora(codigo || "rede");
}

/** Executa uma consulta do supabase-js e devolve os dados, com o erro já traduzido. */
export async function ler<T>(consulta: PromiseLike<{ data: T | null; error: ErroPostgrest | null }>): Promise<T> {
  let r: { data: T | null; error: ErroPostgrest | null };
  try {
    r = await consulta;
  } catch {
    throw traduzir({});
  }
  if (r.error) throw traduzir(r.error);
  return r.data as T;
}

// O correlation_id do pedido (gerado na rota) acompanha a primeira escrita; as seguintes ganham um novo,
// porque o banco recusa reaproveitar o mesmo em outra transação.
const pedido = new AsyncLocalStorage<{ correlationId: string; usado: boolean }>();

export function comCorrelacao<T>(correlationId: string, fn: () => Promise<T>): Promise<T> {
  return pedido.run({ correlationId, usado: false }, fn);
}

export function proximaCorrelacao(): string {
  const p = pedido.getStore();
  if (p && !p.usado) {
    p.usado = true;
    return p.correlationId;
  }
  return randomUUID();
}

/** Chama uma function de escrita do banco, com o usuário do perfil e um correlation_id do servidor. */
export async function escrever<T>(funcao: string, usuarioId: number, args: Record<string, unknown> = {}): Promise<{ dados: T; correlationId: string }> {
  const correlationId = proximaCorrelacao();
  const dados = await ler<T>(banco().rpc(funcao, { p_usuario_id: usuarioId, p_correlation_id: correlationId, ...args }));
  return { dados, correlationId };
}

/** Lê todas as linhas de uma consulta paginada (o banco devolve no máximo 1.000 por pedido). */
export async function lerTudo<T>(montar: (de: number, ate: number) => PromiseLike<{ data: T[] | null; error: ErroPostgrest | null; count?: number | null }>): Promise<T[]> {
  const PAGINA = 1000;
  let primeira: { data: T[] | null; error: ErroPostgrest | null; count?: number | null };
  try {
    primeira = await montar(0, PAGINA - 1);
  } catch {
    throw traduzir({});
  }
  if (primeira.error) throw traduzir(primeira.error);
  const linhas = primeira.data ?? [];
  const total = primeira.count ?? linhas.length;
  if (total <= PAGINA) return linhas;
  const resto = await Promise.all(
    Array.from({ length: Math.ceil(total / PAGINA) - 1 }, (_, i) => ler<T[]>(montar((i + 1) * PAGINA, (i + 2) * PAGINA - 1))),
  );
  return linhas.concat(...resto);
}
