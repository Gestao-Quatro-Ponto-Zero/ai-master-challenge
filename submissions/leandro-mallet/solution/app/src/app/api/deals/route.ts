import { z } from "zod";
import { textoObrigatorio, textoOpcional } from "@/lib/validacao";
import { rota } from "@/server/rota";
import { criarDeal } from "@/server/repositorio";

const corpo = z.object({
  produto: textoObrigatorio(60),
  conta: textoOpcional(120),
  vendedor: textoOpcional(120),
  estagio: z.enum(["Prospecting", "Engaging"]),
  nome: textoOpcional(120),
});

/** Novo lead. Sem vendedor informado: o próprio vendedor, ou o roteamento (manager e admin). */
export const POST = rota({ escrita: true, corpo }, async ({ usuario, corpo }) =>
  criarDeal(usuario, { produto: corpo.produto, conta: corpo.conta || null, vendedor: corpo.vendedor || null, estagio: corpo.estagio, nome: corpo.nome || null }));
