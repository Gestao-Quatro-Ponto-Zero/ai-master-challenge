import { useState } from "react";

/** Controles de paginação — anterior, próxima e ir para página N,
 * consumindo `page`/`total_pages`/`total` do envelope de `/deals`
 * (Requirement "Paginação da listagem"). */
export function PaginationControls({
  page,
  totalPages,
  onChange,
}: {
  page: number;
  totalPages: number;
  onChange: (page: number) => void;
}) {
  const [jumpValue, setJumpValue] = useState("");

  if (totalPages <= 1) return null;

  function jump(e: React.FormEvent) {
    e.preventDefault();
    const n = Number(jumpValue);
    if (Number.isInteger(n) && n >= 1 && n <= totalPages) {
      onChange(n);
      setJumpValue("");
    }
  }

  return (
    <div className="flex items-center gap-3 justify-center py-2">
      <button
        type="button"
        onClick={() => onChange(page - 1)}
        disabled={page <= 1}
        className="text-sm font-semibold text-navy border border-border rounded-xs px-3 py-1.5 disabled:opacity-40 hover:enabled:border-gold"
      >
        ← Anterior
      </button>
      <span className="text-sm text-muted">
        Página {page} de {totalPages}
      </span>
      <button
        type="button"
        onClick={() => onChange(page + 1)}
        disabled={page >= totalPages}
        className="text-sm font-semibold text-navy border border-border rounded-xs px-3 py-1.5 disabled:opacity-40 hover:enabled:border-gold"
      >
        Próxima →
      </button>
      <form onSubmit={jump} className="flex items-center gap-1.5 text-sm text-muted">
        <label htmlFor="ir-para-pagina">Ir para</label>
        <input
          id="ir-para-pagina"
          type="number"
          min={1}
          max={totalPages}
          value={jumpValue}
          onChange={(e) => setJumpValue(e.target.value)}
          className="w-16 border border-border rounded-xs px-2 py-1 text-navy"
        />
        <button type="submit" className="text-navy underline">
          Ir
        </button>
      </form>
    </div>
  );
}
