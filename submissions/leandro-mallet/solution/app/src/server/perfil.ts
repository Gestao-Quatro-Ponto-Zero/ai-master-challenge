import "server-only";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type { Usuario } from "@/lib/tipos";
import { usuarioPorId } from "./repositorio";

export const COOKIE_PERFIL = "g4_usuario";

export async function usuarioAtual(): Promise<Usuario | undefined> {
  const id = Number((await cookies()).get(COOKIE_PERFIL)?.value);
  return Number.isInteger(id) && id > 0 ? usuarioPorId(id) : undefined;
}

/** Nas páginas: sem perfil escolhido, vai para "Quem é você?" e volta para onde estava. */
export async function exigirUsuario(voltar: string): Promise<Usuario> {
  const u = await usuarioAtual();
  if (!u) redirect(`/?voltar=${encodeURIComponent(voltar)}`);
  return u;
}

export function telaInicial(u: Usuario): string {
  return u.papel === "vendedor" ? "/painel" : "/painel";
}
