import { z } from "zod";
import { parte, rota } from "@/server/rota";
import { aplicarTag, ErroCRM, removerTag } from "@/server/repositorio";

const corpo = z.object({ tagId: z.number().int() });

export const POST = rota({ escrita: true, corpo }, async ({ usuario, corpo, req }) => aplicarTag(usuario, parte(req, 3), corpo.tagId));

/** Remover a tag do deal = remoção lógica (fica no histórico). */
export const DELETE = rota({ escrita: true }, async ({ usuario, req }) => {
  const tagId = Number(req.nextUrl.searchParams.get("tagId"));
  if (!Number.isInteger(tagId)) throw new ErroCRM("GS400", "Tag inválida.");
  return removerTag(usuario, parte(req, 3), tagId);
});
