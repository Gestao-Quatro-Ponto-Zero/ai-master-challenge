import { NextResponse } from "next/server";
import { notasDisponiveis, somenteLeitura } from "@/server/repositorio";

export const dynamic = "force-dynamic";

/** Saúde do app: sem chave nem erro cru. O banco entra aqui quando a fonte for o banco. */
export async function GET() {
  try {
    return NextResponse.json({ app: "ok", banco: "nao_configurado", fonte: "arquivo", notas: await notasDisponiveis(), somente_leitura: somenteLeitura() });
  } catch {
    return NextResponse.json({ app: "erro", fonte: "indisponivel" }, { status: 503 });
  }
}
