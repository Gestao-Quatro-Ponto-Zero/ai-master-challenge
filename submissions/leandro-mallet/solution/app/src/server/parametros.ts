import "server-only";
// Lê os parâmetros do link das telas (filtros) com validação. Nada do link é confiado sem conferir.
import { z } from "zod";
import type { ChaveEtiqueta, Etiqueta } from "@/lib/filtro/etiquetas";
import type { Usuario } from "@/lib/tipos";
import { listarEquipe } from "./repositorio";

const CHAVES: ChaveEtiqueta[] = [
  "estagios", "nota_min", "nota_max", "sem_nota", "icones", "abertura_de", "abertura_ate", "sem_abertura", "dias_aberto_min",
  "contato_ha_dias_min", "contato_ha_dias_max", "sem_contato", "sem_contato_principal", "setores", "portes", "sem_empresa",
  "empresas", "produtos", "series", "vendedores", "managers", "regioes", "acoes_sugeridas", "valor_min", "fechamento_de",
  "fechamento_ate", "tags", "sem_tag", "com_comentario", "contem",
];

const valor = z.union([z.string().max(120), z.number().finite(), z.boolean(), z.array(z.string().max(120)).max(50)]);
const esquema = z.array(z.tuple([z.enum(CHAVES as [ChaveEtiqueta, ...ChaveEtiqueta[]]), valor, z.string().max(160)])).max(30);

/** Etiquetas do filtro vindas do link (?f=). Link inválido = sem filtro. */
export function lerEtiquetas(f: string | undefined): Etiqueta[] {
  if (!f) return [];
  try {
    const lido = esquema.safeParse(JSON.parse(f));
    return lido.success ? lido.data.map(([chave, v, rotulo]) => ({ chave, valor: v as Etiqueta["valor"], rotulo })) : [];
  } catch {
    return [];
  }
}

export interface FiltrosEquipe {
  regiao?: string;
  manager?: string;
  vendedor?: string;
  opcoes: { regioes: string[]; managers: string[]; vendedores: string[] };
}

/** Filtros de região, manager e vendedor que o papel pode usar; valores fora do cadastro são ignorados. */
export async function lerFiltrosEquipe(u: Usuario, p: { regiao?: string; manager?: string; vendedor?: string }): Promise<FiltrosEquipe> {
  const equipe = await listarEquipe();
  const unicos = (l: string[]) => [...new Set(l)].sort();
  if (u.papel === "vendedor") return { opcoes: { regioes: [], managers: [], vendedores: [] } };
  if (u.papel === "manager") {
    const vendedores = unicos(equipe.filter((e) => e.manager === u.manager).map((e) => e.vendedor));
    return { vendedor: vendedores.includes(p.vendedor ?? "") ? p.vendedor : undefined, opcoes: { regioes: [], managers: [], vendedores } };
  }
  const regioes = unicos(equipe.map((e) => e.regiao));
  const regiao = regioes.includes(p.regiao ?? "") ? p.regiao : undefined;
  const managers = unicos(equipe.filter((e) => !regiao || e.regiao === regiao).map((e) => e.manager));
  const manager = managers.includes(p.manager ?? "") ? p.manager : undefined;
  const vendedores = unicos(equipe.filter((e) => (!regiao || e.regiao === regiao) && (!manager || e.manager === manager)).map((e) => e.vendedor));
  const vendedor = vendedores.includes(p.vendedor ?? "") ? p.vendedor : undefined;
  return { regiao, manager, vendedor, opcoes: { regioes, managers, vendedores } };
}
