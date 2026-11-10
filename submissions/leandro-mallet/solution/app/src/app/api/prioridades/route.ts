import { z } from "zod";
import { rota } from "@/server/rota";
import { marcarPrioridade } from "@/server/repositorio";

const corpo = z.object({
  dealId: z.string().min(1).max(20),
  resultado: z.enum(["feita", "pulada"]),
  tipoAtividade: z.string().max(40).nullish(),
  comentario: z.string().max(280).nullish(),
});

/** ✓ (com tipo de atividade e comentário obrigatórios) ou ✗ num item das Prioridades do dia. */
export const POST = rota({ escrita: true, corpo }, async ({ usuario, corpo }) =>
  marcarPrioridade(usuario, corpo.dealId, corpo.resultado, { tipoAtividade: corpo.tipoAtividade, comentario: corpo.comentario }));
