import { rota } from "@/server/rota";
import { puxarMaisPrioridades } from "@/server/repositorio";

export const POST = rota({ escrita: true }, async ({ usuario }) => {
  await puxarMaisPrioridades(usuario, 5);
  return { ok: true };
});
