import { formatPct } from "../format";
import type { Fit } from "../types";

/** Um valor de fit (produto ou setor) com o suporte amostral que o
 * sustenta — nunca exibido sem o `n`, para que o número nunca pareça mais
 * sólido do que é (Requirement "Fit histórico do vendedor por produto e
 * por setor"). */
export function FitCell({ label, fit }: { label: string; fit: Fit }) {
  return (
    <div>
      <dt className="text-xs text-muted">{label}</dt>
      {fit.disponivel && fit.valor !== null ? (
        <dd className="text-sm font-semibold text-navy">
          {formatPct(fit.valor)}{" "}
          <span className="text-xs text-muted font-normal">(n={fit.n})</span>
        </dd>
      ) : (
        <dd className="text-sm text-muted italic">Indisponível — sem conta vinculada</dd>
      )}
    </div>
  );
}

/** Ressalva de ausência de significância estatística — DEVE ficar
 * fisicamente junto do número, nunca só em documentação externa
 * (Requirement "Declaração de ausência de significância estatística do
 * fit"). */
export function FitRessalva({ texto }: { texto: string }) {
  return <p className="text-xs text-muted italic mt-2">{texto}</p>;
}
