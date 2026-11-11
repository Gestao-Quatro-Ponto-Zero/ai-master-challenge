// Registrar atendimento (O-31): o primeiro contato registrado leva o lead de Novo lead para Atendimento.
// Tipo de atividade (que conta como contato) e comentário obrigatórios; o banco confere de novo.
import { z } from "zod";
import { CONFIG } from "@/lib/config";
import { textoObrigatorio } from "@/lib/validacao";
import { parte, rota } from "@/server/rota";
import { registrarAtendimento } from "@/server/repositorio";

const TIPOS = CONFIG.tiposAtividade.filter((t) => t.contaComoContato).map((t) => t.codigo) as [string, ...string[]];
const corpo = z.object({ tipoAtividade: z.enum(TIPOS), comentario: textoObrigatorio(280) });

export const POST = rota({ escrita: true, corpo }, async ({ usuario, corpo, req }) =>
  registrarAtendimento(usuario, parte(req, 3), corpo.tipoAtividade, corpo.comentario));
