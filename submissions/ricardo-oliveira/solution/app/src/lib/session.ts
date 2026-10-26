import "server-only";
import { cookies } from "next/headers";
import { findUser } from "./data";
import type { User } from "./types";

// Não é login. É só "quem está olhando": um cookie com a chave do vendedor escolhido.
// Login de verdade (SSO da empresa, cada vendedor vê só o seu) entra com a aprovação da RevOps. Está no README.
const NAME = "ls_quem";

export async function escolherUsuario(key: string): Promise<void> {
  (await cookies()).set(NAME, key, { path: "/", httpOnly: true, sameSite: "lax", maxAge: 60 * 60 * 24 * 30 });
}

export async function limparUsuario(): Promise<void> {
  (await cookies()).set(NAME, "", { path: "/", maxAge: 0 });
}

export async function currentUser(): Promise<User | null> {
  const key = (await cookies()).get(NAME)?.value;
  if (!key) return null;
  return findUser(key);
}
