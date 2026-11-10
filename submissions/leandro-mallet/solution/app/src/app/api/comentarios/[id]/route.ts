import { parte, rota } from "@/server/rota";
import { ErroCRM, removerComentario } from "@/server/repositorio";

/** "Apagar" comentário = remoção lógica: some da tela e da linha do tempo, mas fica guardado. */
export const DELETE = rota({ escrita: true }, async ({ usuario, req }) => {
  const id = Number(parte(req, 3));
  if (!Number.isInteger(id)) throw new ErroCRM("GS400", "Comentário inválido.");
  return removerComentario(usuario, id);
});
