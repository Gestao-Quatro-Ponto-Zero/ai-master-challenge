import { z } from "zod";
import { textoOpcional } from "@/lib/validacao";
import { parte, rota } from "@/server/rota";
import { registrarAcao } from "@/server/repositorio";

const corpo = z.object({ acao: z.enum(["liguei", "requalifiquei", "desisti"]), nota: textoOpcional(280) });

export const POST = rota({ escrita: true, corpo }, async ({ usuario, corpo, req }) =>
  registrarAcao(usuario, parte(req, 3), corpo.acao, corpo.nota || null));
