import { z } from "zod";
import { parte, rota } from "@/server/rota";
import { mudarEstagio } from "@/server/repositorio";

const corpo = z.object({
  versao: z.string().nullable(),
  para: z.enum(["Prospecting", "Engaging", "Won", "Lost"]),
  valor: z.number().int().positive().max(100_000_000).nullish(),
  motivo: z.enum(["preco", "concorrente", "sem_orcamento", "sem_resposta", "outro"]).nullish(),
});

/** Mudança de estágio: a mesma rota para arrastar o cartão e para o seletor. */
export const POST = rota({ escrita: true, corpo }, async ({ usuario, corpo, req }) =>
  mudarEstagio(usuario, parte(req, 3), corpo.versao, corpo.para, { valor: corpo.valor, motivo: corpo.motivo }));
