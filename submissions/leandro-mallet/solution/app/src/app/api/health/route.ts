import { NextResponse } from "next/server";
import { estadoBanco, fonteDosDados, listarUsuarios, somenteLeitura } from "@/server/repositorio";

export const dynamic = "force-dynamic";

/** Saúde do app: confere a leitura dos dados e diz de onde eles vêm. Sem chave nem erro cru. */
export async function GET() {
  try {
    const usuarios = (await listarUsuarios()).length;
    return NextResponse.json({ app: "ok", banco: estadoBanco(), fonte: fonteDosDados(), usuarios, somente_leitura: somenteLeitura() });
  } catch {
    return NextResponse.json({ app: "erro", banco: estadoBanco(), fonte: "indisponivel" }, { status: 503 });
  }
}
