import { z } from "zod";
import { textoObrigatorio, textoOpcional } from "@/lib/validacao";
import { rota } from "@/server/rota";
import { salvarConta } from "@/server/repositorio";

const corpo = z.object({
  nome: textoObrigatorio(120),
  novo: z.boolean(),
  setor: textoOpcional(40),
  funcionarios: z.number().int().min(0).max(10_000_000).nullish(),
  receitaMilhoes: z.number().min(0).max(10_000_000).nullish(),
  anoFundacao: z.number().int().min(1800).max(2100).nullish(),
  sede: textoOpcional(80),
  empresaMae: textoOpcional(120),
});

/** Criar ou editar empresa (o nome não muda depois de criado). */
export const POST = rota({ escrita: true, corpo }, async ({ usuario, corpo }) =>
  salvarConta(usuario, { ...corpo, setor: corpo.setor || null, sede: corpo.sede || null, empresaMae: corpo.empresaMae || null }));
