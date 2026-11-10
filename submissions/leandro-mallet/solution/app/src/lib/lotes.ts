// Ações em lote: rótulos, prazo do "Desfazer este lote" e quem enxerga cada lote. Funções puras.
import { plural } from "./calculos";
import type { LoteRecente, Usuario } from "./tipos";

export type TipoLote = "aplicar_tag" | "remover_tag" | "comentar" | "avancar_estagio" | "encerrar_perdido";

export const ROTULO_LOTE: Record<TipoLote, string> = {
  aplicar_tag: "Aplicar tag",
  remover_tag: "Remover tag",
  comentar: "Comentar",
  avancar_estagio: "Mover para Em negociação",
  encerrar_perdido: "Encerrar como perdido",
};

/** Prazo para desfazer um lote. O banco confere o mesmo prazo (parâmetro horas_desfazer_lote). */
export const HORAS_DESFAZER_LOTE = 24;
const PRAZO_MS = HORAS_DESFAZER_LOTE * 3_600_000;

/** Lote como vem da fonte dos dados (banco ou reserva), antes do recorte por perfil. */
export interface LoteBruto {
  id: number;
  tipo: TipoLote;
  usuarioId: number;
  criadoEm: string;
  aplicados: number;
  pulados: number;
  desfeitoEm: string | null;
  desfeitoPorId: number | null;
}

/** Quem vê (e pode desfazer) o lote: quem aplicou, o manager do time de quem aplicou e o admin. */
export function enxergaLote(u: Usuario, autor: Usuario | undefined, autorId: number): boolean {
  if (u.papel === "admin" || u.id === autorId) return true;
  return u.papel === "manager" && autor?.papel === "vendedor" && !!autor.manager && autor.manager === (u.manager ?? u.nome);
}

/** Lotes das últimas 24 horas que o perfil enxerga, do mais novo para o mais antigo. */
export function lotesRecentesPara(lotes: LoteBruto[], u: Usuario, usuarios: Usuario[], agora: number): LoteRecente[] {
  const porId = new Map(usuarios.map((x) => [x.id, x]));
  return lotes
    .filter((l) => agora - Date.parse(l.criadoEm) <= PRAZO_MS && enxergaLote(u, porId.get(l.usuarioId), l.usuarioId))
    .sort((a, b) => Date.parse(b.criadoEm) - Date.parse(a.criadoEm))
    .map((l) => ({
      id: l.id,
      tipo: l.tipo,
      rotulo: ROTULO_LOTE[l.tipo] ?? "Ação em lote",
      autor: porId.get(l.usuarioId)?.nome ?? "Outra pessoa",
      meu: l.usuarioId === u.id,
      criadoEm: l.criadoEm,
      desfazerAte: new Date(Date.parse(l.criadoEm) + PRAZO_MS).toISOString(),
      aplicados: l.aplicados,
      pulados: l.pulados,
      desfeitoEm: l.desfeitoEm,
      desfeitoPor: l.desfeitoPorId === null ? null : (porId.get(l.desfeitoPorId)?.nome ?? "Outra pessoa"),
    }));
}

/** Frase do aviso depois de desfazer um lote: quantas mudanças voltaram e quantas foram puladas. */
export function fraseLoteDesfeito(r: { restaurados: number; pulados: number }): string {
  const voltaram = plural(r.restaurados, "mudança desfeita", "mudanças desfeitas");
  if (!r.pulados) return `Lote desfeito: ${voltaram}.`;
  const ficaram = r.pulados === 1 ? "1 ficou como está, porque o lead mudou depois" : `${r.pulados} ficaram como estão, porque o lead mudou depois`;
  return `Lote desfeito: ${voltaram}; ${ficaram}.`;
}
