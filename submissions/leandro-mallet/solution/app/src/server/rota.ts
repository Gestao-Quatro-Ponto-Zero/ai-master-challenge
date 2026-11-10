import "server-only";
// Base das rotas de API: usuário pelo cookie, limite por endereço de rede, correlation_id gerado no
// servidor, validação com zod e erro sempre em frase simples (nunca erro cru).
import { randomUUID } from "node:crypto";
import { NextResponse, type NextRequest } from "next/server";
import type { z } from "zod";
import { CONFIG } from "@/lib/config";
import type { Usuario } from "@/lib/tipos";
import { comCorrelacao } from "./banco";
import { ErroCRM, type CodigoErro } from "./repositorio";
import { usuarioAtual } from "./sessao";

const STATUS: Record<CodigoErro, number> = { GS400: 400, GS401: 401, GS403: 403, GS404: 404, GS405: 405, GS409: 409, GS422: 422, GS429: 429, GS503: 503 };

// Limite por IP em memória (por instância do servidor). O banco tem também um teto global.
const janelas = new Map<string, number[]>();

function ipDe(req: NextRequest): string {
  return req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || req.headers.get("x-real-ip") || "local";
}

function dentroDoLimite(ip: string): boolean {
  const { quantidade, janelaSegundos } = CONFIG.limiteEscritasPorIp;
  const agora = Date.now();
  const recentes = (janelas.get(ip) ?? []).filter((t) => agora - t < janelaSegundos * 1000);
  if (recentes.length >= quantidade) {
    janelas.set(ip, recentes);
    return false;
  }
  recentes.push(agora);
  janelas.set(ip, recentes);
  return true;
}

function log(dados: Record<string, unknown>) {
  // Uma linha JSON por pedido; nunca corpo, chave ou texto digitado pelo usuário (BE-07).
  console.log(JSON.stringify({ momento: new Date().toISOString(), ...dados }));
}

interface Opcoes<T> {
  escrita?: boolean;
  semUsuario?: boolean;
  corpo?: z.ZodType<T>;
}

export function rota<T = undefined>(
  opcoes: Opcoes<T>,
  executar: (ctx: { usuario: Usuario; corpo: T; correlationId: string; req: NextRequest }) => Promise<unknown>,
) {
  return async (req: NextRequest): Promise<NextResponse> => {
    const correlationId = randomUUID();
    const inicio = Date.now();
    const responder = (status: number, corpo: unknown) => {
      log({ correlation_id: correlationId, rota: req.nextUrl.pathname, metodo: req.method, status, duracao_ms: Date.now() - inicio });
      return NextResponse.json(corpo, { status, headers: { "x-correlation-id": correlationId } });
    };
    const erro = (status: number, frase: string, detalhe?: unknown) => responder(status, { erro: frase, codigo: correlationId, detalhe });
    try {
      if (opcoes.escrita && !dentroDoLimite(ipDe(req))) return erro(429, "Muitas mudanças seguidas. Espere alguns segundos e tente de novo.");
      const usuario = opcoes.semUsuario ? null : await usuarioAtual();
      if (!opcoes.semUsuario && !usuario) return erro(401, "Escolha um perfil antes de continuar.");
      let corpo = undefined as T;
      if (opcoes.corpo) {
        const lido = opcoes.corpo.safeParse(await req.json().catch(() => null));
        if (!lido.success) return erro(400, "Não entendi o pedido. Recarregue a página e tente de novo.");
        corpo = lido.data;
      }
      // O correlation_id deste pedido acompanha a escrita no banco e liga o log à auditoria.
      const resultado = await comCorrelacao(correlationId, () => executar({ usuario: usuario as Usuario, corpo, correlationId, req }));
      return responder(200, resultado ?? { ok: true });
    } catch (e) {
      if (e instanceof ErroCRM) return erro(STATUS[e.codigo], e.message, e.detalhe);
      console.error(JSON.stringify({ correlation_id: correlationId, erro: e instanceof Error ? e.message : String(e) }));
      return erro(500, "Não foi possível concluir. Tente de novo em alguns segundos.");
    }
  };
}

/** Último trecho dinâmico do caminho (ex.: /api/deals/ABC/estagio → posição 3 = "ABC"). */
export function parte(req: NextRequest, posicao: number): string {
  return decodeURIComponent(req.nextUrl.pathname.split("/")[posicao] ?? "");
}
