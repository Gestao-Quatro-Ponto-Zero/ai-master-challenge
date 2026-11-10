import { z } from "zod";
import { textoObrigatorio } from "@/lib/validacao";
import { parte, rota } from "@/server/rota";
import { comentar } from "@/server/repositorio";

const corpo = z.object({ texto: textoObrigatorio(1000) });

export const POST = rota({ escrita: true, corpo }, async ({ usuario, corpo, req }) => comentar(usuario, parte(req, 3), corpo.texto));
