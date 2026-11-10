import { z } from "zod";
import { rota } from "@/server/rota";
import { criarDeal } from "@/server/repositorio";

const corpo = z.object({
  produto: z.string().min(1).max(60),
  conta: z.string().max(120).nullish(),
  vendedor: z.string().max(120).nullish(),
  estagio: z.enum(["Prospecting", "Engaging"]),
  nome: z.string().max(120).nullish(),
});

/** Novo lead. Sem vendedor informado: o próprio vendedor, ou o roteamento (manager e admin). */
export const POST = rota({ escrita: true, corpo }, async ({ usuario, corpo }) =>
  criarDeal(usuario, { produto: corpo.produto, conta: corpo.conta || null, vendedor: corpo.vendedor || null, estagio: corpo.estagio, nome: corpo.nome || null }));
