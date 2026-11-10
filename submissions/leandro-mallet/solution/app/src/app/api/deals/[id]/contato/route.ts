import { z } from "zod";
import { parte, rota } from "@/server/rota";
import { detalheDeal, salvarContato } from "@/server/repositorio";

const corpo = z.object({
  versao: z.string().nullable(),
  nome: z.string().min(1).max(120),
  cargo: z.string().max(80).nullish(),
  email: z.string().max(160).nullish(),
  telefone: z.string().max(25).nullish(),
});

/** Adiciona um contato e o torna o contato principal do deal. */
export const POST = rota({ escrita: true, corpo }, async ({ usuario, corpo, req }) => {
  const id = parte(req, 3);
  const { deal } = await detalheDeal(id, usuario);
  await salvarContato(usuario, { conta: deal.conta, nome: corpo.nome, cargo: corpo.cargo || null, email: corpo.email || null, telefone: corpo.telefone || null }, id, corpo.versao);
  return { ok: true };
});
