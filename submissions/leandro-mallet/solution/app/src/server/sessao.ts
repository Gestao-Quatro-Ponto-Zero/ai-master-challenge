import "server-only";
// Perfil escolhido na tela (sem login, decisão 12): um cookie com o id do usuário.
// O cookie organiza a tela e assina as ações; não é controle de acesso.
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type { Usuario } from "@/lib/tipos";
import { usuarioPorId } from "./repositorio";

export const COOKIE_PERFIL = "g4_perfil";
/** O usuário "sistema" (id 1) assina as cargas e nunca é aceito vindo da tela. */
const ID_SISTEMA = 1;

export async function usuarioAtual(): Promise<Usuario | null> {
  const bruto = (await cookies()).get(COOKIE_PERFIL)?.value;
  const id = Number(bruto);
  if (!bruto || !Number.isInteger(id) || id <= ID_SISTEMA) return null;
  return (await usuarioPorId(id)) ?? null;
}

/** Para páginas: sem perfil escolhido, vai para a escolha e depois volta. */
export async function exigirUsuario(voltarPara: string): Promise<Usuario> {
  const u = await usuarioAtual();
  if (!u) redirect(`/?voltar=${encodeURIComponent(voltarPara)}`);
  return u;
}
