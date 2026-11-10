// Nota e ícone do deal, montados com os objetos de ui/ (barra única e etiqueta por significado).
import { fraseIcone, ROTULO_ICONE } from "@/lib/calculos";
import type { Icone } from "@/lib/tipos";
import { Etiqueta, type Tom } from "./ui/Etiqueta";
import type { NomeIcone } from "./ui/Icones";

export { BarraNota } from "./ui/BarraNota";

const VISUAL: Record<Icone, { tom: Tom; icone: NomeIcone }> = {
  super_hot: { tom: "destaque", icone: "chama" },
  em_risco: { tom: "atencao", icone: "alerta" },
  esfriou: { tom: "negativo", icone: "floco" },
};

/** Ícone do deal: super hot (destaque), em risco de esfriar (atenção) ou esfriou (negativo). Sempre com ícone e texto. */
export function IconeDeal({ icone, dias }: { icone: Icone | null; dias: number | null; comRotulo?: boolean }) {
  if (!icone) return null;
  const v = VISUAL[icone];
  return (
    <Etiqueta tom={v.tom} icone={v.icone} title={fraseIcone(icone, dias)}>
      {ROTULO_ICONE[icone]}
      <span className="sr-only">. {fraseIcone(icone, dias)}</span>
    </Etiqueta>
  );
}
