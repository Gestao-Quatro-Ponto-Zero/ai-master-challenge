import { z } from "zod";
import { exigir, textoOpcional } from "@/lib/validacao";
import { rota } from "@/server/rota";
import { marcarPrioridade } from "@/server/repositorio";

const corpo = z
  .object({
    dealId: z.string().min(1).max(20),
    resultado: z.enum(["feita", "pulada"]),
    tipoAtividade: textoOpcional(40),
    comentario: textoOpcional(280),
  })
  // O ✓ exige o tipo de atividade e o que foi feito; comentário só com espaços conta como vazio.
  .superRefine((c, ctx) => {
    if (c.resultado !== "feita") return;
    exigir(ctx, "tipoAtividade", c.tipoAtividade);
    exigir(ctx, "comentario", c.comentario);
  });

/** ✓ (com tipo de atividade e comentário obrigatórios) ou ✗ num item das Prioridades do dia. */
export const POST = rota({ escrita: true, corpo }, async ({ usuario, corpo }) =>
  marcarPrioridade(usuario, corpo.dealId, corpo.resultado, { tipoAtividade: corpo.tipoAtividade, comentario: corpo.comentario }));
