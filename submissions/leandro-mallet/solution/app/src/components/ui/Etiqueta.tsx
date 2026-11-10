// Etiqueta: uma forma só (pílula de 24 px), com o tom pelo significado.
//   neutro · atenção (em risco) · negativo (esfriou, queda) · positivo (alta) · destaque (super hot).
// A cor nunca é a única pista: sempre há texto, e ícone quando ajuda.
import type { ReactNode } from "react";
import { Icone, type NomeIcone } from "./Icones";

export type Tom = "neutro" | "atencao" | "negativo" | "positivo" | "destaque";

const TOM: Record<Tom, string> = {
  neutro: "bg-tom-neutro text-tom-neutro-texto",
  atencao: "bg-tom-atencao text-tom-atencao-texto",
  negativo: "bg-tom-negativo text-tom-negativo-texto",
  positivo: "bg-tom-positivo text-tom-positivo-texto",
  destaque: "bg-tom-destaque text-tom-destaque-texto",
};

export const classeEtiqueta = "inline-flex h-6 max-w-full shrink-0 items-center gap-1 rounded-selo px-2 text-xs font-semibold whitespace-nowrap";

export function Etiqueta({ tom = "neutro", icone, title, className = "", children }: { tom?: Tom; icone?: NomeIcone; title?: string; className?: string; children: ReactNode }) {
  return (
    <span title={title} className={`${classeEtiqueta} ${TOM[tom]} ${className}`}>
      {icone ? <Icone nome={icone} className="h-3.5 w-3.5" /> : null}
      <span className="truncate">{children}</span>
    </span>
  );
}

/** Etiqueta com botão de remover (filtros aplicados, tags do deal). */
export function EtiquetaRemovivel({ tom = "neutro", rotuloRemover, onRemover, className = "", children }: { tom?: Tom; rotuloRemover: string; onRemover: () => void; className?: string; children: ReactNode }) {
  return (
    <span className={`${classeEtiqueta} pr-0.5 ${TOM[tom]} ${className}`}>
      <span className="truncate">{children}</span>
      <button type="button" onClick={onRemover} aria-label={rotuloRemover} title={rotuloRemover} className="inline-flex h-5 w-5 items-center justify-center rounded-selo hover:bg-branco/60">
        <Icone nome="x" className="h-3 w-3" />
      </button>
    </span>
  );
}
