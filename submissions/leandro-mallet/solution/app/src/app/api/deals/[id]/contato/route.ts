import { z } from "zod";
import { EMAIL, TELEFONE, textoObrigatorio, textoOpcional } from "@/lib/validacao";
import { parte, rota } from "@/server/rota";
import { detalheDeal, salvarContato } from "@/server/repositorio";

const corpo = z.object({
  versao: z.string().nullable(),
  nome: textoObrigatorio(120),
  cargo: textoOpcional(80),
  // Mesmas regras do banco; vazio = sem e-mail ou sem telefone.
  email: z.string().trim().max(160).refine((v) => v === "" || EMAIL.test(v)).nullish(),
  telefone: z.string().trim().max(25).refine((v) => v === "" || TELEFONE.test(v)).nullish(),
});

/** Adiciona um contato e o torna o contato principal do deal. */
export const POST = rota({ escrita: true, corpo }, async ({ usuario, corpo, req }) => {
  const id = parte(req, 3);
  const { deal } = await detalheDeal(id, usuario);
  await salvarContato(usuario, { conta: deal.conta, nome: corpo.nome, cargo: corpo.cargo || null, email: corpo.email || null, telefone: corpo.telefone || null }, id, corpo.versao);
  return { ok: true };
});
