import { parte, rota } from "@/server/rota";
import { detalheDeal } from "@/server/repositorio";

/** Detalhe do deal para o modal: nota, linha do tempo e comentários. */
export const GET = rota({}, async ({ usuario, req }) => detalheDeal(parte(req, 3), usuario));
