import { parte, rota } from "@/server/rota";
import { detalheConta } from "@/server/repositorio";

/** Ficha da empresa: cadastro, histórico, padrão de compra e deals abertos. */
export const GET = rota({}, async ({ req }) => detalheConta(parte(req, 3)));
