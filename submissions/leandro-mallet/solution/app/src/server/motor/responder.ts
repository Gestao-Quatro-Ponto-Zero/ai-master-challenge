import "server-only";
// Resposta comum das rotas da rotina: 401 sem o segredo; senão roda e devolve o resultado (500 em falha).
import { NextResponse, type NextRequest } from "next/server";
import { rotinaAutorizada } from "./autorizacao";
import { conexaoRotina } from "./conexao";
import { motorInstalado } from "./instalado";
import { rodarRotina } from "./rotina";

export async function responderRotina(req: NextRequest, origem: "cron" | "manual", opcoes: { forcar?: boolean } = {}) {
  if (!rotinaAutorizada(req.headers.get("authorization"))) {
    return NextResponse.json({ erro: "Não autorizado.", codigo: "GS401" }, { status: 401 });
  }
  const r = await rodarRotina(conexaoRotina, motorInstalado, origem, opcoes);
  return NextResponse.json(r, { status: r.status === "falha" ? 500 : 200 });
}
