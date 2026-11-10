import { NextResponse, type NextRequest } from "next/server";
import { z } from "zod";
import { rota } from "@/server/rota";
import { ErroCRM, usuarioPorId } from "@/server/repositorio";
import { COOKIE_PERFIL } from "@/server/sessao";

const corpo = z.object({ usuarioId: z.number().int().min(2) });

/**
 * Escolher o perfil: grava o cookie. O usuário "sistema" (id 1) nunca é aceito.
 * Cookie de sessão do navegador (sem maxAge, O-37): fechou o navegador, escolhe de novo na entrada.
 */
export const POST = async (req: NextRequest) => {
  let id = 0;
  const resposta = await rota({ semUsuario: true, corpo }, async ({ corpo }) => {
    const u = await usuarioPorId(corpo.usuarioId);
    if (!u) throw new ErroCRM("GS404", "Este usuário não existe. Escolha outro na lista.");
    id = u.id;
    return { ok: true, papel: u.papel };
  })(req);
  if (id) resposta.cookies.set(COOKIE_PERFIL, String(id), { httpOnly: true, sameSite: "lax", path: "/" });
  return resposta;
};

/** Trocar perfil: remove só o cookie. */
export const DELETE = async () => {
  const resposta = NextResponse.json({ ok: true });
  resposta.cookies.set(COOKIE_PERFIL, "", { httpOnly: true, sameSite: "lax", path: "/", maxAge: 0 });
  return resposta;
};
