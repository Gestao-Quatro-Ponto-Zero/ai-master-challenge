import { z } from "zod";
import { CONFIG } from "@/lib/config";
import { juntar } from "@/lib/filtro/etiquetas";
import { lerEtiquetas, lerFiltrosEquipe } from "@/server/parametros";
import { rota } from "@/server/rota";
import { buscarDeals, ErroCRM, escopoDe, executarLote, lotesRecentes } from "@/server/repositorio";

/** Lotes das últimas 24 horas que o perfil pode desfazer (os próprios; o manager vê os do time; o admin, todos). */
export const GET = rota({}, async ({ usuario }) => ({ lotes: await lotesRecentes(usuario) }));

const corpo = z.object({
  tipo: z.enum(["aplicar_tag", "remover_tag", "comentar", "avancar_estagio", "encerrar_perdido"]),
  ids: z.array(z.string().min(1).max(20)).max(CONFIG.limiteLote).optional(),
  /** "Selecionar os N do filtro": o servidor refaz a lista com o mesmo filtro, na hora de aplicar. */
  filtro: z.object({ f: z.string().max(8000).optional(), regiao: z.string().optional(), manager: z.string().optional(), vendedor: z.string().optional() }).optional(),
  tagId: z.number().int().optional(),
  texto: z.string().max(1000).optional(),
  motivo: z.enum(["preco", "concorrente", "sem_orcamento", "sem_resposta", "outro"]).nullish(),
});

/** Ação em lote sobre os leads marcados ou sobre todos os do filtro (até o limite). */
export const POST = rota({ escrita: true, corpo }, async ({ usuario, corpo }) => {
  let ids = corpo.ids ?? [];
  if (corpo.filtro) {
    const filtros = await lerFiltrosEquipe(usuario, corpo.filtro);
    const pagina = await buscarDeals(escopoDe(usuario, filtros), juntar(lerEtiquetas(corpo.filtro.f)), "padrao_leads", 0, CONFIG.limiteLote + 1);
    if (pagina.total > CONFIG.limiteLote) throw new ErroCRM("GS400", `O filtro tem ${pagina.total} leads. Selecione até ${CONFIG.limiteLote} por vez; refine o filtro.`);
    ids = pagina.linhas.map((d) => d.id);
  }
  return executarLote(usuario, corpo.tipo, ids, { tagId: corpo.tagId, texto: corpo.texto, motivo: corpo.motivo });
});
