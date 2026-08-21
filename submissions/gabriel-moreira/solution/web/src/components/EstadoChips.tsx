import { ESTADO_CHIP_ATIVO } from "../estadoColors";
import { ESTADO_LABELS, type Estado } from "../types";

/** Filtro de ESTADO por seleção múltipla, restrito aos estados
 * trabalháveis (`revisao_lote` tem visão própria e não aparece aqui) —
 * nenhum selecionado significa os três trabalháveis. A contagem por chip
 * vem do envelope de `/deals` (nunca calculada no cliente), refletindo os
 * demais filtros ativos (Requirement "Filtro de estado"). */
export function EstadoChips({
  estados,
  selecionados,
  counts,
  onChange,
}: {
  estados: Estado[];
  selecionados: Estado[];
  counts: Partial<Record<Estado, number>>;
  onChange: (next: Estado[]) => void;
}) {
  function toggle(estado: Estado) {
    if (selecionados.includes(estado)) {
      onChange(selecionados.filter((e) => e !== estado));
    } else {
      onChange([...selecionados, estado]);
    }
  }

  return (
    <div className="flex flex-wrap gap-2" role="group" aria-label="Filtrar por estado">
      {estados.map((estado) => {
        const ativo = selecionados.includes(estado);
        return (
          <button
            key={estado}
            type="button"
            aria-pressed={ativo}
            onClick={() => toggle(estado)}
            className={
              "px-3 py-1.5 rounded-full text-sm font-semibold border transition-colors " +
              (ativo
                ? ESTADO_CHIP_ATIVO[estado]
                : "bg-white text-navy border-border hover:border-gold")
            }
          >
            {ESTADO_LABELS[estado]}
            <span className="ml-1.5 text-xs opacity-75">({counts[estado] ?? 0})</span>
          </button>
        );
      })}
    </div>
  );
}
