import { z } from "zod";
import { rota } from "@/server/rota";
import { criarTag, listarTags } from "@/server/repositorio";

const corpo = z.object({ nome: z.string().min(1).max(31), cor: z.enum(["tag-1", "tag-2", "tag-3", "tag-4", "tag-5", "tag-6"]) });

export const GET = rota({}, async () => ({ tags: await listarTags() }));

/** Criar tag: manager e admin. */
export const POST = rota({ escrita: true, corpo }, async ({ usuario, corpo }) => criarTag(usuario, corpo.nome, corpo.cor));
