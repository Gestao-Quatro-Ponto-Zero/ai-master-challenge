import { z } from "zod";
import { rota } from "@/server/rota";
import { desfazer, desfazerLote } from "@/server/repositorio";

const corpo = z.object({ token: z.string().min(1).max(40) });

/** "Desfazer" de uma mudança (janela curta) ou de um lote inteiro (token "lote:<id>", até 24 h). */
export const POST = rota({ escrita: true, corpo }, async ({ usuario, corpo }) => {
  const lote = /^lote:(\d+)$/.exec(corpo.token);
  if (lote) return desfazerLote(usuario, Number(lote[1]));
  await desfazer(usuario, corpo.token);
  return { ok: true };
});
