import { z } from "zod";
import { rota } from "@/server/rota";
import { desfazer } from "@/server/repositorio";

const corpo = z.object({ token: z.string().min(1).max(40) });

export const POST = rota({ escrita: true, corpo }, async ({ usuario, corpo }) => {
  await desfazer(usuario, corpo.token);
  return { ok: true };
});
