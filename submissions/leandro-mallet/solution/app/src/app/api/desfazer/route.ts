import { corpoDesfazer } from "@/lib/desfazer";
import { rota } from "@/server/rota";
import { desfazer } from "@/server/repositorio";

/**
 * "Desfazer" de uma mudança, ação, comentário, tag ou lote. Nunca apaga: reverte ou marca como desfeito.
 * Token fora do formato é recusado aqui (400), antes de qualquer chamada ao banco.
 */
export const POST = rota({ escrita: true, corpo: corpoDesfazer }, async ({ usuario, corpo }) => {
  await desfazer(usuario, corpo.token);
  return { ok: true };
});
