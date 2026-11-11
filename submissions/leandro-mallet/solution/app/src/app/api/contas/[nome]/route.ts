import { parte, rota } from "@/server/rota";
import { detalheConta } from "@/server/repositorio";

/** Ficha da empresa: cadastro, histórico e padrão de compra (gerais) e os deals abertos do escopo do perfil. */
export const GET = rota({}, async ({ usuario, req }) => detalheConta(parte(req, 3), usuario));
