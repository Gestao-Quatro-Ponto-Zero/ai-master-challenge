import { Tooltip } from "./Tooltip";
import type { Confianca } from "../types";

const CONFIANCA_COLORS: Record<Confianca, string> = {
  A: "bg-navy text-white",
  B: "bg-navy/70 text-white",
  C: "bg-gray-300 text-navy",
  D: "bg-alert text-white",
};

/** Rótulo legível de CONFIANÇA (a letra vira complemento) com tooltip
 * próprio explicando a distinção "quanto se sabe, não a chance de
 * fechar" seguida da razão específica (Requirement "Rótulo e tooltip de
 * confiança"). Texto do rótulo e da razão vêm sempre da API. */
export function ConfidenceBadge({
  nivel,
  label,
  razao,
}: {
  nivel: Confianca;
  label: string;
  razao: string;
}) {
  return (
    <Tooltip
      content={
        <>
          <p className="font-semibold mb-1">
            CONFIANÇA mede o quanto se sabe sobre a oportunidade — não a chance de fechar.
          </p>
          <p>{razao}</p>
        </>
      }
    >
      <button
        type="button"
        className="inline-flex items-center gap-1.5 text-xs font-medium text-navy bg-transparent border-0 p-0 cursor-help"
      >
        <span
          className={
            "inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold shrink-0 " +
            CONFIANCA_COLORS[nivel]
          }
        >
          {nivel}
        </span>
        <span>{label}</span>
      </button>
    </Tooltip>
  );
}
